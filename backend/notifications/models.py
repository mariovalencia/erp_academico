# notifications/models.py
from django.db import models
from django.utils import timezone
from django.template import Template, Context
from django.core.mail import send_mail
from django.conf import settings

class NotificationChannel(models.Model):
    """Canales de notificación disponibles"""
    CHANNEL_TYPES = (
        ('email', 'Email'),
        ('in_app', 'In-App Notification'),
        ('push', 'Push Notification'),
        ('sms', 'SMS'),
    )
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    is_active = models.BooleanField(default=True)
    config_template = models.JSONField(default=dict, help_text="Configuración específica del canal")
    
    # ✅ AGREGAR campos de auditoría si los necesitas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications_channel'
        verbose_name = 'Canal de Notificación'
        verbose_name_plural = 'Canales de Notificación'
    
    def __str__(self):
        return f"{self.name} ({self.channel_type})"

class NotificationTemplate(models.Model):
    """Plantillas reutilizables para notificaciones"""
    name = models.CharField(max_length=255, verbose_name="Nombre")
    code = models.CharField(max_length=100, unique=True, verbose_name="Código único")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    # Contenido de la notificación
    subject = models.CharField(max_length=255, blank=True, verbose_name="Asunto")
    body = models.TextField(verbose_name="Cuerpo del mensaje")
    body_html = models.TextField(blank=True, verbose_name="Cuerpo HTML (para email)")
    
    # Configuración
    channels = models.ManyToManyField(NotificationChannel, verbose_name="Canales")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    # Variables disponibles en la plantilla
    context_variables = models.JSONField(
        default=list, 
        help_text="Lista de variables disponibles. Ej: ['user_name', 'action_url']"
    )
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_template'
        verbose_name = 'Plantilla de Notificación'
        verbose_name_plural = 'Plantillas de Notificación'
        indexes = [
            models.Index(fields=['code', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def render_content(self, context_dict):
        """Renderiza la plantilla con el contexto proporcionado"""
        try:
            context = Context(context_dict)
            
            rendered = {
                'subject': Template(self.subject).render(context) if self.subject else "",
                'body': Template(self.body).render(context),
            }
            
            if self.body_html:
                rendered['body_html'] = Template(self.body_html).render(context)
            
            return rendered
            
        except Exception as e:
            # Log the error but don't crash
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error rendering template {self.code}: {str(e)}")
            
            # Return basic content without templating
            return {
                'subject': self.subject,
                'body': self.body,
                'body_html': self.body_html,
            }

class Notification(models.Model):
    """Notificaciones enviadas/por enviar"""
    STATUS_CHOICES = (
        ('pending', '🔄 Pendiente'),
        ('sent', '✅ Enviada'),
        ('delivered', '📨 Entregada'),
        ('read', '👀 Leída'),
        ('failed', '❌ Fallida'),
        ('cancelled', '🚫 Cancelada'),
    )
    
    # Destinatario y contenido
    user = models.ForeignKey(
        'core_users.CustomUser', 
        on_delete=models.CASCADE, 
        related_name='notifications',
        verbose_name="Usuario"
    )
    template = models.ForeignKey(
        NotificationTemplate, 
        on_delete=models.CASCADE,
        verbose_name="Plantilla"
    )
    context = models.JSONField(
        default=dict, 
        verbose_name="Contexto",
        help_text="Variables para reemplazar en la plantilla"
    )
    
    # Estado y seguimiento
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Estado"
    )
    scheduled_for = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Programada para",
        help_text="Si está vacío, se envía inmediatamente"
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Enviada el")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Leída el")
    
    # Métricas de entrega
    delivery_attempts = models.IntegerField(default=0, verbose_name="Intentos de envío")
    last_attempt_at = models.DateTimeField(null=True, blank=True, verbose_name="Último intento")
    error_message = models.TextField(blank=True, verbose_name="Mensaje de error")
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizada el")
    
    class Meta:
        db_table = 'notifications_notification'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        indexes = [
            models.Index(fields=['user', 'status', 'created_at']),
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['user', 'read_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notificación para {self.user.email} - {self.template.name}"
    
    def mark_as_read(self):
        """Marca la notificación como leída"""
        if not self.read_at:
            self.read_at = timezone.now()
            self.status = 'read'
            self.save()
    
    def mark_as_sent(self):
        """Marca la notificación como enviada"""
        self.sent_at = timezone.now()
        self.status = 'sent'
        self.save()
    
    def can_send(self):
        """Verifica si la notificación puede ser enviada"""
        if self.status in ['sent', 'delivered', 'read', 'cancelled']:
            return False
        
        if self.scheduled_for and self.scheduled_for > timezone.now():
            return False
            
        return True

class NotificationDelivery(models.Model):
    """Registro de entregas por canal"""
    notification = models.ForeignKey(
        Notification, 
        on_delete=models.CASCADE, 
        related_name='deliveries',
        verbose_name="Notificación"
    )
    channel = models.ForeignKey(
        NotificationChannel, 
        on_delete=models.CASCADE,
        verbose_name="Canal"
    )
    status = models.CharField(
        max_length=20, 
        choices=Notification.STATUS_CHOICES,
        verbose_name="Estado"
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Enviada el")
    external_id = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="ID Externo",
        help_text="ID del proveedor externo (email provider, push service, etc.)"
    )
    error_message = models.TextField(blank=True, verbose_name="Mensaje de error")
    
    class Meta:
        db_table = 'notifications_delivery'
        verbose_name = 'Entrega de Notificación'
        verbose_name_plural = 'Entregas de Notificaciones'
        indexes = [
            models.Index(fields=['notification', 'channel']),
            models.Index(fields=['sent_at']),
        ]
    
    def __str__(self):
        return f"Entrega {self.channel.name} - {self.status}"

class UserNotificationPreference(models.Model):
    """Preferencias de notificación por usuario"""
    user = models.ForeignKey(
        'core_users.CustomUser', 
        on_delete=models.CASCADE, 
        related_name='notification_preferences',
        verbose_name="Usuario"
    )
    template = models.ForeignKey(
        NotificationTemplate, 
        on_delete=models.CASCADE,
        verbose_name="Plantilla"
    )
    channel = models.ForeignKey(
        NotificationChannel, 
        on_delete=models.CASCADE,
        verbose_name="Canal"
    )
    is_enabled = models.BooleanField(default=True, verbose_name="Habilitado")
    
    # Configuración específica por usuario/canal
    config = models.JSONField(
        default=dict, 
        verbose_name="Configuración",
        help_text="Configuración específica para este usuario/canal"
    )
    
    class Meta:
        db_table = 'notifications_user_preference'
        verbose_name = 'Preferencia de Notificación'
        verbose_name_plural = 'Preferencias de Notificación'
        unique_together = ['user', 'template', 'channel']
        indexes = [
            models.Index(fields=['user', 'is_enabled']),
        ]
    
    def __str__(self):
        status = "✅" if self.is_enabled else "❌"
        return f"{self.user.email} - {self.template.name} - {self.channel.name} {status}"