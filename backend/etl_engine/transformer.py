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

    @staticmethod
    def _unaccent(text):
        return (text.replace('á', 'a').replace('é', 'e').replace('í', 'i')
                    .replace('ó', 'o').replace('ú', 'u').replace('ü', 'u'))

    @staticmethod
    def _infer_gender_from_name(name):
        import unicodedata
        if pd.isna(name) or not str(name).strip():
            return None
        first = str(name).strip().split()[0].lower()
        first_norm = Transformer._unaccent(first)

        # Check name lists FIRST (higher priority than suffix heuristics)
        male_names = {
            'jose', 'luis', 'carlos', 'manuel', 'david', 'juan', 'jorge',
            'pedro', 'rafael', 'fernando', 'andres', 'alvaro', 'santiago',
            'felipe', 'sebastian', 'nicolas', 'diego', 'javier',
            'miguel', 'angel', 'ramon', 'simon', 'tomas',
            'julian', 'martin', 'pablo', 'adrian', 'daniel',
            'benjamin', 'vicente', 'esteban', 'mateo', 'matias',
            'francisco', 'jesus', 'cristian', 'cristhian', 'kevin', 'brandon',
            'brayan', 'bryan', 'jhon', 'jhonatan', 'jonathan', 'jonatan', 'ismael',
            'samuel', 'moises', 'elias', 'isaac', 'noe',
            'alan', 'ivan', 'edwin', 'wilson', 'wilmer', 'oswaldo', 'rodolfo',
            'nelson', 'hector', 'leonardo', 'guillermo', 'hernando', 'ricardo',
            'eduardo', 'alfonso', 'alfredo', 'rodrigo', 'camilo', 'mauricio', 'octavio',
            'oscar', 'ulises', 'homero', 'orlando', 'raul', 'humberto',
            'roberto', 'alberto', 'ruben', 'gabriel', 'ezequiel', 'raul',
            'jesus', 'joel', 'saul', 'aaron', 'jacobo', 'uriel', 'eder',
            'fabian', 'gerardo', 'ernesto', 'marcos', 'lucas', 'esteban',
            'rene', 'emilio', 'fidel', 'german', 'hugo', 'ignacio',
            'jaime', 'joaquin', 'leonel', 'marco', 'mario', 'maximo',
            'oliver', 'pascual', 'patricio', 'roque', 'salvador', 'teodoro',
            'valentin', 'william', 'ximeno', 'yonathan', 'zacarias',
            'abraham', 'axel', 'blas', 'cesar', 'cristobal', 'domingo',
            'eleazar', 'enrique', 'eugenio', 'fausto', 'felix', 'florencio',
            'genaro', 'gilberto', 'heriberto', 'honorio', 'isaias', 'isidro',
            'jeremias', 'jonas', 'josue', 'laureano', 'lazaro', 'lorenzo',
            'macario', 'melchor', 'narciso', 'natanael', 'norberto', 'oliverio',
            'primo', 'reinaldo', 'rolando', 'servando', 'tadeo', 'timoteo',
            'tobias', 'troy', 'valerio', 'victor', 'wenceslao', 'yadiel',
            'yair', 'yamil', 'yoel', 'yonaiker', 'yordi',
        }
        if first_norm in male_names:
            return 'M'

        # Expanded female names (stored unaccented for matching)
        female_names = {
            'raquel', 'ester', 'esther', 'yolanda', 'amparo', 'consuelo',
            'mercedes', 'montserrat', 'carmen', 'milagros', 'pilar', 'socorro', 'nieves',
            'luz', 'virtudes', 'dolores', 'asuncion', 'concepcion',
            'angustias', 'esperanza', 'encarnacion', 'noemi',
            'nayibe', 'yaritza', 'yenifer', 'yessica', 'yuliana', 'paulina', 'camila',
            'valentina', 'laura', 'maria', 'ana', 'gabriela', 'fernanda',
            'ximena', 'jimena', 'carolina', 'daniela', 'tatiana', 'katherine', 'johanna',
            'adriana', 'alejandra', 'alicia', 'beatriz', 'bianca', 'blanca',
            'caridad', 'catalina', 'cecilia', 'clara', 'cristina', 'elena',
            'elisa', 'elvira', 'emilia', 'esmeralda', 'eugenia', 'evangelina',
            'flor', 'genoveva', 'gloria', 'graciela', 'guadalupe', 'ines',
            'irene', 'irma', 'jacinta', 'josefina', 'juana', 'julia',
            'leonor', 'leticia', 'lidia', 'liliana', 'lorena', 'lucia',
            'luisa', 'lourdes', 'magdalena', 'margarita', 'maribel', 'marina',
            'marta', 'micaela', 'monica', 'natalia', 'norma', 'olga',
            'patricia', 'paulina', 'perla', 'rebeca', 'rosa', 'rosalia',
            'rosario', 'sandra', 'sara', 'silvia', 'sofia', 'soledad',
            'susana', 'teresa', 'veronica', 'victoria', 'viviana', 'zoraida',
        }
        if first_norm in female_names:
            return 'F'

        # Suffix-based inference (fallback, lower priority)
        if first_norm.endswith(('a', 'ita', 'ina', 'ona', 'ora', 'iana', 'ela')):
            return 'F'
        if first_norm.endswith(('o', 'io', 'ito', 'ino', 'ero', 'oro', 'iano')):
            return 'M'
        if first_norm.endswith(('el', 'ol', 'il', 'al')):
            return 'M'

        return None

    def _normalize_gender(self, df):
        if 'gender' in df.columns:
            gender_map = {
                'm': 'M', 'masculino': 'M', 'male': 'M', 'hombre': 'M', 'h': 'M',
                'f': 'F', 'femenino': 'F', 'female': 'F', 'mujer': 'F', 'mujeres': 'F',
                'o': 'O', 'otro': 'O', 'other': 'O',
            }
            df['gender'] = df['gender'].astype(str).str.lower().str.strip().map(gender_map).fillna('O')

            if 'first_name' in df.columns:
                name_genders = df['first_name'].apply(self._infer_gender_from_name)
                conflicts = (df['gender'] != name_genders) & name_genders.notna()
                fix_count = conflicts.sum()
                if fix_count > 0:
                    df.loc[conflicts, 'gender'] = name_genders[conflicts]
                    self.stats['errors_corrected'] += fix_count
                    self.log('info', f"Corregidos {fix_count} géneros inconsistentes basados en el nombre", 'TRANSFORM')
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
        def _bp_score(sbp, dbp):
            if pd.isna(sbp):
                return 0
            sbp, dbp = float(sbp), float(dbp) if pd.notna(dbp) else 0
            if sbp >= 180 or dbp >= 120:
                return 4
            if sbp >= 140 or dbp >= 90:
                return 3
            if sbp >= 130 or dbp >= 80:
                return 2
            if sbp >= 120:
                return 1
            return 0

        def _glucose_score(glu):
            if pd.isna(glu):
                return 0
            glu = float(glu)
            if glu >= 300:
                return 4
            if glu >= 200:
                return 3
            if glu >= 126:
                return 2
            if glu >= 100:
                return 1
            return 0

        def _bmi_score(bmi):
            if pd.isna(bmi):
                return 0
            bmi = float(bmi)
            if bmi >= 40:
                return 4
            if bmi >= 35:
                return 3
            if bmi >= 30:
                return 2
            if bmi >= 25:
                return 1
            return 0

        def _cholesterol_score(col):
            if pd.isna(col):
                return 0
            col = float(col)
            if col >= 240:
                return 2
            if col >= 200:
                return 1
            return 0

        def _oxygen_score(o2):
            if pd.isna(o2):
                return 0
            o2 = float(o2)
            if o2 < 85:
                return 4
            if o2 < 90:
                return 3
            if o2 < 95:
                return 1
            return 0

        def _hr_score(hr):
            if pd.isna(hr):
                return 0
            hr = float(hr)
            if hr > 120 or hr < 50:
                return 2
            if hr > 100 or hr < 60:
                return 1
            return 0

        def calc_risk(row):
            sbp = _bp_score(row.get('systolic_bp'), row.get('diastolic_bp'))
            glu = _glucose_score(row.get('glucose'))
            bmi = _bmi_score(row.get('bmi'))
            col = _cholesterol_score(row.get('cholesterol'))
            o2 = _oxygen_score(row.get('oxygen_saturation'))
            hr = _hr_score(row.get('heart_rate'))

            lifestyle = 0
            if row.get('smoking'):
                lifestyle += 1
            if not row.get('physical_activity'):
                lifestyle += 1
            if row.get('alcohol_consumption'):
                lifestyle += 1
            if row.get('family_history'):
                lifestyle += 1

            max_single = max(sbp, glu, bmi, col, o2, hr)
            total = sbp + glu + bmi + col + o2 + hr + lifestyle

            has_crisis = (pd.notna(row.get('systolic_bp')) and float(row['systolic_bp']) >= 180) or \
                         (pd.notna(row.get('glucose')) and float(row['glucose']) >= 300) or \
                         (pd.notna(row.get('oxygen_saturation')) and float(row['oxygen_saturation']) < 85)

            if has_crisis or total >= 9:
                category = 'critical'
            elif max_single >= 4 or total >= 6 or (lifestyle >= 3 and max_single >= 2):
                category = 'high'
            elif max_single >= 2 or total >= 3 or lifestyle >= 3:
                category = 'medium'
            else:
                category = 'low'

            risk_score = round(min(total / 14 * 100, 100), 2)

            return category, risk_score

        categories, scores = zip(*df.apply(calc_risk, axis=1))
        df['risk_category'] = categories
        df['risk_score'] = scores
        self.log('info', f"Riesgo calculado para {len(df)} pacientes", 'TRANSFORM')
        return df

    def get_stats(self):
        return self.stats
