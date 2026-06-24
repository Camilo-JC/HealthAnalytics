'use client';

import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/hooks/use-auth';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { apiRequest } from '@/lib/api';
import { Cpu, Play, BarChart3 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { toast } from 'sonner';
import type { MLComparison } from '@/types';

function MLContent() {
  const { hasPermission } = useAuth();
  const [models, setModels] = useState<MLComparison[]>([]);
  const [training, setTraining] = useState(false);
  const [loading, setLoading] = useState(true);
  const [prediction, setPrediction] = useState<Record<string, unknown> | null>(null);
  const [predictForm, setPredictForm] = useState({
    age: '45', bmi: '28', glucose: '110', cholesterol: '200',
    systolic_bp: '130', diastolic_bp: '80', heart_rate: '75',
    smoking: false, family_history: false,
    physical_activity: true, alcohol_consumption: false,
  });

  const loadModels = () => {
    apiRequest<{ success: boolean; results: MLComparison[] }>('/ml/models/comparison/')
      .then(r => setModels(r.results || [])).catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadModels(); }, []);

  const handleTrain = async () => {
    setTraining(true);
    try {
      await apiRequest('/ml/models/train/', { method: 'POST' });
      toast.success('Entrenamiento iniciado');
      setTimeout(loadModels, 3000);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Error al entrenar');
    } finally {
      setTraining(false);
    }
  };

  const handlePredict = async () => {
    try {
      const res = await apiRequest<Record<string, unknown>>('/ml/models/predict/', {
        method: 'POST',
        body: JSON.stringify({
          age: Number(predictForm.age), bmi: Number(predictForm.bmi),
          glucose: Number(predictForm.glucose), cholesterol: Number(predictForm.cholesterol),
          systolic_bp: Number(predictForm.systolic_bp), diastolic_bp: Number(predictForm.diastolic_bp),
          heart_rate: Number(predictForm.heart_rate),
          smoking: predictForm.smoking, family_history: predictForm.family_history,
          physical_activity: predictForm.physical_activity, alcohol_consumption: predictForm.alcohol_consumption,
        }),
      });
      setPrediction(res);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Error en predicción');
    }
  };

  const compareData = models.map(m => ({
    name: m.model_type,
    Accuracy: m.accuracy ? +(m.accuracy * 100).toFixed(1) : 0,
    Precision: m.precision ? +(m.precision * 100).toFixed(1) : 0,
    Recall: m.recall ? +(m.recall * 100).toFixed(1) : 0,
    F1: m.f1_score ? +(m.f1_score * 100).toFixed(1) : 0,
  }));

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 className="page-title">Machine Learning</h2>
          <p className="text-sm text-muted-foreground">Entrenamiento y predicción de modelos</p>
        </div>
        {hasPermission('ml_train') && (
          <Button size="sm" onClick={handleTrain} disabled={training}>
            <Play className="h-4 w-4 mr-2" />{training ? 'Entrenando...' : 'Entrenar Modelos'}
          </Button>
        )}
      </div>

      {compareData.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Comparación de Modelos</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={compareData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                <Tooltip formatter={(v: number) => `${v}%`} />
                <Legend formatter={(value: string) => ({ Accuracy: 'Exactitud', Precision: 'Precisión', Recall: 'Sensibilidad', F1: 'F1' } as Record<string, string>)[value] || value} />
                <Bar dataKey="Accuracy" fill="#22c55e" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Precision" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Recall" fill="#eab308" radius={[4, 4, 0, 0]} />
                <Bar dataKey="F1" fill="#a855f7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-base">Modelos Registrados</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {models.map((m, i) => (
                <div key={i} className="flex items-center justify-between rounded-lg border p-3 text-sm">
                  <div>
                    <p className="font-medium">{m.model}</p>
                    <p className="text-xs text-muted-foreground">v{m.version} · {m.model_type}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {m.is_active && <Badge className="bg-green-100 text-green-800">Activo</Badge>}
                    <span className="text-xs text-muted-foreground">Exactitud: {m.accuracy ? `${(m.accuracy * 100).toFixed(1)}%` : '—'}</span>
                  </div>
                </div>
              ))}
              {models.length === 0 && <p className="text-sm text-muted-foreground py-4 text-center">No hay modelos entrenados</p>}
            </div>
          </CardContent>
        </Card>

        {hasPermission('ml_predict') && (
          <Card>
            <CardHeader><CardTitle className="text-base">Predecir Riesgo</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="col-span-2 grid grid-cols-2 gap-2">
                  {[['smoking', 'Fumador'], ['family_history', 'Antecedentes familiares'],
                    ['physical_activity', 'Actividad física'], ['alcohol_consumption', 'Consumo alcohol'],
                  ].map(([k, label]) => (
                    <label key={k} className="flex items-center gap-2">
                      <input type="checkbox" checked={predictForm[k as keyof typeof predictForm] as boolean}
                        onChange={e => setPredictForm(f => ({ ...f, [k]: e.target.checked }))}
                        className="rounded border-gray-300" />
                      <span className="text-sm">{label}</span>
                    </label>
                  ))}
                </div>
                {Object.entries(predictForm).map(([k, v]) => {
                  if (['smoking', 'family_history', 'physical_activity', 'alcohol_consumption'].includes(k)) return null;
                  return (
                    <div key={k} className="space-y-1">
                      <label className="text-xs text-muted-foreground capitalize">{k.replace('_', ' ')}</label>
                      <Input type="number" value={v as string} onChange={e => setPredictForm(f => ({ ...f, [k]: e.target.value }))} />
                    </div>
                  );
                })}
              </div>
              <Button className="w-full mt-4" onClick={handlePredict}><BarChart3 className="h-4 w-4 mr-2" />Predecir</Button>
              {prediction && (
                <div className="mt-4 rounded-lg border p-3 text-sm space-y-1">
                  <p className="font-medium">Resultado</p>
                  {Object.entries(prediction).filter(([k]) => k !== 'success').map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-muted-foreground capitalize">{k.replace('_', ' ')}</span>
                      <span className="font-medium">{typeof v === 'number' ? `${(v as number).toFixed(2)}` : String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default function MLPage() {
  return (
    <AuthProvider>
      <AppLayout>
        <MLContent />
      </AppLayout>
    </AuthProvider>
  );
}
