##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import json
import logging

import redis
from django.conf import settings

from id_infra.models import AccessHost

logger = logging.getLogger("vdx_id.%s" % __name__)


class NoHostException(Exception):
    """Thrown when an AccessDomain has no Hosts"""

    pass


class VdxCollectionInterface(object):
    """Interface to Redis for extracting access-data collections"""

    def connect(self):
        logger.info(
            "Connecting to Redis Collection Store: %s"
            % settings.COLLECTION_STORE_PARAMS
        )
        try:
            self.client = redis.Redis(**settings.COLLECTION_STORE_PARAMS)
        except Exception:
            logger.error("Connection to Redis Collection Store failed")
            raise

    def get_collections(self, collection_id):
        logger.info("Attempting to find collections for: %s" % collection_id)
        collection_refs = self.client.get(collection_id)
        if collection_refs is None:
            raise NoHostException("Empty collection record - no hosts online")
        collection_refs = collection_refs.decode("utf-8")
        collection_ids = [ref for ref in collection_refs.split(",") if ref]
        return collection_ids

    def get_host_pks(self, collection_id):
        coll_refs = self.get_collections(collection_id)
        return [int(coll_ref.split(".")[1]) for coll_ref in coll_refs]

    def iter_coll_record(self, collection_id):
        """Yields a server_pk and collection from available data."""
        coll_refs = self.get_collections(collection_id)
        for coll_ref in coll_refs:
            coll_id, server_pk = coll_ref.split(".")
            if coll_id != collection_id:
                logger.warning(
                    "Unexpected ref(%s) mismatch in coll_ID: %s"
                    % (coll_id, collection_id)
                )
                continue
            collection = self.client.get(coll_ref)
            collection_dict = json.loads(collection.decode("utf-8"))
            yield int(server_pk), collection_dict

    def disconnect(self):
        try:
            self.client.close()
        except Exception:
            logger.exception("Unexpected error closing database")


class BaseInfraCollector(object):
    def __init__(self, access_domain, collection_id):
        self.access_domain = access_domain
        self.coll_id = collection_id

    ############################
    # COLLECTION LOGIC
    ############################
    def consolidate_collections(self):
        coll_interface = VdxCollectionInterface()
        coll_interface.connect()

        host_pks = coll_interface.get_host_pks(self.coll_id)

        logger.info(
            "Parsing collection(%s) for (%s) Hosts"
            % (self.coll_id, len(host_pks))
        )

        # Used to track the number of records processed for alerts etc
        consolidate_metadata = {"Hosts": len(host_pks)}

        # Retrieve extended_attrib settings to calc Md5 correctly
        ext_attr = {}
        logger.info(f"Processing data with ExtAttr: {ext_attr}")

        # Update all the access_domain hosts
        hosts = AccessHost.objects.filter(pk__in=host_pks)

        coll_iterator = coll_interface.iter_coll_record(self.coll_id)
        for pk, coll_doc in coll_iterator:
            host = hosts.filter(pk=pk).first()
            host.ingest_coll_data(self.coll_id, coll_doc, ext_attr)

        # Update the last collection id
        self.access_domain.last_collection_id = self.coll_id
        self.access_domain.save(update_fields=["last_collection_id"])

        return consolidate_metadata
