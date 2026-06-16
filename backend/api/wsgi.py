import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.core.management import call_command
from django.conf import settings

_IS_VERCEL = bool(os.environ.get('VERCEL'))
if _IS_VERCEL:
    try:
        call_command('migrate', '--noinput')
    except Exception as e:
        import logging
        logging.getLogger('django').warning(f'Migration skipped: {e}')

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
