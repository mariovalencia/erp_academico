import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../services/auth';
import { environment } from '../../../environments/environment';
import { lastValueFrom } from 'rxjs';

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
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  isLoading = signal(false);
  errorMessage = signal<string | null>(null);
  returnUrl = signal<string>('/dashboard'); // URL por defecto

  ngOnInit(): void {
    // Obtener la URL de retorno si existe
    this.route.queryParams.subscribe(params => {
      if (params['returnUrl']) {
        this.returnUrl.set(params['returnUrl']);
        console.log('🔐 URL de retorno:', params['returnUrl']);
      }
    });
    this.loadGoogleOAuthScript();
  }

  private loadGoogleOAuthScript(): void {
    if (window.google?.accounts?.id) {
      this.initializeGoogleSignIn();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => this.initializeGoogleSignIn();
    script.onerror = () => {
      console.error('❌ Error cargando Google Identity Services');
      this.errorMessage.set('Error al cargar el servicio de autenticación');
    };
    document.head.appendChild(script);
  }

  private initializeGoogleSignIn(): void {
    try {
      google.accounts.id.initialize({
        client_id: environment.googleClientId,
        callback: (response: any) => this.handleCredentialResponse(response),
        auto_select: false,
        cancel_on_tap_outside: true,
        context: 'signin',
        ux_mode: 'popup'
      });

      google.accounts.id.renderButton(
        document.getElementById('googleSignInButton'),
        {
          theme: 'outline',
          size: 'large',
          width: 280,
          text: 'signin_with',
          shape: 'rectangular',
          logo_alignment: 'center'
        }
      );

      console.log('✅ Google Sign-In inicializado correctamente');

    } catch (error) {
      console.error('❌ Error inicializando Google Sign-In:', error);
      this.errorMessage.set('Error al inicializar autenticación');
    }
  }

  private async handleCredentialResponse(response: any): Promise<void> {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    if (!response?.credential) {
      this.errorMessage.set('Respuesta de autenticación inválida');
      this.isLoading.set(false);
      return;
    }

    const jwtToken = response.credential;
    
    try {
      console.log('🔐 Enviando JWT al backend para verificación...');

      const loginResult = await lastValueFrom(this.authService.loginWithGoogle(jwtToken));

      if (loginResult?.key && loginResult?.user) {
        this.authService.setAuthToken(loginResult.key, loginResult.user);
        this.handleSuccessfulLogin();
      } else {
        throw new Error('Credenciales inválidas del servidor');
      }

    } catch (error: any) {
      console.error('❌ Error en autenticación:', error);
      this.handleAuthError(error);
    } finally {
      this.isLoading.set(false);
    }
  }

  private handleSuccessfulLogin(): void {
    console.log('✅ Autenticación exitosa, redirigiendo a:', this.returnUrl());
    
    // Redirigir a la URL guardada o al dashboard por defecto
    this.router.navigateByUrl(this.returnUrl());
  }

  private handleAuthError(error: any): void {
    let errorMessage = 'Error al iniciar sesión. Intenta de nuevo.';
    
    if (error?.status === 401) {
      errorMessage = 'Credenciales inválidas o expiradas';
    } else if (error?.status === 403) {
      errorMessage = 'Acceso no autorizado';
    } else if (error?.status === 0) {
      errorMessage = 'Error de conexión. Verifica tu internet.';
    } else if (error?.error?.message) {
      errorMessage = error.error.message;
    }

    this.errorMessage.set(errorMessage);

    setTimeout(() => {
      this.errorMessage.set(null);
    }, 7000);
  }

  ngOnDestroy(): void {
    if (window.google?.accounts?.id) {
      google.accounts.id.cancel();
    }
  }
}