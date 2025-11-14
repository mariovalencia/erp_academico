from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """🔧 PERMISSION FALTANTE: Solo dueño o admin puede acceder"""
    
    def has_object_permission(self, request, view, obj):
        # Los admins pueden ver todo
        if request.user.is_staff:
            return True
        
        # Los usuarios solo pueden ver sus propias notificaciones
        return obj.user == request.user