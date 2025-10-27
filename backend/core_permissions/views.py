from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,IsAdminUser, AllowAny
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import (
    PermissionModule, GranularPermission, Role, 
    UserRole, RoleTemplate, Department
)
from .serializers import *
from .utils import PermissionManager, PermissionCache

class PermissionModuleViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de módulos de permisos"""
    queryset = PermissionModule.objects.all()
    serializer_class = PermissionModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Permisos diferentes según la acción"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]  # 🔥 Lectura para todos
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]  # 🔥 Escritura solo admin
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar módulos activos por defecto"""
        queryset = PermissionModule.objects.all()
        if self.request.query_params.get('active_only'):
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('order', 'name')


class GranularPermissionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de permisos granulares"""
    queryset = GranularPermission.objects.all()
    serializer_class = GranularPermissionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Permisos diferentes según la acción"""
        if self.action in ['list', 'retrieve', 'by_module']:
            permission_classes = [IsAuthenticated]  # 🔥 Lectura para todos
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]  # 🔥 Escritura solo admin
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Optimizar queries con select_related"""
        return GranularPermission.objects.select_related('module').order_by('module__order', 'functionality', 'action')
    
    @action(detail=False, methods=['get'])
    def by_module(self, request):
        """Obtener permisos agrupados por módulo"""
        modules = PermissionModule.objects.filter(is_active=True).prefetch_related('permissions')
        
        result = []
        for module in modules:
            permissions = module.permissions.all()
            result.append({
                'module': PermissionModuleSerializer(module).data,
                'permissions': GranularPermissionSerializer(permissions, many=True).data
            })
        
        return Response(result)


class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de roles"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['role_type', 'is_active', 'is_system_role']
    search_fields = ['name', 'code', 'description']
    
    def get_queryset(self):
        """Optimizar queries con prefetch_related"""
        return Role.objects.prefetch_related('permissions', 'user_assignments').order_by('role_type', 'name')
    
    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        """Asignar múltiples permisos a un rol"""
        role = self.get_object()
        serializer = AssignPermissionsToRoleSerializer(data=request.data)
        
        if serializer.is_valid():
            permission_codes = serializer.validated_data['permission_codes']
            assigned_by = serializer.validated_data.get('assigned_by', request.user)
            
            result = PermissionManager.bulk_assign_permissions_to_role(
                role, permission_codes, assigned_by
            )
            
            return Response({
                'success': True,
                'role': RoleSerializer(role).data,
                'assignment_result': result
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Obtener usuarios que tienen este rol"""
        role = self.get_object()
        user_roles = role.user_assignments.select_related('user', 'department')
        
        page = self.paginate_queryset(user_roles)
        if page is not None:
            serializer = UserRoleSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response(serializer.data)


class UserRoleViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de asignación de roles a usuarios"""
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['user', 'role', 'department', 'is_temporary', 'is_active']
    
    def get_queryset(self):
        """Optimizar queries con select_related"""
        return UserRole.objects.select_related(
            'user', 'role', 'department', 'assigned_by'
        ).order_by('-assigned_at')
    
    @action(detail=False, methods=['post'])
    def assign_role(self, request):
        """Asignar un rol a un usuario"""
        serializer = AssignRoleToUserSerializer(data=request.data)
        
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.validated_data['user_id']
                role = serializer.validated_data['role_id']
                department = serializer.validated_data.get('department_id')
                is_temporary = serializer.validated_data['is_temporary']
                valid_days = serializer.validated_data.get('valid_days')
                notes = serializer.validated_data.get('notes', '')
                
                # Calcular fechas si es temporal
                valid_from = None
                valid_until = None
                if is_temporary and valid_days:
                    valid_from = timezone.now()
                    valid_until = valid_from + timedelta(days=valid_days)
                
                user_role, created = UserRole.objects.get_or_create(
                    user=user,
                    role=role,
                    department=department,
                    defaults={
                        'is_temporary': is_temporary,
                        'valid_from': valid_from,
                        'valid_until': valid_until,
                        'assigned_by': request.user,
                        'notes': notes
                    }
                )
                
                if not created:
                    user_role.is_temporary = is_temporary
                    user_role.valid_from = valid_from
                    user_role.valid_until = valid_until
                    user_role.assigned_by = request.user
                    user_role.notes = notes
                    user_role.save()
                
                # Invalidar caché del usuario
                PermissionCache.invalidate_user_cache(user.id)
                
                return Response({
                    'success': True,
                    'created': created,
                    'user_role': UserRoleSerializer(user_role).data
                })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def user_permissions(self, request):
        """Obtener todos los permisos de un usuario"""
        serializer = UserPermissionsSerializer(data=request.query_params)
        
        if serializer.is_valid():
            user = serializer.validated_data['user_id']
            department = serializer.validated_data.get('department_id')
            
            permissions = PermissionCache.get_user_permissions(user.id, department.id if department else None)
            
            return Response({
                'user_id': user.id,
                'user_email': user.email,
                'department': DepartmentSerializer(department).data if department else None,
                'permissions': GranularPermissionSerializer(permissions, many=True).data,
                'total_permissions': len(permissions)
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def check_permission(self, request):
        """Verificar si un usuario tiene un permiso específico"""
        serializer = CheckPermissionSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user_id']
            permission_code = serializer.validated_data['permission_code']
            department = serializer.validated_data.get('department_id')
            
            has_permission = PermissionCache.user_has_permission(
                user.id, 
                permission_code, 
                department.id if department else None
            )
            
            return Response({
                'has_permission': has_permission,
                'user_id': user.id,
                'permission_code': permission_code,
                'department': DepartmentSerializer(department).data if department else None
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoleTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de plantillas de roles"""
    queryset = RoleTemplate.objects.all()
    serializer_class = RoleTemplateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        """Optimizar queries con prefetch_related"""
        return RoleTemplate.objects.prefetch_related('templaterole_set__role').order_by('template_type', 'name')
    
    @action(detail=True, methods=['post'])
    def apply_to_user(self, request, pk=None):
        """Aplicar plantilla a un usuario"""
        template = self.get_object()
        user_id = request.data.get('user_id')
        department_id = request.data.get('department_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from core_users.models import CustomUser
            user = CustomUser.objects.get(id=user_id)
            department = Department.objects.get(id=department_id) if department_id else None
            
            template.apply_to_user(user, request.user, department)
            
            # Invalidar caché del usuario
            PermissionCache.invalidate_user_cache(user.id)
            
            return Response({
                'success': True,
                'message': f'Plantilla aplicada exitosamente a {user.email}',
                'user': user.email,
                'template': template.name
            })
            
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Department.DoesNotExist:
            return Response(
                {'error': 'Departamento no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de departamentos (temporal)"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'code']


# Views adicionales para funcionalidades específicas
from rest_framework.views import APIView

class PermissionUtilitiesView(APIView):
    """Vista para utilidades del sistema de permisos"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Sincronizar permisos de un usuario"""
        serializer = UserPermissionsSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user_id']
            department = serializer.validated_data.get('department_id')
            
            result = PermissionManager.sync_user_permissions(user, department)
            
            # Invalidar caché
            PermissionCache.invalidate_user_cache(user.id)
            
            return Response({
                'success': True,
                'message': 'Permisos sincronizados exitosamente',
                'sync_result': result
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SystemPermissionsView(APIView):
    """Vista para operaciones del sistema de permisos"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener estadísticas del sistema de permisos"""
        stats = {
            'total_modules': PermissionModule.objects.count(),
            'total_permissions': GranularPermission.objects.count(),
            'total_roles': Role.objects.count(),
            'total_user_assignments': UserRole.objects.count(),
            'active_modules': PermissionModule.objects.filter(is_active=True).count(),
            'active_roles': Role.objects.filter(is_active=True).count(),
            'system_roles': Role.objects.filter(role_type='system').count(),
            'temporary_assignments': UserRole.objects.filter(is_temporary=True).count(),
        }
        
        return Response(stats)