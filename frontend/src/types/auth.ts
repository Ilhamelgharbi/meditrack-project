// src/types/auth.ts
export const UserRole = {
  patient: "patient",
  admin: "admin"
} as const;

export type UserRoleType = typeof UserRole[keyof typeof UserRole];

export interface User {
  id: number;
  full_name: string;
  email: string;
  phone?: string;
  role: UserRoleType;
  date_created: string;
  avatar?: string;
}

export interface UserRegister {
  full_name: string;
  email: string;
  phone?: string;
  password: string;
  role?: UserRoleType;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}