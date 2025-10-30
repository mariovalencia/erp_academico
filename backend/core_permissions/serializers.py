from rest_framework import serializers
from .models import (
    PermissionModule, GranularPermission, Role, 
    UserRole, RoleTemplate, RolePermission, TemplateRole
)

# ✅ IMPORTAR SERIALIZERS DE LOS MÓDULOS CORRECTOS
from core_users.serializers import CustomUserSerializer
from core_organization.serializers import DepartmentSerializer

# ❌ NO hay CustomUserSerializer temporal aquí
# ❌ NO hay DepartmentSerializer temporal aquí

class PermissionModuleSerializer(serializers.ModelSerializer):
    """Serializer para módulos de permisos"""
    permissions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PermissionModule
        fields = [
            'id', 'name', 'code', 'description', 'icon', 
            'is_active', 'order', 'permissions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_permissions_count(self, obj):
        return obj.permissions.count()


class GranularPermissionSerializer(serializers.ModelSerializer):
    """Serializer para permisos granulares"""
    module_name = serializers.CharField(source='module.name', read_only=True)
    module_code = serializers.CharField(source='module.code', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    
    class Meta:
        model = GranularPermission
        fields = [
            'id', 'name', 'permission_code', 'description',
            'module', 'module_name', 'module_code',
            'functionality', 'functionality_code',
            'action', 'action_display', 'scope', 'scope_display',
            'is_dangerous', 'requires_approval',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_permission_code(self, value):
        """Validar que el código de permiso sea único"""
        if GranularPermission.objects.filter(permission_code=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("Ya existe un permiso con este código")
        return value


class RolePermissionSerializer(serializers.ModelSerializer):
    """Serializer para la relación Role-Permission"""
    permission_detail = GranularPermissionSerializer(source='permission', read_only=True)
    assigned_by_email = serializers.CharField(source='assigned_by.email', read_only=True)
    department_filter_detail = DepartmentSerializer(source='department_filter', read_only=True)  # ✅ SERIALIZER REAL
    
    class Meta:
        model = RolePermission
        fields = [
            'id', 'role', 'permission', 'permission_detail',
            'department_filter', 'department_filter_detail',  # ✅ REFERENCIA CORRECTA
            'is_temporary', 'valid_from', 'valid_until',
            'assigned_by', 'assigned_by_email', 'assigned_at'
        ]
        read_only_fields = ['id', 'assigned_at']


class RoleSerializer(serializers.ModelSerializer):
    """Serializer para roles"""
    permissions_count = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()
    parent_role_name = serializers.CharField(source='parent_role.name', read_only=True)
    role_type_display = serializers.CharField(source='get_role_type_display', read_only=True)
    permissions = GranularPermissionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'code', 'description', 'role_type', 'role_type_display',
            'is_active', 'is_super_admin', 'auto_assign_to_new_users',
            'parent_role', 'parent_role_name', 'permissions_count', 'users_count',
            'permissions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_permissions_count(self, obj):
        return obj.permissions.count()
    
    def get_users_count(self, obj):
        return obj.user_assignments.count()
    
    def validate_code(self, value):
        """Validar que el código del rol sea único"""
        if Role.objects.filter(code=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("Ya existe un rol con este código")
        return value


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer para asignación de roles a usuarios"""
    role_detail = RoleSerializer(source='role', read_only=True)
    user_detail = CustomUserSerializer(source='user', read_only=True)  # ✅ SERIALIZER REAL
    assigned_by_email = serializers.CharField(source='assigned_by.email', read_only=True)
    department_detail = DepartmentSerializer(source='department', read_only=True)  # ✅ SERIALIZER REAL
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserRole
        fields = [
            'id', 'user', 'user_detail', 'role', 'role_detail',
            'department', 'department_detail', 'is_temporary',  # ✅ REFERENCIA CORRECTA
            'valid_from', 'valid_until', 'is_active',
            'assigned_by', 'assigned_by_email', 'assigned_at', 'notes'
        ]
        read_only_fields = ['id', 'assigned_at', 'is_active']


class TemplateRoleSerializer(serializers.ModelSerializer):
    """Serializer para roles en plantillas"""
    role_detail = RoleSerializer(source='role', read_only=True)
    
    class Meta:
        model = TemplateRole
        fields = [
            'id', 'template', 'role', 'role_detail',
            'is_required', 'is_temporary', 'valid_days', 'order'
        ]
        read_only_fields = ['id']


class RoleTemplateSerializer(serializers.ModelSerializer):
    """Serializer para plantillas de roles"""
    roles_count = serializers.SerializerMethodField()
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    template_roles = TemplateRoleSerializer(many=True, read_only=True)
    
    class Meta:
        model = RoleTemplate
        fields = [
            'id', 'name', 'template_type', 'template_type_display',
            'description', 'is_active', 'roles_count', 'template_roles',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_roles_count(self, obj):
        return obj.roles.count()


# Serializers para operaciones específicas
class AssignPermissionsToRoleSerializer(serializers.Serializer):
    """Serializer para asignar múltiples permisos a un rol"""
    permission_codes = serializers.ListField(
        child=serializers.CharField(max_length=100),
        help_text="Lista de códigos de permisos a asignar"
    )
    assigned_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUserSerializer.Meta.model.objects.all(),
        required=False
    )


class AssignRoleToUserSerializer(serializers.Serializer):
    """Serializer para asignar un rol a un usuario"""
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUserSerializer.Meta.model.objects.all()
    )
    role_id = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=DepartmentSerializer.Meta.model.objects.all(),  # ✅ REFERENCIA CORRECTA
        required=False, 
        allow_null=True
    )
    is_temporary = serializers.BooleanField(default=False)
    valid_days = serializers.IntegerField(required=False, min_value=1, max_value=365)
    notes = serializers.CharField(required=False, allow_blank=True)


class UserPermissionsSerializer(serializers.Serializer):
    """Serializer para obtener permisos de un usuario"""
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUserSerializer.Meta.model.objects.all()
    )
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=DepartmentSerializer.Meta.model.objects.all(),  # ✅ REFERENCIA CORRECTA
        required=False, 
        allow_null=True
    )


class CheckPermissionSerializer(serializers.Serializer):
    """Serializer para verificar si un usuario tiene un permiso"""
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUserSerializer.Meta.model.objects.all()
    )
    permission_code = serializers.CharField(max_length=100)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=DepartmentSerializer.Meta.model.objects.all(),  # ✅ REFERENCIA CORRECTA
        required=False, 
        allow_null=True
    )