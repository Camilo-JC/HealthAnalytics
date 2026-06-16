from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class DataSource(models.Model):
    class SourceType(models.TextChoices):
        EXCEL = 'excel', _('Excel')
        CSV = 'csv', _('CSV')
        API = 'api', _('API')
        MANUAL = 'manual', _('Manual')

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pendiente')
        PROCESSING = 'processing', _('Procesando')
        COMPLETED = 'completed', _('Completado')
        FAILED = 'failed', _('Fallido')

    name = models.CharField(_('nombre'), max_length=255)
    source_type = models.CharField(_('tipo'), max_length=20, choices=SourceType.choices)
    file = models.FileField(_('archivo'), upload_to='uploads/', null=True, blank=True)
    file_content = models.BinaryField(_('contenido'), null=True, blank=True, editable=False)
    file_content_name = models.CharField(_('nombre archivo'), max_length=255, blank=True)
    original_filename = models.CharField(_('nombre original'), max_length=255, blank=True)
    file_size = models.BigIntegerField(_('tamaño (bytes)'), null=True, blank=True)
    row_count = models.IntegerField(_('filas'), null=True, blank=True)
    status = models.CharField(_('estado'), max_length=20, choices=Status.choices, default=Status.PENDING)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, verbose_name=_('cargado por')
    )
    notes = models.TextField(_('notas'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('fuente de datos')
        verbose_name_plural = _('fuentes de datos')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class ETLExecution(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pendiente')
        EXTRACTING = 'extracting', _('Extrayendo')
        TRANSFORMING = 'transforming', _('Transformando')
        LOADING = 'loading', _('Cargando')
        COMPLETED = 'completed', _('Completado')
        FAILED = 'failed', _('Fallido')

    source = models.ForeignKey(
        DataSource, on_delete=models.CASCADE, related_name='executions',
        verbose_name=_('fuente')
    )
    status = models.CharField(_('estado'), max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(_('iniciado en'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completado en'), null=True, blank=True)
    duration_seconds = models.FloatField(_('duración (s)'), null=True, blank=True)

    records_read = models.IntegerField(_('registros leídos'), default=0)
    records_processed = models.IntegerField(_('registros procesados'), default=0)
    records_loaded = models.IntegerField(_('registros cargados'), default=0)
    records_failed = models.IntegerField(_('registros fallidos'), default=0)
    duplicates_removed = models.IntegerField(_('duplicados eliminados'), default=0)
    errors_corrected = models.IntegerField(_('errores corregidos'), default=0)

    quality_score = models.FloatField(_('puntaje calidad'), null=True, blank=True)
    error_message = models.TextField(_('mensaje error'), blank=True)
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, verbose_name=_('ejecutado por')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('ejecución ETL')
        verbose_name_plural = _('ejecuciones ETL')
        ordering = ['-created_at']

    def __str__(self):
        return f"ETL #{self.id} - {self.source.name} ({self.get_status_display()})"


class ETLLog(models.Model):
    class LogLevel(models.TextChoices):
        DEBUG = 'debug', 'DEBUG'
        INFO = 'info', 'INFO'
        WARNING = 'warning', 'WARNING'
        ERROR = 'error', 'ERROR'
        CRITICAL = 'critical', 'CRITICAL'

    execution = models.ForeignKey(
        ETLExecution, on_delete=models.CASCADE, related_name='logs',
        verbose_name=_('ejecución'), null=True, blank=True
    )
    source = models.ForeignKey(
        DataSource, on_delete=models.CASCADE, related_name='logs',
        verbose_name=_('fuente'), null=True, blank=True
    )
    level = models.CharField(_('nivel'), max_length=10, choices=LogLevel.choices, default=LogLevel.INFO)
    phase = models.CharField(_('fase'), max_length=20, blank=True)
    message = models.TextField(_('mensaje'))
    details = models.JSONField(_('detalles'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('log ETL')
        verbose_name_plural = _('logs ETL')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['level', 'phase']),
            models.Index(fields=['execution', 'level']),
        ]

    def __str__(self):
        return f"[{self.get_level_display()}] {self.phase}: {self.message[:100]}"


class DataQualityMetric(models.Model):
    execution = models.ForeignKey(
        ETLExecution, on_delete=models.CASCADE, related_name='quality_metrics',
        verbose_name=_('ejecución')
    )
    metric_name = models.CharField(_('métrica'), max_length=100)
    metric_value = models.FloatField(_('valor'))
    threshold_min = models.FloatField(_('umbral mínimo'), null=True, blank=True)
    threshold_max = models.FloatField(_('umbral máximo'), null=True, blank=True)
    passed = models.BooleanField(_('aprobado'), default=True)
    details = models.JSONField(_('detalles'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('métrica de calidad')
        verbose_name_plural = _('métricas de calidad')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value}"
