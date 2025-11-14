import logging
from django.db import transaction
from .models import DashboardWidget, UserDashboard, UserWidget, DashboardPreset

logger = logging.getLogger(__name__)

class DashboardService:
    """Servicio para gestión de dashboards"""
    
    @classmethod
    def get_or_create_user_dashboard(cls, user):
        """Obtiene o crea el dashboard para un usuario"""
        try:
            dashboard, created = UserDashboard.objects.get_or_create(user=user)
            if created:
                cls._initialize_user_dashboard(dashboard, user)
                logger.info(f"Dashboard creado para usuario: {user.email}")
            return dashboard
        except Exception as e:
            logger.error(f"Error obteniendo dashboard para {user.email}: {str(e)}")
            return None
    
    @classmethod
    def _initialize_user_dashboard(cls, dashboard, user):
        """Inicializa un dashboard nuevo con widgets por defecto"""
        try:
            # Buscar preset por defecto o por rol del usuario
            preset = cls._get_preset_for_user(user)
            
            if preset:
                cls._apply_preset_to_dashboard(dashboard, preset)
            else:
                # Widgets por defecto si no hay preset
                default_widgets = DashboardWidget.objects.filter(is_active=True)[:4]
                for i, widget in enumerate(default_widgets):
                    UserWidget.objects.create(
                        user_dashboard=dashboard,
                        widget=widget,
                        position={'x': i * 2, 'y': 0, 'cols': 2, 'rows': 1},
                        config=widget.default_config,
                        is_visible=True
                    )
        except Exception as e:
            logger.error(f"Error inicializando dashboard: {str(e)}")
    
    @classmethod
    def _get_preset_for_user(cls, user):
        """Obtiene el preset adecuado para un usuario"""
        # Primero buscar por rol
        try:
            if hasattr(user, 'user_roles') and user.user_roles.exists():
                user_roles = user.user_roles.filter(is_active=True).select_related('role')
                for user_role in user_roles:
                    preset = DashboardPreset.objects.filter(
                        required_role=user_role.role
                    ).first()
                    if preset:
                        return preset
        except Exception as e:
            logger.warning(f"Error buscando preset por rol: {str(e)}")
        
        # Buscar preset por defecto
        return DashboardPreset.objects.filter(is_default=True).first()
    
    @classmethod
    def _apply_preset_to_dashboard(cls, dashboard, preset):
        """Aplica un preset a un dashboard"""
        try:
            preset_widgets = preset.presetwidget_set.select_related('widget').all()
            
            for preset_widget in preset_widgets:
                if preset_widget.widget.is_active:
                    UserWidget.objects.create(
                        user_dashboard=dashboard,
                        widget=preset_widget.widget,
                        position=preset_widget.position,
                        config=preset_widget.config,
                        is_visible=True
                    )
        except Exception as e:
            logger.error(f"Error aplicando preset {preset.name}: {str(e)}")
    
    @classmethod
    def get_available_widgets(cls, user):
        """Obtiene widgets disponibles para un usuario"""
        try:
            all_widgets = DashboardWidget.objects.filter(is_active=True)
            available_widgets = []
            
            for widget in all_widgets:
                if cls._user_can_access_widget(user, widget):
                    available_widgets.append(widget)
            
            return available_widgets
        except Exception as e:
            logger.error(f"Error obteniendo widgets disponibles: {str(e)}")
            return []
    
    @classmethod
    def _user_can_access_widget(cls, user, widget):
        """Verifica si un usuario puede acceder a un widget usando tu sistema de permisos"""
        if not widget.required_permissions.exists():
            return True
        
        # ✅ CORREGIDO: Usar tu sistema de permisos granulares
        try:
            # Obtener todos los permisos del usuario a través de sus roles
            user_permissions = set()
            
            if hasattr(user, 'user_roles'):
                for user_role in user.user_roles.filter(is_active=True):
                    role_permissions = user_role.role.get_all_permissions()
                    user_permissions.update(role_permissions)
            
            # Verificar si el usuario tiene todos los permisos requeridos
            required_permissions = set(widget.required_permissions.all())
            
            # Para el widget, el usuario necesita tener AL MENOS UNO de los permisos requeridos
            # (no necesariamente todos, a menos que quieras cambiar la lógica)
            return bool(user_permissions & required_permissions)
            
        except Exception as e:
            logger.error(f"Error verificando permisos para widget {widget.code}: {str(e)}")
            return False
    
    @classmethod
    def update_dashboard_layout(cls, user, layout_data):
        """Actualiza el layout del dashboard de un usuario"""
        try:
            with transaction.atomic():
                dashboard = cls.get_or_create_user_dashboard(user)
                if not dashboard:
                    return False
                
                # Actualizar layout general
                dashboard.layout = layout_data.get('layout', {})
                dashboard.save()
                
                # Actualizar posiciones de widgets individuales
                for widget_data in layout_data.get('widgets', []):
                    user_widget = UserWidget.objects.filter(
                        user_dashboard=dashboard,
                        widget__code=widget_data['widget_code']
                    ).first()
                    
                    if user_widget:
                        user_widget.position = widget_data['position']
                        user_widget.is_visible = widget_data.get('is_visible', True)
                        user_widget.save()
                
                logger.info(f"Dashboard actualizado para {user.email}")
                return True
                
        except Exception as e:
            logger.error(f"Error actualizando dashboard: {str(e)}")
            return False

class WidgetDataService:
    """Servicio para obtener datos de widgets específicos"""
    
    @classmethod
    def get_notifications_stats(cls, user):
        """Datos para widget de estadísticas de notificaciones"""
        from notifications.models import Notification
        from notifications.services import NotificationService
        
        try:
            user_notifications = Notification.objects.filter(user=user)
            
            stats = {
                'total': user_notifications.count(),
                'unread': NotificationService.get_unread_count(user),
                'read': user_notifications.filter(read_at__isnull=False).count(),
                'sent': user_notifications.filter(status='sent').count(),
                'pending': user_notifications.filter(status='pending').count(),
            }
            
            return {
                'success': True,
                'data': stats,
                'last_updated': str(user_notifications.last().created_at) if user_notifications.exists() else None
            }
        except Exception as e:
            logger.error(f"Error obteniendo stats de notificaciones: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def get_recent_notifications(cls, user, limit=5):
        """Datos para widget de notificaciones recientes"""
        from notifications.services import NotificationService
        
        try:
            recent_notifications = NotificationService.get_recent_notifications(user, limit)
            
            notifications_data = []
            for notification in recent_notifications:
                rendered = notification.template.render_content(notification.context)
                notifications_data.append({
                    'id': notification.id,
                    'title': rendered.get('subject', ''),
                    'message': rendered.get('body', '')[:100] + '...' if len(rendered.get('body', '')) > 100 else rendered.get('body', ''),
                    'is_read': notification.read_at is not None,
                    'created_at': notification.created_at,
                    'type': notification.template.code
                })
            
            return {
                'success': True,
                'data': notifications_data
            }
        except Exception as e:
            logger.error(f"Error obteniendo notificaciones recientes: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def get_user_stats(cls, user):
        """Datos para widget de estadísticas de usuario"""
        try:
            # Aquí puedes integrar con otros módulos de tu core
            stats = {
                'login_count': getattr(user, 'login_count', 0),
                'last_login': user.last_login,
                'date_joined': user.date_joined,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
            }
            
            return {
                'success': True,
                'data': stats
            }
        except Exception as e:
            logger.error(f"Error obteniendo stats de usuario: {str(e)}")
            return {'success': False, 'error': str(e)}