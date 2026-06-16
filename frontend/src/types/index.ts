export interface User {
  id: number;
  email: string;
  full_name: string;
  document_type: string;
  document_id: string;
  phone: string;
  role: 'admin' | 'analyst' | 'doctor';
  avatar: string | null;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
}

export interface AuthResponse {
  success: boolean;
  access: string;
  refresh: string;
  user: User;
}

export interface ProfileResponse {
  success: boolean;
  data: User;
}

export interface ApiError {
  success: false;
  status_code?: number;
  error?: string;
  errors?: { field: string; message: string }[];
}

export interface PaginatedResponse<T> {
  success: boolean;
  count: number;
  total_pages: number;
  current_page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Patient {
  id: number;
  patient_id: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  document_type: string;
  document_number: string;
  age: number;
  gender: string;
  blood_type: string;
  height: number;
  weight: number;
  bmi: number;
  bmi_category: string;
  systolic_bp: number;
  diastolic_bp: number;
  heart_rate: number;
  oxygen_saturation: number;
  glucose: number;
  cholesterol: number;
  cholesterol_ldl: number | null;
  cholesterol_hdl: number | null;
  triglycerides: number | null;
  hemoglobin: number | null;
  creatinine: number | null;
  diagnosis: string;
  diagnosis_code: string;
  comorbidities: string | null;
  smoking: boolean;
  alcohol_consumption: boolean;
  physical_activity: boolean;
  family_history: boolean;
  risk_category: string;
  risk_score: number;
  source_file: string;
  is_processed: boolean;
  is_valid: boolean;
  created_at: string;
  updated_at: string;
}

export interface PatientStats {
  total_patients: number;
  critical_patients: number;
  hypertensive: number;
  diabetic: number;
  smokers: number;
  avg_risk: number;
  etl_executions: number | null;
  etl_records_processed: number | null;
  model_accuracy: number | null;
  model_f1: number | null;
  active_alerts: number | null;
}

export interface ChartData {
  risk_distribution: { risk_category: string; count: number }[];
  gender_distribution: { gender: string; count: number }[];
  age_distribution: { group: string; count: number }[];
  bmi_distribution: { bmi_category: string; count: number }[];
  diagnosis_distribution: { diagnosis: string; count: number }[];
}

export interface ClinicalAlert {
  id: number;
  patient: number;
  patient_name?: string;
  patient_id?: string;
  alert_type: string;
  severity: string;
  description: string;
  parameter?: string;
  value?: string;
  threshold?: string;
  is_active: boolean;
  resolved_at: string | null;
  created_at: string;
}

export interface DataSource {
  id: number;
  name: string;
  source_type: string;
  file: string;
  status: string;
  records_read: number;
  records_loaded: number;
  notes: string;
  created_at: string;
}

export interface ETLExecution {
  id: number;
  source: number;
  source_name?: string;
  status: string;
  records_read: number;
  records_processed: number;
  records_loaded: number;
  records_failed: number;
  duplicates_removed: number;
  errors_corrected: number;
  quality_score: number | null;
  error_message: string;
  duration_seconds: number | null;
  executed_by: number | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface MLModel {
  id: number;
  name: string;
  model_type: string;
  target_variable: string;
  version: string;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  roc_auc: number | null;
  is_active: boolean;
  feature_importance: Record<string, number> | null;
  created_at: string;
}

export interface MLComparison {
  model: string;
  model_type: string;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  roc_auc: number | null;
  version: string;
  is_active: boolean;
  feature_importance: Record<string, number> | null;
}

export interface AnalyticsStats {
  total_patients: number;
  avg_age: number;
  avg_bmi: number;
  avg_glucose: number;
  avg_cholesterol: number;
  avg_systolic_bp: number;
  avg_heart_rate: number;
  gender_distribution: Record<string, number>;
  risk_distribution: Record<string, number>;
  bmi_distribution: Record<string, number>;
  age_distribution: Record<string, number>;
  diagnosis_distribution: Record<string, number>;
}

export interface CorrelationData {
  matrix: number[][];
  features: string[];
}

export interface TrendData {
  dates: string[];
  values: number[];
  metric: string;
}

export interface ReportData {
  generated_at: string;
  period?: string;
  summary: {
    total_patients: number;
    total_etl_executions: number;
    successful_etl: number;
    failed_etl: number;
    total_records_processed: number;
    average_quality_score: number;
  };
  risk_analysis: Record<string, number>;
  demographics: {
    avg_age: number;
    avg_bmi: number;
    avg_glucose: number;
    avg_risk: number;
    hypertensive: number;
    diabetic: number;
    smokers: number;
    obese: number;
  };
  top_diagnoses: { diagnosis: string; count: number }[];
}

export interface RolePermissions {
  admin: string[];
  analyst: string[];
  doctor: string[];
}

export const PERMISSIONS: RolePermissions = {
  admin: [
    'dashboard', 'patients', 'patients_manage', 'patients_delete',
    'etl', 'etl_execute', 'etl_delete',
    'analytics', 'analytics_export',
    'ml', 'ml_train', 'ml_predict',
    'reports', 'reports_export',
    'users_manage', 'users_delete',
    'settings', 'settings_global', 'audit_view',
  ],
  analyst: [
    'dashboard', 'patients',
    'etl', 'etl_execute',
    'analytics', 'analytics_export',
    'ml', 'ml_train', 'ml_predict',
    'reports', 'reports_export',
  ],
  doctor: [
    'dashboard', 'patients', 'analytics', 'reports',
  ],
};

export function hasPermission(role: string | undefined, permission: string): boolean {
  if (!role) return false;
  const perms = PERMISSIONS[role as keyof RolePermissions] || [];
  return perms.includes(permission);
}
