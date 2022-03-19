##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

from rest_framework_extensions.routers import ExtendedSimpleRouter

from . import views

app_name = "id_infra"

router = ExtendedSimpleRouter()

r_acc_dom = router.register(
    r"access_domains", views.AccessDomainViewSet, basename="access_domain"
)
r_acc_dom.register(
    r"api_tasks",
    views.AccDomApiTaskViewSet,
    "access_domain-apitasks",
    parents_query_lookups=["object_id"],
)

router.register(r"servers", views.HostViewSet, basename="server")

r_server_group = router.register(
    r"server_groups", views.HostScanDefViewSet, basename="servergroup"
)
r_server_group.register(
    r"servers",
    views.HostViewSet,
    "scan_group-hosts",
    parents_query_lookups=["source_scan_definition_id"],
)

router.register(r"agents", views.ViAgentViewSet, basename="agent")
router.register(
    r"agent_interfaces", views.ViAgentInterfaceViewSet, basename="agent_iface"
)
router.register(
    r"agent_apitasks", views.AgentApiTaskViewSet, basename="agent_apitask"
)
router.register(
    r"agent_celerytasks",
    views.AgentCeleryTaskViewSet,
    basename="agent_celerytask",
)

urlpatterns = router.urls
