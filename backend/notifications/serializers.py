# notifications/api/serializers.py
from rest_framework import serializers
from .models import Notification, NotificationTemplate, UserNotificationPreference

class NotificationSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    template_code = serializers.CharField(source='template.code', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_email', 'template', 'template_name', 'template_code',
            'context', 'status', 'scheduled_for', 'sent_at', 'read_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'sent_at', 'read_at', 'created_at', 'updated_at'
        ]

class NotificationListSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    preview = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'template_name', 'status', 'preview', 
            'created_at', 'read_at'
        ]
    
    def get_preview(self, obj):
        """Obtener una vista previa del contenido"""
        try:
            rendered = obj.template.render_content(obj.context)
            return rendered.get('subject') or rendered.get('body', '')[:100] + '...'
        except:
            return ''

class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    channel_name = serializers.CharField(source='channel.name', read_only=True)
    
    class Meta:
        model = UserNotificationPreference
        fields = [
            'id', 'template', 'template_name', 'channel', 'channel_name',
            'is_enabled', 'config'
        ]

class MarkAsReadSerializer(serializers.Serializer):
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )

class TestNotificationSerializer(serializers.Serializer):
    """🔧 SERIALIZER FALTANTE: Para notificación de prueba"""
    template_code = serializers.CharField(required=True)
    channels = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['in_app']
    )

class NotificationTemplateSerializer(serializers.ModelSerializer):
    """🔧 SERIALIZER FALTANTE: Para plantillas"""
    channels = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationTemplate
        fields = ['id', 'code', 'name', 'description', 'channels']
    
    def get_channels(self, obj):
        return [channel.name for channel in obj.channels.all()]