##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

from django.template import loader
from rest_framework import renderers, status
from rest_framework.request import override_method

logger = logging.getLogger("vdx_id.%s" % __name__)


class VdxIdApiRenderer(renderers.AdminRenderer):
    template = "vdx_id_renderers/vdxid_ui_api_view.html"
    # filter_template = "rest_framework/filters/base.html"
    format = "admin"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        self.accepted_media_type = accepted_media_type or ""
        self.renderer_context = renderer_context or {}

        response = renderer_context["response"]
        request = renderer_context["request"]
        view = self.renderer_context["view"]

        if response.status_code == status.HTTP_400_BAD_REQUEST:
            # Errors still need to display the list or detail information.
            # The only way we can get at that is to simulate a GET request.
            self.error_form = self.get_rendered_html_form(
                data, view, request.method, request
            )
            self.error_title = {"POST": "Create", "PUT": "Edit"}.get(
                request.method, "Errors"
            )
            if hasattr(view, "get"):
                if request.method == "PUT":
                    data = response.data
                    with override_method(view, request, "GET") as request:
                        response = view.get(request, *view.args, **view.kwargs)
                else:
                    logger.info(self.renderer_context)
                    response = view.get(request, *view.args, **view.kwargs)

        template = loader.get_template(self.template)
        context = self.get_context(data, accepted_media_type, renderer_context)
        ret = template.render(context, request=renderer_context["request"])

        # Creation and deletion should use redirects in the admin style.
        if (
            response.status_code == status.HTTP_201_CREATED
            and "Location" in response
        ):
            response.status_code = status.HTTP_303_SEE_OTHER
            response["Location"] = request.build_absolute_uri()
            ret = ""

        if response.status_code == status.HTTP_204_NO_CONTENT:
            response.status_code = status.HTTP_303_SEE_OTHER
            try:
                # Attempt to get the parent breadcrumb URL.
                response["Location"] = self.get_breadcrumbs(request)[-2][1]
            except KeyError:
                # Otherwise reload current URL to get a 'Not Found' page.
                response["Location"] = request.full_path
            ret = ""

        return ret
