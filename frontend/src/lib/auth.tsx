import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { api, type TokenResponse } from '../lib/api';

interface AuthContextType {
  token: string | null;
  username: string | null;
  isAdmin: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [username, setUsername] = useState<string | null>(localStorage.getItem('username'));
  const [isAdmin, setIsAdmin] = useState(localStorage.getItem('is_admin') === 'true');
  const [initialized, setInitialized] = useState(false);

  const validateToken = useCallback(async () => {
    const currentToken = localStorage.getItem('token');
    if (!currentToken) {
      setInitialized(true);
      return;
    }
    try {
      const data = await api.get<{ username: string; is_admin: boolean }>('/auth/me');
      setUsername(data.username);
      setIsAdmin(data.is_admin);
      setToken(currentToken);
    } catch {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      localStorage.removeItem('is_admin');
      setToken(null);
      setUsername(null);
      setIsAdmin(false);
    } finally {
      setInitialized(true);
    }
  }, []);

  useEffect(() => {
    if (token) {
      validateToken();
    } else {
      setInitialized(true);
    }
  }, []);

  const login = async (user: string, password: string) => {
    const data: TokenResponse = await api.post('/auth/login', { username: user, password });
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('username', data.username);
    localStorage.setItem('is_admin', String(data.is_admin));
    setToken(data.access_token);
    setUsername(data.username);
    setIsAdmin(data.is_admin);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('is_admin');
    setToken(null);
    setUsername(null);
    setIsAdmin(false);
  };

  if (!initialized) return null;

  return (
    <AuthContext.Provider value={{ token, username, isAdmin, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export function useTheme() {
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }, [dark]);

  return { dark, toggle: () => setDark(!dark) };
}
