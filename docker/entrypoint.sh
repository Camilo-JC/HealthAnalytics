#!/bin/bash
set -e

cd /app/backend

mkdir -p /app/backend/logs

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
    python manage.py createsuperuser --noinput --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD" 2>/dev/null || true
fi

WORKERS=${WEB_CONCURRENCY:-1}
exec gunicorn --bind 0.0.0.0:8000 --workers $WORKERS --timeout 120 config.wsgi:application
