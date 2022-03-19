##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

from __future__ import absolute_import

import hashlib
import importlib
import inspect
import logging
import os

logger = logging.getLogger(__name__)


def backoff_hdlr(details):
    logger.exception(
        "Backing off {wait:0.1f} seconds afters {tries} tries "
        "calling function {target} with args {args} and kwargs "
        "{kwargs}".format(**details)
    )


class BaseConnectionInterface(object):
    active_connection = None
    required_parameters = []
    optional_parameters = []

    def __init__(self, **kwargs):
        logger.debug("Initializing interface with kargs%s" % kwargs)
        required_args = list(self.required_parameters)
        for arg, val in kwargs.items():
            setattr(self, arg, val)
            if arg in required_args:
                required_args.remove(arg)
        if required_args:
            raise Exception(
                "Some required arguments missing: %s" % required_args
            )

    def open_connection(self):
        return NotImplementedError()

    def close_connection(self):
        return NotImplementedError()

    def run_command(self):
        return NotImplementedError()


class AgentMultiException(Exception):
    pass


class BasePlatformInterface(object):
    # TODO: Enforce that special attributes (e.g. 'locked' are used)
    # TODO: Collection Schema enforcement
    interface_signature = "interface_action"

    _connection = None
    connection_interface = None

    @property
    def connection_class(self):
        if self.connection_interface is None:
            raise Exception("Connection interface not defined")
        if not self._connection:
            con_mod, con_cls = self.connection_interface.split(":")
            interface_class = importlib.import_module(con_mod)
            self._connection = getattr(interface_class, con_cls)
        return self._connection

    def __get_code_hash(self):
        class_tuple = inspect.getmro(self.__class__)
        md5 = hashlib.md5()
        for cls_inst in class_tuple:
            if cls_inst.__module__ in "builtins":
                continue
            cls_file = os.path.abspath(inspect.getfile(cls_inst))
            md5.update(open(cls_file, "rb").read())
        return md5.hexdigest()

    connection = None
    _cached_connection_args = None

    def get_connection(self, connection_args):
        logger.debug("Connection args: %s" % connection_args)
        all_connection_args = (
            self.connection_class.required_parameters
            + self.connection_class.optional_parameters
        )
        avail_connection_args = {
            k: connection_args[k]
            for k in all_connection_args
            if k in connection_args.keys()
        }
        if (
            self._cached_connection_args == avail_connection_args
            and self.connection
        ):
            return self.connection
        self._cached_connection_args = avail_connection_args
        if self.connection:
            self.connection.close_connection()
        self.connection = self.connection_class(**avail_connection_args)
        self.connection.open_connection()

    def get_apicall_params(self, api_call):
        function_sig = inspect.signature(getattr(self, api_call))
        args, kwargs = [], []
        for name, param in function_sig.parameters.items():
            if param.default == param.empty:
                args.append(name)
            else:
                kwargs.append(name)
        return args, kwargs

    def iterate_call(self, api_call, data_list, **kwargs):
        interface_function = getattr(self, api_call)
        if interface_function is None:
            raise NotImplementedError()

        logger.debug("Data list: %s" % (data_list,))

        required_props, optional_props = self.get_apicall_params(api_call)

        call_errors = []
        for data_obj in data_list:

            logger.warning("Running api-call(%s)" % (api_call))
            self.get_connection(data_obj)

            func_args = [data_obj[prop] for prop in required_props]
            logger.debug("Func args: %s" % (func_args))

            func_kwargs = {}
            for optional_prop in optional_props:
                val = data_obj.get(optional_prop)
                logger.debug("Prop('%s') value: %s" % (optional_prop, val))
                if val:
                    func_kwargs[optional_prop] = val
            logger.debug("Func kwargs: %s" % (func_kwargs))

            try:
                logger.debug(
                    "Calling: %s(%s, %s)"
                    % (interface_function, func_args, func_kwargs)
                )
                func_kwargs.update(kwargs)
                response = interface_function(*func_args, **func_kwargs)
                logger.debug("Response: %s" % response)
            except Exception as e:
                logger.exception("Error calling: %s" % api_call)
                logger.debug("Exception: %s" % e)
                call_errors.append(e)
            finally:
                # TODO: Consider connection pooling here
                self.connection.close_connection()

        if call_errors:
            raise AgentMultiException(call_errors)
