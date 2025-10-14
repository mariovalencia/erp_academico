import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';

// Declarar google para TypeScript
declare var google: any;

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
    console.log('AuthService initialized with Signals');
  }

  loginWithGoogle(googleToken: string): Observable<AuthResponse> {
    console.log('Enviando token a nuestro endpoint personalizado');
    console.log('🔐 [FRONTEND] Enviando token a backend:', googleToken);
    console.log('🔐 [FRONTEND] URL:', `${this.apiUrl}/auth/google/`);

    return this.http.post<AuthResponse>(`${this.apiUrl}/auth/google/`, {
      access_token: googleToken
    }).pipe(
      tap(response => {
        console.log('Respuesta de nuestra API:', response);
        this.setAuthState(response.key, response.user);
      })
    );
  }

  private setAuthState(token: string, user: User): void {
    this.authToken.set(token);
    this.currentUser.set(user);

    localStorage.setItem('authToken', token);
    localStorage.setItem('currentUser', JSON.stringify(user));

    console.log('Auth state updated:', user.email);
  }

  logout(): void {
    this.authToken.set(null);
    this.currentUser.set(null);

    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');

    // 🔹 CORRECCIÓN: Verificar si google existe de forma segura
    this.revokeGoogleSession();

    console.log('User logged out');
  }

  private revokeGoogleSession(): void {
    // Verificar si el objeto google existe de forma segura
    if (typeof window !== 'undefined' && (window as any).google) {
      try {
        const google = (window as any).google;
        google.accounts.id.disableAutoSelect();

        // Opcional: revocar sesión específica
        const userEmail = this.userEmail();
        if (userEmail) {
          google.accounts.id.revoke(userEmail, (done: any) => {
            console.log('Google session revoked for:', userEmail);
          });
        }
      } catch (error) {
        console.warn('Error revoking Google session:', error);
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
}
