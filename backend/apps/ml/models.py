from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class MLModelRegistry(models.Model):
    class ModelType(models.TextChoices):
        RANDOM_FOREST = 'random_forest', 'Random Forest'
        LOGISTIC_REGRESSION = 'logistic_regression', 'Regresión Logística'
        DECISION_TREE = 'decision_tree', 'Árbol de Decisión'

    class TargetVariable(models.TextChoices):
        RISK_CATEGORY = 'risk_category', 'Categoría de Riesgo'
        HYPERTENSION = 'hypertension', 'Hipertensión'
        DIABETES = 'diabetes', 'Diabetes'

    name = models.CharField(_('nombre'), max_length=100)
    model_type = models.CharField(_('tipo de modelo'), max_length=50, choices=ModelType.choices)
    target_variable = models.CharField(_('variable objetivo'), max_length=50, choices=TargetVariable.choices)
    version = models.CharField(_('versión'), max_length=20)
    file_path = models.CharField(_('ruta del modelo'), max_length=255)
    is_active = models.BooleanField(_('activo'), default=True)

    # Métricas
    accuracy = models.FloatField(_('accuracy'), null=True, blank=True)
    precision = models.FloatField(_('precision'), null=True, blank=True)
    recall = models.FloatField(_('recall'), null=True, blank=True)
    f1_score = models.FloatField(_('f1-score'), null=True, blank=True)
    roc_auc = models.FloatField(_('ROC-AUC'), null=True, blank=True)

    # Hyperparameters
    parameters = models.JSONField(_('parámetros'), null=True, blank=True)
    feature_importance = models.JSONField(_('importancia de variables'), null=True, blank=True)
    confusion_matrix = models.JSONField(_('matriz de confusión'), null=True, blank=True)
    classification_report = models.JSONField(_('reporte de clasificación'), null=True, blank=True)

    training_records = models.IntegerField(_('registros entrenamiento'), null=True, blank=True)
    test_records = models.IntegerField(_('registros prueba'), null=True, blank=True)

    training_duration = models.FloatField(_('duración entrenamiento (s)'), null=True, blank=True)
    trained_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, verbose_name=_('entrenado por')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('modelo ML')
        verbose_name_plural = _('modelos ML')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_model_type_display()} v{self.version}"


class MLPrediction(models.Model):
    model = models.ForeignKey(
        MLModelRegistry, on_delete=models.CASCADE, related_name='predictions'
    )
    patient = models.ForeignKey(
        'patients.Patient', on_delete=models.CASCADE, related_name='ml_predictions',
        null=True, blank=True
    )
    input_data = models.JSONField(_('datos de entrada'))
    predicted_risk = models.CharField(_('riesgo predecido'), max_length=20)
    predicted_probability = models.FloatField(_('probabilidad predecida'), null=True, blank=True)
    probabilities = models.JSONField(_('probabilidades por clase'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('predicción ML')
        verbose_name_plural = _('predicciones ML')
        ordering = ['-created_at']
