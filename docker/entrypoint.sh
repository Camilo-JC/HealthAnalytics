#!/bin/bash
set -e

cd /app/backend

mkdir -p /app/backend/logs

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
    echo "--- Checking superuser $ADMIN_EMAIL ---"
    python manage.py shell -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from apps.authentication.models import User
email = os.environ.get('ADMIN_EMAIL', '')
password = os.environ.get('ADMIN_PASSWORD', '')
if email and password:
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'full_name': 'Administrador',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        user.set_password(password)
        user.save()
        print(f'SUPERUSER CREATED: {email}')
    else:
        print(f'SUPERUSER EXISTS: {email}')
else:
    print('ADMIN_EMAIL or ADMIN_PASSWORD not set')
"
    echo "--- Superuser check done ---"
fi

WORKERS=${WEB_CONCURRENCY:-1}
exec gunicorn --bind 0.0.0.0:8000 --workers $WORKERS --timeout 120 config.wsgi:application
