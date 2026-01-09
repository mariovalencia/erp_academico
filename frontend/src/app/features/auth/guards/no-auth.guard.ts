import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const noAuthGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  //console.log('🛡️ NoAuthGuard ejecutándose');

  // Si el usuario YA está autenticado, redirigir al dashboard
  if (authService.isAuthenticated()) {
    console.log('✅ Usuario ya autenticado, redirigiendo a dashboard');
    router.navigate(['/dashboard']);
    return false;
  }

  //console.log('✅ Usuario no autenticado, permitiendo acceso a login');
  return true;
};
