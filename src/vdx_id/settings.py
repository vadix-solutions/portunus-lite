##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

"""
Django settings for vdx_id project.

Generated by 'django-admin startproject' using Django 2.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import ssl
import sys

# from celery.schedules import crontab
from celery.signals import setup_logging
from django.conf.locale.en import formats as en_formats

from .settings_platform import *  # noqa: F403 F401

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "**$8a$hz!t3&s9om95)d0n)@%owfsbjf5z=q4$av2k%o@_q+4q-"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.sites",
    "django.contrib.contenttypes",
    "django.contrib.admindocs",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "jazzmin",
    "vdx_id.apps.PortunusConfig",
    "constance",
    "constance.backends.database",
    "id_infra",  # Core portunus module
    "web_interface",
    "explorer",
    "polymorphic",
    "notifications",
    "report_builder",
    "django_filters",
    "django_extensions",
    "simple_history",
    "django_celery_beat",
    "django_json_widget",
    "debug_toolbar",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "rest_framework",
    "rest_framework_swagger",
    "rest_framework_extensions",
    "django.contrib.admin",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    # "csp.middleware.CSPMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "vdx_id.urls"

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    }
]

WSGI_APPLICATION = "vdx_id.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "HOST": "db",
        "PORT": 5432,
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "MinimumLengthValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "NumericPasswordValidator"
    },
]


REDIS_CACHE = "redis://%s:%s/0" % (
    os.environ.get("REDIS_HOST", "redis"),
    os.environ.get("REDIS_PORT", 16379),
)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_CACHE,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "vdx_cache",
    },
    "db_cache": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "db_cache",
    },
}
CACHE_TTL = 60 * 15


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_ID = 1

LOGIN_REDIRECT_URL = "/"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = "/static/"

AUTH_USER_MODEL = "vdx_id.VdxIdUser"  # new

CRISPY_TEMPLATE_PACK = "bootstrap4"

# ########################### REST Framework/Swaggah ##########################
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend"
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAdminUser"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",  # noqa: E501
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "PAGE_SIZE": 250,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}

SWAGGER_SETTINGS = {
    "exclude_namespaces": [],
    "api_version": "0.3.0",
    "api_path": "/",
    "enabled_methods": ["get", "post"],
    "is_authenticated": False,
    "is_superuser": False,
    "permission_denied_handler": None,
    "info": {
        "contact": "dan.vagg@vadix.io",
        "description": "VaDiX Portunus REST API. ",
        "title": "Portunus API",
    },
    "doc_expansion": "full",
    "model_rendering": "schema",
}
# ----------------------------------------------------------------------------

# ########################### Logging ###########################
# TODO: Syslog logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s"
            "[%(name)s.%(funcName)s:%(lineno)d]"
            "%(message)s"
        },
        "simple": {
            "format": "%(asctime)s %(levelname)s"
            "[%(funcName)s:%(lineno)d]"
            "%(message)s"
        },
    },
    "filters": {
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue"}
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            # "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "stream": sys.stderr,
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "daphne": {"handlers": ["console"], "level": "DEBUG"},
        "django": {"handlers": ["console"], "propagate": True},
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "vdx_id": {
            "handlers": ["console", "mail_admins"],
            "level": "INFO",
            # Set to False to prevent double logging in Celery
            "propagate": False,
        },
        "celery": {
            "handlers": ["console", "mail_admins"],
            "level": "INFO",
            "propagate": False,
        },
        "celery.app": {
            "handlers": ["console", "mail_admins"],
            "level": "WARN",
            "propagate": False,
        },
        "celery.worker": {
            "handlers": ["console", "mail_admins"],
            "level": "WARN",
            "propagate": False,
        },
        "celery.beat": {
            "handlers": ["console", "mail_admins"],
            "level": "WARN",
            "propagate": True,
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

# This is done so that PyTest will get logs
if "PYTEST_CURRENT_TEST" in os.environ:
    LOGGING["loggers"]["vdx_id"]["propagate"] = True


@setup_logging.connect
def configure_logging(sender=None, **kwargs):
    import logging
    import logging.config

    logging.config.dictConfig(LOGGING)


NOTEBOOK_ARGUMENTS = [
    "--allow-root",
    "--notebook-dir",
    "/opt/vdx_id/notebooks",
    "--ip",
    "0.0.0.0",
    "--port",
    "1337",
]

#  ---------------------------------------------------------------------------

# Channels settings
ASGI_APPLICATION = "vdx_id.routing.application"

redis_backend_url = "redis://%s:%s/5" % (
    os.environ.get("REDIS_HOST", "redis_int"),
    os.environ.get("REDIS_PORT", 16379),
)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": ({"address": redis_backend_url},)
        },
    }
}

# Use this to control django debug toolbar appearing
INTERNAL_IPS = [
    "127.0.0.1",
    "172.17.0.1",
    "172.18.0.1",
    "172.20.0.1",
    # '172.18.0.18',
]
if DEBUG:
    import socket  # only if you haven't already imported this

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[:-1] + "1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]


def show_toolbar(request):
    return True


# DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": show_toolbar}

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

CONSTANCE_ADDITIONAL_FIELDS = {
    "json": [
        "django.contrib.postgres.forms.JSONField",
        {
            "widget": "django_json_widget.widgets.JSONEditorWidget",
            "widget_kwargs": {"width": "600px"},
        },
    ],
    # "duration": [
    #     "django.forms.DurationField",
    #     {
    #         "widget": "django_json_widget.widgets.DurationField",
    #     },
    # ]
}
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_DATABASE_CACHE_BACKEND = "default"
CONSTANCE_DATABASE_PREFIX = "constance:portunus:"

# Django-CSP (used for embeds)
# CSP_SCRIPT_SRC = (
#     "'self'",
#     "'unsafe-inline'",
#     "https://cdn.datatables.net",
#     "https://cdnjs.cloudflare.com",
#     "https://cdn.rawgit.com",
#     "https://cdn.segment.com",
#     "https://unpkg.com",
# )
# CSP_STYLE_SRC = (
#     "'self'",
#     "'unsafe-inline'",
#     "fonts.googleapis.com",
#     "https://cdn.datatables.net",
#     "https://maxcdn.bootstrapcdn.com",
#     "https://unpkg.com",
# )
# CSP_FONT_SRC = (
#     "'self'",
#     "fonts.gstatic.com",
#     "https://maxcdn.bootstrapcdn.com",
# )
# CSP_IMG_SRC = (
#     "'self'",
#     "https://www.gravatar.com",
#     "https://api.mapbox.com"
# )
# CSP_FRAME_SRC = ("'self'", "https://biteable.com")
# CSP_FRAME_ANCESTORS = ("'self'", "biteable.com")

# Show datestamps with second-level accuracy
en_formats.DATETIME_FORMAT = "d M Y H:i:s"
