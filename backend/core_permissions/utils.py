from django.core.exceptions import ValidationError
from django.db import transaction, models  # 🔥 IMPORTAR models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType  # 🔥 IMPORTAR ContentType
from django.contrib.auth.models import Permission as AuthPermission
from .models import (
    GranularPermission, Role, UserRole, RoleTemplate, 
    PermissionModule, Department
)

class PermissionManager:
    """
    Utilidades para gestión masiva de permisos
    """
    
    @classmethod
    def create_module_permissions(cls, module_code, functionalities_actions):
        """
        Crea permisos masivamente para un módulo
        
        Args:
            module_code (str): Código del módulo
            functionalities_actions (dict): {
                'functionality_code': ['view', 'create', 'edit', ...],
                ...
            }
        """
        try:
            module = PermissionModule.objects.get(code=module_code)
        except PermissionModule.DoesNotExist:
            raise ValueError(f"Módulo '{module_code}' no existe")
        
        created_permissions = []
        
        with transaction.atomic():
            for func_code, actions in functionalities_actions.items():
                functionality = func_code.replace('_', ' ').title()
                
                for action in actions:
                    for scope in ['all', 'department', 'own']:
                        try:
                            # 🔥 CREAR INSTANCIA PRIMERO Y LUEGO GUARDAR
                            permission = GranularPermission(
                                module=module,
                                functionality=functionality,
                                functionality_code=func_code,
                                action=action,
                                scope=scope
                            )
                            
                            # 🔥 FORZAR LA GENERACIÓN DEL NOMBRE Y CÓDIGO
                            if not permission.name:
                                permission.name = f"{module.name} - {functionality} - {dict(permission.ACTION_CHOICES)[action]} - {dict(permission.SCOPE_CHOICES)[scope]}"
                            
                            if not permission.permission_code:
                                permission.permission_code = f"{module.code}.{func_code}.{action}.{scope}"
                            
                            # 🔥 MARCAR ACCIONES PELIGROSAS AUTOMÁTICAMENTE
                            if action in ['delete', 'approve', 'reject']:
                                permission.is_dangerous = True
                            
                            permission.save()
                            created_permissions.append(permission)
                            created_permissions.append(permission)

                        except ValidationError as e:
                            print(f"Error creando permiso {func_code}.{action}.{scope}: {e}")

                        except Exception as e:
                            print(f"❌ Error inesperado con {func_code}.{action}.{scope}: {e}")
        
        return created_permissions
    
    @classmethod
    def bulk_assign_permissions_to_role(cls, role, permission_codes, assigned_by=None):
        """
        Asigna múltiples permisos a un rol
        
        Args:
            role: Instancia de Role
            permission_codes (list): Lista de códigos de permisos
            assigned_by: Usuario que realiza la asignación
        """
        permissions = GranularPermission.objects.filter(
            permission_code__in=permission_codes
        )
        
        assigned = []
        failed = []
        
        with transaction.atomic():
            for permission in permissions:
                try:
                    role.permissions.add(permission)
                    assigned.append(permission.permission_code)
                except Exception as e:
                    failed.append({
                        'permission': permission.permission_code,
                        'error': str(e)
                    })
        
        return {
            'assigned': assigned,
            'failed': failed,
            'total_assigned': len(assigned)
        }
    
    @classmethod
    def sync_user_permissions(cls, user, department=None):
        """
        Sincroniza todos los permisos de un usuario basado en sus roles
        
        Args:
            user: Instancia de CustomUser
            department: Departamento para filtros (opcional)
        """
        user_roles = UserRole.objects.filter(
            user=user
        ).select_related('role')
        
        if department:
            user_roles = user_roles.filter(
                models.Q(department=department) | models.Q(department__isnull=True)
            )
        
        all_permissions = set()
        
        for user_role in user_roles:
            if user_role.is_active:  # 🔥 USAR LA PROPERTY is_active
                role_permissions = user_role.role.get_all_permissions()
                all_permissions.update(role_permissions)
        
        # Convertir a formato para el sistema de permisos de Django
        auth_permissions = []
        content_type = ContentType.objects.get_for_model(GranularPermission)  # 🔥 DEFINIR content_type
        
        for perm in all_permissions:
            # Crear o obtener el permiso de Django
            auth_perm, created = AuthPermission.objects.get_or_create(
                codename=perm.permission_code,
                content_type=content_type,  # 🔥 USAR content_type definido
                defaults={
                    'name': perm.name,
                }
            )
            auth_permissions.append(auth_perm)
        
        # Asignar permisos al usuario
        user.user_permissions.set(auth_permissions)
        
        return {
            'total_permissions': len(all_permissions),
            'auth_permissions': len(auth_permissions)
        }


class RoleTemplateManager:
    """
    Utilidades para gestión de plantillas de roles
    """
    
    @classmethod
    def create_university_template(cls):
        """
        Crea plantilla predefinida para universidad
        """
        template, created = RoleTemplate.objects.get_or_create(
            name="ERP Universitario Básico",
            template_type='university',
            defaults={
                'description': 'Plantilla con roles básicos para sistema universitario'
            }
        )
        
        # Roles predefinidos para universidad
        university_roles = [
            ('estudiante', 'Estudiante', 'business'),
            ('docente', 'Docente', 'business'),
            ('coordinador', 'Coordinador Académico', 'business'),
            ('administrativo', 'Personal Administrativo', 'business'),
            ('super_admin', 'Super Administrador', 'system'),
        ]
        
        for role_code, role_name, role_type in university_roles:
            role, _ = Role.objects.get_or_create(
                code=role_code,
                defaults={
                    'name': role_name,
                    'role_type': role_type,
                    'description': f'Rol de {role_name.lower()} en el sistema universitario'
                }
            )
            template.roles.add(role)
        
        return template
    
    @classmethod
    def apply_template_to_users(cls, template, users, assigned_by=None, department=None):
        """
        Aplica una plantilla a múltiples usuarios
        """
        results = {
            'success': [],
            'failed': []
        }
        
        for user in users:
            try:
                template.apply_to_user(user, assigned_by, department)
                results['success'].append(user.email)
            except Exception as e:
                results['failed'].append({
                    'user': user.email,
                    'error': str(e)
                })
        
        return results


class PermissionCache:
    """
    Sistema de caché para permisos frecuentes
    """
    _user_permissions_cache = {}
    _role_permissions_cache = {}
    
    @classmethod
    def get_user_permissions(cls, user_id, department_id=None):
        """
        Obtiene permisos de usuario desde caché o base de datos
        """
        cache_key = f"user_{user_id}_dept_{department_id}"
        
        if cache_key in cls._user_permissions_cache:
            return cls._user_permissions_cache[cache_key]
        
        # Obtener de base de datos
        user_roles = UserRole.objects.filter(
            user_id=user_id
        ).select_related('role', 'department')
        
        if department_id:
            user_roles = user_roles.filter(
                models.Q(department_id=department_id) | models.Q(department__isnull=True)
            )
        
        permissions = set()
        for user_role in user_roles:
            if user_role.is_active:  # 🔥 USAR LA PROPERTY is_active
                role_perms = cls.get_role_permissions(user_role.role_id)
                permissions.update(role_perms)
        
        # Guardar en caché por 5 minutos
        cls._user_permissions_cache[cache_key] = permissions
        
        return permissions
    
    @classmethod
    def get_role_permissions(cls, role_id):
        """
        Obtiene permisos de rol desde caché o base de datos
        """
        if role_id in cls._role_permissions_cache:
            return cls._role_permissions_cache[role_id]
        
        # Obtener de base de datos
        try:
            role = Role.objects.get(id=role_id)
            permissions = role.get_all_permissions()
            cls._role_permissions_cache[role_id] = permissions
            return permissions
        except Role.DoesNotExist:
            return set()
    
    @classmethod
    def invalidate_user_cache(cls, user_id=None, department_id=None):
        """
        Invalida caché de permisos de usuario
        """
        if user_id and department_id:
            cache_key = f"user_{user_id}_dept_{department_id}"
            cls._user_permissions_cache.pop(cache_key, None)
        elif user_id:
            # Invalidar todos los cachés de este usuario
            keys_to_remove = [k for k in cls._user_permissions_cache.keys() if k.startswith(f"user_{user_id}_")]
            for key in keys_to_remove:
                cls._user_permissions_cache.pop(key, None)
        else:
            # Invalidar todo el caché
            cls._user_permissions_cache.clear()
            cls._role_permissions_cache.clear()
    
    @classmethod
    def invalidate_role_cache(cls, role_id=None):
        """
        Invalida caché de permisos de rol
        """
        if role_id:
            cls._role_permissions_cache.pop(role_id, None)
        else:
            cls._role_permissions_cache.clear()
    
    @classmethod
    def user_has_permission(cls, user_id, permission_code, department_id=None):
        """
        Verifica rápidamente si un usuario tiene un permiso específico
        """
        user_permissions = cls.get_user_permissions(user_id, department_id)
        return any(perm.permission_code == permission_code for perm in user_permissions)