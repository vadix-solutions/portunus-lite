##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import importlib
import json
import pkgutil
from datetime import datetime

from celery.utils.log import get_task_logger

from vdx_id_agent.agent_interfaces import AgentMultiException
from vdx_id_agent.vdx_agent import agent

from .agent_crypto import decrypt_payload, get_public_key
from .connection_test import ConnectionTest

logger = get_task_logger(__name__)


@agent.task
def get_agent_metadata(task_id=None):
    """Return the agent health and task metadata.
    This should be called from the platform via
    result = execute_agent_task("get_agent_status")
    """
    # TODO: Add lsof, mem and other health info to this response
    status = {
        "datestamp": "%s" % datetime.now(),
        "public_key": get_public_key(),
    }
    logger.debug("Retrieved agent metadata: %s" % status)
    return status


def get_interface_apis():
    interfaces = {}
    interface_modules = import_interface_submodules("vdx_id_agent")
    for interface_path, module in interface_modules.items():
        logger.debug("Retrieving API of %s" % interface_path)
        interface = module.PlatformInterface()
        interfaces[interface.interface_id] = interface.get_interface_api()
    return interfaces


def import_interface_submodules(package, recursive=True):
    """ Import all submodules of a module, recursively, including subpackages

    :param package: package (name or actual module)
    :type package: str | module
    :rtype: dict[str, types.ModuleType]
    """
    if isinstance(package, str):
        logger.debug("Importing package %s" % package)
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + "." + name
        if name == "interfaces":
            logger.debug("Loading package API (%s): %s" % (package, full_name))
            results[full_name] = importlib.import_module(full_name)
        if recursive and is_pkg:
            results.update(import_interface_submodules(full_name))
    return results


@agent.task(name="connection_test")
def connection_test(src_id, scan_definition, task_id=None):
    """Connection Test

    This function performs connectivity testing based on `scan_definition`

    Attributes:
        src_id (str): Identifier for the agent performing the scan

        scan_definition (dict): Dict of arguments to ConnectionTest instance.

            Should contain ranges=[], ports=[], exclude_ranges=[]
            Where ranges is a list of dict objects:
                {"cidr": "172.20.0.0/16"}

    Todo:
        * Support additional range syntax (e.g. wildcard)

    .. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html
    """
    connection_test = ConnectionTest(**scan_definition)
    test_results = connection_test.execute()

    host_count = 0
    scan_results = {}
    for host in test_results["host"].unique():
        host_results = test_results[test_results["host"] == host]
        for idx, row in host_results.iterrows():
            scan_results["%s" % host] = {
                "%s"
                % row.port: {
                    "connected": row.socket_conn,
                    "error": row.socket_conn_error,
                }
            }
            if row.socket_conn:
                host_count += 1
    scan_results = {"%s" % src_id: scan_results}
    logger.info("Returning Scan Data (%s hosts)" % host_count)
    return scan_results


@agent.task(name="interface_action")
def interface_action(interface_id, action, enc_data_set, *args, **kwargs):
    logger.info("Received Action(%s)" % (action))
    logger.debug("Received Enc Dataset(%s)" % (enc_data_set))
    logger.debug("Received args(%s) kwargs(%s)" % (args, kwargs))

    # Find the appropriate interface
    interface = None
    interface_modules = import_interface_submodules("vdx_id_agent")
    for module in interface_modules.values():
        iface = module.PlatformInterface
        if iface.interface_id == interface_id:
            interface = iface()
            break

    # Then iterate the call to the interface
    if interface:
        try:
            dec_bytes = decrypt_payload(enc_data_set)
            data_set = json.loads(dec_bytes)
        except ValueError:
            logger.error("Data decryption failed - possible stagnant keyset")
            raise
        try:
            interface.iterate_call(action, data_set, *args, **kwargs)
        except AgentMultiException as e:  # noqa: E722
            raise AgentMultiException(str(e))
        except Exception:
            raise Exception("Unexpected agent exception")
        del interface
    else:
        raise KeyError("Interface ID '%s' not matched" % interface_id)
