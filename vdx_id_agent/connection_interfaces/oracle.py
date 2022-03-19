##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

import cx_Oracle
import pandas as pd

from vdx_id_agent.agent_interfaces import BaseConnectionInterface

logger = logging.getLogger(__name__)


class Oracle11Connection(BaseConnectionInterface):

    required_parameters = [
        "host_string",
        "oracle_user",
        "oracle_password",
        "oracle_database",
    ]
    optional_parameters = []

    def run_command(self, cmd_str, many=False):
        return self.fetch_one(cmd_str)

    def open_connection(self):
        self.active_connection = cx_Oracle.connect(
            self.oracle_user,
            self.oracle_password,
            "%s/XE" % self.host_string,
            encoding="UTF-8",
        )
        logger.info("Active conn: %s" % self.active_connection)

    def close_connection(self):
        if self.active_connection:
            self.active_connection.close()

    def fetch_one(self, sql_statement):
        result = None
        cursor = self.active_connection.cursor()

        try:
            cursor.execute(sql_statement)
        except (cx_Oracle.Error) as e:
            logger.exception("Unexpected Oracle error: %s" % e)
            raise
        logger.info("Executed SQL: %s" % sql_statement)

        try:
            response = cursor.fetchall()
            result = pd.DataFrame(
                response, columns=[elt[0] for elt in cursor.description]
            )
        except (cx_Oracle.ProgrammingError, cx_Oracle.InterfaceError) as e:
            logger.warning("Programming error: %s" % e)

        logger.info("Committing to DB")
        self.active_connection.commit()
        cursor.close()

        return result

    # def fetch_many(self, sql_statement):
    #     result = None
    #     cursor = self.active_connection.cursor()
    #     try:
    #         cursor.execute(sql_statement)
    #         result = cursor.fetchmany()
    #     except (Exception, psycopg2.Error) as e:
    #         logger.exception("PostgreSQL error: %s" % e)
    #         raise
    #     finally:
    #         cursor.close()
    #     return result
