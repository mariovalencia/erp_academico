from rest_framework import serializers
from .models import Notification, NotificationTemplate, UserNotificationPreference

class NotificationSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'template', 'template_name', 'context', 'status',
            'created_at', 'sent_at', 'read_at'
        ]
        read_only_fields = ['status', 'created_at', 'sent_at', 'read_at']

class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    channel_name = serializers.CharField(source='channel.name', read_only=True)
    
    class Meta:
        model = UserNotificationPreference
        fields = [
            'id', 'template', 'template_name', 'channel', 'channel_name',
            'is_enabled', 'config'
        ]

# notifications/api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification, UserNotificationPreference
from .serializers import NotificationSerializer, UserNotificationPreferenceSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        unread_notifications = self.get_queryset().filter(read_at__isnull=True)
        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)

class UserNotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = UserNotificationPreferenceSerializer
    
    def get_queryset(self):
        return UserNotificationPreference.objects.filter(user=self.request.user)