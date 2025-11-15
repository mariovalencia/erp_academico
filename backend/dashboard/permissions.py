from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso personalizado para que solo el dueño o un admin pueda acceder
    """
    
    def has_object_permission(self, request, view, obj):
        # Los admins pueden ver todo
        if request.user.is_staff:
            return True
        
        # Verificar si el objeto tiene relación con el usuario
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'user_dashboard'):
            return obj.user_dashboard.user == request.user
        
        return False

class CanAccessWidget(permissions.BasePermission):
    """
    Permiso para verificar acceso a widgets específicos
    """
    
    def has_permission(self, request, view):
        # Para acciones de lista, verificar que pueda acceder a los widgets
        if view.action in ['list', 'available']:
            return True
        
        # Para acciones específicas, la verificación se hace en el objeto
        return True
    
    def has_object_permission(self, request, view, obj):
        from .services import DashboardService
        return DashboardService._user_can_access_widget(request.user, obj)