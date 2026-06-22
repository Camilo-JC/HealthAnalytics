CLINICAL_RANGES = {
    'age': {'min': 0, 'max': 120},
    'height': {'min': 0.01, 'max': 3.00},
    'weight': {'min': 0.1, 'max': 500.0},
    'bmi': {'min': 10.0, 'max': 60.0},
    'systolic_bp': {'min': 50, 'max': 300},
    'diastolic_bp': {'min': 30, 'max': 200},
    'heart_rate': {'min': 30, 'max': 220},
    'oxygen_saturation': {'min': 0, 'max': 100},
    'glucose': {'min': 20.0, 'max': 600.0},
    'cholesterol': {'min': 0, 'max': 500.0},
    'triglycerides': {'min': 20.0, 'max': 2000.0},
    'hemoglobin': {'min': 5.0, 'max': 20.0},
    'creatinine': {'min': 0.1, 'max': 15.0},
}

CLINICAL_ALERT_RULES = [
    {'parameter': 'systolic_bp', 'condition': '>=', 'threshold': 180, 'severity': 'critical', 'alert_type': 'Crisis Hipertensiva'},
    {'parameter': 'diastolic_bp', 'condition': '>=', 'threshold': 120, 'severity': 'critical', 'alert_type': 'Crisis Hipertensiva'},
    {'parameter': 'systolic_bp', 'condition': '>=', 'threshold': 140, 'severity': 'warning', 'alert_type': 'Hipertensión Etapa 2'},
    {'parameter': 'systolic_bp', 'condition': '>=', 'threshold': 130, 'severity': 'info', 'alert_type': 'Hipertensión Etapa 1'},
    {'parameter': 'glucose', 'condition': '>=', 'threshold': 300, 'severity': 'critical', 'alert_type': 'Hiperglucemia Crítica'},
    {'parameter': 'glucose', 'condition': '>=', 'threshold': 126, 'severity': 'warning', 'alert_type': 'Diabetes'},
    {'parameter': 'glucose', 'condition': '>=', 'threshold': 100, 'severity': 'info', 'alert_type': 'Prediabetes'},
    {'parameter': 'glucose', 'condition': '<', 'threshold': 70, 'severity': 'warning', 'alert_type': 'Hipoglucemia'},
    {'parameter': 'oxygen_saturation', 'condition': '<=', 'threshold': 85, 'severity': 'critical', 'alert_type': 'Hipoxia Crítica'},
    {'parameter': 'oxygen_saturation', 'condition': '<=', 'threshold': 90, 'severity': 'warning', 'alert_type': 'Hipoxia Moderada'},
    {'parameter': 'oxygen_saturation', 'condition': '<=', 'threshold': 95, 'severity': 'info', 'alert_type': 'Hipoxia Leve'},
    {'parameter': 'heart_rate', 'condition': '>', 'threshold': 150, 'severity': 'critical', 'alert_type': 'Taquicardia Grave'},
    {'parameter': 'heart_rate', 'condition': '<', 'threshold': 40, 'severity': 'critical', 'alert_type': 'Bradicardia Grave'},
    {'parameter': 'heart_rate', 'condition': '>', 'threshold': 100, 'severity': 'warning', 'alert_type': 'Taquicardia'},
    {'parameter': 'heart_rate', 'condition': '<', 'threshold': 60, 'severity': 'info', 'alert_type': 'Bradicardia'},
    {'parameter': 'bmi', 'condition': '>=', 'threshold': 40, 'severity': 'critical', 'alert_type': 'Obesidad Mórbida'},
    {'parameter': 'bmi', 'condition': '>=', 'threshold': 35, 'severity': 'warning', 'alert_type': 'Obesidad Grado II'},
    {'parameter': 'bmi', 'condition': '>=', 'threshold': 30, 'severity': 'info', 'alert_type': 'Obesidad Grado I'},
    {'parameter': 'cholesterol', 'condition': '>=', 'threshold': 300, 'severity': 'critical', 'alert_type': 'Hipercolesterolemia Muy Alta'},
    {'parameter': 'cholesterol', 'condition': '>=', 'threshold': 240, 'severity': 'warning', 'alert_type': 'Hipercolesterolemia'},
]

BP_CLASSIFICATION = {
    'normal': {'systolic': (None, 120), 'diastolic': (None, 80)},
    'elevated': {'systolic': (120, 130), 'diastolic': (None, 80)},
    'hypertension_stage_1': {'systolic': (130, 140), 'diastolic': (80, 90)},
    'hypertension_stage_2': {'systolic': (140, None), 'diastolic': (90, None)},
    'crisis': {'systolic': (180, None), 'diastolic': (120, None)},
}

HR_CLASSIFICATION = {
    'normal': (60, 100),
    'bradycardia': (None, 60),
    'tachycardia': (100, None),
    'severe_tachycardia': (150, None),
    'severe_bradycardia': (None, 40),
}

O2_CLASSIFICATION = {
    'normal': (95, 100),
    'mild_hypoxia': (90, 95),
    'moderate_hypoxia': (85, 90),
    'critical_hypoxia': (None, 85),
}

BMI_CLASSIFICATION = {
    'underweight': (None, 18.5),
    'normal': (18.5, 25),
    'overweight': (25, 30),
    'obese_i': (30, 35),
    'obese_ii': (35, 40),
    'obese_iii': (40, None),
}

GLUCOSE_CLASSIFICATION = {
    'hypoglycemia': (None, 70),
    'normal': (70, 100),
    'prediabetes': (100, 126),
    'diabetes': (126, None),
}

CHOLESTEROL_CLASSIFICATION = {
    'desirable': (None, 200),
    'borderline_high': (200, 240),
    'high': (240, 300),
    'very_high': (300, None),
}

RISK_CRITICAL_CONDITIONS = [
    ('oxygen_saturation', '<', 85, 'critical_hypoxia'),
    ('systolic_bp', '>=', 180, 'hypertensive_crisis'),
    ('diastolic_bp', '>=', 120, 'hypertensive_crisis'),
    ('heart_rate', '>', 150, 'severe_tachycardia'),
    ('heart_rate', '<', 40, 'severe_bradycardia'),
    ('bmi', '>=', 40, 'morbid_obesity'),
]

RISK_HIGH_CONDITIONS = [
    ('systolic_bp', '>=', 140, 'hypertension_stage_2'),
    ('diastolic_bp', '>=', 90, 'hypertension_stage_2'),
    ('glucose', '>=', 126, 'diabetes'),
    ('bmi', '>=', 35, 'obesity_grade_ii'),
    ('oxygen_saturation', '<=', 90, 'moderate_hypoxia'),
    ('cholesterol', '>=', 240, 'high_cholesterol'),
]

RISK_MODERATE_CONDITIONS = [
    ('systolic_bp', '>=', 120, 'elevated_bp'),
    ('glucose', '>=', 100, 'prediabetes'),
    ('bmi', '>=', 25, 'overweight'),
    ('cholesterol', '>=', 200, 'borderline_cholesterol'),
    ('heart_rate', '>', 100, 'tachycardia'),
    ('heart_rate', '<', 60, 'bradycardia'),
    ('oxygen_saturation', '<=', 95, 'mild_hypoxia'),
    ('diastolic_bp', '>=', 80, 'elevated_bp'),
]

DIAGNOSIS_MAPPING = {
    'hipertension': 'Hypertension',
    'hipertensión': 'Hypertension',
    'hypertension': 'Hypertension',
    'diabetes': 'Diabetes Mellitus',
    'diabettes': 'Diabetes Mellitus',
    'diabetis': 'Diabetes Mellitus',
    'dm tipo 2': 'Diabetes Mellitus Type 2',
    'dm2': 'Diabetes Mellitus Type 2',
    'obesidad': 'Obesity',
    'obesidad morbida': 'Morbid Obesity',
    'obesidad mórbida': 'Morbid Obesity',
    'insuficiencia cardiaca': 'Heart Failure',
    'insuficiencia cardíaca': 'Heart Failure',
    'cardiopatia': 'Heart Disease',
    'cardiopatía': 'Heart Disease',
    'cardiopatia isquemica': 'Ischemic Heart Disease',
    'cardiopatía isquémica': 'Ischemic Heart Disease',
    'epoc': 'COPD',
    'enfermedad pulmonar': 'Lung Disease',
    'asma': 'Asthma',
    'cancer': 'Cancer',
    'cáncer': 'Cancer',
    'artritis': 'Arthritis',
    'artritis reumatoide': 'Rheumatoid Arthritis',
    'depresion': 'Depression',
    'depresión': 'Depression',
    'ansiedad': 'Anxiety',
    'enfermedad renal': 'Chronic Kidney Disease',
    'insuficiencia renal': 'Chronic Kidney Disease',
    'enfermedad hepatica': 'Liver Disease',
    'enfermedad hepática': 'Liver Disease',
    'hipotiroidismo': 'Hypothyroidism',
    'hipertiroidismo': 'Hyperthyroidism',
    'anemia': 'Anemia',
}

DIAGNOSIS_CODES = {
    'Hypertension': 'I10',
    'Diabetes Mellitus': 'E11',
    'Diabetes Mellitus Type 2': 'E11',
    'Obesity': 'E66',
    'Morbid Obesity': 'E66.0',
    'Heart Failure': 'I50',
    'Heart Disease': 'I25',
    'Ischemic Heart Disease': 'I25',
    'COPD': 'J44',
    'Lung Disease': 'J98',
    'Asthma': 'J45',
    'Cancer': 'C80',
    'Arthritis': 'M19',
    'Rheumatoid Arthritis': 'M05',
    'Depression': 'F32',
    'Anxiety': 'F41',
    'Chronic Kidney Disease': 'N18',
    'Liver Disease': 'K76',
    'Hypothyroidism': 'E03',
    'Hyperthyroidism': 'E05',
    'Anemia': 'D64',
}

BMI_CATEGORIES = [
    (0, 18.5, 'underweight', 'Bajo peso'),
    (18.5, 25, 'normal', 'Normal'),
    (25, 30, 'overweight', 'Sobrepeso'),
    (30, 35, 'obese_i', 'Obesidad Grado I'),
    (35, 40, 'obese_ii', 'Obesidad Grado II'),
    (40, float('inf'), 'obese_iii', 'Obesidad Mórbida'),
]

NORMAL_VALUES = {
    'systolic_bp': 120,
    'diastolic_bp': 80,
    'heart_rate': 75,
    'oxygen_saturation': 97,
    'glucose': 95.0,
    'cholesterol': 190.0,
    'triglycerides': 150.0,
    'hemoglobin': 14.0,
    'creatinine': 0.9,
    'height': 1.65,
    'weight': 70.0,
}
