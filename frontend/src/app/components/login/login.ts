import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth';
import { environment } from '../../../environments/environment';

declare var google: any;

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class LoginComponent implements OnInit {
  private authService = inject(AuthService);

  isLoading = signal(false);
  errorMessage = signal<string | null>(null);

  ngOnInit(): void {
    this.loadGoogleOAuthScript();
  }

  private loadGoogleOAuthScript(): void {
    // Cargar script de Google Identity Services
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => {
      //console.log('✅ Google Identity Services cargado');
      this.initializeGoogleSignIn();
    };
    script.onerror = () => {
      console.error('❌ Error cargando Google Identity Services');
      this.errorMessage.set('Error al cargar Google Sign-In');
    };
    document.head.appendChild(script);
  }

  private initializeGoogleSignIn(): void {
    try {
      //console.log('🔐 Inicializando Google Sign-In con Client ID:', environment.googleClientId);

      // 🔥 CONFIGURACIÓN CORRECTA para obtener Access Token
      google.accounts.id.initialize({
        client_id: environment.googleClientId,
        callback: this.handleCredentialResponse.bind(this),
        auto_select: false,
        cancel_on_tap_outside: true,
        context: 'signin'
      });

      // Renderizar botón
      google.accounts.id.renderButton(
        document.getElementById('googleSignInButton'),
        {
          theme: 'outline',
          size: 'large',
          width: 280,
          text: 'continue_with',
          shape: 'rectangular',
          logo_alignment: 'center'
        }
      );

      //console.log('✅ Google Sign-In inicializado correctamente');

    } catch (error) {
      console.error('❌ Error inicializando Google Sign-In:', error);
      this.errorMessage.set('Error al inicializar Google Sign-In');
    }
  }

  // 🔥 NUEVO MÉTODO: Usar Google OAuth2 para obtener Access Token
  async loginWithGoogleOAuth2(): Promise<void> {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    try {
      console.log('🔐 Iniciando flujo OAuth2...');

      // Crear cliente OAuth2
      const client = google.accounts.oauth2.initTokenClient({
        client_id: environment.googleClientId,
        scope: 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
        callback: async (response: any) => {
          if (response.access_token) {
            //console.log('✅ Access Token obtenido:', response.access_token.substring(0, 50) + '...');
            await this.sendTokenToBackend(response.access_token);
          } else {
            console.error('❌ No se pudo obtener access token');
            this.errorMessage.set('Error al obtener token de Google');
            this.isLoading.set(false);
          }
        },
        error_callback: (error: any) => {
          console.error('❌ Error en OAuth2:', error);
          this.errorMessage.set('Error en autenticación con Google');
          this.isLoading.set(false);
        }
      });

      // Solicitar token
      client.requestAccessToken();

    } catch (error) {
      console.error('❌ Error en loginWithGoogleOAuth2:', error);
      this.errorMessage.set('Error al iniciar sesión');
      this.isLoading.set(false);
    }
  }

  // Manejar respuesta del botón estándar (JWT)
  private async handleCredentialResponse(response: any): Promise<void> {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    //console.log('🔐 Respuesta de Google (JWT):', response);

    try {
      // El JWT está en response.credential
      const jwtToken = response.credential;
      //console.log('🔐 JWT Token:', jwtToken.substring(0, 50) + '...');

      // 🔥 PRUEBA: Intentar usar el JWT directamente
      const loginResult: any = await this.authService.loginWithGoogle(jwtToken).toPromise();

      if (loginResult?.key) {
        this.authService.setAuthToken(loginResult.key, loginResult.user);
        this.showSuccessMessage();
        //console.log('✅ Login exitoso con JWT');
      } else {
        throw new Error('Respuesta inválida del servidor');
      }
    } catch (error: any) {
      console.error('❌ Error con JWT:', error);

      // Si falla con JWT, intentar con OAuth2
      console.log('🔄 Intentando con flujo OAuth2...');
      this.loginWithGoogleOAuth2();
    }
  }

  private async sendTokenToBackend(accessToken: string): Promise<void> {
    try {
      //console.log('🔐 Enviando Access Token al backend...');

      const loginResult: any = await this.authService.loginWithGoogle(accessToken).toPromise();

      if (loginResult?.key) {
        this.authService.setAuthToken(loginResult.key, loginResult.user);
        this.showSuccessMessage();
        console.log('✅ Login exitoso con Access Token');
      } else {
        throw new Error('Respuesta inválida del servidor');
      }
    } catch (error: any) {
      console.error('❌ Error enviando token al backend:', error);
      this.handleError(error);
    } finally {
      this.isLoading.set(false);
    }
  }

  private showSuccessMessage(): void {
    const user = this.authService.user();
    const userName = user?.first_name || user?.email || 'Estudiante';
    alert(`🎉 ¡Bienvenido ${userName}! \nLogin exitoso al ERP Universitario`);
  }

  private handleError(error: any): void {
    const message = error?.error?.message ||
                   error?.message ||
                   'Error al iniciar sesión. Intenta de nuevo.';

    this.errorMessage.set(message);

    setTimeout(() => {
      this.errorMessage.set(null);
    }, 5000);
  }
}
