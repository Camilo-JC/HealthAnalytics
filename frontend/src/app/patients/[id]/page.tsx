'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { AuthProvider } from '@/hooks/use-auth';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { apiRequest } from '@/lib/api';
import { getRiskColor, getRiskLabel, getSeverityColor, formatDate, translateGender } from '@/lib/utils';
import { ArrowLeft, AlertTriangle } from 'lucide-react';
import Link from 'next/link';
import type { Patient, ClinicalAlert } from '@/types';

function PatientDetailContent() {
  const { id } = useParams<{ id: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [alerts, setAlerts] = useState<ClinicalAlert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiRequest<{ success: boolean; data: Patient }>(`/patients/${id}/`).then(r => setPatient(r.data)).catch(() => {}),
      apiRequest<{ success: boolean; results: ClinicalAlert[] }>(`/patients/${id}/alerts/`)
        .then(r => setAlerts(r.results || [])).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [id]);

  if (loading) return (
    <div className="page-container flex justify-center pt-12">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  if (!patient) return (
    <div className="page-container"><p className="text-muted-foreground">Paciente no encontrado</p></div>
  );

  const vitals = [
    { label: 'Presión Sistólica', value: `${patient.systolic_bp} mmHg` },
    { label: 'Presión Diastólica', value: `${patient.diastolic_bp} mmHg` },
    { label: 'Frecuencia Cardíaca', value: `${patient.heart_rate} lpm` },
    { label: 'Saturación Oxígeno', value: `${patient.oxygen_saturation}%` },
  ];
  const labs = [
    { label: 'Glucosa', value: `${patient.glucose} mg/dL` },
    { label: 'Colesterol Total', value: `${patient.cholesterol} mg/dL` },
    { label: 'Colesterol LDL', value: patient.cholesterol_ldl != null ? `${patient.cholesterol_ldl} mg/dL` : '—' },
    { label: 'Colesterol HDL', value: patient.cholesterol_hdl != null ? `${patient.cholesterol_hdl} mg/dL` : '—' },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="flex items-center gap-3">
          <Link href="/patients">
            <Button variant="ghost" size="icon"><ArrowLeft className="h-5 w-5" /></Button>
          </Link>
          <div>
            <h2 className="page-title">{patient.first_name} {patient.last_name}</h2>
            <p className="text-sm text-muted-foreground">{patient.patient_id} · {patient.document_type} {patient.document_number}</p>
          </div>
        </div>
        <Badge className={getRiskColor(patient.risk_category)}>{getRiskLabel(patient.risk_category)}</Badge>
      </div>

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
        <Card>
          <CardHeader><CardTitle className="text-base">Datos Demográficos</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">Edad</span><span className="font-medium">{patient.age} años</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Género</span><span className="font-medium">{translateGender(patient.gender)}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Tipo Sangre</span><span className="font-medium">{patient.blood_type || '—'}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Altura</span><span className="font-medium">{patient.height} m</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Peso</span><span className="font-medium">{patient.weight} kg</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">IMC</span><span className="font-medium">{patient.bmi ? Number(patient.bmi).toFixed(1) : '—'}</span></div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">Signos Vitales</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            {vitals.map(v => (
              <div key={v.label} className="flex justify-between">
                <span className="text-muted-foreground">{v.label}</span>
                <span className="font-medium">{v.value}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">Laboratorio</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            {labs.map(l => (
              <div key={l.label} className="flex justify-between">
                <span className="text-muted-foreground">{l.label}</span>
                <span className="font-medium">{l.value}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-base">Diagnóstico y Riesgo</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">Diagnóstico</span><span className="font-medium text-right max-w-[60%]">{patient.diagnosis}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Código</span><span className="font-medium">{patient.diagnosis_code || '—'}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Riesgo</span><Badge className={getRiskColor(patient.risk_category)}>{getRiskLabel(patient.risk_category)}</Badge></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Score</span><span className="font-medium">{patient.risk_score?.toFixed(1)}%</span></div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">Estilo de Vida</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">Fumador</span><span className="font-medium">{patient.smoking ? 'Sí' : 'No'}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Alcohol</span><span className="font-medium">{patient.alcohol_consumption ? 'Sí' : 'No'}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Actividad Física</span><span className="font-medium">{patient.physical_activity ? 'Sí' : 'No'}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Antecedentes</span><span className="font-medium">{patient.family_history ? 'Sí' : 'No'}</span></div>
          </CardContent>
        </Card>
      </div>

      {alerts.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><AlertTriangle className="h-4 w-4" />Alertas ({alerts.length})</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {alerts.map(a => (
              <div key={a.id} className="flex items-center gap-3 rounded-lg border p-3 text-sm">
                <Badge className={getSeverityColor(a.severity)}>{a.severity}</Badge>
                <div className="flex-1"><p className="font-medium">{a.alert_type}</p><p className="text-xs text-muted-foreground">{a.description}</p></div>
                <span className="text-xs text-muted-foreground">{formatDate(a.created_at)}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function PatientDetailPage() {
  return (
    <AuthProvider>
      <AppLayout>
        <PatientDetailContent />
      </AppLayout>
    </AuthProvider>
  );
}
