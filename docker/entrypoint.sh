#!/bin/bash
set -e

cd /app/backend

mkdir -p /app/backend/logs

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

WORKERS=${WEB_CONCURRENCY:-2}
exec gunicorn --bind 0.0.0.0:8000 --workers $WORKERS --timeout 120 config.wsgi:application
