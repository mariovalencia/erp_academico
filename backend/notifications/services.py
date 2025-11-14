# notifications/services.py - VERSIÓN CORREGIDA
import logging
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task  # ✅ IMPORTAR DIRECTAMENTE
from .models import Notification, NotificationTemplate, NotificationDelivery, NotificationChannel

logger = logging.getLogger(__name__)

class NotificationService:
    """Servicio principal para el manejo de notificaciones"""
    
    @classmethod
    def send_notification(cls, user, template_code, context=None, channels=None, scheduled_for=None):
        """
        Envía una notificación a un usuario
        """
        try:
            # Obtener plantilla
            template = NotificationTemplate.objects.get(code=template_code, is_active=True)
            
            # Crear notificación
            notification = Notification.objects.create(
                user=user,
                template=template,
                context=context or {},
                scheduled_for=scheduled_for
            )
            
            logger.info(f"Notificación creada: {notification.id} para {user.email}")
            
            # Procesar envío con Celery
            if scheduled_for and scheduled_for > timezone.now():
                # Programar para después
                cls._schedule_notification.apply_async(
                    args=[notification.id, channels],
                    eta=scheduled_for
                )
                logger.info(f"Notificación {notification.id} programada para {scheduled_for}")
            else:
                # Enviar inmediatamente
                cls._process_notification.delay(notification.id, channels)
                logger.info(f"Notificación {notification.id} enviada a la cola de procesamiento")
            
            return notification
            
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Plantilla de notificación no encontrada: {template_code}")
            return None
        except Exception as e:
            logger.error(f"Error creando notificación: {str(e)}")
            return None
    
    @classmethod
    def send_bulk_notification(cls, users, template_code, context=None, channels=None):
        """
        Envía notificación a múltiples usuarios
        """
        notifications = []
        for user in users:
            notification = cls.send_notification(user, template_code, context, channels)
            if notification:
                notifications.append(notification)
        
        logger.info(f"Notificaciones masivas enviadas: {len(notifications)} notificaciones")
        return notifications
    
    @classmethod
    def get_user_preferences(cls, user, template_code=None):
        """
        Obtiene las preferencias de notificación de un usuario
        """
        from .models import UserNotificationPreference
        
        preferences = UserNotificationPreference.objects.filter(user=user, is_enabled=True)
        
        if template_code:
            preferences = preferences.filter(template__code=template_code)
        
        return preferences

    @staticmethod
    @shared_task(bind=True, max_retries=3)  # ✅ USAR shared_task DIRECTAMENTE
    def _process_notification(self, notification_id, channels=None):
        """Procesa el envío de una notificación (tarea Celery)"""
        try:
            notification = Notification.objects.get(id=notification_id)
            
            # Verificar si puede ser enviada
            if not notification.can_send():
                logger.warning(f"Notificación {notification_id} no puede ser enviada en este momento")
                return
            
            # Obtener canales a usar
            if channels is None:
                channels = notification.template.channels.filter(is_active=True)
            else:
                channels = NotificationChannel.objects.filter(code__in=channels, is_active=True)
            
            # Procesar cada canal
            for channel in channels:
                NotificationService._deliver_to_channel(notification, channel)
            
            # Actualizar estado
            notification.mark_as_sent()
            logger.info(f"Notificación {notification_id} procesada exitosamente")
            
        except Notification.DoesNotExist:
            logger.error(f"Notificación {notification_id} no encontrada")
        except Exception as e:
            logger.error(f"Error procesando notificación {notification_id}: {str(e)}")
            # Reintentar después de 60 segundos
            try:
                self.retry(countdown=60, max_retries=3)
            except self.MaxRetriesExceededError:
                # Actualizar estado a fallido después de reintentos
                notification.status = 'failed'
                notification.error_message = f"Fallido después de 3 intentos: {str(e)}"
                notification.save()

    @staticmethod
    @shared_task  # ✅ USAR shared_task DIRECTAMENTE
    def _schedule_notification(notification_id, channels=None):
        """Programa una notificación para envío futuro"""
        try:
            notification = Notification.objects.get(id=notification_id)
            
            # Verificar si es hora de enviar
            if notification.scheduled_for <= timezone.now():
                NotificationService._process_notification.delay(notification_id, channels)
            else:
                # Re-programar verificación
                eta = notification.scheduled_for
                NotificationService._schedule_notification.apply_async(
                    args=[notification_id, channels], 
                    eta=eta
                )
                
        except Notification.DoesNotExist:
            logger.error(f"Notificación programada {notification_id} no encontrada")

    @classmethod
    def _deliver_to_channel(cls, notification, channel):
        """Envía la notificación a un canal específico"""
        try:
            # Verificar preferencias del usuario
            user_preference = notification.user.notification_preferences.filter(
                template=notification.template,
                channel=channel,
                is_enabled=True
            ).first()
            
            if not user_preference:
                logger.info(f"Usuario {notification.user.email} tiene deshabilitado {channel.name} para {notification.template.name}")
                return
            
            # Renderizar contenido
            rendered_content = notification.template.render_content(notification.context)
            
            # Enviar según el canal
            if channel.channel_type == 'email':
                cls._send_email(notification, channel, rendered_content)
            elif channel.channel_type == 'in_app':
                cls._create_in_app_notification(notification, channel, rendered_content)
            elif channel.channel_type == 'push':
                cls._send_push_notification(notification, channel, rendered_content)
            elif channel.channel_type == 'sms':
                cls._send_sms(notification, channel, rendered_content)
            else:
                logger.warning(f"Canal no soportado: {channel.channel_type}")
            
        except Exception as e:
            logger.error(f"Error enviando a canal {channel.code}: {str(e)}")
            # Registrar fallo en la entrega
            NotificationDelivery.objects.create(
                notification=notification,
                channel=channel,
                status='failed',
                error_message=str(e)
            )
    
    @classmethod
    def _send_email(cls, notification, channel, rendered_content):
        """Envía notificación por email"""
        try:
            send_mail(
                subject=rendered_content['subject'],
                message=rendered_content['body'],
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                html_message=rendered_content.get('body_html'),
                fail_silently=False,
            )
            
            # Registrar entrega exitosa
            NotificationDelivery.objects.create(
                notification=notification,
                channel=channel,
                status='sent',
                sent_at=timezone.now()
            )
            
            logger.info(f"Email enviado a {notification.user.email}")
            
        except Exception as e:
            logger.error(f"Error enviando email a {notification.user.email}: {str(e)}")
            raise
    
    @classmethod
    def _create_in_app_notification(cls, notification, channel, rendered_content):
        """Crea notificación in-app (ya está creada en el modelo Notification)"""
        # Para notificaciones in-app, la notificación principal ya existe
        # Solo marcamos la entrega como exitosa
        
        NotificationDelivery.objects.create(
            notification=notification,
            channel=channel,
            status='delivered',  # In-app se entrega inmediatamente
            sent_at=timezone.now()
        )
        
        logger.info(f"Notificación in-app creada para {notification.user.email}")
    
    @classmethod
    def _send_push_notification(cls, notification, channel, rendered_content):
        """Envía notificación push (placeholder para implementación futura)"""
        # TODO: Integrar con servicio de push notifications (FCM, APNS, etc.)
        logger.info(f"Push notification para {notification.user.email} - {rendered_content['subject']}")
        
        # Por ahora, solo registrar como enviada
        NotificationDelivery.objects.create(
            notification=notification,
            channel=channel,
            status='sent',
            sent_at=timezone.now()
        )
    
    @classmethod
    def _send_sms(cls, notification, channel, rendered_content):
        """Envía notificación SMS (placeholder para implementación futura)"""
        # TODO: Integrar con servicio SMS (Twilio, etc.)
        logger.info(f"SMS para {notification.user.email} - {rendered_content['body']}")
        
        # Por ahora, solo registrar como enviada
        NotificationDelivery.objects.create(
            notification=notification,
            channel=channel,
            status='sent',
            sent_at=timezone.now()
        )
    
    @classmethod
    def mark_as_read(cls, notification_id, user):
        """Marca una notificación como leída por el usuario"""
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            logger.warning(f"Notificación {notification_id} no encontrada para usuario {user.email}")
            return False
    
    @classmethod
    def get_unread_count(cls, user):
        """Obtiene el número de notificaciones no leídas para un usuario"""
        return Notification.objects.filter(user=user, read_at__isnull=True).count()
    
    @classmethod
    def get_recent_notifications(cls, user, limit=10):
        """Obtiene las notificaciones recientes de un usuario"""
        return Notification.objects.filter(user=user).order_by('-created_at')[:limit]