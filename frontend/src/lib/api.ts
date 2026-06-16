const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export function getTokens(): { access: string | null; refresh: string | null } {
  if (typeof window === 'undefined') return { access: null, refresh: null };
  return { access: localStorage.getItem('access_token'), refresh: localStorage.getItem('refresh_token') };
}

function setTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

export function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
}

export function storeUser(user: unknown) {
  localStorage.setItem('user', JSON.stringify(user));
}

export function getStoredUser<T>(): T | null {
  if (typeof window === 'undefined') return null;
  try { return JSON.parse(localStorage.getItem('user') || 'null'); } catch { return null; }
}

async function refreshToken(): Promise<boolean> {
  const { refresh } = getTokens();
  if (!refresh) return false;
  try {
    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    setTokens(data.access, data.refresh || refresh);
    return true;
  } catch { return false; }
}

export async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestInit = {},
  retry = true
): Promise<T> {
  const { access } = getTokens();
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (access) headers['Authorization'] = `Bearer ${access}`;

  const isFormData = options.body instanceof FormData;
  if (isFormData) delete headers['Content-Type'];

  let res = await fetch(url, { ...options, headers });

  if (res.status === 401 && retry) {
    const refreshed = await refreshToken();
    if (refreshed) return apiRequest<T>(endpoint, options, false);
    clearTokens();
    if (typeof window !== 'undefined') window.location.href = '/login';
    throw new Error('Sesión expirada');
  }

  const contentType = res.headers.get('content-type') || '';
  if (!res.ok) {
    const text = await res.text();
    let msg = `Error ${res.status}`;
    try {
      const err = JSON.parse(text);
      msg = err.error || err.detail || (err.errors?.[0]?.message) || '';
      if (!msg) {
        const firstKey = Object.keys(err).find(k => Array.isArray(err[k]));
        if (firstKey) msg = err[firstKey][0];
      }
    } catch {
      msg = text || msg;
    }
    throw new Error(msg);
  }

  if (contentType.includes('application/json')) return res.json();
  return res.text() as T;
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Error de autenticación' }));
    throw new Error(err.error || err.detail || 'Credenciales inválidas');
  }
  const data = await res.json();
  setTokens(data.access, data.refresh);
  storeUser(data.user);
  return data;
}

export async function getProfile() {
  return apiRequest<{ success: boolean; data: { role: string; email: string; full_name: string } }>('/auth/profile/');
}

export async function uploadFile(endpoint: string, file: File, extraFields?: Record<string, string>) {
  const { access } = getTokens();
  const formData = new FormData();
  formData.append('file', file);
  if (extraFields) Object.entries(extraFields).forEach(([k, v]) => formData.append(k, v));

  let res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${access}` },
    body: formData,
  });

  if (res.status === 401) {
    const refreshed = await refreshToken();
    if (refreshed) {
      const { access: newAccess } = getTokens();
      res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${newAccess}` },
        body: formData,
      });
    } else {
      clearTokens();
      window.location.href = '/login';
      throw new Error('Sesión expirada');
    }
  }

  if (!res.ok) {
    try {
      const err = await res.json();
      throw new Error(err.error || `Error ${res.status}`);
    } catch (e: unknown) {
      if (e instanceof TypeError) throw new Error(`Error ${res.status}`);
      throw e;
    }
  }
  return res.json();
}
