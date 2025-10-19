import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth';

interface MenuItem {
  label: string;
  icon: string;
  route: string;
  badge?: number;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css']
})
export class DashboardComponent implements OnInit {
  public authService = inject(AuthService);
  private router = inject(Router);

  // Señales reactivas
  currentUser = signal<any>(null);
  isSidebarCollapsed = signal(false);
  isLoading = signal(true);

  // Menú del dashboard
  menuItems = signal<MenuItem[]>([
    { label: 'Inicio', icon: '🏠', route: '/dashboard' },
    { label: 'Perfil', icon: '👤', route: '/dashboard/profile' },
    { label: 'Cursos', icon: '📚', route: '/dashboard/courses', badge: 5 },
    { label: 'Calificaciones', icon: '📊', route: '/dashboard/grades' },
    { label: 'Horario', icon: '🕒', route: '/dashboard/schedule' },
    { label: 'Mensajes', icon: '💬', route: '/dashboard/messages', badge: 3 },
    { label: 'Configuración', icon: '⚙️', route: '/dashboard/settings' }
  ]);

  // Cards de resumen
  summaryCards = signal([
    { title: 'Cursos Activos', value: '5', icon: '📚', color: 'blue' },
    { title: 'Tareas Pendientes', value: '3', icon: '📝', color: 'orange' },
    { title: 'Promedio Actual', value: '8.5', icon: '⭐', color: 'green' },
    { title: 'Próximos Exámenes', value: '2', icon: '📅', color: 'red' }
  ]);

  ngOnInit(): void {
    this.initializeDashboard();
  }

  private initializeDashboard(): void {
    const user = this.authService.getCurrentUser();
    
    if (!user) {
      this.router.navigate(['/login']);
      return;
    }

    this.currentUser.set(user);
    this.isLoading.set(false);
    
    //console.log('✅ Dashboard inicializado para:', user.email);
  }

  toggleSidebar(): void {
    this.isSidebarCollapsed.update(collapsed => !collapsed);
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  getGreeting(): string {
    const hour = new Date().getHours();
    if (hour < 12) return 'Buenos días';
    if (hour < 18) return 'Buenas tardes';
    return 'Buenas noches';
  }
}