'use client';

import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/hooks/use-auth';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { apiRequest } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { User, Shield, Mail, Phone, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import type { User as UserType } from '@/types';

function SettingsContent() {
  const { user, hasPermission } = useAuth();
  const [users, setUsers] = useState<UserType[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (hasPermission('users_manage')) {
      setLoading(true);
      apiRequest<{ success: boolean; results: UserType[] }>('/auth/users/')
        .then(r => setUsers(r.results || [])).catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [hasPermission]);

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 className="page-title">Configuración</h2>
          <p className="text-sm text-muted-foreground">Perfil y administración del sistema</p>
        </div>
      </div>

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><User className="h-4 w-4" />Mi Perfil</CardTitle></CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="flex items-center gap-3 pb-3 border-b">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-lg">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <div>
                <p className="font-medium">{user?.full_name}</p>
                <p className="text-xs text-muted-foreground capitalize">
                  {user?.role === 'admin' ? 'Administrador' : user?.role === 'analyst' ? 'Analista' : 'Médico'}
                </p>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2"><Mail className="h-4 w-4 text-muted-foreground" /><span>{user?.email}</span></div>
              {user?.phone && <div className="flex items-center gap-2"><Phone className="h-4 w-4 text-muted-foreground" /><span>{user.phone}</span></div>}
              <div className="flex items-center gap-2"><Calendar className="h-4 w-4 text-muted-foreground" /><span>Registrado: {user?.date_joined ? formatDate(user.date_joined) : '—'}</span></div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><Shield className="h-4 w-4" />Información del Sistema</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">Plataforma</span><span className="font-medium">HealthAnalytics IPS</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Versión</span><span className="font-medium">1.0.0</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Backend</span><span className="font-medium">Django REST Framework</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Frontend</span><span className="font-medium">Next.js + TypeScript</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Tu Rol</span>
              <Badge variant="outline" className="capitalize">{user?.role === 'admin' ? 'Administrador' : user?.role === 'analyst' ? 'Analista' : 'Médico'}</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {hasPermission('users_manage') && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <User className="h-4 w-4" />Gestión de Usuarios
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-3 font-medium">Nombre</th>
                    <th className="pb-3 font-medium">Email</th>
                    <th className="pb-3 font-medium">Rol</th>
                    <th className="pb-3 font-medium">Estado</th>
                    <th className="pb-3 font-medium">Registro</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b last:border-0">
                      <td className="py-3 font-medium">{u.full_name}</td>
                      <td className="py-3 text-muted-foreground">{u.email}</td>
                      <td className="py-3">
                        <Badge variant="outline" className="capitalize">{u.role}</Badge>
                      </td>
                      <td className="py-3">
                        <Badge className={u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                          {u.is_active ? 'Activo' : 'Inactivo'}
                        </Badge>
                      </td>
                      <td className="py-3 text-xs text-muted-foreground">{formatDate(u.date_joined)}</td>
                    </tr>
                  ))}
                  {loading && <tr><td colSpan={5} className="py-4 text-center text-muted-foreground">Cargando...</td></tr>}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function SettingsPage() {
  return (
    <AuthProvider>
      <AppLayout>
        <SettingsContent />
      </AppLayout>
    </AuthProvider>
  );
}
