#!/usr/bin/env bash

AGENT_QUEUE=${AGENT_QUEUE:-agent_default}
LOGLEVEL=${LOGLEVEL:-WARN}

echo "Starting agent with queue: $AGENT_QUEUE"
celery -A vdx_id_agent.vdx_agent.agent worker \
    -l $LOGLEVEL -Q agent,$AGENT_QUEUE -E -n $AGENT_QUEUE@%h
