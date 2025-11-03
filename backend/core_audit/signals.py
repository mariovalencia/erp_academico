import threading  # 🔥 IMPORTAR THREADING
from django.db.models.signals import post_save, post_delete, pre_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.utils import timezone
from .models import AuditLog, SecurityEvent, AuditConfiguration
from core_users.models import CustomUser
from core_permissions.models import Role, UserRole
import uuid

CustomUser = get_user_model()

class AuditContext:
    """
    Contexto para almacenar información de auditoría durante una request
    """
    def __init__(self):
        self.request = None
        self.correlation_id = None
        self.start_time = None
        self.user = None
        self.ip_address = None
        self.user_agent = None

# Contexto thread-local para auditoría
_audit_context = threading.local()

def get_audit_context():
    """Obtener el contexto de auditoría actual"""
    if not hasattr(_audit_context, 'current'):
        _audit_context.current = AuditContext()
    return _audit_context.current

def set_audit_context(request=None, user=None, correlation_id=None):
    """Establecer el contexto de auditoría"""
    context = get_audit_context()
    if request:
        context.request = request
        context.ip_address = get_client_ip(request)
        context.user_agent = request.META.get('HTTP_USER_AGENT', '')
        context.user = getattr(request, 'user', None)
    if user:
        context.user = user
    if correlation_id:
        context.correlation_id = correlation_id
    else:
        context.correlation_id = uuid.uuid4()
    context.start_time = timezone.now()

def clear_audit_context():
    """Limpiar el contexto de auditoría"""
    if hasattr(_audit_context, 'current'):
        del _audit_context.current

def get_client_ip(request):
    """Obtener IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def create_audit_log(action_type, action_category, description, 
                    old_values=None, new_values=None, changed_fields=None,
                    content_object=None, is_success=True, error_message='',
                    duration_ms=None, severity='info'):
    """
    Función helper para crear registros de auditoría
    """
    context = get_audit_context()
    
    try:
        # Obtener configuración de auditoría
        config = AuditConfiguration.objects.filter(is_active=True).first()
        if not config:
            return None
        
        # Verificar si esta categoría está habilitada
        category_enabled = {
            'authentication': config.enable_login_auditing,
            'data_access': config.enable_data_access_auditing,
            'permission_management': config.enable_permission_changes_auditing,
            'api': config.enable_api_auditing,
            'business': config.enable_business_process_auditing,
        }.get(action_category, True)
        
        if not category_enabled:
            return None
        
        # Preparar datos del log
        audit_data = {
            'user': context.user if context.user and context.user.is_authenticated else None,
            'user_department': getattr(context.user, 'department', None) if context.user else None,
            'correlation_id': context.correlation_id,
            'action_category': action_category,
            'action_type': action_type,
            'severity': severity,
            'description': description,
            'ip_address': context.ip_address,
            'user_agent': context.user_agent,
            'old_values': old_values,
            'new_values': new_values,
            'changed_fields': changed_fields,
            'is_success': is_success,
            'error_message': error_message,
            'duration_ms': duration_ms,
        }
        
        # Agregar objeto relacionado si existe
        if content_object:
            audit_data['content_object'] = content_object
        
        # Agregar información de request si está disponible
        if context.request:
            audit_data['request_path'] = context.request.path
            audit_data['request_method'] = context.request.method
        
        # Crear el log de auditoría
        audit_log = AuditLog.objects.create(**audit_data)
        
        # Verificar si necesita crear un evento de seguridad
        check_security_event(audit_log, config)
        
        return audit_log
        
    except Exception as e:
        # Fallback silencioso para evitar que la auditoría rompa la aplicación
        print(f"⚠️ Error creating audit log: {e}")
        return None

def check_security_event(audit_log, config):
    """
    Verificar si un log de auditoría requiere un evento de seguridad
    """
    try:
        # Reglas para eventos de seguridad
        security_rules = [
            # Múltiples intentos fallidos de login
            {
                'condition': (
                    audit_log.action_type == 'login_failed' and 
                    config.enable_security_alerts
                ),
                'check_function': check_failed_logins
            },
            # Acceso no autorizado
            {
                'condition': (
                    audit_log.action_type in ['unauthorized_access', 'permission_escalation'] and
                    not audit_log.is_success
                ),
                'event_type': 'unauthorized_access',
                'severity': 'high'
            },
            # Actividad sospechosa
            {
                'condition': (
                    audit_log.severity in ['high', 'critical'] and
                    config.enable_security_alerts
                ),
                'event_type': 'suspicious_activity',
                'severity': audit_log.severity
            },
        ]
        
        for rule in security_rules:
            if rule.get('condition', False):
                if 'check_function' in rule:
                    rule['check_function'](audit_log, config)
                else:
                    create_security_event(
                        rule['event_type'],
                        audit_log,
                        rule['severity']
                    )
                    
    except Exception as e:
        print(f"⚠️ Error checking security event: {e}")

def check_failed_logins(audit_log, config):
    """
    Verificar múltiples intentos fallidos de login
    """
    try:
        if not audit_log.user:
            return
            
        # Contar intentos fallidos recientes
        time_threshold = timezone.now() - timezone.timedelta(
            minutes=config.failed_login_timeframe_minutes
        )
        
        failed_count = AuditLog.objects.filter(
            user=audit_log.user,
            action_type='login_failed',
            timestamp__gte=time_threshold,
            is_success=False
        ).count()
        
        if failed_count >= config.failed_login_threshold:
            create_security_event(
                'multiple_failed_logins',
                audit_log,
                'high',
                additional_data={
                    'failed_attempts': failed_count,
                    'timeframe_minutes': config.failed_login_timeframe_minutes
                }
            )
            
    except Exception as e:
        print(f"⚠️ Error checking failed logins: {e}")

def create_security_event(event_type, audit_log, severity, additional_data=None):
    """
    Crear un evento de seguridad
    """
    try:
        # Verificar si ya existe un evento similar reciente
        recent_threshold = timezone.now() - timezone.timedelta(hours=1)
        existing_event = SecurityEvent.objects.filter(
            event_type=event_type,
            user=audit_log.user,
            detected_at__gte=recent_threshold,
            status__in=['new', 'open', 'investigating']
        ).first()
        
        if existing_event:
            # Actualizar evento existente
            existing_event.occurrence_count += 1
            existing_event.last_occurrence = timezone.now()
            if 'related_logs' not in existing_event.evidence_data:
                existing_event.evidence_data['related_logs'] = []
            existing_event.evidence_data['related_logs'].append(str(audit_log.id))
            existing_event.save()
            return existing_event
        
        # Crear nuevo evento
        event_data = {
            'event_type': event_type,
            'user': audit_log.user,
            'user_department': audit_log.user_department,
            'title': f"{audit_log.get_action_type_display()} - Security Alert",
            'description': f"Security event detected: {audit_log.description}",
            'severity': severity,
            'first_occurrence': audit_log.timestamp,
            'last_occurrence': audit_log.timestamp,
        }
        
        if additional_data:
            event_data['evidence_data'] = additional_data
            
        security_event = SecurityEvent.objects.create(**event_data)
        security_event.related_audit_logs.add(audit_log)
        
        return security_event
        
    except Exception as e:
        print(f"⚠️ Error creating security event: {e}")

# ========== SIGNALS DE AUTENTICACIÓN ==========

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Registrar login exitoso"""
    set_audit_context(request=request, user=user)
    create_audit_log(
        action_type='login_success',
        action_category='authentication',
        description=f'User {user.email} logged in successfully',
        severity='info'
    )

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Registrar login fallido"""
    set_audit_context(request=request)
    email = credentials.get('email', 'Unknown')
    create_audit_log(
        action_type='login_failed',
        action_category='authentication',
        description=f'Failed login attempt for email: {email}',
        is_success=False,
        severity='low'
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Registrar logout"""
    set_audit_context(request=request, user=user)
    create_audit_log(
        action_type='logout',
        action_category='authentication',
        description=f'User {user.email} logged out',
        severity='info'
    )

# ========== SIGNALS DE MODELOS CORE ==========

@receiver(pre_save)
def log_model_changes(sender, instance, **kwargs):
    """Registrar cambios en modelos antes de guardar"""
    # Evitar registrar cambios en modelos de auditoría
    if sender.__name__ in ['AuditLog', 'SecurityEvent', 'SystemChange', 'AuditConfiguration']:
        return
        
    try:
        if instance.pk:
            # Es una actualización, obtener valores antiguos
            old_instance = sender.objects.get(pk=instance.pk)
            old_values = {}
            new_values = {}
            changed_fields = []
            
            for field in instance._meta.fields:
                field_name = field.name
                old_value = getattr(old_instance, field_name, None)
                new_value = getattr(instance, field_name, None)
                
                if old_value != new_value:
                    old_values[field_name] = str(old_value)
                    new_values[field_name] = str(new_value)
                    changed_fields.append(field_name)
            
            if changed_fields:
                # Guardar en el contexto para usar en post_save
                context = get_audit_context()
                context.changed_data = {
                    'old_values': old_values,
                    'new_values': new_values,
                    'changed_fields': changed_fields,
                    'instance': instance
                }
                
    except sender.DoesNotExist:
        # Es una nueva instancia
        pass
    except Exception as e:
        print(f"⚠️ Error in pre_save audit: {e}")

@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    """Registrar creación/actualización de modelos"""
    # Evitar registrar cambios en modelos de auditoría
    if sender.__name__ in ['AuditLog', 'SecurityEvent', 'SystemChange', 'AuditConfiguration']:
        return
        
    try:
        context = get_audit_context()
        action_type = 'record_created' if created else 'record_updated'
        action_category = 'data_modification'
        
        description = f"{sender.__name__} {'created' if created else 'updated'}: {str(instance)}"
        
        old_values = None
        new_values = None
        changed_fields = None
        
        if not created and hasattr(context, 'changed_data'):
            old_values = context.changed_data.get('old_values')
            new_values = context.changed_data.get('new_values')
            changed_fields = context.changed_data.get('changed_fields')
            # Limpiar datos temporales
            if hasattr(context, 'changed_data'):
                delattr(context, 'changed_data')
        
        create_audit_log(
            action_type=action_type,
            action_category=action_category,
            description=description,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            content_object=instance,
            severity='info'
        )
        
    except Exception as e:
        print(f"⚠️ Error in post_save audit: {e}")

@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    """Registrar eliminación de modelos"""
    # Evitar registrar cambios en modelos de auditoría
    if sender.__name__ in ['AuditLog', 'SecurityEvent', 'SystemChange', 'AuditConfiguration']:
        return
        
    try:
        create_audit_log(
            action_type='record_deleted',
            action_category='data_modification',
            description=f"{sender.__name__} deleted: {str(instance)}",
            content_object=instance,
            severity='medium'
        )
    except Exception as e:
        print(f"⚠️ Error in post_delete audit: {e}")

# ========== SIGNALS DE PERMISOS ==========

@receiver(post_save, sender=UserRole)
def log_user_role_change(sender, instance, created, **kwargs):
    """Registrar cambios en roles de usuario"""
    action_type = 'user_role_assigned' if created else 'user_role_updated'
    description = f"Role {instance.role.name} {'assigned to' if created else 'updated for'} user {instance.user.email}"
    
    create_audit_log(
        action_type=action_type,
        action_category='permission_management',
        description=description,
        content_object=instance,
        severity='medium'
    )

@receiver(post_delete, sender=UserRole)
def log_user_role_removal(sender, instance, **kwargs):
    """Registrar eliminación de roles de usuario"""
    description = f"Role {instance.role.name} removed from user {instance.user.email}"
    
    create_audit_log(
        action_type='user_role_removed',
        action_category='permission_management',
        description=description,
        content_object=instance,
        severity='medium'
    )

@receiver(m2m_changed, sender=Role.permissions.through)
def log_role_permission_change(sender, instance, action, pk_set, **kwargs):
    """Registrar cambios en permisos de roles"""
    if action in ['post_add', 'post_remove', 'post_clear']:
        if action == 'post_add':
            action_type = 'permission_assigned'
            description = f"Permissions assigned to role {instance.name}"
        elif action == 'post_remove':
            action_type = 'permission_revoked'
            description = f"Permissions revoked from role {instance.name}"
        else:
            action_type = 'permission_revoked'
            description = f"All permissions cleared from role {instance.name}"
        
        create_audit_log(
            action_type=action_type,
            action_category='permission_management',
            description=description,
            content_object=instance,
            severity='medium'
        )

# ========== MIDDLEWARE PARA CONTEXTO ==========

class AuditMiddleware:
    """Middleware para manejar el contexto de auditoría"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Establecer contexto al inicio de la request
        set_audit_context(request=request)
        
        response = self.get_response(request)
        
        # Limpiar contexto al final de la request
        clear_audit_context()
        
        return response