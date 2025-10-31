from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django import forms
from .models import (
    PermissionModule, GranularPermission, Role, 
    RolePermission, UserRole, RoleTemplate, TemplateRole
)

# ========== INLINES ==========

class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1
    fields = ['permission', 'department_filter', 'is_temporary', 'valid_from', 'valid_until']
    raw_id_fields = ['permission', 'department_filter']
    autocomplete_fields = ['permission']

class TemplateRoleInline(admin.TabularInline):
    model = TemplateRole
    extra = 1
    fields = ['role', 'is_required', 'is_temporary', 'valid_days', 'order']
    raw_id_fields = ['role']
    autocomplete_fields = ['role']

# ========== MODEL ADMINS ==========

@admin.register(PermissionModule)
class PermissionModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'order', 'permissions_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    list_editable = ['is_active', 'order']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['order', 'name']
    
    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = _('Permissions')

@admin.register(GranularPermission)
class GranularPermissionAdmin(admin.ModelAdmin):
    list_display = [
        'permission_code', 'module', 'functionality', 
        'action', 'scope', 'is_dangerous', 'requires_approval', 'created_at'
    ]
    list_filter = [
        'module', 'action', 'scope', 'is_dangerous', 
        'requires_approval', 'created_at'
    ]
    search_fields = [
        'permission_code', 'name', 'functionality', 
        'functionality_code', 'description'
    ]
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['module']
    list_per_page = 50
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'module', 'functionality', 'functionality_code',
                'action', 'scope', 'permission_code'
            )
        }),
        (_('Details'), {
            'fields': (
                'name', 'description'
            )
        }),
        (_('Security'), {
            'fields': (
                'is_dangerous', 'requires_approval'
            ),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'role_type', 'is_active', 
        'is_super_admin', 'parent_role', 'permissions_count', 'created_at'
    ]
    list_filter = ['role_type', 'is_active', 'is_super_admin', 'created_at']
    search_fields = ['name', 'code', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['parent_role']
    inlines = [RolePermissionInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name', 'code', 'role_type', 'description'
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active', 'is_super_admin', 'auto_assign_to_new_users'
            )
        }),
        (_('Hierarchy'), {
            'fields': ('parent_role',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = _('Permissions')

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = [
        'role', 'permission', 'department_filter', 
        'is_temporary', 'assigned_at'
    ]
    list_filter = [
        'role', 'is_temporary', 'assigned_at'
    ]
    search_fields = [
        'role__name', 'permission__permission_code',
        'department_filter__name'
    ]
    readonly_fields = ['assigned_at']
    raw_id_fields = ['role', 'permission', 'department_filter', 'assigned_by']
    list_select_related = ['role', 'permission', 'department_filter']
    
    fieldsets = (
        (_('Assignment'), {
            'fields': (
                'role', 'permission'
            )
        }),
        (_('Scope'), {
            'fields': ('department_filter',)
        }),
        (_('Temporal Settings'), {
            'fields': (
                'is_temporary', 'valid_from', 'valid_until'
            ),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('assigned_at', 'assigned_by'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'role', 'department', 'is_temporary', 
        'is_active', 'assigned_at'
    ]
    list_filter = [
        'role', 'department', 'is_temporary', 'assigned_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'role__name', 'department__name'
    ]
    readonly_fields = ['assigned_at']
    raw_id_fields = ['user', 'role', 'department', 'assigned_by']
    list_select_related = ['user', 'role', 'department']
    list_per_page = 50
    
    fieldsets = (
        (_('Assignment'), {
            'fields': (
                'user', 'role', 'department'
            )
        }),
        (_('Temporal Settings'), {
            'fields': (
                'is_temporary', 'valid_from', 'valid_until'
            ),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('assigned_at', 'assigned_by', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = _('Active')

@admin.register(RoleTemplate)
class RoleTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type', 'is_active', 'roles_count', 'created_at'
    ]
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [TemplateRoleInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name', 'template_type', 'description', 'is_active'
            )
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def roles_count(self, obj):
        return obj.roles.count()
    roles_count.short_description = _('Roles')

@admin.register(TemplateRole)
class TemplateRoleAdmin(admin.ModelAdmin):
    list_display = [
        'template', 'role', 'is_required', 'is_temporary', 
        'valid_days', 'order'
    ]
    list_filter = ['template', 'is_required', 'is_temporary']
    list_editable = ['is_required', 'is_temporary', 'valid_days', 'order']
    raw_id_fields = ['template', 'role']
    ordering = ['template', 'order']
    list_select_related = ['template', 'role']
    
    fieldsets = (
        (_('Assignment'), {
            'fields': (
                'template', 'role'
            )
        }),
        (_('Settings'), {
            'fields': (
                'is_required', 'is_temporary', 'valid_days', 'order'
            )
        }),
    )