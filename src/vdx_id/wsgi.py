##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

"""
WSGI config for vdx_id
vdx_id project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vdx_id.settings")

application = get_wsgi_application()
