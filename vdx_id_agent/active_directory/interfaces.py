##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

import ldap
from ldap.controls.libldap import SimplePagedResultsControl

from vdx_id_agent.agent_interfaces import BasePlatformInterface
from vdx_id_agent.vdx_collections import PlatformCollection, VdxRecordInterface

logger = logging.getLogger(__name__)


class PlatformInterface(BasePlatformInterface, VdxRecordInterface):

    connection_interface = (
        "vdx_id_agent.connection_interfaces.ldap:LdapConnection"
    )

    interface_id = "active_directory"

    @property
    def ld(self):
        return self.connection.active_connection

    def encode_attr_dict(self, attrs):
        """Encodes all attribute values to [bytes]"""
        for k, attr in attrs.items():
            logger.debug("Encoding attr(%s): %s" % (k, attr))
            if type(attr) is not list:
                logger.warning("Attribute (%s) was not list, converting" % k)
                attr = [attr]
            attrs[k] = [self.utf8_encode(v) for v in attr]
        return attrs

    def decode_attr_dict(
        self, attrs, drop_attr=["objectSid", "objectGUID", "logonHours"]
    ):
        """Decodes all attribute values to [str]"""
        attr_keys = list(attrs.keys())
        for k in attr_keys:
            # Ignore drop_attr
            if str(k) in drop_attr:
                logger.debug("Dropping attribute: %s" % k)
                del attrs[k]
                continue

            attr = attrs[k]
            if type(attr) is not list:
                logger.warning("Attribute (%s) was not list, skipping")
                continue

            try:
                attrs[k] = [self.utf8_decode(v) for v in attr]
            except UnicodeEncodeError:
                logger.error("Removing binary data attribute: %s" % k)
                del attrs[k]

        logger.debug("Output attrs: %s" % attrs)
        return attrs

    def collect_access(
        self,
        collection_id,
        server_pk,
        user_containers,
        group_containers,
        ignore_attribs=[],
    ):
        collection = PlatformCollection(server_pk, collection_id)
        self._read_accounts(
            collection,
            ignore_attribs=ignore_attribs,
            user_containers=user_containers,
        )
        self._read_access(
            collection,
            ignore_attribs=ignore_attribs,
            group_containers=group_containers,
        )

        self.connect_to_agent_db()
        self.store_collection(collection, collection_id=collection_id)

    # Todo: Enforce encoding ->
    # https://sourceforge.net/p/python-ldap/mailman/message/8696623/
    def _read_accounts(
        self, collection, ignore_attribs=[], user_containers=["CN=Users"]
    ):
        search_filter = "(&(objectClass=user))"
        for user_container in user_containers:
            search_base = "%s,%s" % (user_container, self.connection.ldap_DC)
            logger.info("Searching %s" % search_base)
            results = self.__read_paginated(
                search_base, ldap.SCOPE_ONELEVEL, search_filter, attrlist=["*"]
            )

            logger.debug("Retrieved %s User records" % len(results))
            for cn, attrs in results:
                attrs = self.decode_attr_dict(attrs, drop_attr=ignore_attribs)
                collection.add_account(cn, attrs)

    def _read_access(
        self, collection, ignore_attribs=[], group_containers=["CN=Users"]
    ):
        search_filter = "(&(objectClass=group))"
        for group_container in group_containers:
            logger.debug("Collecting access for group: %s" % group_container)
            search_base = "%s,%s" % (group_container, self.connection.ldap_DC)

            results = self.__read_paginated(
                search_base, ldap.SCOPE_ONELEVEL, search_filter, attrlist=["*"]
            )

            logger.debug("Retrieved %s Group records" % len(results))
            for cn, attrs in results:
                attrs = self.decode_attr_dict(attrs, drop_attr=ignore_attribs)
                attrs["groupname"] = cn
                collection.add_access_item(cn, attrs)

                for ad_member in attrs.get("member", []):
                    collection.add_membership(cn, ad_member)

    def __read_paginated(self, *args, size=1000, **kwargs):
        page_control = SimplePagedResultsControl(True, size=size, cookie="")
        response = self.ld.search_ext(
            *args, **kwargs, serverctrls=[page_control]
        )

        result = []
        pages = 0
        while True:
            pages += 1
            rtype, rdata, rmsgid, serverctrls = self.ld.result3(response)
            result.extend(rdata)
            controls = [
                control
                for control in serverctrls
                if control.controlType == SimplePagedResultsControl.controlType
            ]
            if not controls:
                print("The server ignores RFC 2696 control")
                break
            if not controls[0].cookie:
                break
            page_control.cookie = controls[0].cookie
            response = self.ld.search_ext(
                *args, **kwargs, serverctrls=[page_control]
            )
        return result

    @staticmethod
    def utf8_encode(i_str):
        return i_str.encode("utf-8")

    @staticmethod
    def utf8_decode(i_bytes):
        return str(i_bytes, "utf-8")
