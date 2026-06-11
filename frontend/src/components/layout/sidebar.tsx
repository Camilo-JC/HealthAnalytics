'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/use-auth';
import {
  LayoutDashboard, Users, Repeat, BarChart3, Cpu, FileText, Settings, Activity, ChevronLeft,
} from 'lucide-react';
import { useState } from 'react';

const menuItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, perm: 'dashboard' },
  { href: '/patients', label: 'Pacientes', icon: Users, perm: 'patients' },
  { href: '/etl', label: 'ETL', icon: Repeat, perm: 'etl' },
  { href: '/analytics', label: 'Analítica', icon: BarChart3, perm: 'analytics' },
  { href: '/ml', label: 'Machine Learning', icon: Cpu, perm: 'ml' },
  { href: '/reports', label: 'Reportes', icon: FileText, perm: 'reports' },
  { href: '/settings', label: 'Configuración', icon: Settings, perm: 'settings' },
];

export function Sidebar() {
  const pathname = usePathname();
  const { hasPermission, user } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        'flex flex-col border-r bg-sidebar text-sidebar-foreground transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      <div className="flex h-14 items-center gap-2 border-b border-white/10 px-4">
        <Activity className="h-6 w-6 text-primary shrink-0" />
        {!collapsed && (
          <span className="font-bold text-sm truncate">HealthAnalytics IPS</span>
        )}
      </div>

      <nav className="flex-1 space-y-1 p-2 overflow-y-auto">
        {menuItems
          .filter((item) => hasPermission(item.perm))
          .map((item) => {
            const Icon = item.icon;
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                  active
                    ? 'bg-primary/20 text-primary-foreground font-medium'
                    : 'text-sidebar-foreground/70 hover:bg-white/10 hover:text-sidebar-foreground'
                )}
                title={collapsed ? item.label : undefined}
              >
                <Icon className="h-5 w-5 shrink-0" />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </Link>
            );
          })}
      </nav>

      <div className="border-t border-white/10 p-2">
        <div className="flex items-center gap-3 rounded-lg px-3 py-2 text-xs text-sidebar-foreground/60">
          {!collapsed && user && (
            <div className="truncate">
              <div className="font-medium truncate">{user.full_name}</div>
              <div className="capitalize">{user.role === 'admin' ? 'Administrador' : user.role === 'analyst' ? 'Analista' : 'Médico'}</div>
            </div>
          )}
          <button onClick={() => setCollapsed(!collapsed)} className="ml-auto shrink-0 p-1 hover:text-sidebar-foreground">
            <ChevronLeft className={cn('h-4 w-4 transition-transform', collapsed && 'rotate-180')} />
          </button>
        </div>
      </div>
    </aside>
  );
}
