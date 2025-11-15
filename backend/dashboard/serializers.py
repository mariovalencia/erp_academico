from rest_framework import serializers
from .models import DashboardWidget, UserDashboard, UserWidget, DashboardPreset

class DashboardWidgetSerializer(serializers.ModelSerializer):
    """Serializer para widgets disponibles"""
    permissions_required = serializers.SerializerMethodField()
    
    class Meta:
        model = DashboardWidget
        fields = [
            'id', 'name', 'code', 'description', 'widget_type', 
            'component_name', 'data_endpoint', 'default_config',
            'default_size', 'permissions_required'
        ]
    
    def get_permissions_required(self, obj):
        return [perm.permission_code for perm in obj.required_permissions.all()]

class UserWidgetSerializer(serializers.ModelSerializer):
    """Serializer para widgets del usuario"""
    widget_details = DashboardWidgetSerializer(source='widget', read_only=True)
    
    class Meta:
        model = UserWidget
        fields = [
            'id', 'widget', 'widget_details', 'position', 'config',
            'is_visible', 'refresh_interval', 'created_at'
        ]

class UserDashboardSerializer(serializers.ModelSerializer):
    """Serializer para dashboard del usuario"""
    widgets = UserWidgetSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserDashboard
        fields = [
            'id', 'user', 'user_email', 'layout', 'widgets',
            'created_at', 'updated_at'
        ]

class DashboardLayoutSerializer(serializers.Serializer):
    """Serializer para actualizar layout"""
    layout = serializers.JSONField(required=True)
    widgets = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )

class AddWidgetSerializer(serializers.Serializer):
    """Serializer para agregar widget al dashboard"""
    widget_code = serializers.CharField(required=True)
    position = serializers.JSONField(default={'x': 0, 'y': 0, 'cols': 2, 'rows': 1})
    config = serializers.JSONField(default=dict)

class WidgetConfigSerializer(serializers.Serializer):
    """Serializer para actualizar configuración de widget"""
    config = serializers.JSONField(required=True)
    is_visible = serializers.BooleanField(required=False)
    refresh_interval = serializers.IntegerField(required=False, min_value=30)