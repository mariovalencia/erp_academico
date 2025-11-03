import threading
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import AuditLog, SecurityEvent, SystemChange, AuditConfiguration
from datetime import timedelta
import json
import uuid

_audit_context = threading.local()

class AuditManager:
    """
    Clase principal para gestión de auditoría
    """
    
    @staticmethod
    def get_audit_configuration():
        """Obtener configuración activa de auditoría"""
        return AuditConfiguration.objects.filter(is_active=True).first()
    
    @staticmethod
    def log_security_incident(event_type, user, description, severity='medium', evidence=None):
        """
        Registrar un incidente de seguridad manualmente
        """
        try:
            event_data = {
                'event_type': event_type,
                'user': user,
                'title': f"Manual Security Alert: {event_type}",
                'description': description,
                'severity': severity,
            }
            
            if evidence:
                event_data['evidence_data'] = evidence
            
            security_event = SecurityEvent.objects.create(**event_data)
            return security_event
            
        except Exception as e:
            print(f"⚠️ Error logging security incident: {e}")
            return None
    
    @staticmethod
    def log_system_change(change_type, changed_by, title, description, 
                         old_config=None, new_config=None, requires_approval=False):
        """
        Registrar un cambio del sistema manualmente
        """
        try:
            change_data = {
                'change_type': change_type,
                'changed_by': changed_by,
                'title': title,
                'description': description,
                'old_configuration': old_config,
                'new_configuration': new_config,
                'requires_approval': requires_approval,
            }
            
            system_change = SystemChange.objects.create(**change_data)
            return system_change
            
        except Exception as e:
            print(f"⚠️ Error logging system change: {e}")
            return None

class AuditReportGenerator:
    """
    Generador de reportes de auditoría
    """
    
    @staticmethod
    def get_activity_summary(days=30):
        """
        Resumen de actividad por categorías
        """
        start_date = timezone.now() - timedelta(days=days)
        
        summary = AuditLog.objects.filter(
            timestamp__gte=start_date
        ).values(
            'action_category', 'action_type', 'severity', 'is_success'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        return list(summary)
    
    @staticmethod
    def get_user_activity_report(user, days=30):
        """
        Reporte de actividad por usuario
        """
        start_date = timezone.now() - timedelta(days=days)
        
        user_activity = AuditLog.objects.filter(
            user=user,
            timestamp__gte=start_date
        ).values(
            'action_category', 'action_type'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'user': user.email,
            'period_days': days,
            'activity': list(user_activity),
            'total_actions': AuditLog.objects.filter(
                user=user, timestamp__gte=start_date
            ).count()
        }
    
    @staticmethod
    def get_security_events_report(days=30, severity=None):
        """
        Reporte de eventos de seguridad
        """
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = SecurityEvent.objects.filter(
            detected_at__gte=start_date
        )
        
        if severity:
            queryset = queryset.filter(severity=severity)
        
        events = queryset.values(
            'event_type', 'severity', 'status', 'assigned_to__email'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'period_days': days,
            'total_events': queryset.count(),
            'events_by_type': list(events),
            'open_events': queryset.filter(status__in=['new', 'open', 'investigating']).count(),
            'resolved_events': queryset.filter(status='resolved').count(),
        }
    
    @staticmethod
    def get_failed_logins_report(days=7, threshold=5):
        """
        Reporte de intentos fallidos de login
        """
        start_date = timezone.now() - timedelta(days=days)
        
        failed_logins = AuditLog.objects.filter(
            action_type='login_failed',
            timestamp__gte=start_date,
            is_success=False
        ).values('user__email', 'ip_address').annotate(
            count=Count('id')
        ).filter(count__gte=threshold).order_by('-count')
        
        return {
            'period_days': days,
            'threshold': threshold,
            'suspicious_activity': list(failed_logins)
        }

class DataRetentionManager:
    """
    Gestor de retención y archivado de datos
    """
    
    @staticmethod
    def cleanup_old_records():
        """
        Limpiar registros antiguos según la configuración de retención
        """
        config = AuditManager.get_audit_configuration()
        if not config:
            return {'error': 'No active audit configuration found'}
        
        results = {}
        
        # Limpiar logs de auditoría antiguos
        if config.audit_log_retention_days > 0:
            cutoff_date = timezone.now() - timedelta(days=config.audit_log_retention_days)
            deleted_logs = AuditLog.objects.filter(
                timestamp__lt=cutoff_date,
                is_archived=True
            ).delete()
            results['audit_logs_deleted'] = deleted_logs[0]
        
        # Limpiar eventos de seguridad antiguos
        if config.security_event_retention_days > 0:
            cutoff_date = timezone.now() - timedelta(days=config.security_event_retention_days)
            deleted_events = SecurityEvent.objects.filter(
                detected_at__lt=cutoff_date,
                status__in=['resolved', 'false_positive', 'closed']
            ).delete()
            results['security_events_deleted'] = deleted_events[0]
        
        return results
    
    @staticmethod
    def archive_old_records():
        """
        Archivar registros antiguos (marcar como archivados)
        """
        config = AuditManager.get_audit_configuration()
        if not config or not config.enable_auto_archiving:
            return {'error': 'Auto archiving is disabled'}
        
        cutoff_date = timezone.now() - timedelta(days=config.archive_after_days)
        
        # Archivar logs de auditoría
        archived_logs = AuditLog.objects.filter(
            timestamp__lt=cutoff_date,
            is_archived=False
        ).update(is_archived=True, archive_date=timezone.now())
        
        return {
            'archived_logs': archived_logs,
            'archive_date': cutoff_date
        }

class SecurityAnalyzer:
    """
    Analizador de patrones de seguridad
    """
    
    @staticmethod
    def detect_anomalous_behavior(user, time_window_hours=24):
        """
        Detectar comportamiento anómalo de usuario
        """
        start_time = timezone.now() - timedelta(hours=time_window_hours)
        
        user_activity = AuditLog.objects.filter(
            user=user,
            timestamp__gte=start_time
        )
        
        # Calcular métricas de actividad
        total_actions = user_activity.count()
        action_types = user_activity.values('action_type').annotate(count=Count('id'))
        failed_actions = user_activity.filter(is_success=False).count()
        
        # Detectar anomalías
        anomalies = []
        
        # Actividad inusualmente alta
        if total_actions > 1000:  # Umbral arbitrario
            anomalies.append({
                'type': 'high_activity',
                'description': f'Unusually high activity: {total_actions} actions in {time_window_hours}h',
                'severity': 'medium'
            })
        
        # Alta tasa de fallos
        if total_actions > 0 and (failed_actions / total_actions) > 0.5:
            anomalies.append({
                'type': 'high_failure_rate',
                'description': f'High failure rate: {failed_actions}/{total_actions} actions failed',
                'severity': 'high'
            })
        
        # Múltiples tipos de acción inusuales
        unusual_actions = ['data_exported', 'bulk_delete', 'permission_escalation']
        unusual_count = user_activity.filter(action_type__in=unusual_actions).count()
        if unusual_count > 10:
            anomalies.append({
                'type': 'unusual_actions',
                'description': f'Multiple unusual actions detected: {unusual_count}',
                'severity': 'high'
            })
        
        return {
            'user': user.email,
            'time_window_hours': time_window_hours,
            'total_actions': total_actions,
            'failed_actions': failed_actions,
            'anomalies': anomalies,
            'is_suspicious': len(anomalies) > 0
        }
    
    @staticmethod
    def analyze_access_patterns(department=None, days=7):
        """
        Analizar patrones de acceso por departamento
        """
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = AuditLog.objects.filter(
            timestamp__gte=start_date,
            action_category='data_access'
        )
        
        if department:
            queryset = queryset.filter(user_department=department)
        
        access_patterns = queryset.values(
            'user__email', 
            'user_department__name',
            'action_type',
            'content_type__model'
        ).annotate(
            access_count=Count('id'),
            unique_objects=Count('object_id', distinct=True)
        ).order_by('-access_count')
        
        return {
            'period_days': days,
            'department': department.name if department else 'All',
            'total_access_events': queryset.count(),
            'patterns': list(access_patterns)
        }

# Utilidades de contexto (para complementar signals.py)
def get_audit_context():
    """Obtener contexto de auditoría actual"""
    if not hasattr(_audit_context, 'current'):
        _audit_context.current = {}
    return _audit_context.current

def set_audit_context(**kwargs):
    """Establecer contexto de auditoría"""
    context = get_audit_context()
    context.update(kwargs)

def clear_audit_context():
    """Limpiar contexto de auditoría"""
    if hasattr(_audit_context, 'current'):
        del _audit_context.current

# Función para uso en APIs y vistas
def audit_api_call(view_func):
    """
    Decorador para auditar llamadas a API
    """
    def wrapper(request, *args, **kwargs):
        from .signals import set_audit_context, create_audit_log
        
        # Establecer contexto
        set_audit_context(request=request)
        
        try:
            response = view_func(request, *args, **kwargs)
            
            # Registrar llamada exitosa
            create_audit_log(
                action_type='api_call',
                action_category='api',
                description=f'API call to {request.path}',
                is_success=True,
                severity='info'
            )
            
            return response
            
        except Exception as e:
            # Registrar error
            create_audit_log(
                action_type='api_call',
                action_category='api',
                description=f'API call to {request.path} failed: {str(e)}',
                is_success=False,
                error_message=str(e),
                severity='medium'
            )
            raise e
            
    return wrapper