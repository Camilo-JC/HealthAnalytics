import logging
import pandas as pd
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from .base import BaseETLComponent
from apps.patients.models import Patient, ClinicalAlert
from apps.etl.models import DataSource, ETLExecution, ETLLog, DataQualityMetric
from .clinical_rules import CLINICAL_ALERT_RULES

logger = logging.getLogger('etl')


class Loader(BaseETLComponent):
    def load(self, df, execution):
        self.log('info', f"Iniciando carga: {len(df)} registros", 'LOAD')
        loaded = 0
        failed = 0
        alerts_created = 0

        for _, row in df.iterrows():
            try:
                with transaction.atomic():
                    patient_data = self._prepare_patient_data(row)
                    patient, created = Patient.objects.update_or_create(
                        patient_id=patient_data.pop('patient_id'),
                        defaults={**patient_data, 'is_processed': True, 'source_file': execution.source.original_filename if execution.source else ''}
                    )
                    loaded += 1

                    alerts = self._check_clinical_alerts(patient, row)
                    for alert_data in alerts:
                        ClinicalAlert.objects.create(patient=patient, **alert_data)
                        alerts_created += 1

            except Exception as e:
                failed += 1
                self.log('error', f"Error cargando registro: {str(e)}", 'LOAD')

        execution.records_loaded = loaded
        execution.records_failed = failed
        execution.save()

        self._calculate_quality_metrics(execution, df)

        self.log('info', f"Carga completada: {loaded} registros, {failed} fallos, {alerts_created} alertas", 'LOAD')
        return loaded, failed

    def _prepare_patient_data(self, row):
        fields = [
            'patient_id', 'first_name', 'last_name', 'document_type', 'document_number',
            'age', 'gender', 'height', 'weight', 'bmi', 'bmi_category',
            'systolic_bp', 'diastolic_bp', 'heart_rate', 'oxygen_saturation',
            'glucose', 'cholesterol',
            'triglycerides', 'hemoglobin', 'creatinine',
            'diagnosis', 'diagnosis_code', 'comorbidities',
            'smoking', 'alcohol_consumption', 'physical_activity', 'family_history',
            'risk_category', 'risk_score',
        ]
        data = {}
        for field in fields:
            val = row.get(field)
            if pd.isna(val) or val is None:
                data[field] = None
            elif isinstance(val, (float, int)):
                if field in ['bmi', 'risk_score'] and val is not None:
                    data[field] = round(float(val), 2)
                else:
                    data[field] = val
            else:
                data[field] = val

        if 'document_number' not in data or not data['document_number']:
            data['document_number'] = data.get('patient_id', f'DOC-{hash(str(row)) % 1000000}')
        if 'document_type' not in data or not data['document_type']:
            data['document_type'] = 'CC'

        for bool_field in ['smoking', 'alcohol_consumption', 'physical_activity', 'family_history']:
            if bool_field in data:
                data[bool_field] = bool(data[bool_field])

        for num_field in ['age', 'systolic_bp', 'diastolic_bp', 'heart_rate', 'oxygen_saturation']:
            if num_field in data and data[num_field] is not None:
                data[num_field] = int(float(data[num_field]))

        for dec_field in ['height', 'weight', 'bmi', 'glucose', 'cholesterol',
                          'triglycerides', 'hemoglobin', 'creatinine', 'risk_score']:
            if dec_field in data and data[dec_field] is not None:
                data[dec_field] = round(float(data[dec_field]), 2)

        return data

    def _check_clinical_alerts(self, patient, row):
        alerts = []
        for rule in CLINICAL_ALERT_RULES:
            param = rule['parameter']
            value = row.get(param)
            if pd.isna(value) or value is None:
                continue
            condition = rule['condition']
            threshold = rule['threshold']
            triggered = False
            if condition == '>=' and float(value) >= threshold:
                triggered = True
            elif condition == '<=' and float(value) <= threshold:
                triggered = True
            elif condition == '>' and float(value) > threshold:
                triggered = True
            elif condition == '<' and float(value) < threshold:
                triggered = True

            if triggered:
                existing = ClinicalAlert.objects.filter(
                    patient=patient, alert_type=rule['alert_type'], is_active=True
                ).exists()
                if not existing:
                    alerts.append({
                        'alert_type': rule['alert_type'],
                        'severity': rule['severity'],
                        'description': f"{rule['alert_type']}: {param}={value} (umbral: {threshold})",
                        'parameter': param,
                        'value': str(value),
                        'threshold': str(threshold),
                    })
        return alerts

    def _calculate_quality_metrics(self, execution, df):
        total = len(df)
        if total == 0:
            return

        completeness = {}
        for col in df.columns:
            non_null = df[col].notna().sum()
            completeness[col] = round((non_null / total) * 100, 2)

        avg_completeness = sum(completeness.values()) / len(completeness) if completeness else 0

        DataQualityMetric.objects.create(
            execution=execution,
            metric_name='completitud_promedio',
            metric_value=avg_completeness,
            threshold_min=90.0,
            passed=avg_completeness >= 90.0,
            details={'column_completeness': completeness}
        )
