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