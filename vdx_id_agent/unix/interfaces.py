##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

from vdx_id_agent.agent_interfaces import BasePlatformInterface
from vdx_id_agent.vdx_collections import PlatformCollection, VdxRecordInterface

logger = logging.getLogger(__name__)


class PlatformInterface(BasePlatformInterface, VdxRecordInterface):
    """Unix collection interface supporting RBAC"""

    connection_interface = (
        "vdx_id_agent.connection_interfaces.ssh:SSHConnection"
    )

    passwd_headers = [
        "username",
        "pass",
        "UID",
        "GID",
        "full_name",
        "home",
        "shell",
    ]
    passwd_stat_headers = [
        "username",
        "lock_status",
        "last_pass_change",
        "min_age",
        "max_age",
        "warn_period",
        "inactive_period",
    ]
    group_headers = ["groupname", "pass", "GID", "users"]

    interface_id = "VDX.Unix.v1"

    def _run_command(self, command_tmpl, **tmpl_params):
        # Potentially include sudo
        if getattr(self.connection, "use_sudo", False) is True:
            tmpl_params["sudo"] = "sudo"
        else:
            tmpl_params["sudo"] = ""
        command = command_tmpl.format(**tmpl_params)
        result = self.connection.run_command(command)
        return result

    def create_account(
        self,
        username,
        home=None,
        GID=None,
        UID=None,
        comment=None,
        password=None,
    ):
        opts = []
        if GID:
            opts.append("--gid %s" % GID)
        if UID:
            opts.append("-u %s" % int(UID))
        if home:
            opts.append("-d %s" % home)
        if comment:
            opts.append("-c %s" % comment)
        opts = " ".join(opts)
        command = "{sudo} useradd {opts} {username}"
        self._run_command(command, opts=opts, username=username)

        # Also set the password if it is provided
        if password:
            command = (
                f'{{sudo}} echo -e "{password}\n{password}"'
                f"| passwd {username}"
            )
            self._run_command(command)

    def delete_account(self, username):
        command = "{sudo} userdel {username}"
        self._run_command(command, username=username)

    def set_password(self, username, password):
        command = 'echo -e "{passw}\n{passw}" | {sudo} passwd {user}'
        self._run_command(command, user=username, passw=password)

    def lock_account(self, username):
        command = "{sudo} passwd -l {username}"
        self._run_command(command, username=username)

    def unlock_account(self, username):
        command = "{sudo} passwd -u {username}"
        self._run_command(command, username=username)

    def add_membership(self, username, groupname):
        command = "{sudo} usermod -a -G {groupname} {username}"
        self._run_command(command, groupname=groupname, username=username)

    def remove_membership(self, groupname, username):
        command = "{sudo} deluser {username} {groupname}"
        self._run_command(command, groupname=groupname, username=username)

    def collect_access(self, collection_id, server_pk):
        collection = PlatformCollection(server_pk, collection_id)
        self._read_accounts(collection)
        self._read_access(collection)
        self._read_host_info(collection)

        self.connect_to_agent_db()
        self.store_collection(collection, collection_id=collection_id)

    def __get_cmd_line_response(self, cmd):
        result = self._run_command(cmd)
        return result.stdout.strip()

    def __get_cmd_list_response(self, cmd):
        result = self._run_command(cmd)
        return result.stdout.splitlines()

    def __get_cmd_dict_response(self, cmd):
        result = self._run_command(cmd)
        res_dict = {}
        for attr in result.stdout.splitlines():
            lside, rside = attr.split(":", 1)
            res_dict[lside.strip()] = rside.strip()
        return res_dict

    def _read_accounts(self, collection, accounts=None):
        accounts = self.__get_cmd_list_response("{sudo} getent passwd")
        passwd_status = self.__get_cmd_list_response("{sudo} passwd -Sa")

        account_dicts = {}
        for account_data in accounts:
            acc_parts = account_data.split(":")
            acc_dict = {k: v for k, v in zip(self.passwd_headers, acc_parts)}
            account_name = acc_dict["username"]

            # Add default embeddded access (default group membership)
            acc_dict["embedded_access"] = [account_name]

            account_dicts[account_name] = acc_dict

        for passwd_data in passwd_status:
            passwd_parts = passwd_data.split(" ")
            pass_dict = {
                k: v for k, v in zip(self.passwd_stat_headers, passwd_parts)
            }
            account_name = pass_dict["username"]
            pass_dict["locked"] = pass_dict["lock_status"] != "P"
            account_dicts[account_name].update(pass_dict)

        for account_name, acc_dict in account_dicts.items():
            collection.add_account(account_name, acc_dict)

    def _read_access(self, collection):
        groups = self.__get_cmd_list_response("{sudo} getent group")

        for group in groups:
            group_parts = group.split(":")
            group_dict = {
                k: v for k, v in zip(self.group_headers, group_parts)
            }
            members = group_dict["users"].split(",")
            accitem_name = group_dict["groupname"]
            collection.add_access_item(accitem_name, group_dict)

            for account_name in members:
                if account_name == "":
                    continue
                collection.add_membership(accitem_name, account_name)

    def _read_host_info(self, collection):
        info_dict = {
            "kernel_release": self.__get_cmd_line_response("uname -r"),
            "machine_arch": self.__get_cmd_line_response("uname -m"),
            "hostname": self.__get_cmd_line_response("hostname"),
            "cpu_info": self.__get_cmd_dict_response("lscpu"),
        }
        collection.set_host_info(info_dict)
