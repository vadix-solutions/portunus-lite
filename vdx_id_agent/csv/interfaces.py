##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging
from io import StringIO

import pandas as pd

from vdx_id_agent.agent_interfaces import BasePlatformInterface
from vdx_id_agent.vdx_collections import PlatformCollection, VdxRecordInterface

logger = logging.getLogger(__name__)


class PlatformInterface(BasePlatformInterface, VdxRecordInterface):
    # TODO: Generate interface_parameters from function calls

    connection_interface = (
        "vdx_id_agent.connection_interfaces.local:LocalConnection"
    )

    interface_id = "csv_local"

    def _run_command(self, command_tmpl, **tmpl_params):
        # Potentially include sudo
        if getattr(self.connection, "use_sudo", False) is True:
            tmpl_params["sudo"] = "sudo"
        else:
            tmpl_params["sudo"] = ""

        encoding = getattr(self.connection, "encoding", "ascii")
        command = command_tmpl.format(**tmpl_params)
        result = self.connection.run_command(command)
        result = result.decode(encoding)
        logger.warning("Result: %s" % result)
        return result

    def collect_access(
        self,
        collection_id,
        server_pk,
        csv_fname_accounts=None,
        csv_fname_access=None,
        account_identifier_column=None,
        access_identifier_column=None,
        access_membership_column=None,
    ):
        collection = PlatformCollection(server_pk, collection_id)
        if csv_fname_accounts:
            if not account_identifier_column:
                raise Exception("Account Identifier must be set")
            self._read_accounts(
                collection, csv_fname_accounts, account_identifier_column
            )
        if csv_fname_access:
            if not access_identifier_column:
                raise Exception("Account Identifier must be set")
            self._read_access(
                collection,
                csv_fname_access,
                access_identifier_column,
                access_membership_column=access_membership_column,
            )
        # Read host info
        self._read_host_info(collection, csv_fname_accounts, csv_fname_access)

        self.connect_to_agent_db()
        self.store_collection(collection, collection_id=collection_id)

    def __get_cmd_line_response(self, cmd, **kwargs):
        result = self._run_command(cmd, **kwargs)
        return result.strip()

    def _read_accounts(
        self, collection, csv_fname_accounts, account_identifier_column
    ):

        csv_string = self.__get_cmd_line_response(
            "{sudo} cat {fname}", fname=csv_fname_accounts
        )
        csv_data = StringIO(csv_string)
        df = pd.read_csv(csv_data, sep=",")

        for idx, row in df.iterrows():
            rdict = row.to_dict()
            acc_name = rdict.get(account_identifier_column)
            collection.add_account(acc_name, rdict)

    def _read_access(
        self,
        collection,
        csv_fname_access,
        access_identifier_column,
        access_membership_column=None,
    ):
        csv_string = self.__get_cmd_line_response(
            "{sudo} cat {fname}", fname=csv_fname_access
        )

        csv_data = StringIO(csv_string)
        df = pd.read_csv(csv_data, sep=",")

        for idx, row in df.iterrows():
            rdict = row.to_dict()
            if access_membership_column:
                memberships = rdict.pop(access_membership_column)
            accitem_name = rdict.get(access_identifier_column)
            collection.add_access_item(accitem_name, rdict)

            if memberships:
                account_names = memberships.split(",")
                for account_name in account_names:
                    collection.add_membership(accitem_name, account_name)

    def _read_host_info(self, collection, account_fname, accitem_fname):
        info_dict = {}
        if account_fname:
            info_dict["account_csv_mtime"] = self.__get_cmd_line_response(
                "date -r {fname}", fname=account_fname
            )
        if accitem_fname:
            info_dict["access_csv_mtime"] = self.__get_cmd_line_response(
                "date -r {fname}", fname=accitem_fname
            )
        collection.set_host_info(info_dict)
