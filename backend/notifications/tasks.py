# notifications/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import Notification
from .services import NotificationService
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_pending_notifications():
    """Procesa todas las notificaciones pendientes"""
    try:
        pending_notifications = Notification.objects.filter(
            status='pending',
            scheduled_for__isnull=True
        ) | Notification.objects.filter(
            status='pending',
            scheduled_for__lte=timezone.now()
        )
        
        count = pending_notifications.count()
        
        for notification in pending_notifications:
            NotificationService._process_notification.delay(notification.id)
        
        logger.info(f"Procesadas {count} notificaciones pendientes")
        return f"Procesadas {count} notificaciones"
        
    except Exception as e:
        logger.error(f"Error procesando notificaciones pendientes: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def cleanup_old_notifications(days=30):
    """Limpia notificaciones antiguas"""
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Eliminar notificaciones antiguas que ya fueron leídas o fallidas
        deleted_count, _ = Notification.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['read', 'failed', 'cancelled']
        ).delete()
        
        logger.info(f"Limpieza completada: {deleted_count} notificaciones eliminadas")
        return f"Eliminadas {deleted_count} notificaciones"
        
    except Exception as e:
        logger.error(f"Error en limpieza de notificaciones: {str(e)}")
        return f"Error: {str(e)}"