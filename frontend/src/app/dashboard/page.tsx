'use client';

import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/hooks/use-auth';
import { AppLayout } from '@/components/layout/app-layout';
import { KPICard } from '@/components/dashboard/kpi-card';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { apiRequest } from '@/lib/api';
import { formatNumber, getRiskColor, getRiskLabel, getSeverityColor, formatDate } from '@/lib/utils';
import {
  Users, Heart, Activity, AlertTriangle, TrendingUp, Wind, Award, Download,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend,
} from 'recharts';
import type { PatientStats, ChartData, ClinicalAlert } from '@/types';

const COLORS = ['#22c55e', '#eab308', '#f97316', '#ef4444', '#3b82f6', '#8b5cf6'];

function DashboardContent() {
  const { hasPermission } = useAuth();
  const [stats, setStats] = useState<PatientStats | null>(null);
  const [charts, setCharts] = useState<ChartData | null>(null);
  const [alerts, setAlerts] = useState<ClinicalAlert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiRequest<{ success: boolean; data: PatientStats }>('/dashboard/kpi/').then(r => setStats(r.data)).catch(() => {}),
      apiRequest<{ success: boolean; data: ChartData }>('/dashboard/charts/').then(r => setCharts(r.data)).catch(() => {}),
      apiRequest<{ success: boolean; data: { recent: ClinicalAlert[] } }>('/dashboard/alerts/')
        .then(r => setAlerts(r.data.recent || [])).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="page-container flex items-center justify-center min-h-[60vh]">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 className="page-title">Dashboard</h2>
          <p className="text-sm text-muted-foreground">Resumen general del sistema</p>
        </div>
        <Button variant="outline" size="sm"><Download className="h-4 w-4 mr-2" />Exportar</Button>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard title="Total Pacientes" value={stats?.total_patients ?? '—'} icon={<Users className="h-5 w-5" />}
          description="Registros activos" />
        <KPICard title="Pacientes Críticos" value={stats?.critical_patients ?? '—'} icon={<AlertTriangle className="h-5 w-5" />}
          description="Riesgo crítico" className="border-red-200" />
        <KPICard title="Hipertensos" value={stats?.hypertensive ?? '—'} icon={<Heart className="h-5 w-5" />}
          description="PA sistólica ≥140" />
        <KPICard title="Fumadores" value={stats?.smokers ?? '—'} icon={<Wind className="h-5 w-5" />}
          description="Hábito registrado" />
        <KPICard title="Riesgo Promedio" value={stats?.avg_risk != null ? `${stats.avg_risk.toFixed(1)}%` : '—'}
          icon={<TrendingUp className="h-5 w-5" />}           description="Puntaje global" />
        {hasPermission('etl') && (
          <KPICard title="ETL Ejecuciones" value={stats?.etl_executions ?? '—'} icon={<Activity className="h-5 w-5" />}
            description={`${formatNumber(stats?.etl_records_processed ?? 0)} registros`} />
        )}
        {hasPermission('ml') && (
          <KPICard title="Precisión ML" value={stats?.model_accuracy != null ? `${(stats.model_accuracy * 100).toFixed(1)}%` : '—'}
            icon={<Award className="h-5 w-5" />} description="Mejor modelo" />
        )}
        <KPICard title="Alertas Activas" value={stats?.active_alerts ?? '—'} icon={<AlertTriangle className="h-5 w-5" />}
          className="border-yellow-200" />
      </div>

      {/* Charts row */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        {charts?.risk_distribution && (
          <Card>
            <CardHeader><CardTitle className="text-base">Distribución de Riesgo</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={charts.risk_distribution} dataKey="count" nameKey="risk_category" cx="50%" cy="50%" outerRadius={90}
                    label={({ risk_category, count }) => `${getRiskLabel(risk_category)}: ${count}`}>
                    {charts.risk_distribution.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => [value, 'Pacientes']} />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {charts?.age_distribution && (
          <Card>
            <CardHeader><CardTitle className="text-base">Distribución por Edad</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={charts.age_distribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="group" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#22c55e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {charts?.gender_distribution && (
          <Card>
            <CardHeader><CardTitle className="text-base">Distribución por Género</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={charts.gender_distribution.map(g => ({ ...g, name: g.gender === 'M' ? 'Masculino' : g.gender === 'F' ? 'Femenino' : 'Otro' }))}
                    dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, count }) => `${name}: ${count}`}>
                    <Cell fill="#22c55e" /><Cell fill="#3b82f6" /><Cell fill="#a855f7" />
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {charts?.diagnosis_distribution && (
          <Card>
            <CardHeader><CardTitle className="text-base">Diagnósticos Principales</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={charts.diagnosis_distribution.slice(0, 8)} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="diagnosis" width={150} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#22c55e" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Alertas Recientes</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.map((a) => (
                <div key={a.id} className="flex items-center gap-3 rounded-lg border p-3 text-sm">
                  <Badge className={getSeverityColor(a.severity)}>
                    {a.severity === 'critical' ? 'Crítico' : a.severity === 'warning' ? 'Advertencia' : 'Info'}
                  </Badge>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{a.alert_type}</p>
                    <p className="text-xs text-muted-foreground truncate">{a.description}</p>
                  </div>
                  <span className="text-xs text-muted-foreground shrink-0">{formatDate(a.created_at)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <AuthProvider>
      <AppLayout>
        <DashboardContent />
      </AppLayout>
    </AuthProvider>
  );
}
