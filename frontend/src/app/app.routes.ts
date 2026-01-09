import { Routes } from '@angular/router';
//import { LoginComponent } from './components/login/login';
//import { DashboardComponent } from './components/dashboard/dashboard';
import { authGuard } from './features/auth/guards/auth.guard';
import { noAuthGuard } from './features/auth/guards/no-auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./features/auth/components/login/login').then(m => m.LoginComponent),
    canActivate: [noAuthGuard]  // 🔒 No permite acceso si ya está autenticado
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/components/dashboard/dashboard').then(m => m.DashboardComponent),
    canActivate: [authGuard]  // 🔒 Proteger ruta
  },
  /*{
    path: 'profile',
    loadComponent: () => import('./components/profile/profile.component').then(m => m.ProfileComponent),
    canActivate: [authGuard]  // 🔒 Protege otras rutas
  },
  {
    path: 'courses',
    loadComponent: () => import('./components/courses/courses.component').then(m => m.CoursesComponent),
    canActivate: [authGuard]  // 🔒 Protege otras rutas
  },*/
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: '**',
    redirectTo: '/dashboard'
  }
];
