import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth';
import { environment } from '../../../environments/environment';

// Declarar google globalmente
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
    this.loadGoogleScript();
  }

  private loadGoogleScript(): void {
    // Verificar si ya está cargado
    if (this.isGoogleLoaded()) {
      this.initializeGoogleSignIn();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => {
      setTimeout(() => this.initializeGoogleSignIn(), 1000);
    };
    script.onerror = () => {
      this.errorMessage.set('Error al cargar Google Sign-In');
    };
    document.head.appendChild(script);
  }

  private isGoogleLoaded(): boolean {
    return typeof google !== 'undefined' && google.accounts;
  }

  private initializeGoogleSignIn(): void {
    if (!this.isGoogleLoaded()) {
      this.errorMessage.set('Google Sign-In no se cargó correctamente');
      return;
    }

    try {
      console.log('🔐 Initializing Google Sign-In with Client ID:', environment.googleClientId);
      google.accounts.id.initialize({
        client_id: environment.googleClientId,
        callback: (response: any) => this.handleGoogleSignIn(response),
        auto_select: false,
        cancel_on_tap_outside: true,
        ux_mode: 'popup',
        itp_support: true
      });

      this.initializeGoogleOAuth2();



    } catch (error) {
      console.error('Error initializing Google Sign-In:', error);
      this.errorMessage.set('Error al inicializar Google Sign-In');
    }
  }

  private initializeGoogleOAuth2(): void {
    google.accounts.id.renderButton(
        document.getElementById('googleSignInButton'),
        {
          theme: 'outline',
          size: 'large',
          width: 280,
          text: 'continue_with',
          shape: 'rectangular',
          logo_alignment: 'center',
          type: 'standard',
          scope: 'profile email openid'
        }
      );

      console.log('Google Sign-In initialized successfully');
  }

  private async handleGoogleSignIn(response: any): Promise<void> {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    try {
      const loginResult = await this.authService.loginWithGoogle(response.credential).toPromise();

      if (loginResult?.key) {
        this.showSuccessMessage();
        console.log('User logged in successfully');
      } else {
        throw new Error('Respuesta inválida del servidor');
      }
    } catch (error: any) {
      console.error('Login error:', error);
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
