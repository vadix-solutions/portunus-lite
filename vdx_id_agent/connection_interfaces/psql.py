##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

import pandas as pd
import psycopg2

from vdx_id_agent.agent_interfaces import BaseConnectionInterface

logger = logging.getLogger(__name__)


class PsqlConnection(BaseConnectionInterface):

    required_parameters = [
        "host_string",
        "psql_user",
        "psql_password",
        "psql_database",
    ]
    optional_parameters = []

    def run_command(self, cmd_str, many=False):
        # if many:
        #     result = self.fetch_many(cmd_str)
        return self.fetch_one(cmd_str)

    def open_connection(self):
        self.active_connection = psycopg2.connect(
            host=self.host_string,
            port="5432",
            user=self.psql_user,
            password=self.psql_password,
            database=self.psql_database,
        )
        logger.debug(
            "Active conn: %s" % self.active_connection.get_dsn_parameters()
        )

    def close_connection(self):
        if self.active_connection:
            self.active_connection.close()

    def fetch_one(self, sql_statement):
        result = None
        cursor = self.active_connection.cursor()

        try:
            cursor.execute(sql_statement)
        except (psycopg2.Error) as e:
            logger.exception("Unexpected PostgreSQL error: %s" % e)
            raise
        logger.debug("Executed PSQL: %s" % sql_statement)

        try:
            response = cursor.fetchall()
            result = pd.DataFrame(
                response, columns=[elt[0] for elt in cursor.description]
            )
        except psycopg2.ProgrammingError as e:
            logger.warning("Programming error: %s" % e)

        logger.debug("Committing to DB")
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
