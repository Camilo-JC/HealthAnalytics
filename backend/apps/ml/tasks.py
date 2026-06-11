import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('ml')


@shared_task(bind=True, max_retries=2)
def train_ml_models(self):
    try:
        from .ml_engine import MLService
        service = MLService()
        result = service.train_and_register()
        logger.info(f"ML models trained: {result.get('best_model', 'N/A')}")
        return result
    except Exception as e:
        logger.exception(f"ML training failed: {str(e)}")
        raise self.retry(exc=e, countdown=300)


@shared_task
def retrain_ml_models():
    from .ml_engine import MLService
    service = MLService()
    result = service.train_and_register()
    return result
