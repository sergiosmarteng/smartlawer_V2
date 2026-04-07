import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/router';
import api from '../../lib/axios';

interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        // Assuming there is an endpoint to get the current user, or we parse JWT
        // We will just set a mock user for now based on the token presence
        // since /api/v1/users/me was not explicitly mentioned.
        setUser({ id: '1', email: 'user@smartlawer.com', firstName: 'Advogado' });
      } catch (error) {
        localStorage.removeItem('access_token');
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();
  }, [router.pathname]);

  const login = (token: string) => {
    localStorage.setItem('access_token', token);
    setUser({ id: '1', email: 'user@smartlawer.com', firstName: 'Advogado' });
    router.push('/dashboard');
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
    router.push('/sign-in');
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
