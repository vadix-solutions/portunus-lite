##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##
import logging

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.postgres import fields
from django.utils.dateparse import parse_datetime
from django.utils.timezone import get_default_timezone, make_aware
from django_json_widget.widgets import JSONEditorWidget

from id_infra.models.agent import AgentApiTask, AgentCeleryTask
from vdx_id.celery import app

from .models import (
    AccessHost,
    HostScanDefinition,
    ViAccessDomain,
    ViAgent,
    ViAgentInterface,
)

logger = logging.getLogger("vdx_id.%s" % __name__)


######
# Inlines
######
class TaskInline(GenericTabularInline):
    model = AgentApiTask
    readonly_fields = (
        "access_domain",
        "server_pks",
        "api_call",
        "tasks_complete",
        "tasks_successful",
        "updated",
    )
    show_change_link = True
    exclude = ("access_domain",)
    ordering = ("-updated",)
    extra = 0


class AccessHostInline(admin.TabularInline):
    model = AccessHost
    max_num = 0
    readonly_fields = (
        "address",
        "agent",
        "last_collection_id",
        "source_scan_definition",
        "access_domain",
    )
    exclude = ["collection_data", "collection_meta"]
    ordering = ("address",)
    show_change_link = True

    def has_add_permission(self, request):
        return False


class HostScanDefInlineAdmin(admin.TabularInline):
    model = HostScanDefinition
    max_num = 0
    readonly_fields = (
        "name",
        "description",
        "scan_definition",
        "access_domain",
    )
    can_delete = False
    exclude = [
        "scan_results",
        # "server_retire_time",
        # "scan_interval",
        "cleanse_hosts",
        "properties",
    ]


class AgentCeleryTaskInline(admin.TabularInline):
    model = AgentCeleryTask
    max_num = 0
    readonly_fields = (
        "task_id",
        "source_api_task",
        "state",
        "created",
        "updated",
    )
    can_delete = False
    show_change_link = True
    ordering = ("-updated",)
    exclude = ["exception"]


######
# Commands!
######
def run_collection(modeladmin, request, queryset):
    for accdom in queryset:
        accdom.request_collection()


def link_agent(modeladmin, request, queryset):
    for agent in queryset:
        logger.info(f"Attempting to link Agent: {agent}")
        result = app.signature(
            "vdx_id_agent.tasks.get_agent_metadata",
            args=(),
            queue=agent.queue_name,
        ).delay()
        result_output = result.get(timeout=10)
        logger.debug(f"Link Response ({result.status}): {result_output} ")
        if result.successful():
            agent.public_key = result_output["public_key"]
            agent.active = True
            agent.link_date = make_aware(
                parse_datetime(result_output["datestamp"]),
                timezone=get_default_timezone(),
            )
            agent.save()
        else:
            raise Exception(f"Agent not linked! {result.result}")


def scan_group(modeladmin, request, queryset):
    for sgroup in queryset:
        sgroup.perform_scan()


def mark_inactive(modeladmin, request, queryset):
    servers = []
    for server in queryset:
        server.active = False
        servers.append(server)
    AccessHost.objects.bulk_update(servers, ["active"])


scan_group.short_description = "Perform Scan"
mark_inactive.short_description = "Mark Inactive"
run_collection.short_description = "Collect Access Data"
link_agent.short_description = "Link Agent to Portunus"


######
# Access Domain
######
@admin.register(ViAccessDomain)
class ViAccessDomainAdmin(admin.ModelAdmin):
    formfield_overrides = {fields.JSONField: {"widget": JSONEditorWidget}}
    exclude = ()
    actions = [run_collection]
    list_display = ("name", "interface")
    readonly_fields = ("last_collection_id",)
    inlines = [TaskInline, AccessHostInline]
    list_filter = ("interface",)
    save_as = True
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "description",
                    "properties",
                    "owner",
                    "group_owner",
                )
            },
        ),
        (
            "AccessDomain Interfacing",
            {
                "classes": ("collapsible",),
                "fields": (
                    "interface",
                    "capabilities",
                    "account_template",
                    "access_item_template",
                ),
            },
        ),
        (
            "AccessDomain Collection",
            {
                "classes": ("collapsible",),
                "fields": (
                    "enable_access_sync",
                    "user_source_authority",
                    "user_account_mapping",
                    "manager_attribute",
                    "last_collection_id",
                    "collection_meta",
                ),
            },
        ),
    )


######
# Servers
######
@admin.register(AccessHost)
class AccessHostAdmin(admin.ModelAdmin):
    read_only_fields = ("created", "updated", "active", "last_collection_id")
    list_display = (
        "address",
        "agent",
        "access_domain",
        "source_scan_definition",
        "created",
        "updated",
        "active",
        "writable",
    )
    list_filter = ("agent", "access_domain", "active", "writable")
    actions = [mark_inactive]
    formfield_overrides = {fields.JSONField: {"widget": JSONEditorWidget}}
    exclude = ()

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related("source_scan_definition")
        return queryset


@admin.register(HostScanDefinition)
class HostScanDefinitionAdmin(admin.ModelAdmin):
    read_only_fields = ("scanning_agent", "description")
    list_filter = ("scanning_agent",)
    list_display = ("name", "scanning_agent", "description")
    formfield_overrides = {fields.JSONField: {"widget": JSONEditorWidget}}
    inlines = [TaskInline, AccessHostInline]
    exclude = ["scan_results"]
    actions = [scan_group]
    save_as = True


######
# Agent
######
@admin.register(ViAgent)
class ViAgentAdmin(admin.ModelAdmin):
    inlines = [HostScanDefInlineAdmin]
    list_display = ("agent_name", "active", "link_date")
    readonly_fields = ("public_key", "active", "link_date")
    actions = [link_agent]


@admin.register(ViAgentInterface)
class ViAgentInterfaceAdmin(admin.ModelAdmin):
    list_display = ("interface_id", "code_fingerprint")
    formfield_overrides = {fields.JSONField: {"widget": JSONEditorWidget}}
    save_as = True


######
# Agent Tasks
######
@admin.register(AgentApiTask)
class AgentApiTaskAdmin(admin.ModelAdmin):
    inlines = [AgentCeleryTaskInline]
    list_display = (
        "api_call",
        "access_domain",
        "tasks_complete",
        "tasks_successful",
        "updated",
        "created",
    )
    list_filter = (
        "access_domain",
        "api_call",
        "tasks_complete",
        "tasks_successful",
    )
    readonly_fields = (
        "api_call",
        "access_domain",
        "tasks_complete",
        "tasks_successful",
        "updated",
        "created",
    )
    exclude = ("content_type", "object_id")


@admin.register(AgentCeleryTask)
class AgentCeleryTaskAdmin(admin.ModelAdmin):
    list_display = (
        "task_id",
        "source_api_task",
        "state",
        "created",
        "updated",
    )
    readonly_fields = ("task_id", "source_api_task", "exception")
    list_filter = ("state",)
