import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('es-CO', {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

export function formatNumber(num: number | null | undefined, decimals = 0): string {
  if (num === null || num === undefined) return '—';
  return num.toLocaleString('es-CO', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

export function formatPercent(num: number | null | undefined): string {
  if (num === null || num === undefined) return '—';
  return `${(num * 100).toFixed(1)}%`;
}

export function getRiskColor(category: string | undefined): string {
  const colors: Record<string, string> = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-orange-100 text-orange-800',
    critical: 'bg-red-100 text-red-800',
  };
  return colors[category || ''] || 'bg-gray-100 text-gray-800';
}

export function getRiskLabel(category: string | undefined): string {
  const labels: Record<string, string> = {
    low: 'Bajo', medium: 'Medio', high: 'Alto', critical: 'Crítico',
  };
  return labels[category || ''] || category || '—';
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    info: 'bg-blue-100 text-blue-800',
    warning: 'bg-yellow-100 text-yellow-800',
    critical: 'bg-red-100 text-red-800',
  };
  return colors[severity] || 'bg-gray-100 text-gray-800';
}

export function translateGender(gender: string): string {
  return gender === 'M' ? 'Masculino' : gender === 'F' ? 'Femenino' : 'Otro';
}


