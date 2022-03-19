##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import json
import logging

import redis

import vdx_id_agent.agent_config as conf

logger = logging.getLogger(__name__)


class PlatformCollection(object):

    accounts = {}
    access_items = {}
    memberships = {}
    host_info = {}
    server_pk = None
    collection_name = None
    _record = None

    def __init__(self, server_pk, collection_name, **kwargs):
        if not server_pk or not collection_name:
            raise Exception("Collection malformed")
        self.server_pk = server_pk
        self.collection_name = collection_name
        self._record = None
        self.accounts = {}
        self.access_items = {}
        self.memberships = {}
        self.host_info = {}

    def add_account(self, account_name, account_data):
        if self.accounts.get(account_name):
            logger.warning(
                "Account with account_name(%s) already exists" % account_name
            )
        self.accounts[account_name] = account_data

    def add_access_item(self, access_item_name, access_item_data):
        if self.access_items.get(access_item_name):
            logger.warning("Account with access_item_name(%s) already exists")
        self.access_items[access_item_name] = access_item_data

    def add_membership(self, access_item_name, account_name):
        if not self.memberships.get(access_item_name):
            self.memberships[access_item_name] = {}
        try:
            self.memberships[access_item_name][account_name] = {}
        except Exception:
            logger.exception(
                "Error adding %s to %s access_item"
                % (account_name, access_item_name)
            )
            raise

    def set_host_info(self, host_info):
        self.host_info = host_info

    def format_as_record(self):
        """Formats the record content for collection storage."""
        server_pk = self.server_pk
        rec = {
            server_pk: {
                "accounts": self.accounts,
                "access_items": self.access_items,
                "memberships": self.memberships,
                "host_info": self.host_info,
            }
        }
        return rec


class VdxRecordInterface(object):
    subcollection_cols = [
        "accounts",
        "access_items",
        "memberships",
        "host_info",
    ]
    delta_cols = ["accounts", "access_items", "memberships"]

    def connect_to_agent_db(self):
        logger.debug("Connecting to redis collection store")
        try:
            self.client = redis.Redis(**conf.COLLECTION_STORE_PARAMS)
            logger.debug("Connected: %s" % self.client)
            return True
        except KeyError:
            logger.exception("Connection failed")
            raise

    def store_host_coll(self, coll_id, host_key, host_coll):
        host_coll_id = "{coll_id}.{host_key}".format(
            coll_id=coll_id, host_key=host_key
        )
        # Convert json to redis-safe-string
        host_coll_str = json.dumps(host_coll, ensure_ascii=False).encode(
            "utf-8"
        )
        # Set the record
        self.client.set(host_coll_id, host_coll_str)
        # Append the host-collection-id to coll_id for referencing
        return self.client.append(coll_id, host_coll_id + ",")

    def store_collection(self, collection, collection_id):
        collection_record = collection.format_as_record()

        for host_key, host_collection in collection_record.items():
            logger.info(
                "Storing Coll[%s] Server-PK: %s" % (collection_id, host_key)
            )
            response = self.store_host_coll(
                collection_id, host_key, host_collection
            )
            logger.debug("Collection stored; response=%s" % response)
