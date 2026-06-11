'use client';

import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/hooks/use-auth';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { apiRequest, uploadFile } from '@/lib/api';
import { formatDate, formatNumber } from '@/lib/utils';
import { Upload, Play, Trash2, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import type { ETLExecution, DataSource } from '@/types';

const statusConfig: Record<string, { label: string; class: string; icon: typeof CheckCircle }> = {
  completed: { label: 'Completado', class: 'bg-green-100 text-green-800', icon: CheckCircle },
  failed: { label: 'Fallido', class: 'bg-red-100 text-red-800', icon: XCircle },
  running: { label: 'Ejecutando', class: 'bg-blue-100 text-blue-800', icon: Clock },
  pending: { label: 'Pendiente', class: 'bg-yellow-100 text-yellow-800', icon: AlertCircle },
  extracting: { label: 'Extrayendo', class: 'bg-blue-100 text-blue-800', icon: Clock },
  transforming: { label: 'Transformando', class: 'bg-blue-100 text-blue-800', icon: Clock },
  loading: { label: 'Cargando', class: 'bg-blue-100 text-blue-800', icon: Clock },
};

function ETLContent() {
  const { hasPermission } = useAuth();
  const [executions, setExecutions] = useState<ETLExecution[]>([]);
  const [sources, setSources] = useState<DataSource[]>([]);
  const [uploading, setUploading] = useState(false);
  const [executing, setExecuting] = useState(false);

  const loadData = () => {
    apiRequest<{ success: boolean; results: ETLExecution[] }>('/etl/executions/history/')
      .then(r => setExecutions(r.results || [])).catch(() => {});
    apiRequest<{ success: boolean; results: DataSource[] }>('/etl/sources/')
      .then(r => setSources(r.results || [])).catch(() => {});
  };

  useEffect(() => { loadData(); }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const res = await uploadFile('/etl/sources/upload/', file, { name: file.name, source_type: file.name.endsWith('.csv') ? 'csv' : 'excel' });
      toast.success('Archivo subido exitosamente');
      loadData();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Error al subir archivo');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleExecute = async (sourceId: number) => {
    setExecuting(true);
    try {
      await apiRequest('/etl/executions/execute/', { method: 'POST', body: JSON.stringify({ data_source_id: sourceId }) });
      toast.success('ETL ejecutado exitosamente');
      loadData();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Error al ejecutar ETL');
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 className="page-title">ETL</h2>
          <p className="text-sm text-muted-foreground">Extracción, Transformación y Carga de datos</p>
        </div>
      </div>

      {hasPermission('etl_execute') && (
        <Card>
          <CardHeader><CardTitle className="text-base">Subir Archivo</CardTitle></CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <label className="flex cursor-pointer items-center gap-2 rounded-lg border-2 border-dashed px-6 py-4 text-sm text-muted-foreground hover:border-primary hover:text-primary transition-colors">
                <Upload className="h-5 w-5" />
                <span>{uploading ? 'Subiendo...' : 'Seleccionar archivo Excel o CSV'}</span>
                <input type="file" className="hidden" accept=".xlsx,.xls,.csv" onChange={handleUpload} disabled={uploading} />
              </label>
            </div>
          </CardContent>
        </Card>
      )}

      {sources.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Fuentes de Datos</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {sources.map((s) => (
                <div key={s.id} className="flex items-center justify-between rounded-lg border p-3 text-sm">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{s.name}</p>
                    <p className="text-xs text-muted-foreground">{s.source_type} · {formatDate(s.created_at)}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant="outline">{s.status}</Badge>
                    {hasPermission('etl_execute') && (
                      <Button variant="outline" size="sm" onClick={() => handleExecute(s.id)} disabled={executing}>
                        <Play className="h-4 w-4" />
                      </Button>
                    )}
                    {hasPermission('etl_delete') && (
                      <Button variant="ghost" size="icon" className="text-destructive">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle className="text-base">Historial de Ejecuciones</CardTitle></CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-3 font-medium">ID</th>
                  <th className="pb-3 font-medium">Estado</th>
                  <th className="pb-3 font-medium">Leídos</th>
                  <th className="pb-3 font-medium">Procesados</th>
                  <th className="pb-3 font-medium">Cargados</th>
                  <th className="pb-3 font-medium">Fallidos</th>
                  <th className="pb-3 font-medium">Calidad</th>
                  <th className="pb-3 font-medium">Duración</th>
                  <th className="pb-3 font-medium">Fecha</th>
                </tr>
              </thead>
              <tbody>
                {executions.map((e) => {
                  const cfg = statusConfig[e.status] || statusConfig.pending;
                  const Icon = cfg.icon;
                  return (
                    <tr key={e.id} className="border-b last:border-0">
                      <td className="py-3 font-mono text-xs">#{e.id}</td>
                      <td className="py-3">
                        <Badge className={cfg.class}><Icon className="h-3 w-3 mr-1" />{cfg.label}</Badge>
                      </td>
                      <td className="py-3">{formatNumber(e.records_read)}</td>
                      <td className="py-3">{formatNumber(e.records_processed)}</td>
                      <td className="py-3">{formatNumber(e.records_loaded)}</td>
                      <td className="py-3">{formatNumber(e.records_failed)}</td>
                      <td className="py-3">{e.quality_score != null ? `${e.quality_score}%` : '—'}</td>
                      <td className="py-3">{e.duration_seconds != null ? `${e.duration_seconds.toFixed(1)}s` : '—'}</td>
                      <td className="py-3 text-xs text-muted-foreground">{formatDate(e.created_at)}</td>
                    </tr>
                  );
                })}
                {executions.length === 0 && (
                  <tr><td colSpan={9} className="py-8 text-center text-muted-foreground">Sin ejecuciones</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function ETLPage() {
  return (
    <AuthProvider>
      <AppLayout>
        <ETLContent />
      </AppLayout>
    </AuthProvider>
  );
}
