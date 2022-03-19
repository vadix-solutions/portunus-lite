##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

from django.conf import settings
from django.core.cache import cache

from vdx_id.celery import app

logger = logging.getLogger(__name__)


def _check_if_cache_lock(
    cache_lock_key, new_task_id, timeout=settings.CACHE_LOCK_TIMEOUT
):
    """Checks for a key in the Redis Cache to prevent undesired parallellism"""
    existing_task_id = cache.get(cache_lock_key)
    if existing_task_id:
        # Get the ready_state
        try:
            ready_state = app.AsyncResult(existing_task_id).ready()
        except AttributeError:
            logger.exception("Failed to find ready_state - marking as true")
            ready_state = True

        if ready_state:
            logger.warning(
                "Cached taskid(%s) found, but was ready()" % cache_lock_key
            )
            cache.delete(cache_lock_key)
        else:
            logger.warning(
                "Cached taskid(%s) not ready - aborting" % cache_lock_key
            )
            return True
    else:
        logger.debug("Setting lock, task_id=%s" % new_task_id)
        cache.set(cache_lock_key, new_task_id, timeout)


def expand_task_to_final_children(task, get_children=False):
    child_ids = []
    if task.parent:
        _, children = expand_task_to_final_children(
            task.parent, get_children=True
        )
        child_ids += children
    if get_children and task.children:
        child_ids += [t.id for t in task.children]
    return task.id, child_ids


# Dont be a punk, gotta chunk de funcs; so message bus not sunk
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]
