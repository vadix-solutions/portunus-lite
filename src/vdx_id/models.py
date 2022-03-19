##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

"""
Mixins for Portunus models
"""
import logging

from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.postgres.fields import JSONField
from django.db import models
from simple_history.models import HistoricalRecords

logger = logging.getLogger("vdx_id.%s" % __name__)


class VdxIdUserManager(UserManager):
    pass


class VdxIdUser(AbstractUser):
    """Custom UserModel to handle auth and special functionality"""

    first_name = models.CharField(
        "First Name of User", blank=True, max_length=20
    )
    last_name = models.CharField(
        "Last Name of User", blank=True, max_length=20
    )

    manager = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True
    )
    properties = JSONField(default=dict, blank=True)

    access_synchronized = models.BooleanField(default=True)
    history = HistoricalRecords()

    class Meta:
        permissions = (("auth_admin", "User can alter all auth"),)

    def mark_out_of_sync(self):
        self.access_synchronized = False
        self.save(update_fields=["access_synchronized"])


class VaultPasswordPolicy(models.Model):
    policy_name = models.CharField(max_length=250)

    def __str__(self):
        return self.policy_name

    @property
    def policy_path(self):
        return f"sys/policies/password/{self.policy_name}/generate"
