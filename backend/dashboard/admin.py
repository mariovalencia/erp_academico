from django.contrib import admin
from .models import DashboardWidget, UserDashboard, UserWidget, DashboardPreset, PresetWidget

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'widget_type', 'default_size', 'is_active']
    list_filter = ['widget_type', 'is_active', 'default_size']
    search_fields = ['name', 'code', 'description']
    filter_horizontal = ['required_permissions']  # ✅ Ahora funciona con GranularPermission
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserDashboard)
class UserDashboardAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserWidget)
class UserWidgetAdmin(admin.ModelAdmin):
    list_display = ['user_dashboard', 'widget', 'is_visible', 'refresh_interval']
    list_filter = ['is_visible', 'widget__widget_type']
    search_fields = ['user_dashboard__user__email', 'widget__name']

@admin.register(DashboardPreset)
class DashboardPresetAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_default', 'required_role']
    list_filter = ['is_default']
    search_fields = ['name', 'code', 'description']

admin.site.register(PresetWidget)