from django.core.management.base import BaseCommand
from dashboard.models import DashboardWidget

class Command(BaseCommand):
    help = 'Crea widgets iniciales para el dashboard'
    
    def handle(self, *args, **options):
        self.stdout.write('Creando widgets de dashboard...')
        
        widgets_data = [
            {
                'name': 'Estadísticas de Notificaciones',
                'code': 'notifications_stats',
                'description': 'Muestra estadísticas de notificaciones del usuario',
                'widget_type': 'notifications_stats',
                'component_name': 'NotificationsStatsWidgetComponent',
                'data_endpoint': '/api/dashboard/widgets/notifications-stats/',
                'default_size': 'medium',
                'default_config': {'refresh_interval': 300}
            },
            {
                'name': 'Notificaciones Recientes',
                'code': 'recent_notifications', 
                'description': 'Muestra las notificaciones más recientes',
                'widget_type': 'recent_notifications',
                'component_name': 'RecentNotificationsWidgetComponent',
                'data_endpoint': '/api/dashboard/widgets/recent-notifications/',
                'default_size': 'large',
                'default_config': {'limit': 5, 'refresh_interval': 60}
            },
            {
                'name': 'Estadísticas de Usuario',
                'code': 'user_stats',
                'description': 'Muestra estadísticas del usuario',
                'widget_type': 'user_stats',
                'component_name': 'UserStatsWidgetComponent', 
                'data_endpoint': '/api/dashboard/widgets/user-stats/',
                'default_size': 'small',
                'default_config': {}
            },
            {
                'name': 'Acciones Rápidas',
                'code': 'quick_actions',
                'description': 'Acciones rápidas del sistema',
                'widget_type': 'quick_actions',
                'component_name': 'QuickActionsWidgetComponent',
                'data_endpoint': '/api/dashboard/widgets/quick-actions/',
                'default_size': 'small', 
                'default_config': {}
            },
        ]
        
        for widget_data in widgets_data:
            widget, created = DashboardWidget.objects.get_or_create(
                code=widget_data['code'],
                defaults=widget_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Widget creado: {widget.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  Widget ya existe: {widget.name}'))
        
        self.stdout.write(self.style.SUCCESS('🎉 Widgets de dashboard creados exitosamente!'))