##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

import django_filters
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.http.response import HttpResponseRedirect
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

from id_infra.models.agent import (
    AgentApiTask,
    AgentCeleryTask,
    ViAgent,
    ViAgentInterface,
)
from id_infra.serializers import ChangeSecretSerializer
from vdx_id.api_renderers import VdxIdApiRenderer
from vdx_id.mixins.drf import ActionMapping
from vdx_id.mixins.serializers import GetSerializerClassMixin
from vdx_id.permissions import (
    IsAdminOrOwner,
    IsPortunusAccessManager,
    IsPortunusAdmin,
    IsUser,
    ReadOnly,
)

from .models import AccessHost, HostScanDefinition, ViAccessDomain
from .serializers import (
    AccessHostSerializer,
    AgentApiTaskSerializer,
    AgentCeleryTaskSerializer,
    HostScanDefSerializer,
    ViAccessDomainSerializer,
    ViAgentInterfaceSerializer,
    ViAgentSerializer,
)

logger = logging.getLogger("%s" % __name__)


class AccessDomainViewSet(
    NestedViewSetMixin, GetSerializerClassMixin, ActionMapping, ModelViewSet
):
    """
    Access Domains: A collection of servers with consistent accounts/items.
    """

    queryset = ViAccessDomain.objects.all()
    serializer_class = ViAccessDomainSerializer
    permission_classes = [IsAdminOrOwner]

    renderer_classes = (JSONRenderer, VdxIdApiRenderer)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    permission_classes = (IsPortunusAccessManager | ReadOnly | IsUser,)
    http_method_names = ["get", "head", "options"]

    @action(
        methods=["get"],
        detail=True,
        permission_classes=[IsPortunusAccessManager],
    )
    def collect(self, request, pk=None):
        """Request a collection of a AccessDomain."""
        accdom = ViAccessDomain.objects.get(id=int(pk))
        logger.info("Requesting collection for %s" % accdom)

        agent_api_task = accdom.request_collection()
        return HttpResponseRedirect(agent_api_task.get_absolute_url())

    @action(
        methods=["get"],
        detail=True,
        permission_classes=[IsPortunusAccessManager],
    )
    def scan(self, request, pk=None):
        """Request a network-scan for associated HostScanDefs."""
        accdom = ViAccessDomain.objects.get(id=int(pk))
        logger.info("Requesting scan for %s" % accdom)

        scan_res = {}
        for host_scan in accdom.scan_definitions.all():
            api_task = host_scan.perform_scan()
            scan_res[host_scan.name] = api_task.get_absolute_url()
        return JsonResponse(scan_res)

    @action(
        methods=["post"],
        detail=True,
        name="Set Secret",
        serializer_class=ChangeSecretSerializer,
        permission_classes=[IsPortunusAdmin],
    )
    def set_secret(self, request, pk, *args, **kwargs):
        """Update the access domain secrets"""
        serializer = ChangeSecretSerializer(data=request.data)
        if serializer.is_valid() and serializer.validate(request.data):
            access_domain = ViAccessDomain.objects.get(pk=pk)
            access_domain.set_vault_secret_dict(
                serializer.validated_data["secret"]
            )
            return Response(
                {"message": "Secret Updated successfully"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=["get"],
        detail=True,
        name="Get Secret",
        permission_classes=[IsPortunusAdmin],
    )
    def get_secret(self, request, pk, *args, **kwargs):
        """Get the vault secret for this account"""
        access_domain = ViAccessDomain.objects.get(pk=pk)
        return JsonResponse(access_domain.get_vault_secret())

    @action(
        methods=["post"], detail=True, permission_classes=[IsPortunusAdmin]
    )
    def attach_servers(self, request, pk=None):
        """Submit an array of server pks to be assigned to this igrp."""
        logger.info("Attaching Servers to pk:%s" % pk)
        access_domain = ViAccessDomain.objects.get(pk=pk)
        logger.info("Attaching Servers: %s" % access_domain)
        server_pks = [int(s) for s in request.data.get("server_pks")]
        logger.info("Attaching Servers %s to igrp_pk=%s" % (server_pks, pk))

        server_set = AccessHost.objects.filter(pk__in=server_pks)
        logger.info("Attaching Servers %s" % (server_set))

        server_set.update(access_domain=access_domain)

        return JsonResponse({"success": "%s" % server_pks})


class HostViewSet(NestedViewSetMixin, ModelViewSet):
    """
    Hosts discovered by Portunus Agents
    """

    queryset = AccessHost.objects.all()
    serializer_class = AccessHostSerializer
    renderer_classes = (JSONRenderer, VdxIdApiRenderer)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    permission_classes = [IsPortunusAccessManager]
    http_method_names = ["get", "head", "retrieve", "options"]


class HostScanDefViewSet(
    NestedViewSetMixin, GetSerializerClassMixin, ActionMapping, ModelViewSet
):
    """
    Host-scan definitions
    """

    queryset = HostScanDefinition.objects.all()
    serializer_class = HostScanDefSerializer
    renderer_classes = (JSONRenderer, VdxIdApiRenderer)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    permission_classes = [IsPortunusAccessManager]
    http_method_names = ["get", "head", "retrieve", "options"]

    @action(
        methods=["get"],
        detail=True,
        permission_classes=[IsPortunusAccessManager],
    )
    def scan(self, request, pk=None):
        hostscandef = HostScanDefinition.objects.get(id=int(pk))
        logger.info("Requesting host-scan for %s" % hostscandef)

        task = hostscandef.perform_scan()
        return HttpResponseRedirect(task.get_absolute_url())


class ViAgentViewSet(ReadOnlyModelViewSet):
    queryset = ViAgent.objects.all()
    serializer_class = ViAgentSerializer
    renderer_classes = (JSONRenderer, VdxIdApiRenderer)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    permission_classes = [IsPortunusAccessManager]


class ViAgentInterfaceViewSet(ReadOnlyModelViewSet):
    queryset = ViAgentInterface.objects.all()
    serializer_class = ViAgentInterfaceSerializer
    renderer_classes = (JSONRenderer, VdxIdApiRenderer)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    permission_classes = [IsPortunusAccessManager]


class AgentApiTaskViewSet(NestedViewSetMixin, ReadOnlyModelViewSet):
    queryset = AgentApiTask.objects.all().select_related("access_domain")
    serializer_class = AgentApiTaskSerializer
    renderer_classes = (JSONRenderer, VdxIdApiRenderer)
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    permission_classes = [IsPortunusAccessManager]
    ordering_fields = ("created", "updated")
    ordering = "-updated"


class AgentCeleryTaskViewSet(NestedViewSetMixin, ReadOnlyModelViewSet):
    queryset = AgentCeleryTask.objects.all()
    serializer_class = AgentCeleryTaskSerializer
    renderer_classes = (JSONRenderer, VdxIdApiRenderer)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    permission_classes = [IsPortunusAccessManager]


class AccDomApiTaskViewSet(AgentApiTaskViewSet):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                content_type=ContentType.objects.get_for_model(ViAccessDomain)
            )
            .select_related("access_domain")
        )
