# notifications/api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Notification, UserNotificationPreference
from .services import NotificationService
from .serializers import (
    NotificationSerializer, 
    NotificationListSerializer,
    UserNotificationPreferenceSerializer,
    MarkAsReadSerializer
)
from rest_framework.pagination import PageNumberPagination

class NotificationPagination(PageNumberPagination):
    """🔧 PAGINACIÓN FALTANTE: Para listas largas"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Las notificaciones se crean via servicio, no directamente
        pass
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Obtener notificaciones no leídas"""
        unread_notifications = self.get_queryset().filter(read_at__isnull=True)
        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Obtener notificaciones recientes (últimas 10)"""
        recent_notifications = self.get_queryset().order_by('-created_at')[:10]
        serializer = self.get_serializer(recent_notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Marcar todas las notificaciones como leídas"""
        notifications = self.get_queryset().filter(read_at__isnull=True)
        updated_count = notifications.update(read_at=timezone.now(), status='read')
        return Response({
            'message': f'{updated_count} notificaciones marcadas como leídas',
            'updated_count': updated_count
        })
    
    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """Marcar notificaciones específicas como leídas"""
        serializer = MarkAsReadSerializer(data=request.data)
        if serializer.is_valid():
            notification_ids = serializer.validated_data['notification_ids']
            notifications = self.get_queryset().filter(
                id__in=notification_ids, 
                read_at__isnull=True
            )
            updated_count = 0
            for notification in notifications:
                if NotificationService.mark_as_read(notification.id, request.user):
                    updated_count += 1
            
            return Response({
                'message': f'{updated_count} notificaciones marcadas como leídas',
                'updated_count': updated_count
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtener estadísticas de notificaciones"""
        queryset = self.get_queryset()
        stats = {
            'total': queryset.count(),
            'unread': queryset.filter(read_at__isnull=True).count(),
            'read': queryset.filter(read_at__isnull=False).count(),
            'sent': queryset.filter(status='sent').count(),
            'pending': queryset.filter(status='pending').count(),
        }
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def test_notification(self, request):
        """🔧 ENDPOINT FALTANTE: Enviar notificación de prueba"""
        from .services import NotificationService
        
        try:
            notification = NotificationService.send_notification(
                user=request.user,
                template_code='welcome_email',  # o permitir especificar template
                context={
                    'user_name': request.user.get_full_name(),
                    'app_name': 'ERP Académico - Prueba'
                },
                channels=['in_app']  # Solo in_app para prueba
            )
            
            if notification:
                return Response({
                    'message': 'Notificación de prueba enviada',
                    'notification_id': notification.id
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'No se pudo enviar la notificación de prueba'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': f'Error enviando notificación: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def templates(self, request):
        """🔧 ENDPOINT FALTANTE: Listar plantillas disponibles"""
        from .models import NotificationTemplate
        
        templates = NotificationTemplate.objects.filter(is_active=True)
        data = [{
            'id': template.id,
            'code': template.code,
            'name': template.name,
            'description': template.description,
            'channels': [channel.name for channel in template.channels.all()]
        } for template in templates]
        
        return Response(data)
    
    @action(detail=False, methods=['get']) 
    def channels(self, request):
        """🔧 ENDPOINT FALTANTE: Listar canales disponibles"""
        from .models import NotificationChannel
        
        channels = NotificationChannel.objects.filter(is_active=True)
        data = [{
            'id': channel.id,
            'code': channel.code,
            'name': channel.name,
            'type': channel.channel_type
        } for channel in channels]
        
        return Response(data)

class UserNotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = UserNotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserNotificationPreference.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def available_templates(self, request):
        """🔧 ENDPOINT FALTANTE: Plantillas disponibles para preferencias"""
        from .models import NotificationTemplate
        
        # Plantillas que no tienen preferencia configurada
        existing_preferences = UserNotificationPreference.objects.filter(
            user=request.user
        ).values_list('template_id', flat=True)
        
        available_templates = NotificationTemplate.objects.filter(
            is_active=True
        ).exclude(id__in=existing_preferences)
        
        data = [{
            'id': template.id,
            'code': template.code,
            'name': template.name
        } for template in available_templates]
        
        return Response(data)