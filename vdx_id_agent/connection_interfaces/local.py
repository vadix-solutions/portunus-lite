##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging
import subprocess

from vdx_id_agent.agent_interfaces import BaseConnectionInterface

logger = logging.getLogger(__name__)


class LocalConnection(BaseConnectionInterface):

    required_parameters = []
    optional_parameters = []

    def open_connection(self):
        pass

    def close_connection(self):
        pass

    def run_command(self, command):
        try:
            logger.info(f"Running command: {command}")
            output = subprocess.check_output(
                command, shell=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            raise Exception(e.output)
        return output
