# notifications/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import NotificationChannel, NotificationTemplate, Notification, NotificationDelivery, UserNotificationPreference

@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel_type', 'code', 'is_active']
    list_filter = ['channel_type', 'is_active']
    search_fields = ['name', 'code']
    # REMOVER: readonly_fields = ['created_at'] - NotificationChannel no tiene created_at

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'channels']
    search_fields = ['name', 'code', 'description']
    filter_horizontal = ['channels']
    readonly_fields = ['created_at', 'updated_at']  # ✅ Este SÍ tiene created_at
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Contenido', {
            'fields': ('subject', 'body', 'body_html')
        }),
        ('Configuración', {
            'fields': ('channels', 'context_variables')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'template', 'status_badge', 'created_at', 'sent_at', 'read_at']
    list_filter = ['status', 'template', 'created_at']
    search_fields = ['user__email', 'template__name']
    readonly_fields = ['created_at', 'updated_at', 'delivery_attempts']  # ✅ Este SÍ tiene created_at
    date_hierarchy = 'created_at'
    
    def status_badge(self, obj):
        status_colors = {
            'pending': 'blue',
            'sent': 'green', 
            'delivered': 'green',
            'read': 'purple',
            'failed': 'red',
            'cancelled': 'orange'
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ['notification', 'channel', 'status', 'sent_at']
    list_filter = ['channel', 'status', 'sent_at']
    search_fields = ['notification__user__email', 'external_id']
    readonly_fields = ['sent_at']  # ✅ Correcto

@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'template', 'channel', 'is_enabled']
    list_filter = ['is_enabled', 'channel', 'template']
    search_fields = ['user__email', 'template__name']
    # ✅ No necesita readonly_fields