##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##
from datetime import datetime, timedelta

from celery.utils.log import get_task_logger
from django.utils.timezone import make_aware

from id_infra.models import HostScanDefinition, ViAccessDomain
from id_infra.models.agent import (
    AgentApiTask,
    AgentCeleryTask,
    CeleryTaskMetaState,
)
from vdx_id.celery import app

from .collection_engine import BaseInfraCollector, NoHostException
from .signals import access_domain_collected

logger = get_task_logger("vdx_id.%s" % __name__)


@app.task()
def read_infra(igrp_id):
    access_domain = ViAccessDomain.objects.get(id=igrp_id)
    agent_api_task = access_domain.request_collection()
    if agent_api_task:
        logger.info("Requested collection: {agent_api_task}")


@app.task(name="consolidate_collections", time_limit=300)
def consolidate_collections(collection_id, igrp_id):
    access_domain = ViAccessDomain.objects.get(id=igrp_id)
    logger.info(f"Consolidating collections for AccDom: {access_domain}")
    collector = BaseInfraCollector(access_domain, collection_id)
    try:
        consolidate_metadata = collector.consolidate_collections()
    except NoHostException:
        logger.warning("Exiting collection consolidate early")
        return
    logger.info("Consolidate metadata: %s" % consolidate_metadata)
    access_domain_collected.send(
        sender=access_domain.__class__,
        pk=access_domain.pk,
        collection_id=collection_id,
    )


@app.task()
def read_netscan_result(scan_result, scan_def_id):
    """Celery task to be chained in order to parse the server scan result"""
    logger.info("Reading netscan result for scandef: %s" % (scan_def_id))
    scan_def = HostScanDefinition.objects.get(pk=scan_def_id)
    scan_def.scan_results = scan_result
    scan_def.register_servers()
    scan_def.save()


@app.task()
def update_apitask_status(max_tasks=50):
    incomplete_tasks = AgentApiTask.objects.filter(tasks_complete=False)
    for task in incomplete_tasks:
        task.update_state(complete_empty=True)


@app.task()
def update_old_apitask_status():
    # Try force update any task >10s old
    updated_10s_ago = make_aware(datetime.now() - timedelta(seconds=10))
    pending_cel_tasks = AgentCeleryTask.objects.filter(
        state=CeleryTaskMetaState.PENDING, updated__lte=updated_10s_ago
    )
    if pending_cel_tasks.exists():
        for task in pending_cel_tasks:
            task.manually_update_state()

    # Delete any task >60s old
    updated_60s_ago = make_aware(datetime.now() - timedelta(seconds=60))
    frozen_cel_tasks = AgentCeleryTask.objects.filter(
        state=CeleryTaskMetaState.PENDING, updated__lte=updated_60s_ago
    )
    if frozen_cel_tasks.exists():
        frozen_cel_task_ids = frozen_cel_tasks.values_list(
            "task_id", flat=True
        )
        logger.warning(f"Removing frozen tasks {frozen_cel_task_ids}")
        frozen_cel_tasks.delete()
