"""Celery Monitor Camera
Monitors the progress of tasks on the messagebus
Will update AgentCeleryTask objects (the children of AgentApiTasks)
Will also send notifications on the messagebus
"""

import logging
import os
import urllib

import django
from asgiref.sync import async_to_sync
from celery import Celery
from django.db.models.functions import Now

from vdx_id import settings
from web_interface.consumers import get_channel

os.environ["DJANGO_SETTINGS_MODULE"] = "vdx_id.settings"
django.setup()

from id_infra.models.agent import AgentCeleryTask  # noqa: E402
from id_infra.models.agent import CeleryTaskMetaState  # noqa: E402

logger = logging.getLogger("vdx_id.%s" % __name__)


def my_monitor(app):
    state = app.events.State()

    def send_channel_message(**packet_kwargs):
        channel_layer_name = "notifications"
        channel = get_channel()

        # This will only send the task id/state
        # The frontend requires a mapping of api-tasks/celery-tasks
        #    in order to render updates properly
        async_to_sync(channel.group_send)(channel_layer_name, packet_kwargs)

    def update_celery_task(event):
        state.event(event)
        # TODO: Filter some of the tasks here - reduce excessive sends

        # task name is sent only with -received event, and state
        # will keep track of this for us.
        if "uuid" in event and "state" in event:
            task_id = event["uuid"]
            task = AgentCeleryTask.objects.filter(task_id=task_id)

            task_state = event["state"]
            if hasattr(CeleryTaskMetaState, task_state):
                new_state = CeleryTaskMetaState.lookup(task_state)
                task.update(state=new_state, updated=Now())
            if task_state == "FAILURE":
                task.update(exception=event["exception"], updated=Now())
            # send_channel_message(
            #     task_id=task_id, task_state=task_state, type="task_update"
            # )
        else:
            task = None
            logger.debug(f"Other event {event} {task}")

    def update_agents(event):
        # TODO: Register Agents here
        logger.info(f"A worker is online: {event}")

    def agent_heartbeat(event):
        # TODO: Keep Agents active here
        logger.debug(f"Heard a worker heartbeat: {event}")

    with app.connection() as connection:
        recv = app.events.Receiver(
            connection,
            handlers={
                "worker-online": update_agents,
                "worker-heartbeat": agent_heartbeat,
                "*": update_celery_task,
            },
        )
        recv.capture(limit=None, timeout=None, wakeup=True)


def create_celery_app():
    celery_broker_url = "redis://%s:%s/1" % (
        settings.REDIS_HOST,
        settings.REDIS_PORT,
    )
    celery_backend_url = "redis://%s:%s/2" % (
        settings.REDIS_HOST,
        settings.REDIS_PORT,
    )
    broker_url = "%s?" % (
        celery_broker_url,
    )
    backend_url = "%s?" % (
        celery_backend_url,
    )

    # logger.info("Broker(%s) Backend(%s)" % (broker_url, backend_url))
    app = Celery("vdx_id", broker=broker_url, backend=backend_url)
    app.config_from_object(settings, namespace="CELERY")
    return app


if __name__ == "__main__":
    app = create_celery_app()
    my_monitor(app)
