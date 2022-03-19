#!/usr/bin/env bash

LLEV=${LOGLEVEL:-INFO}

rm -f './celerybeat.pid'
# celery -A vdx_id worker -l DEBUG --beat
celery -A vdx_id beat -l $LLEV --scheduler django_celery_beat.schedulers:DatabaseScheduler
