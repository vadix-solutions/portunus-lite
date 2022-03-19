##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging
import socket
from ipaddress import IPv4Network
from multiprocessing.pool import ThreadPool as Pool

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ConnectionTest(object):
    def __init__(
        self,
        ranges=[],
        ports=[],
        exclude_ranges=[],
        timeout=1,
        threads=250,
        shuffle=True,
    ):
        """
        params:
            scan_ranges: [{},]
                A list of ranges defined by dictionaries (extensible)
                    {"cidr": "172.20.0.0/16"}
            scan_ports: []
                A set of ports which ALL MUST be reachable
        """
        self.exclude_ranges = exclude_ranges
        self.include_ranges = ranges
        self.scan_ports = ports
        self.timeout = timeout
        self.threads = threads
        self.shuffle = shuffle

    @property
    def evaluate_ranges(self):
        logger.debug("Extracting CIDR ranges")
        ip_addresses = set()
        for scan_range in self.include_ranges:
            ip_addresses = ip_addresses.union(self._expand_range(scan_range))
        for scan_range in self.exclude_ranges:
            ip_addresses = ip_addresses.difference(
                self._expand_range(scan_range)
            )
        return ip_addresses

    def _expand_range(self, scan_range):
        ip_addresses = set()
        logger.debug("Reading range: %s" % scan_range)
        cidr_range = scan_range.get("cidr")
        if cidr_range:
            logger.debug("Yielding: %s" % cidr_range)
            for addr in IPv4Network(cidr_range):
                ip_addresses.add(str(addr))
        return ip_addresses

    def get_scan_df(self):
        # https://docs.python.org/3/library/ipaddress.html
        scan_data = []
        for host in self.evaluate_ranges:
            for port in self.scan_ports:
                scan_data.append([host, port])
        return pd.DataFrame(scan_data, columns=["host", "port"])

    @staticmethod
    def test_conn_socket(connection_df_slice):
        """test a connection"""
        for idx, conn_test_row in connection_df_slice.iterrows():
            logger.debug("Testing connection: %s" % conn_test_row)

            s = socket.socket()
            try:
                port = int(conn_test_row.port)
                s.connect((conn_test_row.host, port))
                connection_df_slice.at[idx, "socket_conn"] = True
                connection_df_slice.at[idx, "socket_conn_error"] = ""
                logger.debug("%s:%s OPEN" % (conn_test_row.host, port))
            except Exception as e:
                connection_df_slice.at[idx, "socket_conn_error"] = "%s" % e
                connection_df_slice.at[idx, "socket_conn"] = False
                logger.debug("%s:%s CLOSED" % (conn_test_row.host, port))

            finally:
                s.close()

        return connection_df_slice

    def test_socket_conns(self, connection_test_df):
        # Create multithread pool
        pool = Pool(self.threads)
        if self.shuffle:
            connection_test_df = connection_test_df.sample(frac=1)
        # Split array up
        df_splits = np.array_split(connection_test_df, self.threads)
        result_df = pd.concat(
            pool.map(self.test_conn_socket, df_splits), sort=False
        )
        pool.close()
        pool.join()
        return result_df

    def execute(self):
        scan_df = self.get_scan_df()
        logger.info(
            "Executing Network Scan (%s tests, %s threads, %s timeout):\n%s"
            % (len(scan_df), self.threads, self.timeout, scan_df)
        )
        socket.setdefaulttimeout(self.timeout)
        result = self.test_socket_conns(scan_df)
        return result
