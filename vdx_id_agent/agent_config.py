##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging
import os
import ssl

logger = logging.getLogger("vdx_id.%s" % __name__)

CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = "UTC"
# CELERY_TIMEZONE = "Europe/Dublin"
TASK_SOFT_TIME_LIMIT = 10

CELERYD_HIJACK_ROOT_LOGGER = False

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = os.environ.get("REDIS_PORT", 16379)

CELERY_BROKER_URL = "redis://%s:%s/1" % (REDIS_HOST, REDIS_PORT)

CELERY_REDIS_MAX_CONNECTIONS = 5
BROKER_POOL_LIMIT = 1
BROKER_HEARTBEAT = None
BROKER_TRANSPORT_OPTIONS = {"max_connections": 30}
CELERY_IGNORE_RESULT = False
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_BACKEND = "redis://%s:%s/2" % (
    REDIS_HOST,
    REDIS_PORT,
)
CELERY_WORKER_MAX_TASKS_PER_CHILD = 50

CELERY_SEND_EVENTS = True
CELERY_TRACK_STARTED = True
CELERY_TASK_TRACK_STARTED = True

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
DJANGO_CELERY_BEAT_TZ_AWARE = False

COLLECTION_STORE_PARAMS = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "db": 3,
}

AGENT_KEY_DIR = "/data/agent_keys/"
AGENT_PRI_ENCKEY_PATH = os.path.join(AGENT_KEY_DIR, "private_key.pem")
AGENT_PUB_ENCKEY_PATH = os.path.join(AGENT_KEY_DIR, "public_key.pem")
