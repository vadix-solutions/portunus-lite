##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging
import re
import warnings
from string import Formatter

from django.conf import settings

_frmtr = Formatter()
logger = logging.getLogger("vdx_id.%s" % __name__)


class MissingArgException(Exception):
    """Used to flag an argument is missing"""

    pass


class UnresolvableArgException(Exception):
    """Used to flag that whatever arg should be omitted"""

    pass


def getattrd(obj, name):
    """
    Same as getattr(), but allows dot notation lookup
    Discussed in:
    http://stackoverflow.com/questions/11975781
    Extended to include Dict/List access
    """
    # TODO: Add support for template-tag effect (|upper)
    # TODO: Add support for Vault access (with cached connection)
    obj_p = obj
    transform = None
    if "|" in name:
        name, transform = name.split("|")
    for npart in name.split("."):
        try:
            if type(obj_p) is dict:
                obj_p = obj_p[npart]
            elif type(obj_p) is list:
                obj_p = obj_p[int(npart)]
            else:
                obj_p = getattr(obj_p, npart)
        except (AttributeError, KeyError) as e:
            raise MissingArgException(
                f"Couldn't resolve {npart} of {name} in {obj}: {e}"
            )
    if transform:
        if hasattr(obj_p, transform):
            return getattr(obj_p, transform)()
        elif hasattr(type(obj_p), transform):
            return getattr(type(obj_p), transform)(obj_p)
        else:
            warnings.warn(f"Unknown Transform: {transform}")
    return obj_p


def resolve_templatevar_in_obj(obj, template_string, raise_unresolved=False):
    """Given an object, and template_string like 'obj.attrib1.prop'
    Will retrieve the value of prop in attrib1 of obj."""
    # Ensure right type
    if type(template_string) not in [bytes, str]:
        return
    # Ensure contains templates
    param_names = re.findall(r"\{(?:[^{}])*\}", template_string)
    if not param_names:
        return
    # Resolve the referenced variable
    for pname in param_names:
        try:
            val = getattrd(obj, pname[1:-1])  # strip the {}
            if val is not None:
                template_string = template_string.replace(pname, str(val))
        except MissingArgException:
            if raise_unresolved:
                raise
            return None
    return template_string


def fulfil_args_from_objects(arg_dict, object_arr, raise_if_missing=True):
    """Retrieves args in arg_dict.keys from objects in object_arr.
    Can optionally raise an exception if args not satisfied (default:true).
    Can override existing values as it searches through Objs (default:false).
    Recurses into objects if values match a regex defined in
        settings.ATTRIBUTE_REGEX
    """
    # Check if we have any arguments to resolve
    if None not in arg_dict.values():
        return

    logger.debug(
        "Resolving args %s from Objs: %s"
        % ([key for key, val in arg_dict.items() if val is None], object_arr)
    )

    # Find the inferred arguments and update them with our initial request
    inf_key_list, inf_arg_dict = extract_inferred_keys(
        arg_dict, pattern_regex=settings.ATTRIBUTE_REGEX
    )
    arg_dict.update(inf_arg_dict)

    _resolve_params_from_objs(arg_dict, object_arr)
    _resolve_secrets(arg_dict)

    # Resolve the inferred args
    # hostname = {address} & address = 1.0.1.0 -> hostname = 1.0.1.0
    for key in inf_key_list:
        satified_str = arg_dict[key].format(**arg_dict)
        if satified_str:
            arg_dict[key] = satified_str

    # Maybe raise an exception if any args missing
    if raise_if_missing and None in arg_dict.values():
        missing_args = list(
            arg for arg, val in arg_dict.items() if val is None
        )
        raise MissingArgException(
            "Args(%s) not satisfied in Objs %s" % (missing_args, object_arr)
        )


def _resolve_secrets(arg_dict):
    """Find and resolve any keys which use the VAULT_ATTRIBUTE_REGEX"""
    secret_key_list, secret_arg_dict = extract_inferred_keys(
        arg_dict, pattern_regex=settings.VAULT_ATTRIBUTE_REGEX
    )
    if len(secret_key_list) == 0:
        return

    # Retrieve the secrets from the HC Vault
    # TODO: Use the VaultMixin on the access-domain...
    # secret_client.resolve_secrets_from_vault(secret_arg_dict)

    # Insert all resolved secret keys
    for key in secret_key_list:
        # Strip the vault: prefix (pattern defined in settings_platform)
        arg_string = arg_dict[key].replace("vault:", "")
        arg_dict[key] = arg_string.format(**secret_arg_dict)


def extract_inferred_keys(arg_dict, pattern_regex):
    """Extracts inferred key info from dict.
    A list is returned for all keys requiring inferred values.
    A dict is returned of {key: None} for each key."""
    inf_key_list = []  # Records keys which infer other args in value
    inf_arg_dict = {}  # A new arg_dict for inferred args
    for k, v in arg_dict.items():
        logger.debug("Checking inferred in '%s'" % str(v))
        matches = pattern_regex.findall(str(v))
        if matches:
            # Store this key as needing inferred value
            inf_key_list.append(k)
            # Enter each of the parameters to the inf arg dict
            for inferred_key in matches:
                inf_arg_dict[inferred_key] = None
    if len(inf_key_list) > 0:
        logger.debug("Found inferred arguments: %s" % inf_arg_dict)
    return inf_key_list, inf_arg_dict


def _resolve_params_from_objs(arg_dict, object_arr):
    def _resolve_paramset_in_obj(arg_param_dict, obj):
        # If this obj is a dictionary and has they key, grab that
        pending_params = set(
            key for key, val in arg_param_dict.items() if val is None
        )
        if len(pending_params) == 0:
            return

        logger.debug("Searching object(%s) for %s" % (obj, pending_params))

        def _resolve_if_dict(o):
            if type(o) == dict:
                matched_params = pending_params.intersection(set(o.keys()))
                logger.debug("Found matching keys: %s" % matched_params)
                for param in matched_params:
                    if o[param] is not None:
                        arg_param_dict[param] = o[param]
                        pending_params.remove(param)

        def _resolve_if_has_attrs(o):
            # Otherwise try get it via attribute
            if hasattr(o, "__dict__"):
                matched_params = pending_params.intersection(
                    set(o.__dict__.keys())
                )
                logger.debug("Found matching attrs: %s" % matched_params)
                for param in matched_params:
                    val = getattr(o, param)
                    if val is not None:
                        arg_param_dict[param] = val
                        pending_params.remove(param)

        if pending_params:
            _resolve_if_dict(obj)
        if pending_params:
            _resolve_if_has_attrs(obj)
        # Finally iterate through task_parameter generator if available
        if pending_params and hasattr(obj, "task_parameters"):
            for obj_params in obj.task_parameters:
                _resolve_if_dict(obj_params)
                _resolve_if_has_attrs(obj_params)

    # For each object in the list given
    for obj in object_arr:
        # For each argument that we need to satisfy
        _resolve_paramset_in_obj(arg_dict, obj)
