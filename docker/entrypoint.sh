#!/bin/bash
set -e

cd /app/backend

mkdir -p /app/backend/logs

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
    python manage.py shell -c "
import os
from apps.authentication.models import User
email = os.environ.get('ADMIN_EMAIL', '')
password = os.environ.get('ADMIN_PASSWORD', '')
if email and password and not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email, password, full_name='Administrador', role='admin')
    print(f'Superuser {email} created')
" 2>&1 || true
fi

WORKERS=${WEB_CONCURRENCY:-1}
exec gunicorn --bind 0.0.0.0:8000 --workers $WORKERS --timeout 120 config.wsgi:application
