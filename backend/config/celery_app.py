from __future__ import absolute_import, unicode_literals
import logging
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('healthcare_etl')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.broker_connection_retry_on_startup = True


logger = logging.getLogger('celery')

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.debug(f'Request: {self.request!r}')
