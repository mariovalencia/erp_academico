# notifications/tasks.py - VERSIÓN CORREGIDA
import logging
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from celery import shared_task  # ✅ IMPORTAR DIRECTAMENTE

logger = logging.getLogger(__name__)

@shared_task
def process_pending_notifications():
    """Procesa todas las notificaciones pendientes (tarea periódica)"""
    try:
        from .models import Notification
        from .services import NotificationService
        
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
    try:
        from .models import Notification
        
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

@shared_task
def send_daily_notifications_summary():
    """Envía resumen diario de notificaciones (para admins)"""
    try:
        from django.contrib.auth import get_user_model
        from django.core.mail import send_mail
        from .models import Notification
        
        User = get_user_model()
        admins = User.objects.filter(is_staff=True, is_active=True)
        
        if not admins.exists():
            logger.warning("No hay administradores para enviar resumen")
            return "No hay administradores"
        
        # Estadísticas del día
        today = timezone.now().date()
        notifications_today = Notification.objects.filter(
            created_at__date=today
        )
        
        stats = {
            'total': notifications_today.count(),
            'sent': notifications_today.filter(status='sent').count(),
            'pending': notifications_today.filter(status='pending').count(),
            'failed': notifications_today.filter(status='failed').count(),
            'read': notifications_today.filter(status='read').count(),
        }
        
        # Enviar email a admins
        subject = f"📊 Resumen de Notificaciones - {today}"
        message = f"""
Resumen diario de notificaciones - {today}

📈 Estadísticas:
• Total: {stats['total']}
• Enviadas: {stats['sent']} 
• Pendientes: {stats['pending']}
• Fallidas: {stats['failed']}
• Leídas: {stats['read']}

Sistema de Notificaciones ERP Académico
        """
        
        for admin in admins:
            try:
                send_mail(
                    subject=subject,
                    message=message.strip(),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin.email],
                    fail_silently=False,
                )
                logger.info(f"Resumen enviado a {admin.email}")
            except Exception as e:
                logger.error(f"Error enviando resumen a {admin.email}: {str(e)}")
        
        logger.info(f"Resumen diario enviado a {admins.count()} administradores")
        return f"Resumen enviado: {stats}"
        
    except Exception as e:
        logger.error(f"Error enviando resumen diario: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def retry_failed_notifications():
    """Reintenta notificaciones fallidas (para casos específicos)"""
    try:
        from .models import Notification
        from .services import NotificationService
        
        # Solo reintentar notificaciones fallidas recientes (últimas 24 horas)
        cutoff_date = timezone.now() - timedelta(hours=24)
        failed_notifications = Notification.objects.filter(
            status='failed',
            created_at__gte=cutoff_date,
            delivery_attempts__lt=3  # Máximo 3 intentos
        )
        
        count = failed_notifications.count()
        
        for notification in failed_notifications:
            notification.status = 'pending'
            notification.error_message = ''
            notification.delivery_attempts += 1
            notification.save()
            
            # Reprocesar
            NotificationService._process_notification.delay(notification.id)
        
        logger.info(f"Reintentadas {count} notificaciones fallidas")
        return f"Reintentadas {count} notificaciones"
        
    except Exception as e:
        logger.error(f"Error reintentando notificaciones fallidas: {str(e)}")
        return f"Error: {str(e)}"