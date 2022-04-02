##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging
from time import strftime

from celery import chord
from celery.utils import uuid
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext as _
from simple_history.models import HistoricalRecords

from id_infra.models.agent import AgentTaskMixin, ViAgent, ViAgentInterface
from vdx_id.celery import app
from vdx_id.mixins.vault import VaultRotatingPasswordAccDomMixin
from vdx_id.models import VdxIdUser

logger = logging.getLogger("vdx_id.%s" % __name__)


class NoAvailableAgentException(Exception):
    """Thrown if no agents are available for a command"""

    pass


class ViAccessDomain(
    AgentTaskMixin, VaultRotatingPasswordAccDomMixin, models.Model
):
    """A logical group of infrastructure.
    Comprised of InfraServers bound to an Agent.
    The Agent Interface is set in the InfraGroup, but the agent is set by
    the InfraServer."""

    help_text = _("An AccessDomain is an access-homogeneous set of hosts.")

    # Task used to trigger a collection against all accounts
    collection_task_sig = "id_infra.tasks.read_infra"

    # Metadata
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(default="")

    interface = models.ForeignKey(
        ViAgentInterface,
        on_delete=models.PROTECT,
        related_name="access_domains",
    )

    properties = JSONField(
        blank=True,
        default=dict,
        help_text="Access Domain properties (configure behaviour)",
    )
    capabilities = JSONField(
        blank=True,
        default=dict,
        help_text="A mapping of capability->interface_function",
    )

    last_collection_id = models.CharField(
        max_length=100, null=True, blank=True
    )
    collection_meta = JSONField(
        default=dict,
        blank=True,
        help_text="Metadata about collections (historic)",
    )

    owner = models.ForeignKey(
        VdxIdUser,
        on_delete=models.PROTECT,
        related_name="owned_access_domains",
    )
    group_owner = models.ForeignKey(
        Group,
        related_name="owned_access_domains",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    history = HistoricalRecords()
    capability_category = "access_domain"

    class Meta:
        verbose_name = "Access Domain"
        verbose_name_plural = "Access Domains"

    def clean(self):
        if self.user_source_authority:
            if not self.user_account_mapping:
                raise ValidationError("User-Account Mapping must be defined")
            elif "{username}" not in self.user_account_mapping:
                raise ValidationError(
                    "User-Account mapping must contain '{username}'"
                )
            self.account_template = None
            self.access_item_template = None

    def __str__(self):
        return self.name

    @property
    def vault_path(self):
        return f"/access_domains/{self.pk}/"

    @property
    def access_domain(self):
        """Interesting workaround for arg referencing working.
        Account needs accdom.vault.pass to work
        So does AccessDomain but both share capabilities"""
        return self

    @property
    def vault_secret(self):
        return self.get_vault_secret()

    @property
    def active_hosts(self):
        return self.hosts.filter(active=True)

    def set_vault_secret_dict(self, sdict):
        return self.write_secret_dict(self.vault_path, sdict)

    def get_vault_secret(self):
        return self.read_secret(self.vault_path)

    def get_collection_id(self):
        coll_id = "COLL_AD%s_%s" % (self.id, strftime(settings.COLL_TSTAMP))
        logger.debug("Created Collection ID: %s" % coll_id)
        return coll_id

    def request_collection(self):
        coll_id = self.get_collection_id()
        agent_api_task, mapped_args = self.generate_capability_task(
            self, "collect", {"collection_id": coll_id}
        )

        collection_tasks = agent_api_task.generate_celery_tasks(
            self, mapped_args
        )
        task_uuids = [task["options"]["task_id"] for task in collection_tasks]

        # consol_sig
        consolidate_uuid = uuid()
        task_uuids.append(consolidate_uuid)

        s_consolidate = app.signature(
            "consolidate_collections",
            args=(coll_id, self.id),
            immutable=True,
            options=({"task_id": consolidate_uuid}),
        ).set(queue="platform")
        # We have to create a separate signature so they don't circular ref
        s_consolidate_err = app.signature(
            "consolidate_collections", args=(coll_id, self.id), immutable=True
        ).set(queue="platform")

        collection_chain = chord(
            collection_tasks, s_consolidate.on_error(s_consolidate_err)
        )
        collection_chain.apply_async()
        # Add a task for tracking the consolidation
        agent_api_task.link_celery_tasks(task_uuids)

        return agent_api_task

    def yield_agent_server_sets(self, server_pks=None):
        """Yields (Agent, [Servers]) for all servers in the access domain"""
        # Get all active servers
        server_filter = {"active": True}
        if server_pks:
            server_filter["pk__in"] = server_pks

        access_hosts = self.hosts.filter(**server_filter).prefetch_related(
            "agent"
        )
        # Raise Error if no servers exist for an AccessDomain
        if not access_hosts.exists():
            logger.warning(f"{self} has no active hosts")

        # Get all unique agents associated with infra servers
        distinct_agent_ids = access_hosts.distinct("agent").values_list(
            "agent", flat=True
        )
        server_agents = ViAgent.objects.filter(pk__in=distinct_agent_ids)

        for agent in server_agents:
            agent_servers = access_hosts.filter(agent=agent)
            yield agent, agent_servers

    def get_api_param_dicts(self, api_call):
        """Returns two dictionaries of arguments for an API call.
        arg_d are Args(required)
        kwarg_d are Kwargs(Optional)"""
        wo_args, wo_kwargs = self.interface.get_apicall_args_kwargs(api_call)
        # Convert api-call args/kwargs into dicts for handling
        arg_d = {k: None for k in wo_args}
        kwarg_d = {k: None for k in wo_kwargs}
        return arg_d, kwarg_d

    def get_capability(self, category, capname):
        # TODO: Add docstring
        # TODO: Remove boilerplate username: name mappings
        assert (
            category in self.capabilities.keys()
        ), f"Capability category {category} is not defined"
        assert (
            capname in self.capabilities[category].keys()
        ), f"Capability name {capname} is not defined"
        # Now attempt to retrieve capabilities
        capdef = self.capabilities[category][capname]
        if len(capdef.keys()) != 1:
            raise KeyError("Capability should have one command only")
        iface_call = list(capdef.keys())[0]
        call_mapped_args = capdef[iface_call]
        # Merge it with DEFAULT
        default_mapped_args = self.capabilities.get("DEFAULT", {})
        call_mapped_args.update(default_mapped_args)
        # Return the interface call and mapped arguments
        return iface_call, call_mapped_args
