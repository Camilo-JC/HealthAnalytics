-- Healthcare ETL Platform - Database Schema
-- PostgreSQL 16

-- Crear base de datos (ejecutar como superusuario)
-- CREATE DATABASE healthcare_etl WITH ENCODING 'UTF8' LC_COLLATE 'es_CO.UTF-8' LC_CTYPE 'es_CO.UTF-8';

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ============================================
-- TABLA: Usuarios (Autenticación)
-- ============================================
CREATE TABLE IF NOT EXISTS authentication_user (
    id BIGSERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    email VARCHAR(254) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(20) DEFAULT 'cc',
    document_id VARCHAR(50) UNIQUE,
    phone VARCHAR(20) DEFAULT '',
    role VARCHAR(20) NOT NULL DEFAULT 'analyst',
    avatar VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_email ON authentication_user(email);
CREATE INDEX idx_user_role ON authentication_user(role);

-- ============================================
-- TABLA: Pacientes
-- ============================================
CREATE TABLE IF NOT EXISTS patients_patient (
    id BIGSERIAL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    document_type VARCHAR(20) DEFAULT 'CC',
    document_number VARCHAR(50) NOT NULL UNIQUE,
    age INTEGER NOT NULL CHECK (age >= 0 AND age <= 120),
    gender VARCHAR(1) NOT NULL CHECK (gender IN ('M', 'F', 'O')),
    height NUMERIC(4,2) NOT NULL CHECK (height >= 0.50 AND height <= 2.50),
    weight NUMERIC(5,1) NOT NULL CHECK (weight >= 20.0 AND weight <= 300.0),
    bmi NUMERIC(5,2),
    bmi_category VARCHAR(20),
    systolic_bp INTEGER NOT NULL CHECK (systolic_bp >= 60 AND systolic_bp <= 280),
    diastolic_bp INTEGER NOT NULL CHECK (diastolic_bp >= 30 AND diastolic_bp <= 180),
    heart_rate INTEGER NOT NULL CHECK (heart_rate >= 30 AND heart_rate <= 250),
    oxygen_saturation INTEGER NOT NULL CHECK (oxygen_saturation >= 50 AND oxygen_saturation <= 100),
    glucose NUMERIC(6,1) NOT NULL CHECK (glucose >= 20.0 AND glucose <= 600.0),
    cholesterol NUMERIC(6,1) NOT NULL CHECK (cholesterol >= 50.0 AND cholesterol <= 500.0),
    triglycerides NUMERIC(6,1),
    hemoglobin NUMERIC(4,1),
    creatinine NUMERIC(4,2),
    diagnosis TEXT DEFAULT '',
    diagnosis_code VARCHAR(20) DEFAULT '',
    comorbidities TEXT,
    smoking BOOLEAN NOT NULL DEFAULT FALSE,
    alcohol_consumption BOOLEAN NOT NULL DEFAULT FALSE,
    physical_activity BOOLEAN NOT NULL DEFAULT FALSE,
    family_history BOOLEAN NOT NULL DEFAULT FALSE,
    risk_category VARCHAR(20),
    risk_score NUMERIC(5,2),
    source_file VARCHAR(255) DEFAULT '',
    is_processed BOOLEAN NOT NULL DEFAULT FALSE,
    is_valid BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_patient_id ON patients_patient(patient_id);
CREATE INDEX idx_patient_document ON patients_patient(document_number);
CREATE INDEX idx_patient_risk ON patients_patient(risk_category);
CREATE INDEX idx_patient_diagnosis ON patients_patient(diagnosis_code);
CREATE INDEX idx_patient_age_gender ON patients_patient(age, gender);
CREATE INDEX idx_patient_valid ON patients_patient(is_valid);

-- ============================================
-- TABLA: Alertas Clínicas
-- ============================================
CREATE TABLE IF NOT EXISTS patients_clinicalalert (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES patients_patient(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    description TEXT NOT NULL,
    parameter VARCHAR(50),
    value VARCHAR(50),
    threshold VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alert_patient ON patients_clinicalalert(patient_id);
CREATE INDEX idx_alert_severity ON patients_clinicalalert(severity);
CREATE INDEX idx_alert_active ON patients_clinicalalert(is_active);

-- ============================================
-- TABLA: Fuentes de Datos (ETL)
-- ============================================
CREATE TABLE IF NOT EXISTS etl_datasource (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('excel', 'csv', 'api', 'manual')),
    file VARCHAR(100),
    original_filename VARCHAR(255) DEFAULT '',
    file_size BIGINT,
    row_count INTEGER,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    uploaded_by_id BIGINT REFERENCES authentication_user(id) ON DELETE SET NULL,
    notes TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================
-- TABLA: Ejecuciones ETL
-- ============================================
CREATE TABLE IF NOT EXISTS etl_etlexecution (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES etl_datasource(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'extracting', 'transforming', 'loading', 'completed', 'failed')),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds DOUBLE PRECISION,
    records_read INTEGER DEFAULT 0,
    records_processed INTEGER DEFAULT 0,
    records_loaded INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    duplicates_removed INTEGER DEFAULT 0,
    errors_corrected INTEGER DEFAULT 0,
    quality_score DOUBLE PRECISION,
    error_message TEXT DEFAULT '',
    executed_by_id BIGINT REFERENCES authentication_user(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_etl_status ON etl_etlexecution(status);
CREATE INDEX idx_etl_source ON etl_etlexecution(source_id);
CREATE INDEX idx_etl_created ON etl_etlexecution(created_at DESC);

-- ============================================
-- TABLA: Logs ETL
-- ============================================
CREATE TABLE IF NOT EXISTS etl_etllog (
    id BIGSERIAL PRIMARY KEY,
    execution_id BIGINT REFERENCES etl_etlexecution(id) ON DELETE CASCADE,
    source_id BIGINT REFERENCES etl_datasource(id) ON DELETE CASCADE,
    level VARCHAR(10) NOT NULL CHECK (level IN ('debug', 'info', 'warning', 'error', 'critical')),
    phase VARCHAR(20) DEFAULT '',
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_log_level ON etl_etllog(level, phase);
CREATE INDEX idx_log_execution ON etl_etllog(execution_id);

-- ============================================
-- TABLA: Métricas de Calidad
-- ============================================
CREATE TABLE IF NOT EXISTS etl_dataqualitymetric (
    id BIGSERIAL PRIMARY KEY,
    execution_id BIGINT NOT NULL REFERENCES etl_etlexecution(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    threshold_min DOUBLE PRECISION,
    threshold_max DOUBLE PRECISION,
    passed BOOLEAN NOT NULL DEFAULT TRUE,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================
-- TABLA: Modelos ML
-- ============================================
CREATE TABLE IF NOT EXISTS ml_mlmodelregistry (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL CHECK (model_type IN ('random_forest', 'logistic_regression', 'decision_tree')),
    target_variable VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    accuracy DOUBLE PRECISION,
    precision DOUBLE PRECISION,
    recall DOUBLE PRECISION,
    f1_score DOUBLE PRECISION,
    roc_auc DOUBLE PRECISION,
    parameters JSONB,
    feature_importance JSONB,
    confusion_matrix JSONB,
    classification_report JSONB,
    training_records INTEGER,
    test_records INTEGER,
    training_duration DOUBLE PRECISION,
    trained_by_id BIGINT REFERENCES authentication_user(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================
-- TABLA: Predicciones ML
-- ============================================
CREATE TABLE IF NOT EXISTS ml_mlprediction (
    id BIGSERIAL PRIMARY KEY,
    model_id BIGINT NOT NULL REFERENCES ml_mlmodelregistry(id) ON DELETE CASCADE,
    patient_id BIGINT REFERENCES patients_patient(id) ON DELETE SET NULL,
    input_data JSONB NOT NULL,
    predicted_risk VARCHAR(20) NOT NULL,
    predicted_probability DOUBLE PRECISION,
    probabilities JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================
-- TABLA: Token Blacklist (JWT)
-- ============================================
CREATE TABLE IF NOT EXISTS token_blacklist_blacklistedtoken (
    id BIGSERIAL PRIMARY KEY,
    token_id VARCHAR(255) NOT NULL UNIQUE,
    blacklisted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS token_blacklist_outstandingtoken (
    id BIGSERIAL PRIMARY KEY,
    token_id VARCHAR(255) NOT NULL UNIQUE,
    token TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    user_id BIGINT REFERENCES authentication_user(id) ON DELETE SET NULL,
    jti VARCHAR(255)
);

-- ============================================
-- VISTAS
-- ============================================

-- Vista: Resumen de pacientes por riesgo
CREATE OR REPLACE VIEW v_patient_risk_summary AS
SELECT
    risk_category,
    COUNT(*) AS total_patients,
    AVG(age) AS avg_age,
    AVG(bmi) AS avg_bmi,
    AVG(risk_score) AS avg_risk_score,
    SUM(CASE WHEN smoking THEN 1 ELSE 0 END) AS smokers,
    SUM(CASE WHEN systolic_bp >= 140 THEN 1 ELSE 0 END) AS hypertensive,
    SUM(CASE WHEN glucose >= 126 THEN 1 ELSE 0 END) AS diabetic
FROM patients_patient
WHERE is_valid = TRUE
GROUP BY risk_category
ORDER BY risk_category;

-- Vista: Resumen ETL
CREATE OR REPLACE VIEW v_etl_summary AS
SELECT
    COUNT(*) AS total_executions,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS successful,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
    COALESCE(SUM(records_loaded), 0) AS total_records_loaded,
    COALESCE(AVG(duration_seconds), 0) AS avg_duration,
    COALESCE(AVG(quality_score), 0) AS avg_quality
FROM etl_etlexecution;

-- ============================================
-- FUNCIONES
-- ============================================

-- Función: Calcular IMC
CREATE OR REPLACE FUNCTION fn_calculate_bmi(p_weight NUMERIC, p_height NUMERIC)
RETURNS NUMERIC(5,2) AS $$
BEGIN
    IF p_height > 0 THEN
        RETURN ROUND(p_weight / (p_height * p_height), 2);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Función: Clasificar IMC
CREATE OR REPLACE FUNCTION fn_classify_bmi(p_bmi NUMERIC)
RETURNS VARCHAR(20) AS $$
BEGIN
    RETURN CASE
        WHEN p_bmi < 18.5 THEN 'underweight'
        WHEN p_bmi < 25 THEN 'normal'
        WHEN p_bmi < 30 THEN 'overweight'
        WHEN p_bmi < 35 THEN 'obese_i'
        WHEN p_bmi < 40 THEN 'obese_ii'
        ELSE 'obese_iii'
    END;
END;
$$ LANGUAGE plpgsql;
