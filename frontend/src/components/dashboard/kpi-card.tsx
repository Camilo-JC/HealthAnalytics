import { type ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';

interface KPICardProps {
  title: string;
  value: string | number | null;
  icon: ReactNode;
  description?: string;
  trend?: { value: number; positive: boolean };
  className?: string;
}

export function KPICard({ title, value, icon, description, trend, className }: KPICardProps) {
  return (
    <Card className={cn('kpi-card', className)}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="stat-label">{title}</p>
            <p className="stat-value">{value ?? '—'}</p>
            {description && <p className="text-xs text-muted-foreground">{description}</p>}
            {trend && (
              <p className={cn('text-xs font-medium', trend.positive ? 'text-green-600' : 'text-red-600')}>
                {trend.positive ? '↑' : '↓'} {trend.value}%
              </p>
            )}
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
