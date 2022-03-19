##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

from action_serializer import ModelActionSerializer
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_extensions.fields import ResourceUriField

from id_infra.models.agent import AgentApiTask, AgentCeleryTask

from .models import (
    AccessHost,
    HostScanDefinition,
    ViAccessDomain,
    ViAgent,
    ViAgentInterface,
)

logger = logging.getLogger("vdx_id.%s" % __name__)


class ChangeSecretSerializer(serializers.Serializer):
    model = ViAccessDomain

    """
    Serializer for password change endpoint.
    """
    secret = serializers.JSONField()

    def validate(self, data):
        """Check secret is valid.. somehow?"""
        # if data["password"] != data["confirm_password"]:
        #     raise serializers.ValidationError("Passwords must match")
        return data


class ViAccessDomainSerializer(ModelActionSerializer):
    # TODO: Add Api task list
    url = ResourceUriField(
        view_name="api:id_infra:access_domain-detail", read_only=True
    )
    interface = serializers.SlugRelatedField(
        queryset=ViAgentInterface.objects.all(),
        many=False,
        read_only=False,
        slug_field="interface_id",
    )
    api_tasks = serializers.SerializerMethodField()

    def get_api_tasks(self, obj):
        return reverse(
            "api:id_infra:access_domain-apitasks-list",
            kwargs={"parent_lookup_object_id": obj.id},
            request=self.context["request"],
        )

    class Meta:
        model = ViAccessDomain
        fields = ("url", "name", "description", "api_tasks", "interface")
        read_only_fields = ()


class AccessHostSerializer(ModelActionSerializer):
    url = ResourceUriField(
        view_name="api:id_infra:server-detail", read_only=True
    )
    server_name = serializers.SerializerMethodField()
    created = serializers.DateTimeField()
    last_seen = serializers.DateTimeField(source="updated")

    def get_server_name(self, obj):
        return obj.__str__()

    class Meta:
        model = AccessHost
        fields = (
            "url",
            "address",
            "source_scan_definition",
            "agent",
            "created",
            "last_seen",
            "collection_data",
        )
        action_fields = {
            "list": {
                "fields": (
                    "url",
                    "address",
                    "server_name",
                    "agent",
                    "created",
                    "last_seen",
                )
            }
        }


class HostScanDefSerializer(ModelActionSerializer):
    url = ResourceUriField(
        view_name="api:id_infra:servergroup-detail", read_only=True
    )

    active_host_count = serializers.SerializerMethodField()
    host_count = serializers.SerializerMethodField()
    hosts = serializers.SerializerMethodField()

    def get_hosts(self, obj):
        return reverse(
            "api:id_infra:scan_group-hosts-list",
            kwargs={"parent_lookup_source_scan_definition_id": obj.id},
            request=self.context["request"],
        )

    def get_host_count(self, obj):
        return obj.hosts.count()

    def get_active_host_count(self, obj):
        return obj.hosts.filter(active=True).count()

    class Meta:
        model = HostScanDefinition
        fields = (
            "pk",
            "url",
            "name",
            "description",
            "hosts",
            "host_count",
            "active_host_count",
            "scan_definition",
        )
        action_fields = {
            "list": {
                "fields": (
                    "url",
                    "name",
                    "hosts",
                    "host_count",
                    "active_host_count",
                )
            }
        }


class ViAgentSerializer(ModelActionSerializer):
    url = ResourceUriField(
        view_name="api:id_infra:agent-detail", read_only=True
    )

    class Meta:
        model = ViAgent
        fields = ("pk", "url", "agent_name", "description", "active")
        read_only_fields = ("active",)


class ViAgentInterfaceSerializer(ModelActionSerializer):
    url = ResourceUriField(
        view_name="api:id_infra:agent_iface-detail", read_only=True
    )

    class Meta:
        model = ViAgentInterface
        fields = (
            "url",
            "interface_id",
            "default_capabilities",
            "task_signature",
            "api",
            "code_fingerprint",
            "date_updated",
        )
        action_fields = {
            "list": {
                "fields": (
                    "url",
                    "interface_id",
                    "code_fingerprint",
                    "date_updated",
                )
            }
        }


class AgentCeleryTaskSerializer(ModelActionSerializer):
    url = ResourceUriField(
        view_name="api:id_infra:agent_celerytask-detail", read_only=True
    )
    # TODO: Convert state to string value

    class Meta:
        model = AgentCeleryTask
        fields = ("task_id", "state", "created", "updated")


class AgentApiTaskSerializer(ModelActionSerializer):
    url = ResourceUriField(
        view_name="api:id_infra:agent_apitask-detail", read_only=True
    )
    access_domain = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    celery_task_list = serializers.SerializerMethodField()

    def get_celery_task_list(self, obj):
        tasks = AgentCeleryTask.objects.filter(source_api_task=obj)
        serializer = AgentCeleryTaskSerializer(instance=tasks, many=True)
        return serializer.data

    class Meta:
        model = AgentApiTask
        fields = (
            "url",
            "api_call",
            "access_domain",
            "tasks_complete",
            "tasks_successful",
            "celery_task_list",
            "created",
            "updated",
        )
        action_fields = {
            "list": {
                "fields": (
                    "url",
                    "api_call",
                    "access_domain",
                    "tasks_complete",
                    "tasks_successful",
                    "created",
                )
            }
        }
