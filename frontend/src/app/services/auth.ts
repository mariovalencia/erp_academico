import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  picture?: string;
}

interface AuthResponse {
  key: string;
  user: User;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  private currentUser = signal<User | null>(this.getStoredUser());
  private authToken = signal<string | null>(this.getStoredToken());

  public isLoggedIn = computed(() => !!this.authToken());
  public user = computed(() => this.currentUser());
  public userEmail = computed(() => this.currentUser()?.email || '');

  constructor() {
    //console.log('AuthService initialized with Signals');
  }

  loginWithGoogle(googleToken: string): Observable<AuthResponse> {
    //console.log('🔐 [FRONTEND] Enviando token a backend:', googleToken);
    //console.log('🔐 [FRONTEND] URL:', `${this.apiUrl}/auth/google/`);

    return this.http.post<AuthResponse>(`${this.apiUrl}/auth/google/`, {
      access_token: googleToken
    }).pipe(
      tap(response => {
        //console.log('✅ [FRONTEND] Respuesta del backend:', response);
        this.setAuthToken(response.key, response.user);
      })
    );
  }

  // 🔥 MÉTODO QUE FALTABA
  setAuthToken(token: string, user: User): void {
    //console.log('🔐 [FRONTEND] Guardando token y usuario');

    // Actualizar signals
    this.authToken.set(token);
    this.currentUser.set(user);

    // Persistir en localStorage
    localStorage.setItem('authToken', token);
    localStorage.setItem('currentUser', JSON.stringify(user));

    //console.log('✅ [FRONTEND] Auth state actualizado:', user.email);
  }

  logout(): void {
    console.log('🔐 [FRONTEND] Cerrando sesión');

    // Limpiar signals
    this.authToken.set(null);
    this.currentUser.set(null);

    // Limpiar localStorage
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');

    // Cerrar sesión de Google
    this.revokeGoogleSession();

    console.log('✅ [FRONTEND] Sesión cerrada');
  }

  private revokeGoogleSession(): void {
    if (typeof window !== 'undefined' && (window as any).google) {
      try {
        const google = (window as any).google;
        google.accounts.id.disableAutoSelect();
        console.log('✅ [FRONTEND] Sesión de Google revocada');
      } catch (error) {
        console.warn('⚠️ [FRONTEND] Error revocando sesión de Google:', error);
      }
    }
  }

  getToken(): string | null {
    return this.authToken();
  }

  private getStoredUser(): User | null {
    const storedUser = localStorage.getItem('currentUser');
    return storedUser ? JSON.parse(storedUser) : null;
  }

  private getStoredToken(): string | null {
    return localStorage.getItem('authToken');
  }

  // 🔥 MÉTODOS ADICIONALES ÚTILES
  getAuthHeaders(): { [header: string]: string } {
    const token = this.getToken();
    return token ? { 'Authorization': `Token ${token}` } : {};
  }

  clearAuth(): void {
    this.logout();
  }

  // Para debugging
  printAuthState(): void {
    console.log('🔐 [FRONTEND] Estado de autenticación:');
    console.log('  - isLoggedIn:', this.isLoggedIn());
    console.log('  - user:', this.user());
    console.log('  - token:', this.getToken()?.substring(0, 20) + '...');
    console.log('  - localStorage token:', !!localStorage.getItem('authToken'));
    console.log('  - localStorage user:', !!localStorage.getItem('currentUser'));
  }
}
