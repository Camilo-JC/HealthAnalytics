from rest_framework import serializers
from .models import Patient, ClinicalAlert


class ClinicalAlertSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = ClinicalAlert
        fields = '__all__'
        read_only_fields = ('created_at',)

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class PatientListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age_group = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = (
            'id', 'patient_id', 'first_name', 'last_name', 'full_name', 'age', 'age_group', 'gender',
            'blood_type', 'height', 'weight', 'bmi', 'bmi_category', 'diagnosis', 'diagnosis_code',
            'risk_category', 'risk_score', 'glucose', 'systolic_bp', 'diastolic_bp',
            'heart_rate', 'oxygen_saturation', 'cholesterol',
            'smoking', 'alcohol_consumption', 'physical_activity', 'family_history',
            'is_valid', 'is_processed', 'source_file', 'created_at', 'updated_at'
        )

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age_group(self, obj):
        if obj.age < 18:
            return 'Pediatrico'
        elif obj.age < 40:
            return 'Joven'
        elif obj.age < 60:
            return 'Adulto'
        else:
            return 'Adulto Mayor'


class PatientDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    alerts = ClinicalAlertSerializer(many=True, read_only=True)
    alerts_count = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = '__all__'

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_alerts_count(self, obj):
        return obj.alerts.filter(is_active=True).count()


class PatientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = (
            'patient_id', 'first_name', 'last_name', 'document_type', 'document_number',
            'age', 'gender', 'blood_type', 'height', 'weight',
            'systolic_bp', 'diastolic_bp', 'heart_rate', 'oxygen_saturation',
            'glucose', 'cholesterol', 'cholesterol_ldl', 'cholesterol_hdl',
            'triglycerides', 'hemoglobin', 'creatinine',
            'diagnosis', 'diagnosis_code', 'comorbidities',
            'smoking', 'alcohol_consumption', 'physical_activity', 'family_history',
        )


class PatientBulkUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    source_name = serializers.CharField(required=False, default='manual_upload')


class PatientExportSerializer(serializers.Serializer):
    format = serializers.ChoiceField(choices=['csv', 'xlsx', 'pdf'], default='csv')
    filters = serializers.DictField(required=False, default=dict)
