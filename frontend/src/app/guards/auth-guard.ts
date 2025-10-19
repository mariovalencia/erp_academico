import { inject } from '@angular/core';
import { CanActivateFn, Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { AuthService } from '../services/auth';

export const authGuard: CanActivateFn = (
  route: ActivatedRouteSnapshot,
  state: RouterStateSnapshot
) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  console.log('🛡️ AuthGuard ejecutándose para:', state.url);

  // Verificar si el usuario está autenticado
  if (authService.isAuthenticated()) {
    console.log('✅ Usuario autenticado, acceso permitido');
    return true;
  } else {
    console.log('❌ Usuario NO autenticado, redirigiendo a login');
    
    // Guardar la URL a la que intentaba acceder para redirigir después del login
    const returnUrl = state.url;
    router.navigate(['/login'], { 
      queryParams: { returnUrl: returnUrl } 
    });
    
    return false;
  }
};