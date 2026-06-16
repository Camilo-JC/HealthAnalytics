'use client';

import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/hooks/use-auth';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { apiRequest } from '@/lib/api';
import { formatNumber } from '@/lib/utils';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line,
} from 'recharts';

const RISK_COLORS: Record<string, string> = {
  low: '#22c55e',
  Bajo: '#22c55e',
  medium: '#eab308',
  Medio: '#eab308',
  high: '#f97316',
  Alto: '#f97316',
  critical: '#ef4444',
  Crítico: '#ef4444',
};
const COLORS = ['#22c55e', '#eab308', '#f97316', '#ef4444', '#3b82f6', '#8b5cf6', '#06b6d4', '#ec4899'];

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4 text-center">
        <p className="text-xs text-muted-foreground uppercase tracking-wider leading-tight">{label}</p>
        <p className="text-2xl font-bold mt-1 text-foreground">{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
      </CardContent>
    </Card>
  );
}

function AdvancedStatRow({ label, stats }: { label: string; stats: { mean?: number; median?: number; mode?: number; std?: number } }) {
  return (
    <div className="grid grid-cols-4 gap-2 py-2 border-b last:border-0 text-sm">
      <div className="font-medium text-muted-foreground col-span-1">{label}</div>
      <div className="text-center">
        <div className="text-xs text-muted-foreground">Media</div>
        <div className="font-semibold">{formatNumber(stats.mean, 1)}</div>
      </div>
      <div className="text-center">
        <div className="text-xs text-muted-foreground">Mediana</div>
        <div className="font-semibold">{formatNumber(stats.median, 1)}</div>
      </div>
      <div className="text-center">
        <div className="text-xs text-muted-foreground">Desv. Est.</div>
        <div className="font-semibold">{formatNumber(stats.std, 2)}</div>
      </div>
    </div>
  );
}

function AnalyticsContent() {
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest<{ success: boolean; data: Record<string, unknown> }>('/analytics/stats/')
      .then(r => setStats(r.data)).catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="page-container flex justify-center pt-12">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  if (!stats) return (
    <div className="page-container">
      <div className="flex flex-col items-center justify-center pt-16 text-center">
        <p className="text-muted-foreground">No hay datos disponibles. Ejecuta el ETL primero para cargar pacientes.</p>
      </div>
    </div>
  );

  const s = stats as any;

  const vitals = s?.vitals_averages as Record<string, number> | undefined;
  const mainMetrics = [
    { label: 'Total Pacientes', value: formatNumber(s?.total_patients), sub: 'registros activos' },
    { label: 'Edad Promedio', value: formatNumber(s?.age_stats?.mean, 1), sub: 'años' },
    { label: 'IMC Promedio', value: formatNumber(vitals?.avg_bmi, 1), sub: 'kg/m²' },
    { label: 'Glucosa Promedio', value: formatNumber(vitals?.avg_glucose, 1), sub: 'mg/dL' },
    { label: 'Colesterol Prom.', value: formatNumber(vitals?.avg_cholesterol, 1), sub: 'mg/dL' },
    { label: 'PA Sistólica', value: formatNumber(vitals?.avg_systolic, 1), sub: 'mmHg' },
  ];

  const advancedStats = s?.advanced_stats as Record<string, { mean: number; median: number; mode: number; std: number }> | undefined;

  const riskDist = (s?.risk_distribution || []) as { risk_category: string; count: number }[];
  const riskData = riskDist.map(d => ({
    name: d.risk_category === 'low' ? 'Bajo' : d.risk_category === 'medium' ? 'Medio' : d.risk_category === 'high' ? 'Alto' : d.risk_category === 'critical' ? 'Crítico' : d.risk_category || 'S/R',
    value: d.count,
    key: d.risk_category || 'unknown',
  }));

  const ageDist = (s?.age_distribution || []) as { group: string; count: number }[];
  const ageData = ageDist.map(d => ({ group: d.group, count: d.count }));

  const diagDist = (s?.diagnosis_distribution || []) as { diagnosis: string; count: number }[];
  const diagData = diagDist.slice(0, 10).map(d => ({ diagnosis: d.diagnosis || 'Sin diagnóstico', count: d.count }));

  const genderDist = (s?.gender_distribution || []) as { gender: string; count: number }[];
  const genderData = genderDist.map(d => ({
    name: d.gender === 'M' ? 'Masculino' : d.gender === 'F' ? 'Femenino' : d.gender || 'Otro',
    value: d.count,
  }));

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 className="page-title">Analítica Clínica</h2>
          <p className="text-sm text-muted-foreground">Estadísticas, métricas y distribuciones de la población clínica</p>
        </div>
        <Badge variant="outline" className="text-xs">{formatNumber(s?.total_patients)} pacientes</Badge>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
        {mainMetrics.map(m => (
          <StatCard key={m.label} label={m.label} value={m.value} sub={m.sub} />
        ))}
      </div>

      {/* Charts Row 1 */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
        {riskData.length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-base">Distribución de Riesgo</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={85} innerRadius={40}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}>
                    {riskData.map((d, i) => (
                      <Cell key={i} fill={RISK_COLORS[d.key] || COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => [`${v} pacientes`, '']} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {ageData.length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-base">Distribución por Edad</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={ageData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="group" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v: number) => [`${v} pacientes`, 'Cantidad']} />
                  <Bar dataKey="count" fill="#22c55e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {genderData.length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-base">Distribución por Género</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={genderData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={85} innerRadius={40}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}>
                    {genderData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => [`${v} pacientes`, '']} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Diagnoses chart - full width */}
      {diagData.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Top 10 Diagnósticos más Frecuentes</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={diagData} layout="vertical" margin={{ left: 10, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="diagnosis" width={220} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => [`${v} casos`, 'Frecuencia']} />
                <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Advanced Statistics Table */}
      {advancedStats && Object.keys(advancedStats).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Estadísticas Descriptivas Avanzadas</CardTitle>
            <p className="text-xs text-muted-foreground mt-1">Media, mediana y desviación estándar por variable clínica</p>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <div className="min-w-[400px]">
                <div className="grid grid-cols-4 gap-2 pb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider border-b">
                  <div>Variable</div>
                  <div className="text-center">Media</div>
                  <div className="text-center">Mediana</div>
                  <div className="text-center">Desv. Est.</div>
                </div>
                {Object.entries(advancedStats).map(([key, s]) => {
                  const labels: Record<string, string> = {
                    age: 'Edad (años)',
                    bmi: 'IMC (kg/m²)',
                    glucose: 'Glucosa (mg/dL)',
                    cholesterol: 'Colesterol (mg/dL)',
                    systolic_bp: 'PA Sistólica (mmHg)',
                    diastolic_bp: 'PA Diastólica (mmHg)',
                    heart_rate: 'Frec. Cardíaca (bpm)',
                    hemoglobin: 'Hemoglobina (g/dL)',
                    creatinine: 'Creatinina (mg/dL)',
                  };
                  return (
                    <AdvancedStatRow
                      key={key}
                      label={labels[key] || key}
                      stats={s}
                    />
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <AuthProvider>
      <AppLayout>
        <AnalyticsContent />
      </AppLayout>
    </AuthProvider>
  );
}
