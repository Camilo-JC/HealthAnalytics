'use client';

import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/hooks/use-auth';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { apiRequest } from '@/lib/api';
import { formatDate, getRiskColor, getRiskLabel, translateGender } from '@/lib/utils';
import { Plus, Search, Filter, Download, ChevronLeft, ChevronRight, AlertTriangle } from 'lucide-react';
import type { Patient } from '@/types';

function PatientsContent() {
  const { hasPermission } = useAuth();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const pageSize = 20;

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (search) params.set('search', search);
    apiRequest<{ success: boolean; count: number; total_pages: number; results: Patient[] }>(`/patients/?${params}`)
      .then(r => { setPatients(r.results); setTotal(r.count); setTotalPages(r.total_pages || 1); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page, search]);

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 className="page-title">Pacientes</h2>
          <p className="text-sm text-muted-foreground">{total} registros</p>
        </div>
        <div className="flex items-center gap-2">
          {hasPermission('patients_manage') && (
            <Button size="sm"><Plus className="h-4 w-4 mr-2" />Nuevo Paciente</Button>
          )}
          <Button variant="outline" size="sm"><Download className="h-4 w-4 mr-2" />Exportar</Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Buscar paciente..." className="pl-9" value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }} />
            </div>
            <Button variant="outline" size="icon"><Filter className="h-4 w-4" /></Button>
          </div>

          {loading ? (
            <div className="flex justify-center py-12"><div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-muted-foreground">
                      <th className="pb-3 font-medium">ID</th>
                      <th className="pb-3 font-medium">Nombre</th>
                      <th className="pb-3 font-medium">Edad</th>
                      <th className="pb-3 font-medium">Género</th>
                      <th className="pb-3 font-medium">Diagnóstico</th>
                      <th className="pb-3 font-medium">Riesgo</th>
                      <th className="pb-3 font-medium">IMC</th>
                      <th className="pb-3 font-medium">Creado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {patients.map((p) => (
                      <tr key={p.id} className="border-b last:border-0 hover:bg-muted/50 cursor-pointer"
                        onClick={() => window.location.href = `/patients/${p.id}`}>
                        <td className="py-3 font-mono text-xs">{p.patient_id}</td>
                        <td className="py-3 font-medium">{p.full_name || `${p.first_name} ${p.last_name}`}</td>
                        <td className="py-3">{p.age}</td>
                        <td className="py-3">{translateGender(p.gender)}</td>
                        <td className="py-3 max-w-[200px] truncate">{p.diagnosis || '—'}</td>
                        <td className="py-3">
                          <Badge className={getRiskColor(p.risk_category)}>{getRiskLabel(p.risk_category)}</Badge>
                        </td>
                        <td className="py-3">{p.bmi ? Number(p.bmi).toFixed(1) : '—'}</td>
                        <td className="py-3 text-xs text-muted-foreground">{formatDate(p.created_at)}</td>
                      </tr>
                    ))}
                    {patients.length === 0 && (
                      <tr><td colSpan={8} className="py-8 text-center text-muted-foreground">No se encontraron pacientes</td></tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <p className="text-xs text-muted-foreground">Página {page} de {totalPages} ({total} total)</p>
                <div className="flex items-center gap-1">
                  <Button variant="outline" size="icon" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="icon" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function PatientsPage() {
  return (
    <AuthProvider>
      <AppLayout>
        <PatientsContent />
      </AppLayout>
    </AuthProvider>
  );
}
