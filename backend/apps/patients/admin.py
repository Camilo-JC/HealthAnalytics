from django.contrib import admin
from .models import Patient, ClinicalAlert


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'full_name', 'age', 'gender', 'bmi', 'risk_category', 'diagnosis_code')
    list_filter = ('risk_category', 'gender', 'bmi_category', 'smoking', 'is_valid')
    search_fields = ('patient_id', 'first_name', 'last_name', 'document_number')
    readonly_fields = ('bmi', 'bmi_category', 'risk_score', 'risk_category')

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Nombre'


@admin.register(ClinicalAlert)
class ClinicalAlertAdmin(admin.ModelAdmin):
    list_display = ('patient', 'alert_type', 'severity', 'is_active', 'created_at')
    list_filter = ('severity', 'is_active', 'alert_type')
    search_fields = ('patient__first_name', 'patient__last_name', 'alert_type')
