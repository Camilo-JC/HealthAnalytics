import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)


def generate_clinical_dataset(n_records=1850):
    first_names_m = [
        'Carlos', 'Juan', 'Pedro', 'Luis', 'Andres', 'Miguel', 'Jose', 'Diego',
        'Fernando', 'Ricardo', 'Alberto', 'Manuel', 'Gabriel', 'David', 'Santiago',
        'Pablo', 'Oscar', 'Jorge', 'Ramon', 'Victor', 'Julian', 'Hector', 'Mario',
        'Sergio', 'Guillermo', 'Francisco', 'Alejandro', 'Eduardo', 'Roberto', 'Raul',
        'Enrique', 'Joaquin', 'Ivan', 'Cesar', 'Arturo', 'Felipe', 'Javier', 'Esteban',
        'Hugo', 'Marco', 'Ruben', 'Adrian', 'Daniel', 'Angel', 'Rafael', 'Fernando',
        'Mauricio', 'Fabian', 'Leonardo', 'Gustavo'
    ]
    first_names_f = [
        'Maria', 'Ana', 'Carmen', 'Luz', 'Patricia', 'Gloria', 'Sofia', 'Laura',
        'Diana', 'Marta', 'Elena', 'Rosa', 'Julia', 'Teresa', 'Claudia', 'Silvia',
        'Adriana', 'Paula', 'Andrea', 'Veronica', 'Isabel', 'Gabriela', 'Sara',
        'Valentina', 'Camila', 'Daniela', 'Natalia', 'Margarita', 'Lucia', 'Carolina',
        'Liliana', 'Monica', 'Alejandra', 'Viviana', 'Rocio', 'Beatriz', 'Cristina',
        'Esperanza', 'Pilar', 'Leticia', 'Mariana', 'Ximena', 'Jimena', 'Fernanda',
        'Catalina', 'Manuela', 'Angela', 'Tatiana', 'Marcela', 'Nadia'
    ]
    last_names = [
        'Garcia', 'Rodriguez', 'Martinez', 'Lopez', 'Gonzalez', 'Perez', 'Sanchez',
        'Ramirez', 'Torres', 'Flores', 'Rivera', 'Gomez', 'Diaz', 'Moreno', 'Jimenez',
        'Ruiz', 'Alvarez', 'Romero', 'Herrera', 'Castro', 'Ortiz', 'Medina', 'Vargas',
        'Reyes', 'Gutierrez', 'Castillo', 'Mendoza', 'Cruz', 'Morales', 'Ortega',
        'Delgado', 'Vasquez', 'Rojas', 'Campos', 'Nunez', 'Iglesias', 'Pena',
        'Cabrera', 'Santiago', 'Hernandez', 'Santos', 'Vega', 'Arias', 'Molina',
        'Aguilar', 'Contreras', 'Navarro', 'Chavez', 'Pacheco', 'Guerrero'
    ]

    diagnoses = [
        ('Hypertension', 'I10', 0.20),
        ('Diabetes Mellitus Type 2', 'E11', 0.15),
        ('Obesity', 'E66', 0.12),
        ('Heart Disease', 'I25', 0.08),
        ('COPD', 'J44', 0.05),
        ('Asthma', 'J45', 0.06),
        ('Chronic Kidney Disease', 'N18', 0.04),
        ('Hypothyroidism', 'E03', 0.05),
        ('Anemia', 'D64', 0.04),
        ('Arthritis', 'M19', 0.06),
        ('Depression', 'F32', 0.07),
        ('Anxiety', 'F41', 0.08),
    ]

    records = []
    for i in range(1, n_records + 1):
        gender = np.random.choice(['M', 'F'], p=[0.48, 0.52])
        age = int(np.random.normal(48, 18))
        age = max(1, min(95, age))

        if gender == 'M':
            first_name = np.random.choice(first_names_m)
        else:
            first_name = np.random.choice(first_names_f)
        last_name = f"{np.random.choice(last_names)} {np.random.choice(last_names)}"
        document = f"{np.random.randint(1000000, 12000000)}"

        height = np.random.normal(1.70 if gender == 'M' else 1.58, 0.08)
        height = round(max(1.40, min(2.10, height)), 2)

        if age < 30:
            base_weight = np.random.normal(65, 12)
        elif age < 50:
            base_weight = np.random.normal(72, 14)
        else:
            base_weight = np.random.normal(75, 15)
        base_weight = max(38, min(160, base_weight))

        bmi_correction = 0
        diagnosis = np.random.choice([d[0] for d in diagnoses], p=[d[2] for d in diagnoses])
        if diagnosis in ['Obesity']:
            bmi_correction = np.random.uniform(6, 15)
        elif diagnosis in ['Diabetes Mellitus Type 2', 'Hypertension', 'Heart Disease']:
            bmi_correction = np.random.uniform(2, 8)

        weight = round(base_weight + bmi_correction, 1)
        weight = max(38, min(180, weight))
        bmi = round(weight / (height ** 2), 2)

        if bmi < 18.5:
            bmi_cat = 'underweight'
        elif bmi < 25:
            bmi_cat = 'normal'
        elif bmi < 30:
            bmi_cat = 'overweight'
        elif bmi < 35:
            bmi_cat = 'obese_i'
        elif bmi < 40:
            bmi_cat = 'obese_ii'
        else:
            bmi_cat = 'obese_iii'

        if age > 50 or diagnosis in ['Hypertension', 'Heart Disease', 'Chronic Kidney Disease']:
            systolic = np.random.normal(140, 15)
        elif age > 30:
            systolic = np.random.normal(125, 12)
        else:
            systolic = np.random.normal(115, 10)
        systolic = int(max(85, min(220, systolic)))

        diastolic = int(max(50, min(130, systolic - np.random.normal(40, 8))))

        heart_rate = int(np.random.normal(76, 12))
        heart_rate = max(45, min(160, heart_rate))

        spo2 = int(np.random.normal(96, 3))
        spo2 = max(75, min(100, spo2))

        if diagnosis in ['Diabetes Mellitus Type 2']:
            glucose = np.random.normal(160, 40)
        elif diagnosis in ['Obesity']:
            glucose = np.random.normal(110, 20)
        else:
            glucose = np.random.normal(92, 15)
        glucose = round(max(50, min(450, glucose)), 1)

        if diagnosis in ['Heart Disease', 'Hypertension']:
            cholesterol = np.random.normal(230, 35)
        elif diagnosis in ['Obesity', 'Diabetes Mellitus Type 2']:
            cholesterol = np.random.normal(210, 30)
        else:
            cholesterol = np.random.normal(185, 25)
        cholesterol = round(max(80, min(400, cholesterol)), 1)

        ldl = round(cholesterol * np.random.uniform(0.5, 0.7), 1)
        hdl = round(np.random.normal(45 if gender == 'M' else 52, 8), 1)
        hdl = max(15, min(100, hdl))
        triglycerides = round(np.random.normal(150, 50), 1)
        triglycerides = max(40, min(800, triglycerides))
        hemoglobin = round(np.random.normal(15 if gender == 'M' else 13.5, 1.2), 1)
        hemoglobin = max(6, min(18, hemoglobin))
        creatinine = round(np.random.normal(0.95 if gender == 'M' else 0.85, 0.25), 2)
        creatinine = max(0.3, min(8, creatinine))

        smoking = np.random.choice([True, False], p=[0.18, 0.82])
        alcohol = np.random.choice([True, False], p=[0.35, 0.65])
        physical_activity = np.random.choice([True, False], p=[0.40, 0.60])
        family_history = np.random.choice([True, False], p=[0.25, 0.75])

        blood_type = np.random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
                                      p=[0.30, 0.06, 0.09, 0.02, 0.04, 0.01, 0.40, 0.08])

        diag_list = []
        if diagnosis == 'Hypertension':
            diag_list.append('Hypertension')
            if np.random.random() < 0.3:
                diag_list.append(np.random.choice(['Diabetes Mellitus Type 2', 'Obesity', 'Heart Disease']))
        elif diagnosis == 'Diabetes Mellitus Type 2':
            diag_list.append(diagnosis)
            if np.random.random() < 0.35:
                diag_list.append(np.random.choice(['Hypertension', 'Obesity', 'Chronic Kidney Disease']))
        elif diagnosis == 'Obesity':
            diag_list.append(diagnosis)
            if np.random.random() < 0.25:
                diag_list.append(np.random.choice(['Hypertension', 'Diabetes Mellitus Type 2', 'Sleep Apnea']))
        else:
            diag_list.append(diagnosis)

        risk_score = 0
        if age > 60: risk_score += 10
        elif age > 45: risk_score += 5
        if bmi >= 40: risk_score += 15
        elif bmi >= 30: risk_score += 10
        elif bmi >= 25: risk_score += 5
        if systolic >= 180: risk_score += 20
        elif systolic >= 160: risk_score += 15
        elif systolic >= 140: risk_score += 10
        elif systolic >= 130: risk_score += 5
        if glucose >= 300: risk_score += 20
        elif glucose >= 200: risk_score += 15
        elif glucose >= 126: risk_score += 10
        elif glucose >= 100: risk_score += 5
        if cholesterol >= 240: risk_score += 10
        if heart_rate >= 100: risk_score += 5
        if smoking: risk_score += 10
        if family_history: risk_score += 5
        if not physical_activity: risk_score += 5
        if alcohol: risk_score += 5

        risk_score = min(risk_score, 100)
        if risk_score >= 50: risk_cat = 'critical'
        elif risk_score >= 30: risk_cat = 'high'
        elif risk_score >= 15: risk_cat = 'medium'
        else: risk_cat = 'low'

        records.append({
            'patient_id': f'PT-{str(i).zfill(6)}',
            'first_name': first_name,
            'last_name': last_name,
            'document_type': 'CC',
            'document_number': document,
            'age': age,
            'gender': gender,
            'blood_type': blood_type,
            'height': height,
            'weight': weight,
            'bmi': bmi,
            'bmi_category': bmi_cat,
            'systolic_bp': systolic,
            'diastolic_bp': diastolic,
            'heart_rate': heart_rate,
            'oxygen_saturation': spo2,
            'glucose': glucose,
            'cholesterol': cholesterol,
            'cholesterol_ldl': ldl,
            'cholesterol_hdl': hdl,
            'triglycerides': triglycerides,
            'hemoglobin': hemoglobin,
            'creatinine': creatinine,
            'diagnosis': diagnosis,
            'diagnosis_code': '',
            'comorbidities': ', '.join(diag_list) if len(diag_list) > 1 else '',
            'smoking': smoking,
            'alcohol_consumption': alcohol,
            'physical_activity': physical_activity,
            'family_history': family_history,
            'risk_category': risk_cat,
            'risk_score': risk_score,
        })

    return pd.DataFrame(records)


def save_dataset(df, output_dir='data/outputs'):
    os.makedirs(output_dir, exist_ok=True)
    xlsx_path = os.path.join(output_dir, 'dataset_clinico_enriquecido.xlsx')
    csv_path = os.path.join(output_dir, 'dataset_clinico_enriquecido.csv')

    df.to_excel(xlsx_path, index=False, engine='openpyxl')
    df.to_csv(csv_path, index=False, encoding='utf-8')

    print(f"Dataset generado: {len(df)} registros")
    print(f"Excel: {xlsx_path}")
    print(f"CSV: {csv_path}")

    return xlsx_path, csv_path


if __name__ == '__main__':
    df = generate_clinical_dataset(1850)
    save_dataset(df)
    print(f"\nDistribución de riesgo:")
    print(df['risk_category'].value_counts())
    print(f"\nDistribución por sexo:")
    print(df['gender'].value_counts())
    print(f"\nEdad promedio: {df['age'].mean():.1f}")
    print(f"IMC promedio: {df['bmi'].mean():.1f}")
