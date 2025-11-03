from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Q
from django.contrib import messages
from .models import AuditLog, SecurityEvent, SystemChange, AuditConfiguration
from django.utils import timezone
import json
from datetime import timedelta

# ========== FILTROS PERSONALIZADOS ==========

class SeverityFilter(admin.SimpleListFilter):
    title = _('severity level')
    parameter_name = 'severity'

    def lookups(self, request, model_admin):
        return [
            ('high_critical', _('High & Critical')),
            ('medium', _('Medium')),
            ('low_info', _('Low & Info')),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'high_critical':
            return queryset.filter(severity__in=['high', 'critical'])
        elif self.value() == 'medium':
            return queryset.filter(severity='medium')
        elif self.value() == 'low_info':
            return queryset.filter(severity__in=['low', 'info'])
        return queryset

class TimeRangeFilter(admin.SimpleListFilter):
    title = _('time range')
    parameter_name = 'time_range'

    def lookups(self, request, model_admin):
        return [
            ('today', _('Today')),
            ('last_7_days', _('Last 7 days')),
            ('last_30_days', _('Last 30 days')),
            ('last_90_days', _('Last 90 days')),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            return queryset.filter(timestamp__date=now.date())
        elif self.value() == 'last_7_days':
            return queryset.filter(timestamp__gte=now - timedelta(days=7))
        elif self.value() == 'last_30_days':
            return queryset.filter(timestamp__gte=now - timedelta(days=30))
        elif self.value() == 'last_90_days':
            return queryset.filter(timestamp__gte=now - timedelta(days=90))
        return queryset

# ========== INLINES ==========

class SecurityEventInline(admin.TabularInline):
    model = SecurityEvent.related_audit_logs.through
    extra = 0
    verbose_name = _('Related Security Event')
    verbose_name_plural = _('Related Security Events')
    can_delete = False
    readonly_fields = ['security_event_link']

    def security_event_link(self, instance):
        if instance.securityevent:
            url = f'/admin/core_audit/securityevent/{instance.securityevent.id}/change/'
            return format_html('<a href="{}">{}</a>', url, instance.securityevent)
        return '-'
    security_event_link.short_description = _('Security Event')

# ========== MODEL ADMINS ==========

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'action_type_display', 'user_display', 
        'ip_address', 'severity_badge', 'is_success_badge', 'duration_display'
    ]
    list_filter = [
        'action_category', 'action_type', SeverityFilter, 
        'is_success', TimeRangeFilter, 'user_department'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'description', 'ip_address', 'correlation_id'
    ]
    readonly_fields = [
        'id', 'correlation_id', 'timestamp', 'created_at', 'updated_at',
        'user_info', 'request_info', 'data_changes', 'related_events'
    ]
    list_per_page = 50
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'id', 'correlation_id', 'timestamp', 'duration_display'
            )
        }),
        (_('Action Details'), {
            'fields': (
                'action_category', 'action_type', 'severity_badge', 
                'is_success_badge', 'description'
            )
        }),
        (_('User Information'), {
            'fields': ('user_info',)
        }),
        (_('Request Information'), {
            'fields': ('request_info',)
        }),
        (_('Data Changes'), {
            'fields': ('data_changes',),
            'classes': ('collapse',)
        }),
        (_('Related Events'), {
            'fields': ('related_events',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def action_type_display(self, obj):
        return obj.get_action_type_display()
    action_type_display.short_description = _('Action Type')

    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.email} ({obj.user.get_full_name()})"
        return _('System')
    user_display.short_description = _('User')

    def severity_badge(self, obj):
        colors = {
            'critical': 'red', 'high': 'orange', 'medium': 'yellow',
            'low': 'green', 'info': 'blue', 'debug': 'gray'
        }
        color = colors.get(obj.severity, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_badge.short_description = _('Severity')

    def is_success_badge(self, obj):
        if obj.is_success:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">✓</span>'
            )
        else:
            return format_html(
                '<span style="background-color: red; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">✗</span>'
            )
    is_success_badge.short_description = _('Success')

    def duration_display(self, obj):
        if obj.duration_ms:
            return f"{obj.duration_ms}ms"
        return '-'
    duration_display.short_description = _('Duration')

    def user_info(self, obj):
        info = []
        if obj.user:
            info.append(f"<strong>User:</strong> {obj.user.email}")
            if obj.user.get_full_name():
                info.append(f"<strong>Name:</strong> {obj.user.get_full_name()}")
        if obj.user_department:
            info.append(f"<strong>Department:</strong> {obj.user_department.name}")
        if obj.ip_address:
            info.append(f"<strong>IP:</strong> {obj.ip_address}")
        return format_html('<br>'.join(info))
    user_info.short_description = _('User Information')

    def request_info(self, obj):
        info = []
        if obj.request_path:
            info.append(f"<strong>Path:</strong> {obj.request_path}")
        if obj.request_method:
            info.append(f"<strong>Method:</strong> {obj.request_method}")
        if obj.user_agent:
            # Acortar user agent si es muy largo
            ua = obj.user_agent[:100] + '...' if len(obj.user_agent) > 100 else obj.user_agent
            info.append(f"<strong>User Agent:</strong> {ua}")
        return format_html('<br>'.join(info)) if info else '-'
    request_info.short_description = _('Request Information')

    def data_changes(self, obj):
        changes = []
        if obj.old_values:
            changes.append(f"<strong>Old Values:</strong><pre>{json.dumps(obj.old_values, indent=2)}</pre>")
        if obj.new_values:
            changes.append(f"<strong>New Values:</strong><pre>{json.dumps(obj.new_values, indent=2)}</pre>")
        if obj.changed_fields:
            changes.append(f"<strong>Changed Fields:</strong> {', '.join(obj.changed_fields)}")
        return format_html('<br>'.join(changes)) if changes else _('No data changes')
    data_changes.short_description = _('Data Changes')

    def related_events(self, obj):
        events = obj.security_events.all()
        if events:
            links = []
            for event in events:
                url = f'/admin/core_audit/securityevent/{event.id}/change/'
                links.append(f'<a href="{url}">{event}</a>')
            return format_html('<br>'.join(links))
        return '-'
    related_events.short_description = _('Related Security Events')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    # 🔥 CORRECCIÓN: Incluir los campos reales en list_display para poder editarlos
    list_display = [
        'event_type_display', 'title', 'user_display', 'severity', 'priority', 'status',
        'detected_at', 'occurrence_count'
    ]
    list_filter = [
        'event_type', 'severity', 'priority', 'status', 'detected_at'
    ]
    search_fields = [
        'title', 'description', 'user__email', 'user__first_name', 
        'user__last_name', 'event_id'
    ]
    readonly_fields = [
        'event_id', 'detected_at', 'first_occurrence', 'last_occurrence',
        'occurrence_count', 'evidence_display', 'investigation_timeline',
        'related_logs_display'
    ]
    # 🔥 CORRECCIÓN: Ahora status y priority están en list_display
    list_editable = ['status', 'priority']
    actions = ['mark_as_investigating', 'mark_as_resolved', 'mark_as_false_positive']
    date_hierarchy = 'detected_at'
    
    fieldsets = (
        (_('Event Information'), {
            'fields': (
                'event_id', 'event_type', 'title', 'description',
                'severity', 'priority', 'status'
            )
        }),
        (_('User Context'), {
            'fields': ('user', 'user_department')
        }),
        (_('Timeline'), {
            'fields': (
                'detected_at', 'first_occurrence', 'last_occurrence',
                'resolved_at', 'closed_at', 'occurrence_count'
            )
        }),
        (_('Evidence'), {
            'fields': ('evidence_display', 'related_logs_display'),
            'classes': ('collapse',)
        }),
        (_('Investigation'), {
            'fields': ('assigned_to', 'investigation_notes', 'investigation_timeline'),
            'classes': ('collapse',)
        }),
        (_('Resolution'), {
            'fields': ('resolution_notes', 'resolution_code'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def event_type_display(self, obj):
        return obj.get_event_type_display()
    event_type_display.short_description = _('Event Type')

    def user_display(self, obj):
        if obj.user:
            return obj.user.email
        return _('Unknown')
    user_display.short_description = _('User')

    def evidence_display(self, obj):
        if obj.evidence_data:
            return format_html('<pre>{}</pre>', json.dumps(obj.evidence_data, indent=2))
        return _('No evidence data')
    evidence_display.short_description = _('Evidence Data')

    def related_logs_display(self, obj):
        logs = obj.related_audit_logs.all()[:10]  # Limitar a 10 logs
        if logs:
            log_links = []
            for log in logs:
                url = f'/admin/core_audit/auditlog/{log.id}/change/'
                log_links.append(f'<a href="{url}">{log.timestamp} - {log.get_action_type_display()}</a>')
            return format_html('<br>'.join(log_links))
        return _('No related audit logs')
    related_logs_display.short_description = _('Related Audit Logs')

    def investigation_timeline(self, obj):
        if obj.investigation_notes:
            timeline = []
            for note in obj.investigation_notes:
                timeline.append(f"<strong>{note.get('timestamp', '')}:</strong> {note.get('note', '')}")
            return format_html('<br>'.join(timeline))
        return _('No investigation notes')
    investigation_timeline.short_description = _('Investigation Timeline')

    # Actions
    def mark_as_investigating(self, request, queryset):
        updated = queryset.update(status='investigating', assigned_to=request.user)
        self.message_user(request, f'{updated} events marked as under investigation.')
    mark_as_investigating.short_description = _('Mark selected events as under investigation')

    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(
            status='resolved', 
            resolved_at=timezone.now(),
            assigned_to=request.user
        )
        self.message_user(request, f'{updated} events marked as resolved.')
    mark_as_resolved.short_description = _('Mark selected events as resolved')

    def mark_as_false_positive(self, request, queryset):
        updated = queryset.update(
            status='false_positive',
            resolution_code='false_positive',
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{updated} events marked as false positives.')
    mark_as_false_positive.short_description = _('Mark selected events as false positives')

@admin.register(SystemChange)
class SystemChangeAdmin(admin.ModelAdmin):
    list_display = [
        'change_type_display', 'title', 'changed_by_display', 
        'impact_level', 'requires_approval', 'is_reverted', 
        'changed_at'
    ]
    list_filter = ['change_type', 'impact_level', 'requires_approval', 'is_reverted']
    search_fields = ['title', 'description', 'changed_by__email']
    readonly_fields = [
        'changed_at', 'configuration_changes', 'approval_status', 
        'reversion_status'
    ]
    raw_id_fields = ['changed_by', 'approved_by', 'reverted_by']
    date_hierarchy = 'changed_at'
    
    fieldsets = (
        (_('Change Information'), {
            'fields': (
                'change_type', 'title', 'description', 'change_summary'
            )
        }),
        (_('Impact Analysis'), {
            'fields': (
                'impact_level', 'affected_users', 'rollback_plan'
            )
        }),
        (_('Configuration Changes'), {
            'fields': ('configuration_changes',),
            'classes': ('collapse',)
        }),
        (_('Approval Process'), {
            'fields': (
                'requires_approval', 'approved_by', 'approved_at', 'approval_notes'
            )
        }),
        (_('Reversion'), {
            'fields': (
                'can_be_reverted', 'is_reverted', 'reverted_by', 
                'reverted_at', 'revert_reason'
            )
        }),
        (_('Scheduling'), {
            'fields': ('scheduled_for', 'is_emergency_change'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('changed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def change_type_display(self, obj):
        return obj.get_change_type_display()
    change_type_display.short_description = _('Change Type')

    def changed_by_display(self, obj):
        return obj.changed_by.email
    changed_by_display.short_description = _('Changed By')

    def configuration_changes(self, obj):
        changes = []
        if obj.old_configuration:
            changes.append(f"<strong>Old Configuration:</strong><pre>{json.dumps(obj.old_configuration, indent=2)}</pre>")
        if obj.new_configuration:
            changes.append(f"<strong>New Configuration:</strong><pre>{json.dumps(obj.new_configuration, indent=2)}</pre>")
        return format_html('<br>'.join(changes)) if changes else _('No configuration changes')
    configuration_changes.short_description = _('Configuration Changes')

    def approval_status(self, obj):
        if obj.requires_approval:
            if obj.approved_by:
                return f"Approved by {obj.approved_by.email} on {obj.approved_at}"
            else:
                return "Pending approval"
        return "Not required"
    approval_status.short_description = _('Approval Status')

    def reversion_status(self, obj):
        if obj.is_reverted:
            return f"Reverted by {obj.reverted_by.email} on {obj.reverted_at}"
        elif obj.can_be_reverted:
            return "Can be reverted"
        return "Cannot be reverted"
    reversion_status.short_description = _('Reversion Status')

@admin.register(AuditConfiguration)
class AuditConfigurationAdmin(admin.ModelAdmin):
    list_display = ['is_active', 'audit_log_retention_days', 'updated_at']
    readonly_fields = ['updated_at', 'updated_by', 'configuration_summary']
    
    fieldsets = (
        (_('Retention Settings'), {
            'fields': (
                'audit_log_retention_days',
                'security_event_retention_days', 
                'system_change_retention_days'
            )
        }),
        (_('Event Auditing'), {
            'fields': (
                'enable_login_auditing',
                'enable_data_access_auditing',
                'enable_permission_changes_auditing',
                'enable_api_auditing',
                'enable_business_process_auditing'
            )
        }),
        (_('Security Alerts'), {
            'fields': (
                'enable_security_alerts',
                'failed_login_threshold',
                'failed_login_timeframe_minutes',
                'alert_email_recipients'
            )
        }),
        (_('Archiving'), {
            'fields': (
                'enable_auto_archiving',
                'archive_after_days',
                'enable_compression'
            )
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Summary'), {
            'fields': ('configuration_summary',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def configuration_summary(self, obj):
        summary = []
        summary.append(f"<strong>Audit Log Retention:</strong> {obj.get_audit_log_retention_days_display()}")
        summary.append(f"<strong>Security Events Retention:</strong> {obj.get_security_event_retention_days_display()}")
        summary.append(f"<strong>Active Auditing Categories:</strong> {self.get_active_categories(obj)}")
        summary.append(f"<strong>Security Alerts:</strong> {'Enabled' if obj.enable_security_alerts else 'Disabled'}")
        return format_html('<br>'.join(summary))
    configuration_summary.short_description = _('Configuration Summary')

    def get_active_categories(self, obj):
        categories = []
        if obj.enable_login_auditing: categories.append('Login')
        if obj.enable_data_access_auditing: categories.append('Data Access')
        if obj.enable_permission_changes_auditing: categories.append('Permissions')
        if obj.enable_api_auditing: categories.append('API')
        if obj.enable_business_process_auditing: categories.append('Business')
        return ', '.join(categories) if categories else 'None'

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        # Solo permitir una configuración
        return not AuditConfiguration.objects.filter(is_active=True).exists()