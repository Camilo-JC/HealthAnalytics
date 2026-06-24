import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('etl')


@shared_task(bind=True, max_retries=3)
def run_etl_pipeline(self, execution_id):
    from etl_engine.pipeline import ETLPipeline
    from .models import ETLExecution

    try:
        execution = ETLExecution.objects.get(id=execution_id)
        source = execution.source
        import os
        file_path = None
        if source.file and os.path.exists(source.file.path):
            file_path = source.file.path
        if file_path is None and source.file_content:
            import tempfile
            ext = os.path.splitext(source.file_content_name or source.original_filename or 'file.xlsx')[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(source.file_content)
                file_path = tmp.name
        if file_path is None:
            execution.status = 'failed'
            execution.error_message = 'No hay archivo asociado'
            execution.save()
            return {'success': False, 'error': 'No hay archivo asociado'}

        pipeline = ETLPipeline(execution_id=execution_id)
        result = pipeline.run(file_path, source.source_type)

        return result

    except ETLExecution.DoesNotExist:
        logger.error(f"ETL execution {execution_id} not found")
        return {'success': False, 'error': 'Ejecución no encontrada'}
    except Exception as e:
        logger.exception(f"ETL task failed: {str(e)}")
        try:
            execution = ETLExecution.objects.get(id=execution_id)
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.save()
        except Exception:
            pass
        raise self.retry(exc=e, countdown=60)


@shared_task
def execute_scheduled_etl():
    from .models import DataSource
    pending = DataSource.objects.filter(status='pending')
    for source in pending:
        execution = ETLExecution.objects.create(
            source=source,
            status='pending'
        )
        run_etl_pipeline.delay(execution.id)
    return {'scheduled': pending.count()}
