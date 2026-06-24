'use client';

import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/hooks/use-auth';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { apiRequest, getTokens } from '@/lib/api';
import { toast } from 'sonner';
import { formatDate, getRiskColor, getRiskLabel, translateGender } from '@/lib/utils';
import { Plus, Search, Filter, X, Download, ChevronLeft, ChevronRight, Loader2, Trash2 } from 'lucide-react';
import type { Patient } from '@/types';

const GENDER_OPTIONS = [
  { value: 'M', label: 'Masculino' },
  { value: 'F', label: 'Femenino' },
  { value: 'O', label: 'Otro' },
];

const DOCUMENT_TYPE_OPTIONS = [
  { value: 'CC', label: 'Cédula de Ciudadanía' },
  { value: 'CE', label: 'Cédula de Extranjería' },
  { value: 'PA', label: 'Pasaporte' },
  { value: 'TI', label: 'Tarjeta de Identidad' },
];

const initialFormState = {
  patient_id: '',
  first_name: '',
  last_name: '',
  document_type: 'CC',
  document_number: '',
  age: 30,
  gender: '',
  height: 1.70,
  weight: 70,
  systolic_bp: 120,
  diastolic_bp: 80,
  heart_rate: 75,
  oxygen_saturation: 98,
  glucose: 90,
  cholesterol: 180,
  triglycerides: '',
  hemoglobin: '',
  creatinine: '',
  diagnosis: '',
  diagnosis_code: '',
  comorbidities: '',
  smoking: false,
  alcohol_consumption: false,
  physical_activity: false,
  family_history: false,
};

function PatientsContent() {
  const { hasPermission } = useAuth();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({ gender: '', risk_category: '', bmi_category: '', smoking: '', diagnosis: '' });
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState(initialFormState);
  const pageSize = 20;

  useEffect(() => {
    if (!dialogOpen) setError('');
  }, [dialogOpen]);

  const loadPatients = () => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (search) params.set('search', search);
    Object.entries(filters).forEach(([k, v]) => {
      if (v) {
        if (k === 'diagnosis') {
          params.set('diagnosis__icontains', v);
        } else {
          params.set(k, v);
        }
      }
    });
    apiRequest<{ success: boolean; count: number; total_pages: number; results: Patient[] }>(`/patients/?${params}`)
      .then(r => { setPatients(r.results); setTotal(r.count); setTotalPages(r.total_pages || 1); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadPatients(); }, [page, search, filters]);

  const updateField = (field: string, value: string | number | boolean) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const updateFilter = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(1);
  };

  const clearFilters = () => {
    setFilters({ gender: '', risk_category: '', bmi_category: '', smoking: '', diagnosis: '' });
    setPage(1);
  };

  const hasActiveFilters = Object.values(filters).some(v => v !== '');

  const handleExport = async () => {
    try {
      const { access } = getTokens();
      const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${base}/patients/export/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${access}` },
        body: JSON.stringify({ format: 'csv' }),
      });
      if (!res.ok) throw new Error('Error al exportar');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'pacientes.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Error al exportar');
    }
  };

  const handleDelete = async (patientId: number, fullName: string) => {
    if (!confirm(`¿Eliminar el paciente "${fullName}"? Esta acción no se puede deshacer.`)) return;
    try {
      await apiRequest(`/patients/${patientId}/`, { method: 'DELETE' });
      toast.success('Paciente eliminado');
      loadPatients();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Error al eliminar paciente');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload = {
        ...form,
        height: Number(form.height),
        weight: Number(form.weight),
        systolic_bp: Number(form.systolic_bp),
        diastolic_bp: Number(form.diastolic_bp),
        heart_rate: Number(form.heart_rate),
        oxygen_saturation: form.oxygen_saturation ? Number(form.oxygen_saturation) : undefined,
        glucose: Number(form.glucose),
        cholesterol: Number(form.cholesterol),
        triglycerides: form.triglycerides !== '' ? Number(form.triglycerides) : undefined,
        hemoglobin: form.hemoglobin !== '' ? Number(form.hemoglobin) : undefined,
        creatinine: form.creatinine !== '' ? Number(form.creatinine) : undefined,
        age: Number(form.age),
      };
      await apiRequest('/patients/', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      setDialogOpen(false);
      setForm(initialFormState);
      setPage(1);
      setSearch('');
      loadPatients();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al crear paciente');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 className="page-title">Pacientes</h2>
          <p className="text-sm text-muted-foreground">{total} registros</p>
        </div>
        <div className="flex items-center gap-2">
          {hasPermission('patients_manage') && (
            <Button size="sm" onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />Nuevo Paciente
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={handleExport}><Download className="h-4 w-4 mr-2" />Exportar</Button>
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
            <Button variant="outline" size="icon" onClick={() => setShowFilters(!showFilters)}>
              <Filter className="h-4 w-4" />
            </Button>
          </div>

          {showFilters && (
            <div className="flex flex-wrap items-end gap-3 mb-4 p-3 rounded-lg border bg-muted/30">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Género</label>
                <Select options={GENDER_OPTIONS} placeholder="Todos" value={filters.gender}
                  onChange={e => updateFilter('gender', e.target.value)} />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Riesgo</label>
                <Select options={[
                  { value: 'low', label: 'Bajo' },
                  { value: 'medium', label: 'Medio' },
                  { value: 'high', label: 'Alto' },
                  { value: 'critical', label: 'Crítico' },
                ]} placeholder="Todos" value={filters.risk_category}
                  onChange={e => updateFilter('risk_category', e.target.value)} />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">IMC</label>
                <Select options={[
                  { value: 'underweight', label: 'Bajo peso' },
                  { value: 'normal', label: 'Normal' },
                  { value: 'overweight', label: 'Sobrepeso' },
                  { value: 'obese_i', label: 'Obesidad I' },
                  { value: 'obese_ii', label: 'Obesidad II' },
                  { value: 'obese_iii', label: 'Obesidad III' },
                ]} placeholder="Todos" value={filters.bmi_category}
                  onChange={e => updateFilter('bmi_category', e.target.value)} />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Fumador</label>
                <Select options={[
                  { value: 'true', label: 'Sí' },
                  { value: 'false', label: 'No' },
                ]} placeholder="Todos" value={filters.smoking}
                  onChange={e => updateFilter('smoking', e.target.value)} />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Diagnóstico</label>
                <Input placeholder="Filtrar por diagnóstico..." className="h-9 text-xs" value={filters.diagnosis}
                  onChange={e => updateFilter('diagnosis', e.target.value)} />
              </div>
              {hasActiveFilters && (
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  <X className="h-3.5 w-3.5 mr-1" />Limpiar
                </Button>
              )}
            </div>
          )}

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
                      {hasPermission('patients_delete') && <th className="pb-3 font-medium w-10"></th>}
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
                        {hasPermission('patients_delete') && (
                          <td className="py-3">
                            <Button variant="ghost" size="icon" className="text-destructive h-8 w-8"
                              onClick={e => { e.stopPropagation(); handleDelete(p.id, p.full_name || `${p.first_name} ${p.last_name}`); }}>
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </td>
                        )}
                      </tr>
                    ))}
                    {patients.length === 0 && (
                      <tr><td colSpan={hasPermission('patients_delete') ? 9 : 8} className="py-8 text-center text-muted-foreground">No se encontraron pacientes</td></tr>
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

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogContent className="w-full max-w-2xl">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Nuevo Paciente</DialogTitle>
              <DialogDescription>Ingrese los datos del paciente para registrarlo en el sistema.</DialogDescription>
            </DialogHeader>

            <div className="p-6 space-y-6">
              {error && (
                <div className="p-3 text-sm bg-destructive/10 text-destructive rounded-lg border border-destructive/20">
                  {error}
                </div>
              )}

              <div>
                <h4 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wider">Identificación</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-sm font-medium">ID del Paciente *</label>
                    <Input value={form.patient_id} onChange={e => updateField('patient_id', e.target.value)} required />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Tipo Documento</label>
                    <Select options={DOCUMENT_TYPE_OPTIONS} value={form.document_type}
                      onChange={e => updateField('document_type', e.target.value)} />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Nombres *</label>
                    <Input value={form.first_name} onChange={e => updateField('first_name', e.target.value)} required />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Apellidos *</label>
                    <Input value={form.last_name} onChange={e => updateField('last_name', e.target.value)} required />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">N° Documento *</label>
                    <Input value={form.document_number} onChange={e => updateField('document_number', e.target.value)} required />
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wider">Datos Demográficos</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Edad *</label>
                    <Input type="number" min={0} max={120} value={form.age}
                      onChange={e => updateField('age', parseInt(e.target.value) || 0)} required />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Género *</label>
                    <Select options={GENDER_OPTIONS} placeholder="Seleccione..." value={form.gender}
                      onChange={e => updateField('gender', e.target.value)} required />
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wider">Signos Vitales</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Altura (m) *</label>
                    <Input type="number" step="0.01" min={0.5} max={2.5} value={form.height}
                      onChange={e => updateField('height', e.target.value)} required />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Peso (kg) *</label>
                    <Input type="number" step="0.1" min={20} max={300} value={form.weight}
                      onChange={e => updateField('weight', e.target.value)} required />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">P. Sistólica *</label>
                    <Input type="number" min={60} max={280} value={form.systolic_bp}
                      onChange={e => updateField('systolic_bp', parseInt(e.target.value) || 0)} required />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">P. Diastólica *</label>
                    <Input type="number" min={30} max={180} value={form.diastolic_bp}
                      onChange={e => updateField('diastolic_bp', parseInt(e.target.value) || 0)} required />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Frec. Cardíaca *</label>
                    <Input type="number" min={30} max={250} value={form.heart_rate}
                      onChange={e => updateField('heart_rate', parseInt(e.target.value) || 0)} required />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Sat. Oxígeno (%)</label>
                    <Input type="number" min={50} max={100} value={form.oxygen_saturation}
                      onChange={e => updateField('oxygen_saturation', e.target.value)} />
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wider">Laboratorio</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Glucosa (mg/dL) *</label>
                    <Input type="number" step="0.1" min={20} max={600} value={form.glucose}
                      onChange={e => updateField('glucose', e.target.value)} required />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Colesterol Total</label>
                    <Input type="number" step="0.1" min={0} max={500} value={form.cholesterol}
                      onChange={e => updateField('cholesterol', e.target.value)} required />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Triglicéridos</label>
                    <Input type="number" step="0.1" value={form.triglycerides}
                      onChange={e => updateField('triglycerides', e.target.value)} />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Hemoglobina</label>
                    <Input type="number" step="0.1" value={form.hemoglobin}
                      onChange={e => updateField('hemoglobin', e.target.value)} />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Creatinina</label>
                    <Input type="number" step="0.01" value={form.creatinine}
                      onChange={e => updateField('creatinine', e.target.value)} />
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wider">Diagnóstico</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="space-y-1 md:col-span-2">
                    <label className="text-sm font-medium">Diagnóstico Principal</label>
                    <Input value={form.diagnosis} onChange={e => updateField('diagnosis', e.target.value)} />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Código Diagnóstico</label>
                    <Input value={form.diagnosis_code} onChange={e => updateField('diagnosis_code', e.target.value)} />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Comorbilidades</label>
                    <Input value={form.comorbidities} onChange={e => updateField('comorbidities', e.target.value)} />
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wider">Estilo de Vida</h4>
                <div className="flex flex-wrap gap-6">
                  {[
                    { key: 'smoking', label: 'Tabaquismo' },
                    { key: 'alcohol_consumption', label: 'Consumo de Alcohol' },
                    { key: 'physical_activity', label: 'Actividad Física' },
                    { key: 'family_history', label: 'Antecedentes Familiares' },
                  ].map(({ key, label }) => (
                    <label key={key} className="flex items-center gap-2 text-sm cursor-pointer">
                      <input type="checkbox" checked={(form as any)[key]} className="rounded border-gray-300"
                        onChange={e => updateField(key, e.target.checked)} />
                      {label}
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} disabled={saving}>
                Cancelar
              </Button>
              <Button type="submit" disabled={saving}>
                {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {saving ? 'Guardando...' : 'Guardar Paciente'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
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
