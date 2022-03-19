##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import os
import re
import ssl
from datetime import timedelta

##########################
# 'all-auth' settings
##########################
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_QUERY_EMAIL = True
LOGIN_REDIRECT_URL = "/"


# Admin
JAZZMIN_SETTINGS = {
    "site_title": "Portunus Lite Admin",
    "site_header": "Portunus Lite",
    "site_brand": "Portunus Lite",
    "site_logo": "/portunus_logo_800600.png",
    # CSS classes that are applied to the logo above
    "site_logo_classes": "img-circle",
    "site_icon": "/favicon.ico",
    # Welcome text on the login screen
    "welcome_sign": "Welcome to Portunus Lite",
    # Copyright on the footer
    "copyright": "VaDiX Solutions Ltd",
    "user_avatar": None,
    ############
    # Top Menu #
    ############
    # Links to put along the top menu
    "topmenu_links": [
        # Url that gets reversed (Permissions can be added)
        {
            "name": "Home",
            "url": "admin:index",
            "permissions": ["auth.view_user"],
        },
        # external url that opens in a new window (Permissions can be added)
        {"name": "Documentation", "url": "/docs", "new_window": True},
        # model admin to link to (Permissions checked against model)
        {"app": "id_infra"},
    ],
    #############
    # User Menu #
    #############
    "usermenu_links": [{"model": "auth.user"}],
    #############
    # Side Menu #
    #############
    # Whether to display the side menu
    "show_sidebar": True,
    # Whether to aut expand the menu
    "navigation_expanded": False,
    # Hide these apps when generating side menu e.g (auth)
    "hide_apps": ["account", "allauth"],
    "hide_models": [],
    "order_with_respect_to": [],
    # Custom links to append to app groups, keyed on app name
    # "custom_links": {
    #     "id_infra": [{
    #         "name": "Make Messages",
    #         "url": "id_infra",
    #         "icon": "fas fa-comments",
    #         # "permissions": ["id_infra"]
    #     }]
    # },
    # for the full list of 5.13.0 free icon classes
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    #################
    # Related Modal #
    #################
    # Use modals instead of popups
    "related_modal_active": True,
    #############
    # UI Tweaks #
    #############
    # Relative paths to custom CSS/JS scripts (must be present in static files)
    "custom_css": None,
    "custom_js": None,
    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": True,
    ###############
    # Change view #
    ###############
    # - single
    # - horizontal_tabs (default)
    # - vertical_tabs
    # - collapsible
    # - carousel
    "changeform_format": "vertical_tabs",
    # override change forms on a per modeladmin basis
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
    # Add a language dropdown into the admin
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "cosmo",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-outline-info",
        "warning": "btn-outline-warning",
        "danger": "btn-outline-danger",
        "success": "btn-outline-success",
    },
}


##########################
# Celery settings
##########################
BASE_DATA_DIR = "/data/"

# https://github.com/celery/celery/issues/4184#issuecomment-321456270
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = "UTC"
# CELERY_TIMEZONE = "Europe/Dublin"

TASK_SOFT_TIME_LIMIT = 600

REDIS_HOST = os.environ.get("REDIS_HOST", "redis_int")
REDIS_PORT = os.environ.get("REDIS_PORT", 16379)

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"

CELERY_IGNORE_RESULT = False

CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_PERSISTENT = True

CELERY_ACCEPT_CONTENT = ["json"]
task_serializer = "json"
CELERY_RESULT_SERIALIZER = "json"

CELERY_SEND_EVENTS = True
CELERY_TRACK_STARTED = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SEND_SENT_EVENT = True

CELERY_TASK_DEFAULT_QUEUE = "platform"
task_default_queue = CELERY_TASK_DEFAULT_QUEUE
CELERY_TASK_TIME_LIMIT = 90
CELERY_WORKER_MAX_TASKS_PER_CHILD = 50

CELERY_WORKER_HIJACK_ROOT_LOGGER = False

DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000

###########################
# Portunus settings
###########################
DATA_DIR = "/data"
DAG_DIR = "/data/dags"

# Collection records
# https://redislabs.com/wp-content/uploads/2017/02/04-Yossi-Gottlieb-Redis-Labs.pdf
COLLECTION_STORE_PARAMS = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "db": 3,
}

EXPLORER_CONNECTION_NAME = "default"
EXPLORER_CONNECTIONS = {"default": "default"}
EXPLORER_DEFAULT_CONNECTION = "default"
EXPLORER_TASKS_ENABLED = True
EXPLORER_ASYNC_SCHEMA = True

CELERY_QUEUE_ACCOUNTS = "agent"
ATTRIBUTE_REGEX = re.compile(r"\{([A-z_\.]+)\}")

VAULT_ATTRIBUTE_REGEX = re.compile(r"\{vault:([A-z_\.]+)\}")
VAULT_HOST = "http://vault:8200"
VAULT_SECRET_MOUNT = "portunus"

COLL_TSTAMP = "%Y%m%dT%H%M%S"
# SERVERSIDE_TABLES:
# Tables rendered by the platform will be fitlered/searched on the server-side
SERVERSIDE_TABLES = False

# AGENT_TASK_POOL_TIME: Duration(s) tasks remain in pool for batch submission
RETRY_BACKOFF = 2
CACHE_LOCK_TIMEOUT = 10

# AUTO_COLLECT_COUNTDOWN:
# How long to wait(seconds) before running a collection after a AgentApiTask
#   on that access-domain has completed
AUTO_COLLECT_COUNTDOWN = 3

# Max amount of workorders to submit in a single iter of
#   submit_pending_workorders()
# How many separate tasks should be sent to the agent for a WorkOrder
#   e.g. a WO with 50 servers, and segmentation of 5 will send 5 tasks
#         each with the arguments for 10 servers
# This allows for parallelisation if there are sufficient worker threads
AGENT_TASK_SEGMENTATION = 5

# SQL explorer (False for testing)
EXPLORER_ENABLE_TASKS = False
EXPLORER_ASYNC_SCHEMA = False

VAULT_URL = "http://localhost:8000/"

CONSTANCE_CONFIG = {
    "MAP_COORDINATES": (
        {},
        "GPS coordinates for AccessDomains/Agents/etc",
        "json",
    ),
}


# GROUP Definitions used throughout platform
# Only change these if the Groups in Portunus Admin have changed
GROUP_PORTUNUS_ADMIN = "Portunus Operator"
from vdx_id.celery import app  # noqa: E402

app.autodiscover_tasks()
