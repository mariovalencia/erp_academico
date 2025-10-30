from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from core_users.models import CustomUser
from core_users.models import CustomUser
from core_organization.models import Department, Location


class PermissionModule(models.Model):
    """
    Módulo principal del sistema (Ej: Académico, Financiero, etc.)
    """
    name = models.CharField(_('module name'), max_length=100, unique=True)
    code = models.CharField(_('module code'), max_length=50, unique=True)
    description = models.TextField(_('description'), blank=True)
    icon = models.CharField(_('icon'), max_length=50, blank=True, help_text=_('Icono para la UI'))
    is_active = models.BooleanField(_('active'), default=True)
    order = models.PositiveIntegerField(_('order'), default=0)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'core_permission_modules'
        verbose_name = _('permission module')
        verbose_name_plural = _('permission modules')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class GranularPermission(models.Model):
    """
    Permiso granular unificado - Combina módulo, funcionalidad, acción y alcance
    """
    # Nivel 1: Módulo
    module = models.ForeignKey(
        PermissionModule, 
        on_delete=models.CASCADE,
        related_name='permissions'
    )
    
    # Nivel 2: Funcionalidad
    functionality = models.CharField(_('functionality'), max_length=100)
    functionality_code = models.CharField(_('functionality code'), max_length=50)
    
    # Nivel 3: Acción
    ACTION_CHOICES = [
        ('view', _('View')),
        ('create', _('Create')),
        ('edit', _('Edit')),
        ('delete', _('Delete')),
        ('export', _('Export')),
        ('import', _('Import')),
        ('approve', _('Approve')),
        ('reject', _('Reject')),
        ('manage', _('Manage')),
    ]
    action = models.CharField(_('action'), max_length=20, choices=ACTION_CHOICES)
    
    # Nivel 4: Alcance
    SCOPE_CHOICES = [
        ('all', _('All')),
        ('department', _('My Department')),
        ('own', _('Own Only')),
        ('custom', _('Custom')),
    ]
    scope = models.CharField(_('scope'), max_length=20, choices=SCOPE_CHOICES)
    
    # Campos adicionales
    name = models.CharField(_('permission name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    is_dangerous = models.BooleanField(_('dangerous action'), default=False)
    requires_approval = models.BooleanField(_('requires approval'), default=False)
    
    # Código único para el permiso (para búsquedas rápidas)
    permission_code = models.CharField(
        _('permission code'), 
        max_length=100, 
        unique=True,
        help_text=_('Formato: module.functionality.action.scope')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'core_granular_permissions'
        verbose_name = _('granular permission')
        verbose_name_plural = _('granular permissions')
        ordering = ['module', 'functionality', 'action']
        # Índices para mejor performance
        indexes = [
            models.Index(fields=['module', 'functionality']),
            models.Index(fields=['permission_code']),
        ]

    def __str__(self):
        return self.name
    
    def clean(self):
        """
        Validaciones robustas del modelo
        """
        errors = {}
        
        # 1. Validar formato del functionality_code (solo letras, números y underscores)
        import re
        if self.functionality_code and not re.match(r'^[a-z][a-z0-9_]*$', self.functionality_code):
            errors['functionality_code'] = _(
                'Solo letras minúsculas, números y underscores. Debe empezar con letra.'
            )
        
        # 2. Validar que action y scope sean válidos
        valid_actions = dict(self.ACTION_CHOICES).keys()
        valid_scopes = dict(self.SCOPE_CHOICES).keys()
        
        if self.action not in valid_actions:
            errors['action'] = _('Acción no válida')
        
        if self.scope not in valid_scopes:
            errors['scope'] = _('Alcance no válido')
        
        # 3. Validar permisos peligrosos
        dangerous_actions = ['delete', 'approve', 'reject']
        if self.action in dangerous_actions and not self.is_dangerous:
            print(f"⚠️ Advertencia: La acción '{self.get_action_display()}' debería marcarse como peligrosa")
        
        # 4. Validar permisos que requieren aprobación
        if self.requires_approval and self.scope == 'own':
            errors['requires_approval'] = _(
                'Los permisos de alcance "Solo Míos" no pueden requerir aprobación'
            )
        
        # 5. Validar consistencia del permission_code
        if all([self.module, self.functionality_code, self.action, self.scope]):
            expected_code = f"{self.module.code}.{self.functionality_code}.{self.action}.{self.scope}"
            if self.permission_code and self.permission_code != expected_code:
                errors['permission_code'] = _(
                    f'El código debe ser: {expected_code}'
                )
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Save sobreescrito con generación automática de campos
        """
        # Generar automáticamente el código del permiso PRIMERO
        if self.module and self.functionality_code and self.action and self.scope:
            self.permission_code = f"{self.module.code}.{self.functionality_code}.{self.action}.{self.scope}"
        
        # Generar nombre automáticamente si no se proporciona
        if not self.name and self.module and self.functionality and self.action:
            self.name = f"{self.module.name} - {self.functionality} - {self.get_action_display()} - {self.get_scope_display()}"
        
        # Marcar automáticamente acciones peligrosas
        dangerous_actions = ['delete', 'approve', 'reject']
        if self.action in dangerous_actions:
            self.is_dangerous = True
        
        # Ahora ejecutar validaciones
        try:
            self.full_clean()
        except ValidationError as e:
            # Para creación masiva, ser más permisivo con las validaciones
            if 'name' in e.error_dict and 'cannot be blank' in str(e.error_dict['name']):
                # Si el nombre está vacío pero podemos generarlo, intentar de nuevo
                if not self.name and self.module and self.functionality and self.action:
                    self.name = f"{self.module.name} - {self.functionality} - {self.get_action_display()} - {self.get_scope_display()}"
                    self.full_clean()  # Validar nuevamente
            else:
                raise e
            
        super().save(*args, **kwargs)


class Role(models.Model):
    """
    Rol del sistema con permisos granulares
    """
    ROLE_TYPE_CHOICES = [
        ('system', _('System Role')),
        ('business', _('Business Role')),
        ('custom', _('Custom Role')),
    ]
    
    name = models.CharField(_('role name'), max_length=100, unique=True)
    code = models.CharField(_('role code'), max_length=50, unique=True)
    role_type = models.CharField(
        _('role type'), 
        max_length=20, 
        choices=ROLE_TYPE_CHOICES,
        default='business'
    )
    description = models.TextField(_('description'), blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    
    # Herencia de roles
    parent_role = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='child_roles'
    )
    
    # Permisos granulares asignados a este rol
    permissions = models.ManyToManyField(
        GranularPermission,
        through='RolePermission',
        related_name='roles',
        blank=True
    )
    
    # Metadatos
    is_super_admin = models.BooleanField(_('super admin role'), default=False)
    auto_assign_to_new_users = models.BooleanField(
        _('auto assign to new users'), 
        default=False
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'core_roles'
        verbose_name = _('role')
        verbose_name_plural = _('roles')
        ordering = ['role_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_role_type_display()})"
    
    def get_all_permissions(self):
        """
        Obtiene todos los permisos del rol, incluyendo herencia
        """
        permissions = set(self.permissions.all())
        
        # Incluir permisos del rol padre (herencia)
        if self.parent_role:
            permissions.update(self.parent_role.get_all_permissions())
            
        return permissions
    
    def has_permission(self, permission_code):
        """
        Verifica si el rol tiene un permiso específico
        """
        all_permissions = self.get_all_permissions()
        return any(perm.permission_code == permission_code for perm in all_permissions)


class RolePermission(models.Model):
    """
    Tabla intermedia para permisos de roles con metadatos adicionales
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(GranularPermission, on_delete=models.CASCADE)
    
    # Restricciones adicionales
    department_filter = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text=_('Aplicar permiso solo a este departamento')
    )
    
    # Permisos temporales
    is_temporary = models.BooleanField(_('temporary'), default=False)
    valid_from = models.DateTimeField(_('valid from'), null=True, blank=True)
    valid_until = models.DateTimeField(_('valid until'), null=True, blank=True)
    
    # Auditoría
    assigned_at = models.DateTimeField(_('assigned at'), auto_now_add=True)
    assigned_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='assigned_permissions'
    )

    class Meta:
        db_table = 'core_role_permissions'
        verbose_name = _('role permission')
        verbose_name_plural = _('role permissions')
        unique_together = ['role', 'permission', 'department_filter']


class UserRole(models.Model):
    """
    Asignación de roles a usuarios
    """
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='user_roles'
    )
    role = models.ForeignKey(
        Role, 
        on_delete=models.CASCADE, 
        related_name='user_assignments'
    )
    
    # Alcance específico del rol para este usuario
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text=_('Departamento específico para este rol')
    )
    
    # Rol temporal
    is_temporary = models.BooleanField(_('temporary'), default=False)
    valid_from = models.DateTimeField(_('valid from'), null=True, blank=True)
    valid_until = models.DateTimeField(_('valid until'), null=True, blank=True)
    
    # Auditoría
    assigned_at = models.DateTimeField(_('assigned at'), auto_now_add=True)
    assigned_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='assigned_roles'
    )
    notes = models.TextField(_('assignment notes'), blank=True)
    
    class Meta:
        db_table = 'core_user_roles'
        verbose_name = _('user role')
        verbose_name_plural = _('user roles')
        unique_together = ['user', 'role', 'department']
        indexes = [
            models.Index(fields=['user', 'role']),
            models.Index(fields=['valid_until']),  # Para limpieza de roles expirados
        ]

    def __str__(self):
        base = f"{self.user.email} - {self.role.name}"
        if self.department:
            return f"{base} ({self.department.name})"
        return base
    
    @property
    def is_active(self):
        """Verifica si el rol está activo (no expirado)"""
        if not self.is_temporary:
            return True
        
        from django.utils import timezone
        now = timezone.now()
        
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
            
        return True


class RoleTemplate(models.Model):
    """
    Plantillas predefinidas de roles para diferentes tipos de negocio
    """
    TEMPLATE_TYPE_CHOICES = [
        ('university', _('University')),
        ('hospital', _('Hospital')),
        ('ecommerce', _('E-commerce')),
        ('project', _('Project Management')),
        ('custom', _('Custom')),
    ]
    
    name = models.CharField(_('template name'), max_length=100)
    template_type = models.CharField(
        _('template type'), 
        max_length=20, 
        choices=TEMPLATE_TYPE_CHOICES
    )
    description = models.TextField(_('description'), blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    
    # Roles incluidos en esta plantilla
    roles = models.ManyToManyField(
        Role,
        through='TemplateRole',
        related_name='templates'
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'core_role_templates'
        verbose_name = _('role template')
        verbose_name_plural = _('role templates')
        ordering = ['template_type', 'name']
        unique_together = ['name', 'template_type']

    def __str__(self):
        return f"{self.get_template_type_display()} - {self.name}"
    
    def apply_to_user(self, user, assigned_by=None, department=None):
        """
        Aplica todos los roles de la plantilla a un usuario
        """
        for template_role in self.templaterole_set.all():
            UserRole.objects.get_or_create(
                user=user,
                role=template_role.role,
                department=department,
                assigned_by=assigned_by,
                defaults={
                    'is_temporary': template_role.is_temporary,
                    'valid_from': template_role.valid_from,
                    'valid_until': template_role.valid_until,
                }
            )


class TemplateRole(models.Model):
    """
    Tabla intermedia para roles en plantillas
    """
    template = models.ForeignKey(RoleTemplate, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    is_required = models.BooleanField(_('required'), default=True)
    is_temporary = models.BooleanField(_('temporary'), default=False)
    valid_days = models.PositiveIntegerField(
        _('valid days'), 
        null=True, 
        blank=True,
        help_text=_('Número de días que el rol será válido (solo para temporales)')
    )
    order = models.PositiveIntegerField(_('order'), default=0)
    
    class Meta:
        db_table = 'core_template_roles'
        verbose_name = _('template role')
        verbose_name_plural = _('template roles')
        ordering = ['template', 'order']
        unique_together = ['template', 'role']