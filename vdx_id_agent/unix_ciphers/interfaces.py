##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

from vdx_id_agent.unix.interfaces import PlatformInterface as UnixInterface

logger = logging.getLogger(__name__)


class PlatformInterface(UnixInterface):
    def _read_host_info(self, collection):
        info_dict = {
            "cipher_suites": self.__get_cmd_dict_response("openssl ciphers -v")
        }
        collection.set_host_info(info_dict)
