##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##
import logging
import math

from asgiref.sync import async_to_sync
from constance import config
from django.conf import settings
from django.db.models import signals as db_signal
from django.dispatch import Signal, receiver

from id_infra.models import ViAccessDomain
from id_infra.models.agent import AgentApiTask
from vdx_id.celery import app
from vdx_id.util.task_util import chunks
from web_interface.consumers import get_channel

logger = logging.getLogger("vdx_id.%s" % __name__)

access_domain_collected = Signal(providing_args=["pk", "collection_id"])


@receiver(db_signal.pre_save, sender=ViAccessDomain)
def suggest_rule_reviewer(sender, instance, **kwargs):
    if not instance.capabilities:
        instance.capabilities = instance.interface.default_capabilities.copy()


@receiver(db_signal.post_save, sender=AgentApiTask)
def auto_run_collect(sender, instance, **kwargs):
    logger.debug(f"Evaluating auto-collect for {instance}")
    if type(instance.content_object) is ViAccessDomain:
        return
    if instance.access_domain is None:
        # Don't run if AccDom not defined, or if the task was from an AccDom!
        return

    logger.debug("Type: %s" % type(instance.content_object))
    pending_adom_tasks = AgentApiTask.objects.filter(
        access_domain=instance.access_domain, tasks_complete=False
    )
    if pending_adom_tasks.exists():
        logger.debug("Not collecting - pending tasks for access domain")
        logger.debug(pending_adom_tasks)
        return
    else:
        read_sig = app.signature(
            "id_infra.tasks.read_infra", args=(instance.access_domain.pk,)
        )
        logger.info("Queueing automatic collection")
        read_sig.apply_async(
            countdown=settings.AUTO_COLLECT_COUNTDOWN,
            task_id=f"collect-task-{instance.access_domain.id}",
        )


@receiver(db_signal.post_save, sender=AgentApiTask)
def ws_notifications_for_api_task(sender, instance, created=False, **kwargs):
    tasks_complete = instance.tasks_complete

    channel_layer_name = "notifications"
    channel = get_channel()
    map_locations = config.MAP_COORDINATES

    heading = None
    style = "info"
    accdom_part = ""
    if instance.access_domain:
        accdom_part = f" on {instance.access_domain}"
    if created:
        text = f"Running ({instance.api_call}){accdom_part}"
    # elif tasks_complete:
    #     text = f"Completed ({instance.api_call}){accdom_part}"
    #     style = "success"

    # if created or tasks_complete:
    if created:
        async_to_sync(channel.group_send)(
            channel_layer_name,
            {
                "type": "notification",
                "style": style,
                "heading": heading,
                "icon": "",
                "text": text,
            },
        )

    # Generate map updates (if you have an access_domain)
    if instance.access_domain is None:
        return

    map_flows = {}
    flowback_apicalls = ["collect_access"]

    portunus_loc = map_locations.get("PORTUNUS")
    agent_server_gen = instance.access_domain.yield_agent_server_sets(
        server_pks=instance.server_pks
    )

    map_flows[instance.pk] = []

    for agent, agent_servers in agent_server_gen:
        agent_loc = map_locations.get(f"AGENT_{agent.pk}")
        # Create the Portunus -> Agent flow
        if created:
            map_flows[instance.pk] += [
                {
                    "from": portunus_loc,
                    "to": agent_loc,
                    "labels": ["PORTUNUS", agent.agent_name],
                    "color": "#4076e3",
                    "value": 1,
                }
            ]
        # Create the Agent -> Portunus flow
        elif tasks_complete and instance.api_call in flowback_apicalls:
            map_flows[instance.pk] += [
                {
                    "from": agent_loc,
                    "to": portunus_loc,
                    "labels": [agent.agent_name, "PORTUNUS"],
                    "color": "#36c943",
                    "value": len(agent_servers),
                }
            ]

        # Create the Agent -> Servers -> Agent flows
        else:
            accdom_loc = map_locations.get(
                f"ACCESS_DOMAIN_{instance.access_domain.pk}"
            )
            if not accdom_loc:
                logger.warning(
                    f"No AccessDomain LOC: {instance.access_domain.pk}"
                )
                continue
            servers_per_chunk = -(
                instance.access_domain.active_hosts.count()
                // -settings.AGENT_TASK_SEGMENTATION
            )
            circ_radius = float(servers_per_chunk) / 50
            arc_seg = (math.pi * 2) / settings.AGENT_TASK_SEGMENTATION
            for idx, server_chunk in enumerate(
                chunks(agent_servers, servers_per_chunk)
            ):
                server_loc = list(accdom_loc)
                server_loc[0] += circ_radius * math.sin(arc_seg * idx)
                server_loc[1] += circ_radius * math.cos(arc_seg * idx)

                map_flows[instance.pk] += [
                    {
                        "from": agent_loc,
                        "to": server_loc,
                        "labels": [agent.agent_name],
                        "color": "#3a3aA1",
                        "value": 1,
                    },
                    {
                        "from": server_loc,
                        "to": agent_loc,
                        "labels": [
                            ",".join([serv.address for serv in server_chunk])
                        ],
                        "color": "#40e3b2",
                        "value": 1,
                    },
                ]

        async_to_sync(channel.group_send)(
            channel_layer_name, {"type": "map_update", "flows": map_flows}
        )
