##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

"""vdx_id
vdx_id URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import notifications.urls
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework_swagger.views import get_swagger_view

app_name = "vdx_id"

api_urls = [
    path("infra/", include("id_infra.urls")),
]

urlpatterns = [
    path("", include(("web_interface.urls", "web"), namespace="web")),
    path("api/", include((api_urls, "api"), namespace="api")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("allauth_accounts/", include("allauth.urls")),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path(
        "inbox/notifications/",
        include(
            (notifications.urls, "notifications"), namespace="notifications"
        ),
    ),
    path("docs_api/", get_swagger_view(title="Portunus API")),
    path("explorer/", include("explorer.urls")),
    path("report_builder/", include("report_builder.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls))
    ] + urlpatterns
