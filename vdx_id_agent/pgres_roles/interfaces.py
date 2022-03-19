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
        "vdx_id_agent.connection_interfaces.psql:PsqlConnection"
    )

    SQL_SETPW = """ALTER USER {username} WITH PASSWORD '{password}';"""

    interface_id = "pgres_roles"

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
            SELECT u.usename AS "Role name",
              CASE WHEN u.usesuper AND u.usecreatedb THEN
                CAST('superuser, create database' AS pg_catalog.text)
                   WHEN u.usesuper THEN CAST('superuser' AS pg_catalog.text)
                   WHEN u.usecreatedb THEN CAST('create database' AS
                        pg_catalog.text)
                   ELSE CAST('' AS pg_catalog.text)
              END AS "Attributes"
            FROM pg_catalog.pg_user u
            ORDER BY 1;"""
        )
        logger.debug("Account data:\n: %s" % ident_df)

        for idx, row in ident_df.iterrows():
            account_name = row["Role name"]
            ident_dict = {"memberships": row["Attributes"].split(",")}
            collection.add_account(account_name, ident_dict)

    def _read_access_items(self, collection, access_items=None, accounts=None):
        access_items_members = self.connection.run_command(
            """SELECT
                  r.rolname,
                  r.rolsuper,
                  r.rolinherit,
                  r.rolcreaterole,
                  r.rolcreatedb,
                  r.rolcanlogin,
                  r.rolconnlimit, r.rolvaliduntil,
              ARRAY(SELECT b.rolname
                    FROM pg_catalog.pg_auth_members m
                    JOIN pg_catalog.pg_roles b ON (m.roleid = b.oid)
                    WHERE m.member = r.oid) as memberof
            , r.rolreplication
            FROM pg_catalog.pg_roles r
            ORDER BY 1;
            """
        )
        logger.debug("Group data:\n: %s" % access_items_members)

        defined_roles = []
        for idx, row in access_items_members.iterrows():
            memberships = row.memberof
            psql_role_account = row.rolname

            for role in memberships:
                # Conditionally add the role to the collection if not seen
                if role not in defined_roles:
                    accitem_dict = {"groupname": role}
                    collection.add_access_item(role, accitem_dict)
                    defined_roles.append(role)
                # Add membership
                collection.add_membership(role, psql_role_account)
