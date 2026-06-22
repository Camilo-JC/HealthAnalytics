import pandas as pd
from django.core.management.base import BaseCommand
from apps.patients.models import Patient
from etl_engine.transformer import Transformer


class Command(BaseCommand):
    help = 'Recalcula diagnóstico, código y riesgo de todos los pacientes usando la lógica actual del Transformer'

    def handle(self, *args, **options):
        t = Transformer()
        patients = list(Patient.objects.all().iterator())
        self.stdout.write(f'Pacientes: {len(patients)}')

        rows = []
        for p in patients:
            rows.append({
                'patient_id': p.patient_id,
                'diagnosis': p.diagnosis or '',
                'diagnosis_code': p.diagnosis_code or '',
                'systolic_bp': float(p.systolic_bp) if p.systolic_bp else None,
                'diastolic_bp': float(p.diastolic_bp) if p.diastolic_bp else None,
                'glucose': float(p.glucose) if p.glucose else None,
                'bmi': float(p.bmi) if p.bmi else None,
                'cholesterol': float(p.cholesterol) if p.cholesterol else None,
                'oxygen_saturation': float(p.oxygen_saturation) if p.oxygen_saturation else None,
                'heart_rate': float(p.heart_rate) if p.heart_rate else None,
                'smoking': p.smoking,
                'physical_activity': p.physical_activity,
                'alcohol_consumption': p.alcohol_consumption,
                'family_history': p.family_history,
            })

        df = pd.DataFrame(rows)
        df = t._normalize_diagnosis(df)
        df = t._assign_clinical_diagnosis(df)
        df = t._calculate_risk(df)

        updated_dx = 0
        updated_risk = 0
        for i, p in enumerate(patients):
            new_diag = df.iloc[i]['diagnosis']
            new_code = df.iloc[i]['diagnosis_code'] if pd.notna(df.iloc[i]['diagnosis_code']) else ''
            new_risk_cat = df.iloc[i]['risk_category']
            new_risk_score = float(df.iloc[i]['risk_score']) if pd.notna(df.iloc[i]['risk_score']) else None

            changed = False
            if str(new_diag) != str(p.diagnosis or ''):
                p.diagnosis = new_diag
                p.diagnosis_code = new_code
                changed = True
                updated_dx += 1
            if str(new_risk_cat) != str(p.risk_category or '') or (new_risk_score != float(p.risk_score or 0)):
                p.risk_category = new_risk_cat
                p.risk_score = new_risk_score
                changed = True
                updated_risk += 1
            if changed:
                p.save(update_fields=['diagnosis', 'diagnosis_code', 'risk_category', 'risk_score'])

        self.stdout.write(self.style.SUCCESS(f'Diagnósticos actualizados: {updated_dx}'))
        self.stdout.write(self.style.SUCCESS(f'Riesgos actualizados: {updated_risk}'))

        empty = Patient.objects.filter(diagnosis__isnull=True) | Patient.objects.filter(diagnosis='')
        empty = empty.distinct().count()
        self.stdout.write(f'Pacientes sin diagnóstico: {empty}')
