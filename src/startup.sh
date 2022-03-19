#!/usr/bin/env bash
python3 /opt/vdx_id/manage.py migrate
python3 /opt/vdx_id/manage.py clear_cache
python3 /opt/vdx_id/manage.py runserver 0.0.0.0:8000
