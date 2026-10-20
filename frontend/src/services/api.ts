import axios from 'axios';
import { credentialHeaders } from './credentials';

// In production the frontend host proxies /api to the backend, so the browser only ever
// talks to its own origin. That keeps the session cookie first-party (it works in
// Safari and with third-party-cookie blocking) and removes the need for CORS.
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

apiClient.interceptors.request.use((config) => {
  for (const [name, value] of Object.entries(credentialHeaders())) {
    config.headers.set(name, value);
  }
  return config;
});

// Fired when the server says the session is gone, so the app can return to the sign-in page.
export const SESSION_EXPIRED_EVENT = 'agentflow:session-expired';

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const url = error.config?.url ?? '';
      // Wrong-password and "who am I" probes are expected 401s, not an expired session.
      if (!url.startsWith('/auth/')) window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
    }
    return Promise.reject(error);
  },
);
