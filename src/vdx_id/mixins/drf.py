##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging
from collections import OrderedDict

from django.urls import NoReverseMatch, reverse

logger = logging.getLogger(__name__)


# api:id_infra:access_domain-attach-servers
# api:id_infra:access_domain-detail


class ActionMapping(object):
    def get_extra_action_url_map(self):
        action_urls = OrderedDict()

        # exit early if `detail` has not been provided
        if self.detail is None:
            return action_urls

        # filter for the relevant extra actions
        actions = [
            action
            for action in self.get_extra_actions()
            if action.detail == self.detail
        ]
        for action in actions:
            try:
                url_name = "%s-%s" % (self.basename, action.url_name)
                namespace = self.request.resolver_match.namespace
                if namespace:
                    url_name = "%s:%s" % (namespace, url_name)
                url = reverse(url_name, kwargs=self.kwargs)
                view = self.__class__(**action.kwargs)
                action_urls[view.get_view_name()] = url
            except NoReverseMatch as exc:
                logger.error(f"Issue resolving action({action}): {exc}")
                pass  # URL requires additional arguments, ignore

        return action_urls
