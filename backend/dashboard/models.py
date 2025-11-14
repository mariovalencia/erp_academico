from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.conf import settings

User = get_user_model()

class DashboardWidget(models.Model):
    """Widgets disponibles para el dashboard"""
    
    WIDGET_TYPES = (
        ('notifications_stats', 'Estadísticas de Notificaciones'),
        ('recent_activity', 'Actividad Reciente'),
        ('user_stats', 'Estadísticas de Usuario'),
        ('system_health', 'Salud del Sistema'),
        ('quick_actions', 'Acciones Rápidas'),
        ('recent_notifications', 'Notificaciones Recientes'),
    )
    
    SIZE_CHOICES = (
        ('small', 'Pequeño (1x1)'),
        ('medium', 'Mediano (2x1)'),
        ('large', 'Grande (2x2)'),
        ('xlarge', 'Extra Grande (3x2)'),
    )
    
    name = models.CharField(_("Nombre"), max_length=255)
    code = models.CharField(_("Código único"), max_length=100, unique=True)
    description = models.TextField(_("Descripción"), blank=True)
    widget_type = models.CharField(_("Tipo de Widget"), max_length=50, choices=WIDGET_TYPES)
    component_name = models.CharField(_("Componente Angular"), max_length=255, help_text="Nombre del componente Angular para este widget")
    data_endpoint = models.CharField(_("Endpoint de datos"), max_length=255, help_text="URL para obtener datos del widget")
    default_config = models.JSONField(_("Configuración por defecto"), default=dict)
    default_size = models.CharField(_("Tamaño por defecto"), max_length=20, choices=SIZE_CHOICES, default='medium')
    is_active = models.BooleanField(_("Activo"), default=True)
    
    # ✅ CORREGIDO: Usar GranularPermission de tu core
    required_permissions = models.ManyToManyField(
        'core_permissions.GranularPermission',  # Tu modelo personalizado
        blank=True,
        verbose_name=_("Permisos requeridos"),
        help_text=_("Permisos necesarios para ver este widget")
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_widget'
        verbose_name = _('Widget de Dashboard')
        verbose_name_plural = _('Widgets de Dashboard')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_widget_type_display()})"

class UserDashboard(models.Model):
    """Configuración de dashboard por usuario"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='dashboard_config',
        verbose_name=_("Usuario")
    )
    
    layout = models.JSONField(
        _("Layout"),
        default=dict,
        help_text=_("Configuración del layout en formato Gridster")
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_user_dashboard'
        verbose_name = _('Dashboard de Usuario')
        verbose_name_plural = _('Dashboards de Usuario')
    
    def __str__(self):
        return f"Dashboard de {self.user.email}"

class UserWidget(models.Model):
    """Widgets asignados a un usuario específico"""
    
    user_dashboard = models.ForeignKey(
        UserDashboard, 
        on_delete=models.CASCADE, 
        related_name='widgets',
        verbose_name=_("Dashboard de usuario")
    )
    
    widget = models.ForeignKey(
        DashboardWidget, 
        on_delete=models.CASCADE,
        verbose_name=_("Widget")
    )
    
    position = models.JSONField(
        _("Posición y tamaño"),
        default=dict,
        help_text=_("Posición en el grid: {x, y, cols, rows}")
    )
    
    config = models.JSONField(
        _("Configuración específica"),
        default=dict,
        help_text=_("Configuración personalizada para este widget")
    )
    
    is_visible = models.BooleanField(_("Visible"), default=True)
    refresh_interval = models.IntegerField(_("Intervalo de actualización (segundos)"), default=300)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_user_widget'
        verbose_name = _('Widget de Usuario')
        verbose_name_plural = _('Widgets de Usuario')
        unique_together = ['user_dashboard', 'widget']
        ordering = ['position']
    
    def __str__(self):
        return f"{self.widget.name} - {self.user_dashboard.user.email}"

class DashboardPreset(models.Model):
    """Presets de dashboard para diferentes roles"""
    
    name = models.CharField(_("Nombre"), max_length=255)
    code = models.CharField(_("Código único"), max_length=100, unique=True)
    description = models.TextField(_("Descripción"), blank=True)
    is_default = models.BooleanField(_("Preset por defecto"), default=False)
    widgets = models.ManyToManyField(
        DashboardWidget,
        through='PresetWidget',
        verbose_name=_("Widgets")
    )
    
    # ✅ CORREGIDO: Usar Role de tu core
    required_role = models.ForeignKey(
        'core_permissions.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Rol requerido")
    )
    
    class Meta:
        db_table = 'dashboard_preset'
        verbose_name = _('Preset de Dashboard')
        verbose_name_plural = _('Presets de Dashboard')
    
    def __str__(self):
        return self.name

class PresetWidget(models.Model):
    """Widgets incluidos en un preset"""
    
    preset = models.ForeignKey(DashboardPreset, on_delete=models.CASCADE)
    widget = models.ForeignKey(DashboardWidget, on_delete=models.CASCADE)
    position = models.JSONField(default=dict)
    config = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'dashboard_preset_widget'
        unique_together = ['preset', 'widget']