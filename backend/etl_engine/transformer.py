import pandas as pd
import numpy as np
import re
import logging
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from .base import BaseETLComponent
from .clinical_rules import (
    CLINICAL_RANGES, DIAGNOSIS_MAPPING, DIAGNOSIS_CODES,
    BMI_CATEGORIES, RISK_RULES, NORMAL_VALUES
)

logger = logging.getLogger('etl')

COLUMN_MAPPING = {
    'id': 'patient_id',
    'id_paciente': 'patient_id',
    'paciente': 'patient_id',
    'paciente_id': 'patient_id',
    'nombre': 'first_name',
    'nombres': 'first_name',
    'apellido': 'last_name',
    'apellidos': 'last_name',
    'nombre_completo': None,
    'doc': 'document_number',
    'documento': 'document_number',
    'cedula': 'document_number',
    'cédula': 'document_number',
    'edad': 'age',
    'sexo': 'gender',
    'genero': 'gender',
    'género': 'gender',
    'tipo_sangre': 'blood_type',
    'tipo_sanguineo': 'blood_type',
    'rh': 'blood_type',
    'estatura': 'height',
    'altura': 'height',
    'talla': 'height',
    'peso': 'weight',
    'imc': 'bmi',
    'bmi': 'bmi',
    'presion_sistolica': 'systolic_bp',
    'presión_sistólica': 'systolic_bp',
    'sistolica': 'systolic_bp',
    'sistólica': 'systolic_bp',
    'presion_diastolica': 'diastolic_bp',
    'presión_diastólica': 'diastolic_bp',
    'diastolica': 'diastolic_bp',
    'diastólica': 'diastolic_bp',
    'presion_arterial': None,
    'frecuencia_cardiaca': 'heart_rate',
    'frecuencia_cardíaca': 'heart_rate',
    'pulso': 'heart_rate',
    'saturacion': 'oxygen_saturation',
    'saturación': 'oxygen_saturation',
    'saturacion_oxigeno': 'oxygen_saturation',
    'saturación_oxígeno': 'oxygen_saturation',
    'oxigeno': 'oxygen_saturation',
    'oxígeno': 'oxygen_saturation',
    'spo2': 'oxygen_saturation',
    'glucosa': 'glucose',
    'colesterol': 'cholesterol',
    'colesterol_total': 'cholesterol',
    'colesterol_ldl': 'cholesterol_ldl',
    'colesterol_hdl': 'cholesterol_hdl',
    'trigliceridos': 'triglycerides',
    'triglicéridos': 'triglycerides',
    'hemoglobina': 'hemoglobin',
    'creatinina': 'creatinine',
    'diagnostico': 'diagnosis',
    'diagnóstico': 'diagnosis',
    'diagnostico_preliminar': 'diagnosis',
    'diagnóstico_preliminar': 'diagnosis',
    'codigo_diagnostico': 'diagnosis_code',
    'código_diagnóstico': 'diagnosis_code',
    'comorbilidades': 'comorbidities',
    'fuma': 'smoking',
    'tabaquismo': 'smoking',
    'fumador': 'smoking',
    'alcohol': 'alcohol_consumption',
    'consumo_alcohol': 'alcohol_consumption',
    'actividad_fisica': 'physical_activity',
    'actividad_física': 'physical_activity',
    'ejercicio': 'physical_activity',
    'antecedentes': 'family_history',
    'antecedentes_familiares': 'family_history',
    'riesgo_enfermedad': 'risk_category',
    'fecha_consulta': None,
    'temperatura': None,
}


class Transformer(BaseETLComponent):
    def __init__(self, execution_id=None):
        super().__init__(execution_id)
        self.stats = {
            'duplicates_removed': 0,
            'errors_corrected': 0,
            'nulls_imputed': 0,
            'outliers_treated': 0,
        }

    def transform(self, df):
        self.log('info', f"Iniciando transformación: {len(df)} registros", 'TRANSFORM')
        df = df.copy()

        df = self._normalize_columns(df)
        df = self._remove_duplicates(df)
        df = self._clean_string_fields(df)
        df = self._convert_data_types(df)
        df = self._normalize_gender(df)
        df = self._normalize_diagnosis(df)
        df = self._validate_ranges(df)
        df = self._treat_outliers(df)
        df = self._impute_missing_values(df)
        df = self._calculate_bmi(df)
        df = self._classify_bmi(df)
        df = self._calculate_risk(df)

        self.log('info', f"Transformación completada: {len(df)} registros válidos", 'TRANSFORM', self.stats)
        return df

    def _normalize_columns(self, df):
        df.columns = [col.strip().lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        df.rename(columns=COLUMN_MAPPING, inplace=True)
        df = df.loc[:, ~df.columns.duplicated()]
        return df

    def _remove_duplicates(self, df):
        initial = len(df)
        if 'patient_id' in df.columns:
            df = df.drop_duplicates(subset=['patient_id'], keep='first')
        elif 'document_number' in df.columns:
            df = df.drop_duplicates(subset=['document_number'], keep='first')
        else:
            df = df.drop_duplicates()
        removed = initial - len(df)
        self.stats['duplicates_removed'] = removed
        if removed > 0:
            self.log('info', f"Eliminados {removed} duplicados", 'TRANSFORM')
        return df

    def _clean_string_fields(self, df):
        text_fields = ['first_name', 'last_name', 'diagnosis', 'diagnosis_code', 'comorbidities']
        for field in text_fields:
            if field in df.columns:
                df[field] = df[field].astype(str).str.strip().str.title()
                df[field] = df[field].replace(['Nan', 'N/A', 'None', 'Null', '', ' '], np.nan)
        return df

    def _convert_data_types(self, df):
        numeric_fields = {
            'age': 'int', 'height': 'float', 'weight': 'float', 'bmi': 'float',
            'systolic_bp': 'int', 'diastolic_bp': 'int', 'heart_rate': 'int',
            'oxygen_saturation': 'int', 'glucose': 'float', 'cholesterol': 'float',
            'cholesterol_ldl': 'float', 'cholesterol_hdl': 'float',
            'triglycerides': 'float', 'hemoglobin': 'float', 'creatinine': 'float',
        }
        for field, dtype in numeric_fields.items():
            if field in df.columns:
                original_errors = df[field].isna().sum()
                df[field] = pd.to_numeric(df[field], errors='coerce')
                new_errors = df[field].isna().sum()
                if new_errors > original_errors:
                    self.stats['errors_corrected'] += (new_errors - original_errors)

        boolean_fields = ['smoking', 'alcohol_consumption', 'physical_activity', 'family_history']
        bool_map = {True: True, False: False, 1: True, 0: False, 'si': True, 'no': False,
                     'sí': True, 'true': True, 'false': False, 'yes': True, 'no': False}
        for field in boolean_fields:
            if field in df.columns:
                df[field] = df[field].map(bool_map).fillna(False).astype(bool)

        if 'first_name' not in df.columns and 'last_name' not in df.columns:
            if 'full_name' in df.columns:
                name_parts = df['full_name'].str.split(' ', n=1, expand=True)
                df['first_name'] = name_parts[0]
                df['last_name'] = name_parts[1]
                df.drop(columns=['full_name'], inplace=True)

        if 'patient_id' not in df.columns:
            df['patient_id'] = [f'PT-{str(i).zfill(6)}' for i in range(1, len(df) + 1)]

        return df

    def _normalize_gender(self, df):
        if 'gender' in df.columns:
            gender_map = {
                'm': 'M', 'masculino': 'M', 'male': 'M', 'hombre': 'M', 'h': 'M',
                'f': 'F', 'femenino': 'F', 'female': 'F', 'mujer': 'F', 'mujeres': 'F',
                'o': 'O', 'otro': 'O', 'other': 'O',
            }
            df['gender'] = df['gender'].astype(str).str.lower().str.strip().map(gender_map).fillna('O')
        return df

    def _normalize_diagnosis(self, df):
        if 'diagnosis' in df.columns:
            def normalize_diag(diag):
                if pd.isna(diag):
                    return np.nan
                diag_lower = str(diag).lower().strip()
                if diag_lower in DIAGNOSIS_MAPPING:
                    return DIAGNOSIS_MAPPING[diag_lower]
                for key, val in DIAGNOSIS_MAPPING.items():
                    if key in diag_lower:
                        return val
                return str(diag).strip()

            df['diagnosis'] = df['diagnosis'].apply(normalize_diag)

            def get_code(diag):
                if pd.isna(diag):
                    return np.nan
                return DIAGNOSIS_CODES.get(str(diag).strip(), '')

            df['diagnosis_code'] = df['diagnosis'].apply(get_code)
        return df

    def _validate_ranges(self, df):
        for field, range_vals in CLINICAL_RANGES.items():
            if field in df.columns:
                invalid = df[field].between(range_vals['min'], range_vals['max'], inclusive='both') == False
                invalid_count = invalid.sum()
                if invalid_count > 0:
                    df.loc[invalid, field] = np.nan
                    self.log('warning', f"{invalid_count} valores inválidos en {field} eliminados", 'TRANSFORM')
        return df

    def _treat_outliers(self, df):
        outlier_fields = ['glucose', 'cholesterol', 'triglycerides', 'creatinine', 'bmi']
        for field in outlier_fields:
            if field in df.columns:
                q1 = df[field].quantile(0.01)
                q99 = df[field].quantile(0.99)
                outliers = (df[field] < q1) | (df[field] > q99)
                count = outliers.sum()
                if count > 0:
                    df.loc[df[field] < q1, field] = q1
                    df.loc[df[field] > q99, field] = q99
                    self.stats['outliers_treated'] += count
                    self.log('info', f"Tratados {count} outliers en {field}", 'TRANSFORM')
        return df

    def _impute_missing_values(self, df):
        for field in ['height', 'weight']:
            if field in df.columns and df[field].isna().any():
                median_val = df[field].median()
                df[field].fillna(median_val, inplace=True)
                self.stats['nulls_imputed'] += 1

        clinical_impute = {
            'systolic_bp': ('age', lambda age: 120 if age < 60 else 130),
            'diastolic_bp': ('age', lambda age: 80 if age < 60 else 85),
            'heart_rate': (None, 75),
            'oxygen_saturation': (None, 97),
            'glucose': (None, 95.0),
            'cholesterol': (None, 190.0),
            'cholesterol_ldl': (None, 100.0),
            'cholesterol_hdl': (None, 45.0),
            'triglycerides': (None, 150.0),
            'hemoglobin': ('gender', lambda g: 14.0 if g == 'M' else 13.0),
            'creatinine': ('gender', lambda g: 0.9 if g == 'M' else 0.7),
            'age': (None, 45),
        }

        for field, (dep, default) in clinical_impute.items():
            if field in df.columns and df[field].isna().any():
                null_count = df[field].isna().sum()
                if dep and dep in df.columns:
                    for idx in df[df[field].isna()].index:
                        dep_val = df.loc[idx, dep]
                        if callable(default):
                            try:
                                df.loc[idx, field] = default(dep_val)
                            except Exception:
                                df.loc[idx, field] = NORMAL_VALUES.get(field, 0)
                        else:
                            df.loc[idx, field] = default
                else:
                    value = default() if callable(default) else default
                    df[field].fillna(value, inplace=True)
                self.stats['nulls_imputed'] += null_count
                self.log('info', f"Imputados {null_count} valores nulos en {field}", 'TRANSFORM')

        return df

    def _calculate_bmi(self, df):
        if 'bmi' not in df.columns or df['bmi'].isna().all():
            if 'height' in df.columns and 'weight' in df.columns:
                df['bmi'] = df.apply(
                    lambda row: round(row['weight'] / (row['height'] ** 2), 2)
                    if row['height'] > 0 and row['weight'] > 0 else np.nan,
                    axis=1
                )
                self.log('info', f"IMC calculado para {df['bmi'].notna().sum()} registros", 'TRANSFORM')
        return df

    def _classify_bmi(self, df):
        if 'bmi' in df.columns:
            def classify(bmi):
                if pd.isna(bmi):
                    return None
                for lo, hi, cat, _ in BMI_CATEGORIES:
                    if lo <= bmi < hi:
                        return cat
                return 'obese_iii'

            df['bmi_category'] = df['bmi'].apply(classify)
        return df

    def _calculate_risk(self, df):
        def calc_risk(row):
            score = 0
            max_score = 100

            if pd.notna(row.get('age')) and row['age'] > 60:
                score += 10
            elif pd.notna(row.get('age')) and row['age'] > 45:
                score += 5

            if pd.notna(row.get('bmi')) and row['bmi'] >= 40:
                score += 15
            elif pd.notna(row.get('bmi')) and row['bmi'] >= 30:
                score += 10
            elif pd.notna(row.get('bmi')) and row['bmi'] >= 25:
                score += 5

            if pd.notna(row.get('systolic_bp')):
                if row['systolic_bp'] >= 180:
                    score += 20
                elif row['systolic_bp'] >= 160:
                    score += 15
                elif row['systolic_bp'] >= 140:
                    score += 10
                elif row['systolic_bp'] >= 130:
                    score += 5

            if pd.notna(row.get('glucose')):
                if row['glucose'] >= 300:
                    score += 20
                elif row['glucose'] >= 200:
                    score += 15
                elif row['glucose'] >= 126:
                    score += 10
                elif row['glucose'] >= 100:
                    score += 5

            if pd.notna(row.get('cholesterol')) and row['cholesterol'] >= 240:
                score += 10

            if pd.notna(row.get('heart_rate')) and row['heart_rate'] >= 100:
                score += 5

            if row.get('smoking'):
                score += 10
            if row.get('family_history'):
                score += 5
            if not row.get('physical_activity'):
                score += 5
            if row.get('alcohol_consumption'):
                score += 5

            risk_score = min(score, max_score)

            if risk_score >= 50:
                category = 'critical'
            elif risk_score >= 30:
                category = 'high'
            elif risk_score >= 15:
                category = 'medium'
            else:
                category = 'low'

            return category, risk_score

        categories, scores = zip(*df.apply(calc_risk, axis=1))
        df['risk_category'] = categories
        df['risk_score'] = scores
        self.log('info', f"Riesgo calculado para {len(df)} pacientes", 'TRANSFORM')
        return df

    def get_stats(self):
        return self.stats
