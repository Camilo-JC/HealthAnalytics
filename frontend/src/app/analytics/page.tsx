'use client';

import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/hooks/use-auth';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { apiRequest } from '@/lib/api';
import { formatNumber } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#22c55e', '#eab308', '#f97316', '#ef4444', '#3b82f6', '#8b5cf6'];

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

  const metrics = [
    { label: 'Total Pacientes', value: formatNumber((stats as any)?.total_patients) },
    { label: 'Edad Promedio', value: formatNumber((stats as any)?.avg_age, 1) },
    { label: 'IMC Promedio', value: formatNumber((stats as any)?.avg_bmi, 1) },
    { label: 'Glucosa Promedio', value: formatNumber((stats as any)?.avg_glucose, 1) },
    { label: 'Colesterol Prom.', value: formatNumber((stats as any)?.avg_cholesterol, 1) },
    { label: 'PA Sistólica Prom.', value: formatNumber((stats as any)?.avg_systolic_bp, 1) },
  ];

  const riskDist = stats?.risk_distribution as Record<string, number> | undefined;
  const riskData = riskDist ? Object.entries(riskDist).map(([k, v]) => ({ name: k === 'low' ? 'Bajo' : k === 'medium' ? 'Medio' : k === 'high' ? 'Alto' : 'Crítico', value: v })) : [];
  const ageDist = stats?.age_distribution as Record<string, number> | undefined;
  const ageData = ageDist ? Object.entries(ageDist).map(([k, v]) => ({ group: k, count: v })) : [];
  const diagDist = stats?.diagnosis_distribution as Record<string, number> | undefined;
  const diagData = diagDist ? Object.entries(diagDist).slice(0, 10).map(([k, v]) => ({ diagnosis: k, count: v })) : [];

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 className="page-title">Analítica</h2>
          <p className="text-sm text-muted-foreground">Estadísticas y métricas de la población</p>
        </div>
      </div>

      <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
        {metrics.map(m => (
          <Card key={m.label}>
            <CardContent className="p-4 text-center">
              <p className="text-xs text-muted-foreground uppercase tracking-wider">{m.label}</p>
              <p className="text-xl font-bold mt-1">{m.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        {riskData.length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-base">Distribución de Riesgo</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90}
                    label={({ name, value }) => `${name}: ${value}`}>
                    {riskData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
        {ageData.length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-base">Distribución por Edad</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={ageData}>
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
        {diagData.length > 0 && (
          <Card className="lg:col-span-2">
            <CardHeader><CardTitle className="text-base">Diagnósticos más Frecuentes</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={diagData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="diagnosis" width={200} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#22c55e" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>
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
