'use client';

import { useAuth } from '@/hooks/use-auth';
import { LogOut, User, Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { usePathname } from 'next/navigation';

const pageTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/patients': 'Pacientes',
  '/etl': 'ETL',
  '/analytics': 'Analítica',
  '/ml': 'Machine Learning',
  '/reports': 'Reportes',
  '/settings': 'Configuración',
};

export function Header() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const title = Object.entries(pageTitles).find(([k]) => pathname.startsWith(k))?.[1] || 'HealthAnalytics IPS';

  return (
    <header className="flex h-14 items-center justify-between border-b bg-white px-6">
      <h1 className="text-lg font-semibold">{title}</h1>
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] font-bold text-destructive-foreground">3</span>
        </Button>
        <div className="flex items-center gap-2 text-sm">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary font-semibold text-xs">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="hidden md:block">
            <div className="font-medium leading-none">{user?.full_name || 'Usuario'}</div>
            <div className="text-xs text-muted-foreground capitalize">{user?.role === 'admin' ? 'Administrador' : user?.role === 'analyst' ? 'Analista' : 'Doctor'}</div>
          </div>
        </div>
        <Button variant="ghost" size="icon" onClick={logout} title="Cerrar sesión">
          <LogOut className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}
