from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = 'M', _('Masculino')
        FEMALE = 'F', _('Femenino')
        OTHER = 'O', _('Otro')

    class RiskCategory(models.TextChoices):
        LOW = 'low', _('Bajo')
        MEDIUM = 'medium', _('Medio')
        HIGH = 'high', _('Alto')
        CRITICAL = 'critical', _('Crítico')

    class BmiCategory(models.TextChoices):
        UNDERWEIGHT = 'underweight', _('Bajo peso')
        NORMAL = 'normal', _('Normal')
        OVERWEIGHT = 'overweight', _('Sobrepeso')
        OBESE_I = 'obese_i', _('Obesidad Grado I')
        OBESE_II = 'obese_ii', _('Obesidad Grado II')
        OBESE_III = 'obese_iii', _('Obesidad Grado III')

    # Identificación
    patient_id = models.CharField(_('ID del paciente'), max_length=50, unique=True)
    first_name = models.CharField(_('nombres'), max_length=100)
    last_name = models.CharField(_('apellidos'), max_length=100)
    document_type = models.CharField(_('tipo documento'), max_length=20, default='CC')
    document_number = models.CharField(_('número documento'), max_length=50, unique=True)

    # Datos demográficos
    age = models.IntegerField(_('edad'), validators=[MinValueValidator(0), MaxValueValidator(120)])
    gender = models.CharField(_('sexo'), max_length=1, choices=Gender.choices)

    # Signos vitales
    height = models.DecimalField(_('altura (m)'), max_digits=4, decimal_places=2, validators=[MinValueValidator(Decimal('0.50')), MaxValueValidator(Decimal('2.50'))])
    weight = models.DecimalField(_('peso (kg)'), max_digits=5, decimal_places=1, validators=[MinValueValidator(Decimal('20.0')), MaxValueValidator(Decimal('300.0'))])
    bmi = models.DecimalField(_('IMC'), max_digits=5, decimal_places=2, null=True, blank=True)
    bmi_category = models.CharField(_('categoría IMC'), max_length=20, choices=BmiCategory.choices, null=True, blank=True)
    systolic_bp = models.IntegerField(_('presión sistólica'), validators=[MinValueValidator(60), MaxValueValidator(280)])
    diastolic_bp = models.IntegerField(_('presión diastólica'), validators=[MinValueValidator(30), MaxValueValidator(180)])
    heart_rate = models.IntegerField(_('frecuencia cardíaca'), validators=[MinValueValidator(30), MaxValueValidator(250)])
    oxygen_saturation = models.IntegerField(_('saturación oxígeno (%)'), validators=[MinValueValidator(50), MaxValueValidator(100)], null=True, blank=True)

    # Laboratorio
    glucose = models.DecimalField(_('glucosa (mg/dL)'), max_digits=6, decimal_places=1, validators=[MinValueValidator(Decimal('20.0')), MaxValueValidator(Decimal('600.0'))])
    cholesterol = models.DecimalField(_('colesterol total (mg/dL)'), max_digits=6, decimal_places=1, validators=[MinValueValidator(Decimal('50.0')), MaxValueValidator(Decimal('500.0'))])
    triglycerides = models.DecimalField(_('triglicéridos (mg/dL)'), max_digits=6, decimal_places=1, null=True, blank=True)
    hemoglobin = models.DecimalField(_('hemoglobina (g/dL)'), max_digits=4, decimal_places=1, null=True, blank=True)
    creatinine = models.DecimalField(_('creatinina (mg/dL)'), max_digits=4, decimal_places=2, null=True, blank=True)

    # Diagnóstico
    diagnosis = models.TextField(_('diagnóstico principal'), blank=True)
    diagnosis_code = models.CharField(_('código diagnóstico'), max_length=20, blank=True)
    comorbidities = models.TextField(_('comorbilidades'), blank=True, null=True)

    # Estilo de vida
    smoking = models.BooleanField(_('tabaquismo'), default=False)
    alcohol_consumption = models.BooleanField(_('consumo de alcohol'), default=False)
    physical_activity = models.BooleanField(_('actividad física'), default=False)
    family_history = models.BooleanField(_('antecedentes familiares'), default=False)

    # Riesgo
    risk_category = models.CharField(_('categoría de riesgo'), max_length=20, choices=RiskCategory.choices, null=True, blank=True)
    risk_score = models.DecimalField(_('puntaje de riesgo'), max_digits=5, decimal_places=2, null=True, blank=True)

    # Metadatos
    source_file = models.CharField(_('archivo origen'), max_length=255, blank=True)
    is_processed = models.BooleanField(_('procesado'), default=False)
    is_valid = models.BooleanField(_('válido'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('paciente')
        verbose_name_plural = _('pacientes')
        ordering = ['patient_id']
        indexes = [
            models.Index(fields=['patient_id', 'document_number']),
            models.Index(fields=['risk_category']),
            models.Index(fields=['diagnosis_code']),
            models.Index(fields=['age', 'gender']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.patient_id})"


class ClinicalAlert(models.Model):
    class Severity(models.TextChoices):
        INFO = 'info', _('Informativo')
        WARNING = 'warning', _('Advertencia')
        CRITICAL = 'critical', _('Crítico')

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='alerts',
        verbose_name=_('paciente')
    )
    alert_type = models.CharField(_('tipo de alerta'), max_length=100)
    severity = models.CharField(_('severidad'), max_length=20, choices=Severity.choices)
    description = models.TextField(_('descripción'))
    parameter = models.CharField(_('parámetro'), max_length=50)
    value = models.CharField(_('valor'), max_length=50)
    threshold = models.CharField(_('umbral'), max_length=50)
    is_active = models.BooleanField(_('activa'), default=True)
    resolved_at = models.DateTimeField(_('resuelta en'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('alerta clínica')
        verbose_name_plural = _('alertas clínicas')
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.patient} - {self.alert_type}"
