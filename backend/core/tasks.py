import logging
from celery import shared_task

logger = logging.getLogger('django')


@shared_task
def cleanup_old_logs():
    from django.utils import timezone
    from datetime import timedelta
    from apps.etl.models import ETLLog, ETLExecution

    cutoff = timezone.now() - timedelta(days=90)
    deleted_logs = ETLLog.objects.filter(created_at__lt=cutoff).delete()[0]
    deleted_exec = ETLExecution.objects.filter(created_at__lt=cutoff).delete()[0]
    logger.info(f"Cleaned up {deleted_logs} logs and {deleted_exec} executions older than 90 days")
    return {'deleted_logs': deleted_logs, 'deleted_executions': deleted_exec}
