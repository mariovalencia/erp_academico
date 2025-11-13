# notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.utils import timezone  # ✅ AGREGAR ESTE IMPORT
from core_audit.models import AuditLog, SecurityEvent
from core_users.models import CustomUser
from .services import NotificationService

@receiver(post_save, sender=CustomUser)
def notify_user_creation(sender, instance, created, **kwargs):
    """Notifica cuando se crea un nuevo usuario"""
    if created:
        # Notificar al usuario
        NotificationService.send_notification(
            user=instance,
            template_code='welcome_email',
            context={
                'user_name': instance.get_full_name() or instance.email,
                'app_name': 'Sistema Académico'
            }
        )
        
        # Notificar a administradores (opcional)
        admins = CustomUser.objects.filter(is_staff=True, is_active=True)
        NotificationService.send_bulk_notification(
            users=admins,
            template_code='new_user_registered',
            context={
                'user_email': instance.email,
                'registration_date': instance.date_joined.strftime('%Y-%m-%d %H:%M')
            }
        )

@receiver(user_login_failed)
def notify_failed_login_attempt(sender, credentials, **kwargs):
    """Notifica intentos fallidos de login"""
    from django.utils import timezone  # ✅ IMPORT DENTRO DE LA FUNCIÓN también por si acaso
    
    email = credentials.get('email')
    request = kwargs.get('request')
    
    if email and request:
        try:
            user = CustomUser.objects.get(email=email)
            
            NotificationService.send_notification(
                user=user,
                template_code='failed_login_attempt',
                context={
                    'user_name': user.get_full_name() or user.email,
                    'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M'),
                    'ip_address': request.META.get('REMOTE_ADDR', 'Desconocida')
                }
            )
        except CustomUser.DoesNotExist:
            # Usuario no existe - posible ataque
            pass

@receiver(post_save, sender=AuditLog)
def notify_important_audit_events(sender, instance, created, **kwargs):
    """Notifica eventos importantes de auditoría"""
    if not created:
        return
    
    # Definir qué eventos son importantes
    important_events = [
        'user_created', 'user_deleted', 'permission_granted', 
        'permission_revoked', 'security_breach'
    ]
    
    if instance.action_type in important_events:
        admins = CustomUser.objects.filter(is_staff=True, is_active=True)
        
        NotificationService.send_bulk_notification(
            users=admins,
            template_code='important_audit_event',
            context={
                'event_type': instance.get_action_type_display(),
                'description': instance.description,
                'user_involved': str(instance.user) if instance.user else 'Sistema',
                'timestamp': instance.timestamp.strftime('%Y-%m-%d %H:%M')
            }
        )