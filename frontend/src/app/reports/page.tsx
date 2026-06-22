'use client';

import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/hooks/use-auth';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { apiRequest, getTokens } from '@/lib/api';
import { toast } from 'sonner';
import { formatNumber, getRiskColor, getRiskLabel } from '@/lib/utils';
import { FileText, Download, FileSpreadsheet, FileDown, Table2, ChevronLeft, ChevronRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import type { ReportData } from '@/types';

const COLORS = ['#22c55e', '#eab308', '#f97316', '#ef4444'];

interface RawDataResponse {
  source_name: string;
  source_type: string;
  columns: string[];
  rows: (string | number | boolean | null)[][];
  total: number;
  page: number;
  max_rows: number;
  total_pages: number;
}

function ReportsContent() {
  const { hasPermission } = useAuth();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [dataSources, setDataSources] = useState<any[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState<number | null>(null);
  const [rawData, setRawData] = useState<RawDataResponse | null>(null);
  const [rawLoading, setRawLoading] = useState(false);
  const [rawPage, setRawPage] = useState(0);
  const [showRawData, setShowRawData] = useState(false);

  useEffect(() => {
    apiRequest<{ success: boolean; results: any[] }>('/etl/sources/?page_size=100')
      .then(r => setDataSources(r.results || [])).catch(() => {});
  }, []);

  useEffect(() => {
    apiRequest<{ success: boolean; data: ReportData }>('/reports/executive/')
      .then(r => setReport(r.data)).catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleExport = async (format: string) => {
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const { access } = getTokens();

    const supported = ['csv', 'xlsx'];
    try {
      const res = await fetch(`${base}/reports/export/patients/?fmt=${format}`, {
        headers: { Authorization: `Bearer ${access}` },
      });
      if (!res.ok) throw new Error('Error al exportar');
      const blob = await res.blob();
      if (blob.size < 100) {
        const text = await blob.text();
        try { const j = JSON.parse(text); throw new Error(j.error || 'Error'); } catch {}
      }
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const ext = format === 'xlsx' ? 'xlsx' : format;
      a.href = url;
      a.download = `reporte_pacientes_${new Date().toISOString().slice(0, 10)}.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`Reporte ${format.toUpperCase()} descargado`);
    } catch {
      if (!supported.includes(format)) {
        if (!report) { toast.error('Sin datos para exportar'); return; }
        const demo = report.demographics;
        const rows: string[][] = [['Métrica', 'Valor']];
        rows.push(['Total Pacientes', String(report.summary?.total_patients ?? '')]);
        rows.push(['Pacientes Críticos', String(report.risk_analysis?.critical ?? '')]);
        rows.push(['Edad Promedio', String(demo?.avg_age ?? '')]);
        rows.push(['IMC Promedio', String(demo?.avg_bmi ?? '')]);
        rows.push(['Glucosa Promedio', String(demo?.avg_glucose ?? '')]);
        rows.push(['Riesgo Promedio', demo?.avg_risk ? `${demo.avg_risk}%` : '']);
        rows.push(['Hipertensos', String(demo?.hypertensive ?? '')]);
        rows.push(['Diabéticos', String(demo?.diabetic ?? '')]);
        rows.push(['Fumadores', String(demo?.smokers ?? '')]);
        rows.push(['Calidad ETL', report.summary?.average_quality_score != null ? `${report.summary.average_quality_score}%` : '']);
        rows.push(['Registros Procesados', String(report.summary?.total_records_processed ?? '')]);
        if (report.top_diagnoses?.length) {
          rows.push([], ['Top Diagnósticos', '']);
          report.top_diagnoses.slice(0, 10).forEach(d => rows.push([d.diagnosis || 'S/D', String(d.count)]));
        }
        const csv = rows.map(r => r.join(',')).join('\r\n');
        const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `reporte_ejecutivo_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success(`Reporte ${format.toUpperCase()} descargado (formato CSV)`);
        return;
      }
      toast.error('Error al descargar ' + format.toUpperCase());
    }
  };

  const fetchRawData = async (sourceId: number, page = 0) => {
    setRawLoading(true);
    setRawPage(page);
    try {
      const res = await apiRequest<{ success: boolean; data: RawDataResponse }>(
        `/reports/raw/${sourceId}/?page=${page}&max_rows=50`
      );
      setRawData(res.data);
    } catch {
      toast.error('Error al cargar datos originales');
    } finally {
      setRawLoading(false);
    }
  };

  const handleViewRaw = (sourceId: number) => {
    setSelectedSourceId(sourceId);
    setShowRawData(true);
    fetchRawData(sourceId, 0);
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
          <p className="stat-value">{demo?.avg_risk ? `${demo.avg_risk}%` : '—'}</p>
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

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Ver datos originales</CardTitle>
          <div className="flex items-center gap-2">
            <select
              className="border rounded px-2 py-1 text-sm"
              value={selectedSourceId ?? ''}
              onChange={e => {
                const v = e.target.value;
                if (v) handleViewRaw(Number(v));
              }}
            >
              <option value="">Seleccionar fuente...</option>
              {dataSources.map((ds: any) => (
                <option key={ds.id} value={ds.id}>{ds.name}</option>
              ))}
            </select>
          </div>
        </CardHeader>
        {showRawData && rawData && (
          <CardContent className="overflow-auto max-h-[500px]">
            {rawLoading ? (
              <div className="flex justify-center py-4">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              </div>
            ) : (
              <>
                <p className="text-xs text-muted-foreground mb-2">
                  {rawData.source_name} — {rawData.total} filas, mostrando {rawData.page * rawData.max_rows + 1} a {Math.min((rawData.page + 1) * rawData.max_rows, rawData.total)}
                </p>
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-muted">
                      {rawData.columns.map((col, i) => (
                        <th key={i} className="border px-2 py-1 text-left font-medium whitespace-nowrap">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rawData.rows.map((row, ri) => (
                      <tr key={ri} className={ri % 2 === 0 ? 'bg-background' : 'bg-muted/30'}>
                        {row.map((cell, ci) => (
                          <td key={ci} className="border px-2 py-1 whitespace-nowrap">{cell ?? '—'}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {rawData.total_pages > 1 && (
                  <div className="flex items-center justify-center gap-2 mt-3">
                    <Button variant="outline" size="sm" disabled={rawPage <= 0} onClick={() => fetchRawData(selectedSourceId!, rawPage - 1)}>
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-xs">Pág. {rawPage + 1} de {rawData.total_pages}</span>
                    <Button variant="outline" size="sm" disabled={rawPage >= rawData.total_pages - 1} onClick={() => fetchRawData(selectedSourceId!, rawPage + 1)}>
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </>
            )}
          </CardContent>
        )}
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
