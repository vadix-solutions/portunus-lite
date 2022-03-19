##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging
import os
from datetime import timedelta

import hvac
from django.conf import settings
from django.db import models
from django.utils import timezone

logger = logging.getLogger("vdx_id.%s" % __name__)

VAULT_CLIENT = None


class MissingSecretException(Exception):
    pass


class VaultMixin(object):
    """Mixin to give an object access to the configured HC Vault"""

    def init_client(self):
        global VAULT_CLIENT
        assert "VAULT_TOKEN" in os.environ
        VAULT_CLIENT = hvac.Client(
            url=settings.VAULT_HOST, token=os.environ["VAULT_TOKEN"]
        )

    @property
    def _vault_client(self):
        if VAULT_CLIENT is None:
            self.init_client()
        return VAULT_CLIENT

    @property
    def _kv_vault_client(self):
        return self._vault_client.secrets.kv.v1

    def read_secret(self, path, **kwargs):
        try:
            res = self._kv_vault_client.read_secret(
                mount_point=settings.VAULT_SECRET_MOUNT, path=path, **kwargs
            )
            logger.info(f"Read response: {res}")
            return res["data"]
        except hvac.exceptions.InvalidPath as exc:
            raise hvac.exceptions.InvalidPath(
                f"Secret has not been set on {self}: {exc}"
            )

    def write_secret_dict(self, path, secret_dict):
        assert type(secret_dict) == dict
        res = self._kv_vault_client.create_or_update_secret(
            mount_point=settings.VAULT_SECRET_MOUNT,
            path=path,
            secret=secret_dict,
        )
        logger.info(f"Write response: {res}")
        return res


class VaultRotatingPasswordAccDomMixin(models.Model, VaultMixin):
    """Mixin for objects which should have rotating passwords"""

    rotate_password_policy = models.ForeignKey(
        "vdx_id.VaultPasswordPolicy",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The Vault password policy to use for this object",
    )
    rotate_password_interval = models.DurationField(default=timedelta(days=90))
    passwords_last_rotated = models.DateTimeField(
        auto_created=True, default=timezone.now
    )

    class Meta:
        abstract = True

    def _generate_vault_password(self):
        request = self._vault_client.read(
            self.rotate_password_policy.policy_path
        )
        return request["data"]
