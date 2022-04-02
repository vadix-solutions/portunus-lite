# Portunus Lite

Infrastructure identification and data collection should not be hard.

Portunus Lite provides a relatively simple platform that can handle IOT scale infrastructure, with enterprise legacy components, quickly.

## Getting started

1. Start up the platform
`docker-compose up -d`
2. Migrate
`docker-compose exec django_wsgi python3 manage.py migrate`
3. Collect Static for frontend
`docker-compose exec django_wsgi python3 manage.py collectstatic --no-input`
4. Load data to have a starting point
```docker-compose exec django_wsgi python3 manage.py loaddata init_data
docker-compose exec django_wsgi python3 manage.py loaddata periodic_tasks
```
5. Check the logs for any exceptions!
`docker-compose logs -f --tail 50`

This will start up Portunus with a simple 'AccessDomain', a Host-scan definition to find some hosts, and a few other pieces.
It is functional at this stage but you should refer to the Docs to properly manage Portunus.

## Deploying an Agent

Portunus uses Agents to scan infrastructure. It deploys by default with one LOCAL agent, but is designed to have a number of them, even globally distributed.

Here is how you can deploy an Agent:

I.O.U docs

