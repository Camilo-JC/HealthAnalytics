import time
import logging
from datetime import datetime
from django.utils import timezone
from .extractor import Extractor
from .transformer import Transformer
from .loader import Loader
from apps.etl.models import DataSource, ETLExecution, ETLLog
from apps.ml.ml_engine import MLService

logger = logging.getLogger('etl')


class ETLPipeline:
    def __init__(self, execution_id=None, source_id=None):
        self.execution_id = execution_id
        self.source_id = source_id
        self.extractor = Extractor(execution_id)
        self.transformer = Transformer(execution_id)
        self.loader = Loader(execution_id)

    def run(self, file_path, source_type='excel', user=None, source_name=None):
        start_time = time.time()
        logs = []

        try:
            execution = ETLExecution.objects.get(id=self.execution_id) if self.execution_id else None
            if execution:
                execution.status = 'extracting'
                execution.started_at = timezone.now()
                execution.save()
                ETLLog.objects.create(
                    execution=execution,
                    source=execution.source,
                    level='info',
                    phase='EXTRACT',
                    message=f"Iniciando extracción: {file_path}"
                )

            df = self.extractor.extract(file_path, source_type)
            records_read = len(df)

            if execution:
                execution.status = 'transforming'
                execution.records_read = records_read
                execution.save()
                ETLLog.objects.create(
                    execution=execution,
                    source=execution.source,
                    level='info',
                    phase='TRANSFORM',
                    message=f"Iniciando transformación de {records_read} registros"
                )

            df = self.transformer.transform(df)
            records_processed = len(df)

            if execution:
                execution.status = 'loading'
                execution.records_processed = records_processed
                execution.duplicates_removed = self.transformer.stats['duplicates_removed']
                execution.errors_corrected = self.transformer.stats['errors_corrected']
                execution.save()
                ETLLog.objects.create(
                    execution=execution,
                    source=execution.source,
                    level='info',
                    phase='LOAD',
                    message=f"Cargando {records_processed} registros"
                )

            loaded, failed = self.loader.load(df, execution)

            try:
                ml_service = MLService()
                ml_result = ml_service.train_and_register(user)
                if ml_result.get('success'):
                    ETLLog.objects.create(
                        execution=execution,
                        source=execution.source,
                        level='info',
                        phase='ML',
                        message=f"Modelos ML entrenados: mejor={ml_result.get('best_model')}, accuracy={max(m.get('accuracy',0) for m in ml_result.get('comparison',{}).values()):.2%}"
                    )
            except Exception as ml_e:
                logger.warning(f"Entrenamiento ML automático omitido: {ml_e}")

            duration = time.time() - start_time
            if execution:
                execution.status = 'completed'
                execution.completed_at = timezone.now()
                execution.duration_seconds = round(duration, 2)
                execution.quality_score = self._calculate_quality(df)
                execution.save()
                ETLLog.objects.create(
                    execution=execution,
                    source=execution.source,
                    level='info',
                    phase='COMPLETE',
                    message=f"ETL completado: {loaded} cargados, {failed} fallidos en {duration:.2f}s"
                )

            return {
                'success': True,
                'execution_id': self.execution_id,
                'records_read': records_read,
                'records_processed': records_processed,
                'records_loaded': loaded,
                'records_failed': failed,
                'duplicates_removed': self.transformer.stats['duplicates_removed'],
                'errors_corrected': self.transformer.stats['errors_corrected'],
                'nulls_imputed': self.transformer.stats['nulls_imputed'],
                'outliers_treated': self.transformer.stats['outliers_treated'],
                'duration_seconds': round(duration, 2),
                'quality_score': execution.quality_score if execution else None,
            }

        except Exception as e:
            duration = time.time() - start_time
            logger.exception(f"ETL failed: {str(e)}")
            if execution:
                execution.status = 'failed'
                execution.completed_at = timezone.now()
                execution.duration_seconds = round(duration, 2)
                execution.error_message = str(e)
                execution.save()
                ETLLog.objects.create(
                    execution=execution,
                    source=execution.source,
                    level='error',
                    phase='ERROR',
                    message=f"ETL fallido: {str(e)}"
                )
            return {
                'success': False,
                'execution_id': self.execution_id,
                'error': str(e),
                'duration_seconds': round(duration, 2),
            }

    def _calculate_quality(self, df):
        try:
            total = len(df)
            if total == 0:
                return 0
            non_null_ratio = sum(df[col].notna().sum() / total for col in df.columns) / len(df.columns)
            completeness = non_null_ratio * 40
            has_bmi = df['bmi'].notna().sum() / total * 15 if 'bmi' in df.columns else 0
            has_risk = df['risk_category'].notna().sum() / total * 15 if 'risk_category' in df.columns else 0
            has_diagnosis = df['diagnosis'].notna().sum() / total * 15 if 'diagnosis' in df.columns else 0
            has_vitals = 0
            for col in ['systolic_bp', 'glucose', 'cholesterol']:
                if col in df.columns:
                    has_vitals += df[col].notna().sum() / total * 5
            return round(completeness + has_bmi + has_risk + has_diagnosis + has_vitals, 2)
        except Exception:
            return 0
