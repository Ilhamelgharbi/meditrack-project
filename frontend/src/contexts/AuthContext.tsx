// src/contexts/AuthContext.tsx
import  { createContext, useContext, useState, useEffect} from 'react';
import type {ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/auth.service';
import type { User, LoginCredentials, RegisterData, AuthContextType } from '../types/auth.types';

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const isAuthenticated = !!user;

  // Check if user is already logged in on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('meditrack_token');
      const storedUser = localStorage.getItem('meditrack_user');
      
      if (token && storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch {
          localStorage.removeItem('meditrack_user');
        }
      } else if (token) {
        try {
          const userData = await authService.getCurrentUser();
          setUser(userData);
          localStorage.setItem('meditrack_user', JSON.stringify(userData));
        } catch {
          localStorage.removeItem('meditrack_token');
          localStorage.removeItem('meditrack_user');
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      const authResponse = await authService.login(credentials);
      localStorage.setItem('meditrack_token', authResponse.access_token);
      
      const userData = await authService.getCurrentUser();
      setUser(userData);
      localStorage.setItem('meditrack_user', JSON.stringify(userData));
      localStorage.setItem('meditrack_user', JSON.stringify(userData));

      // Redirect based on role
      if (userData.role === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/patient/dashboard');
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Login failed';
      throw new Error(message);
    }
  };

  const register = async (data: RegisterData) => {
    try {
      await authService.register(data);
      navigate('/login');
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Registration failed';
      throw new Error(message);
    }
  };

  const logout = () => {
    authService.logout();
    localStorage.removeItem('meditrack_user');
    setUser(null);
    navigate('/login');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};