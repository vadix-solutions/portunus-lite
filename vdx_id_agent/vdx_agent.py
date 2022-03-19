##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

from __future__ import absolute_import

import logging
import urllib

from celery import Celery
from celery._state import _set_current_app
from celery.app.log import TaskFormatter

from . import agent_config
from .agent_crypto import prepare_keys

logger = logging.getLogger()
sh = logging.StreamHandler()
sh.setFormatter(
    TaskFormatter(
        "%(asctime)s - %(task_id)s - %(task_name)s -\
 %(name)s - %(levelname)s - %(message)s"
    )
)
logger.setLevel(logging.DEBUG)
logger.addHandler(sh)

# https://docs.celeryproject.org/en/latest/userguide/tasks.html#changing-the-automatic-naming-behavior
# https://medium.com/@taylorhughes/three-quick-tips-from-two-years-with-celery-c05ff9d7f9eb


celery_broker_url = "redis://%s:%s/1" % (
    agent_config.REDIS_HOST,
    agent_config.REDIS_PORT,
)
celery_backend_url = "redis://%s:%s/2" % (
    agent_config.REDIS_HOST,
    agent_config.REDIS_PORT,
)
broker_url = "%s" % (
    celery_broker_url,
)
backend_url = "%s" % (
    celery_backend_url,
)

agent = Celery(
    "vdx_id_agent",
    # include=get_task_dirs(),
    include=["vdx_id_agent.tasks"],
    broker=broker_url,
    backend=backend_url,
)
agent.config_from_object(agent_config, namespace="CELERY")
_set_current_app(agent)
prepare_keys()
