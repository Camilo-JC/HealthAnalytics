'use client';

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { login as apiLogin, clearTokens, getStoredUser, storeUser, getProfile } from '@/lib/api';
import type { User } from '@/types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasPermission: (perm: string) => boolean;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refresh = useCallback(async () => {
    try {
      const profile = await getProfile();
      if (profile.success) {
        setUser(profile.data as unknown as User);
        storeUser(profile.data);
      }
    } catch {
      setUser(null);
      clearTokens();
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const stored = getStoredUser<User>();
    if (stored) setUser(stored);
    if (typeof window !== 'undefined' && localStorage.getItem('access_token')) {
      refresh();
    } else {
      setLoading(false);
    }
  }, [refresh]);

  const login = useCallback(async (email: string, password: string) => {
    const data = await apiLogin(email, password);
    setUser(data.user);
    storeUser(data.user);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    clearTokens();
    router.push('/login');
  }, [router]);

  const hasPermission = useCallback((perm: string): boolean => {
    if (!user) return false;
    const perms: Record<string, string[]> = {
      admin: ['dashboard', 'patients', 'patients_manage', 'patients_delete', 'etl', 'etl_execute', 'etl_delete',
        'analytics', 'analytics_export', 'ml', 'ml_train', 'ml_predict', 'reports', 'reports_export',
        'users_manage', 'users_delete', 'settings', 'settings_global', 'audit_view'],
      analyst: ['dashboard', 'patients', 'etl', 'etl_execute', 'analytics', 'analytics_export',
        'ml', 'ml_train', 'ml_predict', 'reports', 'reports_export'],
      doctor: ['dashboard', 'patients', 'analytics', 'reports'],
    };
    return (perms[user.role] || []).includes(perm);
  }, [user]);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, hasPermission, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
}
