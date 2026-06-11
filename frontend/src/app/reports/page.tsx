'use client';

import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/hooks/use-auth';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { apiRequest } from '@/lib/api';
import { formatNumber, getRiskColor, getRiskLabel, formatPercent } from '@/lib/utils';
import { FileText, Download, FileSpreadsheet, FileDown } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import type { ReportData } from '@/types';

const COLORS = ['#22c55e', '#eab308', '#f97316', '#ef4444'];

function ReportsContent() {
  const { hasPermission } = useAuth();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest<{ success: boolean; data: ReportData }>('/reports/executive/')
      .then(r => setReport(r.data)).catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleExport = (format: string) => {
    window.open(`${process.env.NEXT_PUBLIC_API_URL}/reports/export/${format}/`, '_blank');
  };

  if (loading) return (
    <div className="page-container flex justify-center pt-12">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  const s = report?.summary;
  const risk = report?.risk_analysis || {};
  const demo = report?.demographics;
  const riskData = Object.keys(risk).length > 0
    ? Object.entries(risk).map(([k, v]) => ({ name: getRiskLabel(k), value: v }))
    : [];
  const totalPatients = s?.total_patients || 0;
  const criticalCount = risk?.critical || 0;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 className="page-title">Reportes</h2>
          <p className="text-sm text-muted-foreground">Reporte ejecutivo y exportación de datos</p>
        </div>
        {hasPermission('reports_export') && (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => handleExport('pdf')}>
              <FileText className="h-4 w-4 mr-2" />PDF
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleExport('xlsx')}>
              <FileSpreadsheet className="h-4 w-4 mr-2" />Excel
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleExport('csv')}>
              <FileDown className="h-4 w-4 mr-2" />CSV
            </Button>
          </div>
        )}
      </div>

      <div className="grid gap-4 grid-cols-2 sm:grid-cols-4">
        <Card><CardContent className="p-4 text-center">
          <p className="stat-label">Total Pacientes</p>
          <p className="stat-value">{formatNumber(totalPatients)}</p>
        </CardContent></Card>
        <Card><CardContent className="p-4 text-center">
          <p className="stat-label">Críticos</p>
          <p className="stat-value text-red-600">{formatNumber(criticalCount)}</p>
        </CardContent></Card>
        <Card><CardContent className="p-4 text-center">
          <p className="stat-label">Riesgo Promedio</p>
          <p className="stat-value">{demo?.avg_age ? `${demo.avg_age} años` : '—'}</p>
        </CardContent></Card>
        <Card><CardContent className="p-4 text-center">
          <p className="stat-label">Calidad ETL</p>
          <p className="stat-value">{s?.average_quality_score != null ? `${s.average_quality_score}%` : '—'}</p>
        </CardContent></Card>
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

        {report?.top_diagnoses && report.top_diagnoses.length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-base">Principales Diagnósticos</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={report.top_diagnoses.slice(0, 8)} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="diagnosis" width={160} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#22c55e" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">Resumen Ejecutivo</CardTitle></CardHeader>
        <CardContent className="text-sm space-y-2">
          <p>Reporte generado con {formatNumber(totalPatients)} pacientes registrados en la plataforma.
          {criticalCount ? ` Se identificaron ${criticalCount} pacientes en estado crítico que requieren atención prioritaria.` : ''}
          {demo?.avg_age ? ` Edad promedio de ${demo.avg_age} años, IMC promedio ${demo.avg_bmi}.` : ''}
          {s?.total_records_processed ? ` Registros procesados: ${formatNumber(s.total_records_processed)} con calidad del ${s.average_quality_score}%.` : ''}</p>
        </CardContent>
      </Card>
    </div>
  );
}

export default function ReportsPage() {
  return (
    <AuthProvider>
      <AppLayout>
        <ReportsContent />
      </AppLayout>
    </AuthProvider>
  );
}
