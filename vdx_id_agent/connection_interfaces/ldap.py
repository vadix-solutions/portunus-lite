##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

import ldap

from vdx_id_agent.agent_interfaces import BaseConnectionInterface

logger = logging.getLogger(__name__)


class LdapConnection(BaseConnectionInterface):

    required_parameters = [
        "host_string",
        "ldap_CN",
        "ldap_DC",
        "ldap_password",
    ]
    optional_parameters = []

    def open_connection(self):
        # ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        con = ldap.initialize("ldap://%s" % self.host_string)

        cn_str = "%s,%s" % (self.ldap_CN, self.ldap_DC)
        logger.info(
            "Authenticating to LDAP(%s) using: %s" % (self.host_string, cn_str)
        )
        con.simple_bind_s(cn_str, self.ldap_password)

        self.active_connection = con

    def close_connection(self):
        if self.active_connection:
            self.active_connection.unbind_s()
