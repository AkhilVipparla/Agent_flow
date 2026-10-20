import { createContext, useCallback, useContext, useEffect, useMemo, type ReactNode } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { SESSION_EXPIRED_EVENT } from '../services/api';
import { setCredentialsOwner } from '../services/credentials';
import {
  fetchCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
  signup as signupRequest,
  type AuthUser,
} from '../services/authService';

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  /** The server could not be reached (as opposed to the visitor being signed out). */
  unreachable: boolean;
  retryConnection: () => void;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const ME_KEY = ['auth', 'me'];

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();

  const {
    data: user = null,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ME_KEY,
    queryFn: fetchCurrentUser,
    staleTime: Infinity,
    // A sleeping free host answers 502/timeouts for up to a minute: retry before giving up.
    retry: 3,
    retryDelay: 2000,
  });
  const retryConnection = useCallback(() => void refetch(), [refetch]);

  // Keys saved in this browser belong to the signed-in account, not the device.
  useEffect(() => {
    setCredentialsOwner(user?.id ?? null);
  }, [user?.id]);

  // A different account must never see the previous account's cached data.
  const resetCaches = useCallback(() => {
    // Drop everything except the auth query itself: clear() would detach the live
    // observer, and the next setQueryData would then never reach this provider.
    queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== 'auth' });
    try {
      localStorage.removeItem('agentflow.activeRunId');
    } catch {
      /* ignore */
    }
  }, [queryClient]);

  // A request came back 401. Don't take that at face value: ask the server whether we are
  // really signed out, and only then drop back to the sign-in page. One odd response (or a
  // request that raced a login) must not kick someone out of a session that is still valid.
  useEffect(() => {
    let checking = false;
    const onUnauthorized = async () => {
      if (checking) return;
      checking = true;
      try {
        if (await fetchCurrentUser()) return; // still signed in: ignore the stray 401
      } catch {
        return; // server unreachable: stay where we are rather than guess
      } finally {
        checking = false;
      }
      resetCaches();
      queryClient.setQueryData(ME_KEY, null);
    };
    const listener = () => void onUnauthorized();
    window.addEventListener(SESSION_EXPIRED_EVENT, listener);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, listener);
  }, [queryClient, resetCaches]);

  const login = useCallback(
    async (email: string, password: string) => {
      const next = await loginRequest(email, password);
      resetCaches();
      queryClient.setQueryData(ME_KEY, next);
    },
    [queryClient, resetCaches],
  );

  const signup = useCallback(
    async (email: string, password: string, name: string) => {
      const next = await signupRequest(email, password, name);
      resetCaches();
      queryClient.setQueryData(ME_KEY, next);
    },
    [queryClient, resetCaches],
  );

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } finally {
      resetCaches();
      queryClient.setQueryData(ME_KEY, null);
    }
  }, [queryClient, resetCaches]);

  const value = useMemo(
    () => ({ user, isLoading, unreachable: isError && !user, retryConnection, login, signup, logout }),
    [user, isLoading, isError, retryConnection, login, signup, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
