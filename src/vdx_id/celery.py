##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

from __future__ import absolute_import

import os
import urllib

from celery import Celery

# from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vdx_id.settings")

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = os.environ.get("REDIS_PORT", 16379)

celery_broker_url = "redis://%s:%s/1" % (REDIS_HOST, REDIS_PORT)
celery_backend_url = "redis://%s:%s/2" % (REDIS_HOST, REDIS_PORT)
broker_url = "%s?" % (
    celery_broker_url,
)
backend_url = "%s?" % (
    celery_backend_url,
)

app = Celery("vdx_id", broker=broker_url, backend=backend_url)
app.config_from_object("vdx_id.settings", namespace="CELERY")
app.autodiscover_tasks()
