##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

from vdx_id_agent.agent_interfaces import BasePlatformInterface
from vdx_id_agent.vdx_collections import PlatformCollection, VdxRecordInterface

logger = logging.getLogger(__name__)


class PlatformInterface(BasePlatformInterface, VdxRecordInterface):
    # TODO: Generate interface_parameters from function calls

    connection_interface = (
        "vdx_id_agent.connection_interfaces.oracle:Oracle11Connection"
    )

    SQL_SETPW = """ALTER USER {username} WITH PASSWORD '{password}';"""

    interface_id = "oracle_roles"

    def collect_access(
        self, collection_id, server_pk, account_set=None, access_item_set=None
    ):
        collection = PlatformCollection(server_pk, collection_id)
        self._read_accounts(collection, accounts=account_set)
        self._read_access_items(
            collection, accounts=account_set, access_items=access_item_set
        )

        self.connect_to_agent_db()
        self.store_collection(collection, collection_id=collection_id)

    def _read_accounts(self, collection, accounts=None):
        ident_df = self.connection.run_command(
            """
            SELECT USERNAME FROM DBA_USERS ORDER BY 1"""
        )
        logger.info("Account data:\n: %s" % ident_df)

        for idx, row in ident_df.iterrows():
            account_name = row.USERNAME
            account_attrib = {"username": account_name}
            collection.add_account(account_name, account_attrib)

    def _read_access_items(self, collection, access_items=None, accounts=None):
        access_items_members = self.connection.run_command(
            """SELECT
                    grantee AS username,
                    granted_role AS approle
                FROM
                    dba_role_privs
                WHERE
                    granted_role != 'CONNECT'
                ORDER BY 1
            """
        )
        logger.info("Group data:\n: %s" % access_items_members)

        defined_roles = []
        for idx, row in access_items_members.iterrows():
            member_user = row.USERNAME
            oracle_role = row.APPROLE

            # Conditionally add the role to the collection if not seen
            if oracle_role not in defined_roles:
                accitem_dict = {"groupname": oracle_role}
                collection.add_access_item(oracle_role, accitem_dict)
                defined_roles.append(oracle_role)

            # Add membership
            collection.add_membership(oracle_role, member_user)
