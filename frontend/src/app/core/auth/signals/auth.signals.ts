import { signal, computed } from '@angular/core';

export interface AuthUser {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  avatar?: string;
  roles: string[];
  permissions: string[];
  isActive: boolean;
  lastLogin?: string;
}

export interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('token') || null,
  isAuthenticated: false,
  loading: true,
  error: null
};

export const authState = signal<AuthState>(initialState);

// Computed signals
export const isAuthenticated = computed(() => authState().isAuthenticated);
export const currentUser = computed(() => authState().user);
export const isLoading = computed(() => authState().loading);
export const authError = computed(() => authState().error);
export const userPermissions = computed(() => authState().user?.permissions || []);
export const userRoles = computed(() => authState().user?.roles || []);

// Verificar si usuario tiene permiso específico
export const hasPermission = (permission: string) =>
  userPermissions().includes(permission);

// Verificar si usuario tiene rol específico
export const hasRole = (role: string) =>
  userRoles().includes(role);

// Actions
export function setAuthUser(user: AuthUser, token: string): void {
  localStorage.setItem('token', token);
  authState.set({
    user,
    token,
    isAuthenticated: true,
    loading: false,
    error: null
  });
}

export function setLoading(loading: boolean): void {
  authState.update(state => ({ ...state, loading }));
}

export function setError(error: string | null): void {
  authState.update(state => ({ ...state, error }));
}

export function updateUser(updates: Partial<AuthUser>): void {
  authState.update(state => ({
    ...state,
    user: state.user ? { ...state.user, ...updates } : null
  }));
}

export function logout(): void {
  localStorage.removeItem('token');
  authState.set({
    user: null,
    token: null,
    isAuthenticated: false,
    loading: false,
    error: null
  });
}

// Función para inicializar auth desde localStorage
export function initializeAuth(): void {
  const token = localStorage.getItem('token');
  if (token) {
    authState.update(state => ({
      ...state,
      token,
      loading: true
    }));
  } else {
    setLoading(false);
  }
}
