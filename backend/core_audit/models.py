from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ValidationError
import uuid
from core_organization.models import Department

CustomUser = get_user_model()

class BaseAuditModel(models.Model):
    """
    Modelo base para auditoría con campos comunes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        abstract = True

class CustomJSONField(JSONField):
    """
    JSONField personalizado con validación mejorada
    """
    def __init__(self, *args, **kwargs):
        kwargs['encoder'] = DjangoJSONEncoder
        super().__init__(*args, **kwargs)
    
    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        # Validar que el JSON no sea demasiado grande (1MB máximo)
        if value and len(str(value)) > 1_000_000:
            raise ValidationError(_('JSON data too large (max 1MB)'))

class AuditLog(BaseAuditModel):
    """
    Registro centralizado de auditoría para todas las acciones del sistema
    """
    ACTION_CATEGORIES = [
        ('authentication', _('Authentication')),
        ('user_management', _('User Management')),
        ('permission_management', _('Permission Management')),
        ('data_access', _('Data Access')),
        ('data_modification', _('Data Modification')),
        ('system_config', _('System Configuration')),
        ('security', _('Security')),
        ('business', _('Business Process')),
        ('api', _('API Access')),
    ]

    ACTION_TYPES = [
        # Authentication
        ('login_success', _('Login Successful')),
        ('login_failed', _('Login Failed')),
        ('logout', _('Logout')),
        ('session_timeout', _('Session Timeout')),
        ('password_change', _('Password Changed')),
        ('password_reset', _('Password Reset')),
        ('2fa_enabled', _('2FA Enabled')),
        ('2fa_disabled', _('2FA Disabled')),
        ('2fa_verified', _('2FA Verified')),
        
        # User Management
        ('user_created', _('User Created')),
        ('user_updated', _('User Updated')),
        ('user_deleted', _('User Deleted')),
        ('user_activated', _('User Activated')),
        ('user_deactivated', _('User Deactivated')),
        ('profile_updated', _('Profile Updated')),
        
        # Permission Management
        ('role_created', _('Role Created')),
        ('role_updated', _('Role Updated')),
        ('role_deleted', _('Role Deleted')),
        ('permission_assigned', _('Permission Assigned')),
        ('permission_revoked', _('Permission Revoked')),
        ('user_role_assigned', _('User Role Assigned')),
        ('user_role_removed', _('User Role Removed')),
        ('permission_escalation', _('Permission Escalation')),
        
        # Data Access
        ('data_viewed', _('Data Viewed')),
        ('data_exported', _('Data Exported')),
        ('data_imported', _('Data Imported')),
        ('sensitive_data_accessed', _('Sensitive Data Accessed')),
        ('bulk_data_accessed', _('Bulk Data Accessed')),
        
        # Data Modification
        ('record_created', _('Record Created')),
        ('record_updated', _('Record Updated')),
        ('record_deleted', _('Record Deleted')),
        ('bulk_update', _('Bulk Update')),
        ('bulk_delete', _('Bulk Delete')),
        
        # System
        ('config_changed', _('Configuration Changed')),
        ('system_backup', _('System Backup')),
        ('system_restore', _('System Restore')),
        ('maintenance_mode', _('Maintenance Mode')),
        
        # API
        ('api_call', _('API Call')),
        ('api_rate_limit', _('API Rate Limit Exceeded')),
        ('api_authentication_failed', _('API Authentication Failed')),
    ]

    SEVERITY_LEVELS = [
        ('debug', _('Debug')),
        ('info', _('Info')),
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]

    # Información básica
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('user'),
        db_index=True
    )
    user_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('user department'),
        db_index=True
    )
    
    # Identificador único de correlación
    correlation_id = models.UUIDField(
        _('correlation ID'),
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text=_('ID para correlacionar eventos relacionados')
    )
    
    # Categorización
    action_category = models.CharField(
        _('action category'),
        max_length=50,
        choices=ACTION_CATEGORIES,
        db_index=True
    )
    action_type = models.CharField(
        _('action type'),
        max_length=50,
        choices=ACTION_TYPES,
        db_index=True
    )
    severity = models.CharField(
        _('severity level'),
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='info',
        db_index=True
    )
    
    # Descripción
    description = models.TextField(_('description'))
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True, db_index=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    
    # Contexto de la acción
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('content type'),
        db_index=True
    )
    object_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)  # Cambiado a CharField para mayor flexibilidad
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Datos de la acción
    old_values = CustomJSONField(_('old values'), null=True, blank=True)
    new_values = CustomJSONField(_('new values'), null=True, blank=True)
    changed_fields = CustomJSONField(_('changed fields'), null=True, blank=True)
    request_path = models.CharField(_('request path'), max_length=500, blank=True)
    request_method = models.CharField(_('request method'), max_length=10, blank=True)
    
    # Metadata
    is_success = models.BooleanField(_('successful'), default=True, db_index=True)
    error_message = models.TextField(_('error message'), blank=True)
    stack_trace = models.TextField(_('stack trace'), blank=True)
    session_key = models.CharField(_('session key'), max_length=40, blank=True, db_index=True)
    
    # Tiempo y performance
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True, db_index=True)
    duration_ms = models.PositiveIntegerField(_('duration milliseconds'), null=True, blank=True)
    
    # Retención
    is_archived = models.BooleanField(_('archived'), default=False, db_index=True)
    archive_date = models.DateTimeField(_('archive date'), null=True, blank=True)

    class Meta:
        db_table = 'core_audit_logs'
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'action_category']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action_type', 'is_success']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['content_type', 'object_id', 'timestamp']),
            models.Index(fields=['correlation_id']),
        ]

    def __str__(self):
        user_info = self.user.email if self.user else 'System'
        return f"{self.get_action_type_display()} - {user_info} - {self.timestamp}"

    def clean(self):
        """Validaciones adicionales"""
        errors = {}
        
        # Validar que duration_ms sea razonable
        if self.duration_ms and self.duration_ms > 300000:  # 5 minutos
            errors['duration_ms'] = _('Duration seems too long (max 5 minutes)')
        
        # Validar que IP sea válida si se proporciona
        if self.ip_address:
            import ipaddress
            try:
                ipaddress.ip_address(self.ip_address)
            except ValueError:
                errors['ip_address'] = _('Invalid IP address format')
        
        if errors:
            raise ValidationError(errors)

class SecurityEvent(BaseAuditModel):
    """
    Eventos de seguridad específicos que requieren atención
    """
    EVENT_TYPES = [
        ('multiple_failed_logins', _('Multiple Failed Logins')),
        ('suspicious_activity', _('Suspicious Activity')),
        ('unauthorized_access', _('Unauthorized Access Attempt')),
        ('data_breach_attempt', _('Data Breach Attempt')),
        ('privilege_escalation', _('Privilege Escalation Attempt')),
        ('malicious_activity', _('Malicious Activity Detected')),
        ('brute_force_attempt', _('Brute Force Attempt')),
        ('anomalous_behavior', _('Anomalous User Behavior')),
        ('data_exfiltration', _('Data Exfiltration Attempt')),
        ('account_takeover', _('Account Takeover Attempt')),
    ]

    STATUS_CHOICES = [
        ('new', _('New')),
        ('open', _('Open')),
        ('investigating', _('Under Investigation')),
        ('escalated', _('Escalated')),
        ('resolved', _('Resolved')),
        ('false_positive', _('False Positive')),
        ('closed', _('Closed')),
    ]

    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]

    # Identificación
    event_id = models.UUIDField(
        _('event ID'),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )
    event_type = models.CharField(
        _('event type'),
        max_length=50,
        choices=EVENT_TYPES,
        db_index=True
    )
    
    # Usuario y contexto
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_events',
        db_index=True
    )
    user_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('user department')
    )
    
    # Descripción y severidad
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    severity = models.CharField(
        _('severity level'),
        max_length=20,
        choices=AuditLog.SEVERITY_LEVELS,
        default='medium',
        db_index=True
    )
    priority = models.CharField(
        _('priority'),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        db_index=True
    )
    
    # Evidencia
    related_audit_logs = models.ManyToManyField(
        AuditLog,
        related_name='security_events',
        blank=True
    )
    evidence_data = CustomJSONField(_('evidence data'), default=dict)
    ip_addresses = CustomJSONField(_('IP addresses'), default=list)
    user_agents = CustomJSONField(_('user agents'), default=list)
    
    # Seguimiento
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True
    )
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_security_events'
    )
    
    # Notas y resolución
    investigation_notes = CustomJSONField(_('investigation notes'), default=list)
    resolution_notes = models.TextField(_('resolution notes'), blank=True)
    resolution_code = models.CharField(
        _('resolution code'),
        max_length=50,
        blank=True,
        choices=[
            ('benign', _('Benign Activity')),
            ('malicious', _('Malicious Activity')),
            ('misconfiguration', _('System Misconfiguration')),
            ('user_error', _('User Error')),
            ('other', _('Other')),
        ]
    )
    
    # Tiempos
    detected_at = models.DateTimeField(_('detected at'), auto_now_add=True, db_index=True)
    first_occurrence = models.DateTimeField(_('first occurrence'), null=True, blank=True)
    last_occurrence = models.DateTimeField(_('last occurrence'), null=True, blank=True)
    resolved_at = models.DateTimeField(_('resolved at'), null=True, blank=True, db_index=True)
    closed_at = models.DateTimeField(_('closed at'), null=True, blank=True)
    
    # Metadata
    occurrence_count = models.PositiveIntegerField(_('occurrence count'), default=1)
    is_auto_resolved = models.BooleanField(_('auto resolved'), default=False)

    class Meta:
        db_table = 'core_security_events'
        verbose_name = _('security event')
        verbose_name_plural = _('security events')
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['event_type', 'status']),
            models.Index(fields=['severity', 'priority']),
            models.Index(fields=['detected_at', 'resolved_at']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.title} - {self.detected_at}"

    def clean(self):
        """Validaciones de eventos de seguridad"""
        if self.resolved_at and not self.resolution_notes:
            raise ValidationError({
                'resolution_notes': _('Resolution notes are required when resolving an event')
            })

class SystemChange(BaseAuditModel):
    """
    Cambios críticos en la configuración del sistema
    """
    CHANGE_TYPES = [
        ('user_permissions', _('User Permissions')),
        ('role_config', _('Role Configuration')),
        ('system_settings', _('System Settings')),
        ('security_policies', _('Security Policies')),
        ('business_rules', _('Business Rules')),
        ('audit_config', _('Audit Configuration')),
        ('notification_config', _('Notification Configuration')),
    ]

    change_type = models.CharField(
        _('change type'),
        max_length=50,
        choices=CHANGE_TYPES,
        db_index=True
    )
    changed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='system_changes',
        db_index=True
    )
    
    # Descripción del cambio
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    old_configuration = CustomJSONField(_('old configuration'), null=True, blank=True)
    new_configuration = CustomJSONField(_('new configuration'), null=True, blank=True)
    change_summary = models.TextField(_('change summary'), blank=True)
    
    # Aprobación
    requires_approval = models.BooleanField(_('requires approval'), default=False)
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_changes'
    )
    approved_at = models.DateTimeField(_('approved at'), null=True, blank=True)
    approval_notes = models.TextField(_('approval notes'), blank=True)
    
    # Reversión
    can_be_reverted = models.BooleanField(_('can be reverted'), default=True)
    is_reverted = models.BooleanField(_('is reverted'), default=False)
    reverted_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reverted_changes'
    )
    reverted_at = models.DateTimeField(_('reverted at'), null=True, blank=True)
    revert_reason = models.TextField(_('revert reason'), blank=True)
    
    # Impacto
    impact_level = models.CharField(
        _('impact level'),
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('medium', _('Medium')),
            ('high', _('High')),
            ('critical', _('Critical')),
        ],
        default='medium'
    )
    affected_users = models.PositiveIntegerField(_('affected users'), default=0)
    rollback_plan = models.TextField(_('rollback plan'), blank=True)
    
    # Metadata
    changed_at = models.DateTimeField(_('changed at'), auto_now_add=True, db_index=True)
    scheduled_for = models.DateTimeField(_('scheduled for'), null=True, blank=True)
    is_emergency_change = models.BooleanField(_('emergency change'), default=False)

    class Meta:
        db_table = 'core_system_changes'
        verbose_name = _('system change')
        verbose_name_plural = _('system changes')
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['change_type', 'changed_at']),
            models.Index(fields=['changed_by', 'changed_at']),
            models.Index(fields=['requires_approval', 'approved_at']),
        ]

    def __str__(self):
        return f"{self.get_change_type_display()} - {self.title} - {self.changed_by.email}"

    def clean(self):
        """Validaciones de cambios del sistema"""
        if self.requires_approval and self.approved_at and not self.approved_by:
            raise ValidationError({
                'approved_by': _('Approver must be specified when change is approved')
            })
        
        if self.is_reverted and not self.reverted_by:
            raise ValidationError({
                'reverted_by': _('Reverter must be specified when change is reverted')
            })

class AuditConfiguration(BaseAuditModel):
    """
    Configuración del sistema de auditoría
    """
    RETENTION_CHOICES = [
        (30, _('30 days')),
        (90, _('90 days')),
        (180, _('180 days')),
        (365, _('1 year')),
        (730, _('2 years')),
        (1825, _('5 years')),
        (0, _('Indefinitely')),
    ]

    # Retención de logs
    audit_log_retention_days = models.IntegerField(
        _('audit log retention days'),
        choices=RETENTION_CHOICES,
        default=365
    )
    security_event_retention_days = models.IntegerField(
        _('security event retention days'),
        choices=RETENTION_CHOICES,
        default=730
    )
    system_change_retention_days = models.IntegerField(
        _('system change retention days'),
        choices=RETENTION_CHOICES,
        default=1825
    )
    
    # Configuración de eventos
    enable_login_auditing = models.BooleanField(_('enable login auditing'), default=True)
    enable_data_access_auditing = models.BooleanField(_('enable data access auditing'), default=True)
    enable_permission_changes_auditing = models.BooleanField(_('enable permission changes auditing'), default=True)
    enable_api_auditing = models.BooleanField(_('enable API auditing'), default=True)
    enable_business_process_auditing = models.BooleanField(_('enable business process auditing'), default=True)
    
    # Alertas
    enable_security_alerts = models.BooleanField(_('enable security alerts'), default=True)
    failed_login_threshold = models.PositiveIntegerField(_('failed login threshold'), default=5)
    failed_login_timeframe_minutes = models.PositiveIntegerField(
        _('failed login timeframe (minutes)'),
        default=30
    )
    alert_email_recipients = models.TextField(
        _('alert email recipients'),
        blank=True,
        help_text=_('Comma-separated list of email addresses')
    )
    
    # Archivo y compresión
    enable_auto_archiving = models.BooleanField(_('enable auto archiving'), default=True)
    archive_after_days = models.PositiveIntegerField(_('archive after days'), default=90)
    enable_compression = models.BooleanField(_('enable compression'), default=True)
    
    # Metadata
    updated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('updated by')
    )
    is_active = models.BooleanField(_('active'), default=True)

    class Meta:
        db_table = 'core_audit_configurations'
        verbose_name = _('audit configuration')
        verbose_name_plural = _('audit configurations')

    def __str__(self):
        return _('Audit System Configuration')

    def clean(self):
        """Validaciones de configuración"""
        if self.failed_login_threshold < 1:
            raise ValidationError({
                'failed_login_threshold': _('Failed login threshold must be at least 1')
            })
        
        if self.archive_after_days >= self.audit_log_retention_days and self.audit_log_retention_days != 0:
            raise ValidationError({
                'archive_after_days': _('Archive days must be less than retention days')
            })

    def save(self, *args, **kwargs):
        # Solo debe haber una configuración activa
        if not self.pk and AuditConfiguration.objects.filter(is_active=True).exists():
            # Si ya existe una configuración activa, desactivarla
            AuditConfiguration.objects.filter(is_active=True).update(is_active=False)
        return super().save(*args, **kwargs)