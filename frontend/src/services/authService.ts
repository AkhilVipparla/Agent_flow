import { apiClient } from './api';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  // Answers 200 with { user: null } when signed out, so page load never logs a failed request.
  const { data } = await apiClient.get<{ user: AuthUser | null }>('/auth/session');
  return data.user;
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const { data } = await apiClient.post<AuthUser>('/auth/login', { email, password });
  return data;
}

export async function signup(email: string, password: string, name: string): Promise<AuthUser> {
  const { data } = await apiClient.post<AuthUser>('/auth/signup', { email, password, name });
  return data;
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout');
}

/** Pull the server's human-readable message out of an axios error. */
export function errorMessage(err: unknown, fallback = 'Something went wrong. Please try again.'): string {
  const e = err as { response?: { data?: { detail?: unknown } }; message?: string };
  const detail = e.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string };
    if (first?.msg) return first.msg.replace(/^Value error, /, '');
  }
  if (!e.response) return 'Could not reach the server. Check your connection.';
  return fallback;
}
