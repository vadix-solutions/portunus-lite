##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import copy
import hashlib
import json
import logging

import celery
from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.expressions import RawSQL
from django.utils import timezone

from id_infra.models.agent import AgentApiTask, AgentTaskMixin
from vdx_id.celery import app
from vdx_id.util.task_util import expand_task_to_final_children
from web_interface.consumers import get_channel

logger = logging.getLogger("vdx_id.%s" % __name__)


class HostScanDefinition(AgentTaskMixin, models.Model):
    """Defines a network segment to scan for Hosts with required Ports."""

    name = models.CharField(max_length=255)
    description = models.TextField(default="")

    scan_definition = JSONField(
        default=dict, help_text="A JSON object: 'ports':[], 'ranges':[{},]"
    )
    scan_results = JSONField(default=dict, blank=True)

    # TODO: Return scanning intervals and auto-retire
    #       Refer to tasks.py:L57 - celery task implemented
    # scan_interval = models.DurationField(
    #     help_text="Rescan this network group after this much time",
    #     default="30:00",
    # )
    # server_retire_time = models.DurationField(
    #     help_text="Remove any server that has not been detected time",
    #     default="60:00",
    # )

    access_domain = models.ForeignKey(
        "id_infra.ViAccessDomain",
        related_name="scan_definitions",
        on_delete=models.CASCADE,
    )
    scanning_agent = models.ForeignKey(
        "id_infra.ViAgent",
        related_name="scan_definitions",
        on_delete=models.CASCADE,
    )

    hosts_default_active = models.BooleanField(
        default=True,
        help_text="Are new hosts set as 'active' in their AccessDomain?",
    )
    hosts_default_writable = models.BooleanField(
        default=True,
        help_text="Are new Hosts set as writable (provisionable)?",
    )

    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def perform_scan(self):
        if not self.scanning_agent.active:
            raise Exception("Agent %s is not active" % self.scanning_agent)

        # Chain to wait for Collection, then parsing
        task_args = (self.scanning_agent.pk, self.scan_definition)
        conn_test = app.signature(
            "connection_test",
            args=task_args,
            kwargs={},
            queue=self.scanning_agent.queue_name,
        )
        parse_res = app.signature(
            "id_infra.tasks.read_netscan_result",
            args=(self.pk,),
            queue=settings.CELERY_TASK_DEFAULT_QUEUE,
        )

        celtask_chain = celery.chain(conn_test, parse_res).apply_async()
        logger.info("Called chain: %s" % celtask_chain)

        # Here we create a small object to track the task progress
        # TODO: Deprecate this function - just get the IDs without magic
        parent_id, children_ids = expand_task_to_final_children(celtask_chain)
        task = AgentApiTask.objects.create(
            api_call="server_scan", content_object=self
        )
        task.link_celery_tasks(children_ids + [parent_id])

        return task

    def register_servers(self):
        """This is called from tasks.read_netscan_result to parse self.scan_results
        The scan_result attribute is populated as the result is read."""
        hosts_detected = 0

        current_time = timezone.now()
        logger.info(f"Marking all hosts inactive for {self}")
        all_known_hosts = AccessHost.objects.filter(
            source_scan_definition=self, access_domain=self.access_domain
        )

        found_existing_hosts = []
        new_discovered_hosts = []

        for agent_id, agent_data in self.scan_results.items():

            logger.info(f"Reading scan from agent({agent_id})")
            for address, p_scan in agent_data.items():

                fully_connected = False not in [
                    result["connected"] for result in p_scan.values()
                ]
                if fully_connected:
                    logger.debug("Address found: %s" % address)
                    hosts_detected += 1
                else:
                    logger.debug(
                        "Address(%s) not fully reachable: %s", address, p_scan
                    )
                    continue

                existing_host = all_known_hosts.filter(
                    address=address, agent_id=agent_id
                )
                if existing_host.exists():
                    found_existing_hosts += existing_host.values_list(
                        "pk", flat=True
                    )
                else:
                    new_discovered_hosts.append(
                        AccessHost(
                            address=address,
                            agent_id=agent_id,
                            source_scan_definition=self,
                            access_domain=self.access_domain,
                            active=self.hosts_default_active,
                            writable=self.hosts_default_writable,
                            created=current_time,
                            updated=current_time,
                        )
                    )
        # Mark all unseen hosts as inactive
        mcount = all_known_hosts.exclude(pk__in=found_existing_hosts).update(
            active=False
        )
        # Mark all seen hosts as active
        ocount = all_known_hosts.filter(pk__in=found_existing_hosts).update(
            active=True, updated=current_time
        )
        # Create all new hosts
        AccessHost.objects.bulk_create(new_discovered_hosts)

        # Now send a notification
        channel = get_channel()
        channel_layer_name = "notifications"
        msg_dict = {
            "type": "notification",
            "icon": "info",
            "heading": "Host Scan Complete",
            "text": f"""
            <span class="badge badge-primary p-1">{self.name}</span>
            <ul>
                <li>{len(new_discovered_hosts)} New Hosts</li>
                <li>{ocount} Existing Hosts</li>
                <li>{mcount} Missing</li>
            </ul>""",
        }
        async_to_sync(channel.group_send)(channel_layer_name, msg_dict)

    def perform_capability(self, *args, **kwargs):
        raise NotImplementedError()

    def generate_capability_task(self, *args, **kwargs):
        raise NotImplementedError()


class AccessHost(models.Model):
    """Represents a single Host for a particular AccessDomain.
    Is reachable from a particular Agent."""

    address = models.CharField(
        max_length=255, help_text="Machine-readable address of Host"
    )

    active = models.BooleanField(
        default=True, help_text="Is this host active in its AccessDomain?"
    )
    writable = models.BooleanField(
        default=True,
        help_text="Should provisioning occur on this host? (False for DR)",
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    agent = models.ForeignKey(
        "id_infra.ViAgent", related_name="hosts", on_delete=models.CASCADE
    )

    source_scan_definition = models.ForeignKey(
        HostScanDefinition,
        related_name="hosts",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    access_domain = models.ForeignKey(
        "id_infra.ViAccessDomain",
        related_name="hosts",
        on_delete=models.CASCADE,
    )

    collection_data = JSONField(
        default=dict, blank=True, help_text="Latest collected data"
    )
    last_collection_id = models.CharField(
        max_length=100, null=True, blank=True
    )
    collection_meta = JSONField(
        default=dict,
        blank=True,
        help_text="Metadata about collections (historic)",
    )

    def __str__(self):
        return self.address

    def ingest_coll_data(self, collection_id, collection_data, ext_attr):
        """Ingest collection data AND create a metadata record"""
        this_host = AccessHost.objects.filter(pk=self.pk)
        # Get metadata record
        meta_record = self._generate_coll_meta_record(
            copy.deepcopy(collection_data), ext_attr
        )
        meta_record_string = json.dumps(meta_record)
        logger.debug(f"Ingested data for host {self}")
        # Update this host with collection data, meta, and last ID
        # Collect meta updated with RawSQL for cheaper DB insert
        this_host.update(
            last_collection_id=collection_id,
            collection_data=collection_data,
            collection_meta=RawSQL(
                f"""
                jsonb_set(
                    collection_meta,
                    '{{"{collection_id}"}}',
                    '{meta_record_string}',
                    true
                )""",
                [],
            ),
        )

    def _generate_coll_meta_record(self, coll_data, ext_attr):
        """Generate metadata from collection data record
        A copy of the collection data is used so that removing keys does not
        affect the Host collection data entry."""
        # TODO: Add additional metadata here as we need
        meta_record = {}

        for dtype in ["accounts", "access_items", "memberships", "host_info"]:
            coll_rec = coll_data.get(dtype)
            if not coll_rec:
                continue
            exclude_attribs = ext_attr.get(dtype, [])
            for name in coll_rec.keys():
                for attr_key in exclude_attribs:
                    coll_rec[name].pop(attr_key, None)

            data_md5 = hashlib.md5(
                json.dumps(coll_rec, sort_keys=True).encode("utf-8")
            ).hexdigest()

            meta_record[dtype] = {"md5": data_md5, "count": len(coll_rec)}
        return meta_record
