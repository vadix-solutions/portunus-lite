##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

from constance import config
from django.apps import AppConfig
from django.utils.module_loading import import_string

from vdx_id.celery import app

logger = logging.getLogger("vdx_id.%s" % __name__)


class PortunusConfig(AppConfig):
    name = "vdx_id"
    verbose_name = "VaDiX Portunus Lite"

    def ready(self):
        pass
