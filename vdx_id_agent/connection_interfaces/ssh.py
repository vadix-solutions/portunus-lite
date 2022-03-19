##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

from fabric import Connection

from vdx_id_agent.agent_interfaces import BaseConnectionInterface

logger = logging.getLogger(__name__)


class SSHConnection(BaseConnectionInterface):

    required_parameters = ["host_string", "ssh_user", "ssh_password"]
    optional_parameters = ["use_sudo"]

    def open_connection(self):
        self.active_connection = Connection(
            host=self.host_string,
            user=self.ssh_user,
            connect_timeout=5,
            connect_kwargs={"password": self.ssh_password},
        )

    def close_connection(self):
        if self.active_connection:
            self.active_connection.close()

    def run_command(self, command):
        result = None
        try:
            logger.debug("About to run_command(%s)" % command)
            logger.debug("Active conn: %s" % self.active_connection)
            if self.active_connection:
                logger.debug("Executing: %s" % command)
                result = self.active_connection.run(command, hide=True)
                logger.debug("Result: %s" % result)
        except Exception as e:
            logger.error("Command run failed: %s" % e)
            self.close_connection()
            err_str = f"Error from {self.host_string}\n{e}"
            if hasattr(e, "result"):
                err_str = f"Error from {self.host_string}\n{e.result}"
            raise Exception(err_str)
        return result
