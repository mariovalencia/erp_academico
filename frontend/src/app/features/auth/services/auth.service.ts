import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, tap, catchError, of } from 'rxjs';
import { environment } from '../../../../environments/environment';

declare var google: any;

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_staff?: boolean;
  is_superuser?: boolean;
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

  // ✅ Usando signals para estado reactivo (Angular 16+)
  private authToken = signal<string | null>(null);
  private currentUser = signal<User | null>(null);

  // Exponer signals como readonly
  user = this.currentUser.asReadonly();
  token = this.authToken.asReadonly();

  /**
   * Verifica si el usuario está autenticado
   */
  isAuthenticated(): boolean {
    const token = this.authToken();

    // Verificar si existe token
    if (!token) {
      //console.log('🔐 No hay token en memoria');
      return false;
    }

    // Verificar si el token está almacenado en localStorage (para persistencia)
    const storedToken = localStorage.getItem('authToken');
    if (!storedToken || storedToken !== token) {
      console.log('🔐 Token no coincide con almacenamiento');
      return false;
    }

    // Opcional: Verificar expiración del token (si tu backend usa JWT expirable)
    // if (this.isTokenExpired(token)) {
    //   this.logout();
    //   return false;
    // }

    //console.log('🔐 Usuario autenticado correctamente');
    return true;
  }

  /**
   * Inicializa el estado de autenticación desde localStorage
   */
  initializeAuthState(): void {
    const token = localStorage.getItem('authToken');
    const userData = localStorage.getItem('userData');

    //console.log('🔐 Inicializando estado de autenticación...');

    if (token && userData) {
      try {
        const user = JSON.parse(userData);
        this.authToken.set(token);
        this.currentUser.set(user);
        //console.log('✅ Estado de autenticación restaurado:', user.email);
      } catch (error) {
        console.error('❌ Error parseando userData:', error);
        this.clearAuthData();
      }
    } else {
      //console.log('🔐 No hay datos de autenticación persistentes');
    }
  }

  /**
   * Login con Google (JWT)
   */

  loginWithGoogle(jwtToken: string): Observable<AuthResponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    /*console.log('🔐 Enviando JWT al backend...', {
    token: jwtToken,
    tokenLength: jwtToken.length,
    first50Chars: jwtToken.substring(0, 50)
    });*/

    return this.http.post<AuthResponse>(
      `${this.apiUrl}/auth/google/`,
      { access_token: jwtToken },
      { headers }
    ).pipe(
      tap(response => {
        //console.log('✅ Respuesta del backend:', response)
        //console.log('✅ Login exitoso, estableciendo token...');
        this.setAuthToken(response.key, response.user);
      }),
      catchError(error => {
        console.error('❌ Error en login:', error);
        console.log('📋 Detalles del error:', {
        status: error.status,
        statusText: error.statusText,
        error: error.error, // Esto suele contener el mensaje específico
        headers: error.headers
        });
        this.clearAuthData();
        throw error;
      })
    );
  }
  /**
   * Establece el token de autenticación
   */
  setAuthToken(token: string, user: User): void {
    // Guardar en localStorage para persistencia
    localStorage.setItem('authToken', token);
    localStorage.setItem('userData', JSON.stringify(user));

    // Actualizar signals
    this.authToken.set(token);
    this.currentUser.set(user);

    //console.log('✅ Token establecido para usuario:', user.email);
  }

  /**
   * Cierra la sesión
   */

  logout(): void {
    //console.log('🔐 Cerrando sesión...');

    const userEmail = this.currentUser()?.email;

    this.clearAuthData();

    // Cerrar sesión de Google
    if (window.google?.accounts?.id) {
      if (userEmail) {
        google.accounts.id.revoke(userEmail, (done: any) => {
          //console.log('✅ Sesión de Google revocada');
        });
      }
      google.accounts.id.disableAutoSelect();
    }

    //console.log('✅ Sesión cerrada completamente');

  }

  /**
   * Limpia todos los datos de autenticación
   */

  private clearAuthData(): void {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    this.authToken.set(null);
    this.currentUser.set(null);
  }

  /**
   * Obtiene el usuario actual
   */
  getCurrentUser(): User | null {
    return this.currentUser();
  }

  /**
   * Obtiene las iniciales del usuario para avatares
   */
  getUserInitials(): string {
    const user = this.currentUser();
    if (!user) return 'U';

    const firstName = user.first_name?.charAt(0) || '';
    const lastName = user.last_name?.charAt(0) || '';

    return (firstName + lastName).toUpperCase() || 'U';
  }

  /**
   * Verifica si el token ha expirado (para JWT)
   */
  private isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // Convertir a milisegundos
      return Date.now() >= exp;
    } catch {
      return true; // Si hay error al parsear, considerar como expirado
    }
  }

  /**
   * Verifica si el usuario tiene un rol específico
   */
  hasRole(role: string): boolean {
    const user = this.currentUser();
    if (!user) return false;

    switch (role) {
      case 'admin':
        return user.is_superuser === true;
      case 'staff':
        return user.is_staff === true || user.is_superuser === true;
      default:
        return false;
    }
  }
}
