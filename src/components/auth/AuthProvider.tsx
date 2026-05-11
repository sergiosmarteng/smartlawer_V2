import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/router';
import api from '../../lib/axios';

const ACCESS_TOKEN_KEY = 'access_token';
const ACCESS_TOKEN_COOKIE = 'smartlawer_access_token';
const DEFAULT_AUTH_REDIRECT = '/dashboard';
const DEFAULT_SIGN_OUT_REDIRECT = '/sign-in';

interface User {
  id: string;
  email: string;
  username: string;
  role?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (token: string, redirectTo?: string) => Promise<void>;
  logout: (redirectTo?: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function isBrowser() {
  return typeof window !== 'undefined';
}

function normalizeRedirectPath(path?: string) {
  if (!path || !path.startsWith('/')) {
    return DEFAULT_AUTH_REDIRECT;
  }

  return path;
}

function readAuthCookie() {
  if (!isBrowser()) {
    return null;
  }

  const match = document.cookie.match(
    new RegExp(`(?:^|; )${ACCESS_TOKEN_COOKIE}=([^;]*)`)
  );

  return match ? decodeURIComponent(match[1]) : null;
}

function writeAuthCookie(token: string) {
  if (!isBrowser()) {
    return;
  }

  document.cookie = `${ACCESS_TOKEN_COOKIE}=${encodeURIComponent(token)}; Path=/; SameSite=Lax`;
}

function clearPersistedToken() {
  if (!isBrowser()) {
    return;
  }

  localStorage.removeItem(ACCESS_TOKEN_KEY);
  document.cookie = `${ACCESS_TOKEN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
}

function persistToken(token: string) {
  if (!isBrowser()) {
    return;
  }

  localStorage.setItem(ACCESS_TOKEN_KEY, token);
  writeAuthCookie(token);
}

function getPersistedToken() {
  if (!isBrowser()) {
    return null;
  }

  const token = localStorage.getItem(ACCESS_TOKEN_KEY);

  if (token) {
    if (readAuthCookie() !== token) {
      writeAuthCookie(token);
    }
    return token;
  }

  if (readAuthCookie()) {
    clearPersistedToken();
  }

  return null;
}

function mapUser(currentUser: any): User {
  return {
    id: String(currentUser.id),
    email: currentUser.email,
    username: currentUser.username,
    role: currentUser.role,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let isMounted = true;

    const syncSession = async () => {
      setIsLoading(true);

      if (!getPersistedToken()) {
        if (isMounted) {
          setUser(null);
          setIsLoading(false);
        }
        return;
      }

      try {
        const response = await api.get('/users/me');

        if (isMounted) {
          setUser(mapUser(response.data));
        }
      } catch (_error) {
        clearPersistedToken();

        if (isMounted) {
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    const handleStorage = (event: StorageEvent) => {
      if (event.key === ACCESS_TOKEN_KEY) {
        void syncSession();
      }
    };

    void syncSession();
    window.addEventListener('storage', handleStorage);

    return () => {
      isMounted = false;
      window.removeEventListener('storage', handleStorage);
    };
  }, []);

  const login = async (token: string, redirectTo?: string) => {
    persistToken(token);
    setIsLoading(true);

    try {
      const response = await api.get('/users/me');
      setUser(mapUser(response.data));
      await router.replace(normalizeRedirectPath(redirectTo));
    } catch (error) {
      clearPersistedToken();
      setUser(null);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = (redirectTo = DEFAULT_SIGN_OUT_REDIRECT) => {
    clearPersistedToken();
    setUser(null);
    void router.replace(redirectTo);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
