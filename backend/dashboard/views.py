from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import DashboardWidget, UserDashboard, UserWidget
from .services import DashboardService, WidgetDataService
from .serializers import (
    DashboardWidgetSerializer, UserDashboardSerializer, UserWidgetSerializer,
    DashboardLayoutSerializer, AddWidgetSerializer, WidgetConfigSerializer
)
from .permissions import IsOwnerOrAdmin, CanAccessWidget

class DashboardWidgetViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para widgets disponibles del dashboard
    """
    serializer_class = DashboardWidgetSerializer
    permission_classes = [IsAuthenticated, CanAccessWidget]
    
    def get_queryset(self):
        return DashboardService.get_available_widgets(self.request.user)
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Lista de widgets disponibles para el usuario actual
        """
        available_widgets = self.get_queryset()
        serializer = self.get_serializer(available_widgets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """
        Obtener datos para un widget específico
        """
        widget = self.get_object()
        
        # Mapear tipos de widget a métodos del servicio
        data_handlers = {
            'notifications_stats': WidgetDataService.get_notifications_stats,
            'recent_notifications': WidgetDataService.get_recent_notifications,
            'user_stats': WidgetDataService.get_user_stats,
            # Agregar más handlers según necesites
        }
        
        handler = data_handlers.get(widget.widget_type)
        if handler:
            data = handler(request.user)
            return Response(data)
        else:
            return Response({
                'success': False,
                'error': f'No data handler for widget type: {widget.widget_type}'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)

class UserDashboardViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el dashboard del usuario
    """
    serializer_class = UserDashboardSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        return UserDashboard.objects.filter(user=self.request.user)
    
    def get_object(self):
        """✅ VERSIÓN ROBUSTA: Manejar diferentes casos de retorno"""
        result = DashboardService.get_or_create_user_dashboard(self.request.user)
        
        # Si retorna una tupla (objeto, created)
        if isinstance(result, tuple) and len(result) == 2:
            dashboard, created = result
            return dashboard
        # Si retorna solo el objeto
        elif isinstance(result, UserDashboard):
            return result
        else:
            # Crear uno nuevo si es necesario
            return UserDashboard.objects.create(user=self.request.user)
    
    @action(detail=False, methods=['get', 'put'])
    def layout(self, request):
        """
        Obtener o actualizar el layout del dashboard
        """
        dashboard = self.get_object()
        
        if request.method == 'GET':
            serializer = UserDashboardSerializer(dashboard)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            serializer = DashboardLayoutSerializer(data=request.data)
            if serializer.is_valid():
                success = DashboardService.update_dashboard_layout(
                    request.user, 
                    serializer.validated_data
                )
                if success:
                    return Response({'message': 'Layout updated successfully'})
                else:
                    return Response(
                        {'error': 'Failed to update layout'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def add_widget(self, request):
        """
        Agregar un widget al dashboard del usuario
        """
        serializer = AddWidgetSerializer(data=request.data)
        if serializer.is_valid():
            widget_code = serializer.validated_data['widget_code']
            position = serializer.validated_data['position']
            config = serializer.validated_data['config']
            
            try:
                widget = DashboardWidget.objects.get(code=widget_code, is_active=True)
                dashboard = self.get_object()
                
                # Verificar que el usuario puede acceder a este widget
                if not DashboardService._user_can_access_widget(request.user, widget):
                    return Response(
                        {'error': 'You do not have permission to add this widget'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Crear o actualizar el widget del usuario
                user_widget, created = UserWidget.objects.get_or_create(
                    user_dashboard=dashboard,
                    widget=widget,
                    defaults={
                        'position': position,
                        'config': config,
                        'is_visible': True
                    }
                )
                
                if not created:
                    user_widget.position = position
                    user_widget.config = config
                    user_widget.is_visible = True
                    user_widget.save()
                
                return Response({
                    'message': 'Widget added successfully',
                    'user_widget_id': user_widget.id
                }, status=status.HTTP_201_CREATED)
                
            except DashboardWidget.DoesNotExist:
                return Response(
                    {'error': 'Widget not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserWidgetViewSet(viewsets.ModelViewSet):
    """
    ViewSet para widgets específicos del usuario
    """
    serializer_class = UserWidgetSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        dashboard = DashboardService.get_or_create_user_dashboard(self.request.user)
        if dashboard:
            return UserWidget.objects.filter(user_dashboard=dashboard)
        return UserWidget.objects.none()
    
    def destroy(self, request, *args, **kwargs):
        """
        Remover widget del dashboard (soft delete - marcar como no visible)
        """
        user_widget = self.get_object()
        user_widget.is_visible = False
        user_widget.save()
        
        return Response({'message': 'Widget removed from dashboard'})
    
    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """
        Obtener datos actualizados para un widget específico
        """
        user_widget = self.get_object()
        widget = user_widget.widget
        
        # Mapear tipos de widget a métodos del servicio
        data_handlers = {
            'notifications_stats': WidgetDataService.get_notifications_stats,
            'recent_notifications': WidgetDataService.get_recent_notifications,
            'user_stats': WidgetDataService.get_user_stats,
        }
        
        handler = data_handlers.get(widget.widget_type)
        if handler:
            data = handler(request.user)
            return Response(data)
        else:
            return Response({
                'success': False,
                'error': f'No data handler for widget type: {widget.widget_type}'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
    
    @action(detail=True, methods=['put'])
    def config(self, request, pk=None):
        """
        Actualizar configuración de un widget
        """
        user_widget = self.get_object()
        serializer = WidgetConfigSerializer(data=request.data)
        
        if serializer.is_valid():
            if 'config' in serializer.validated_data:
                user_widget.config = serializer.validated_data['config']
            if 'is_visible' in serializer.validated_data:
                user_widget.is_visible = serializer.validated_data['is_visible']
            if 'refresh_interval' in serializer.validated_data:
                user_widget.refresh_interval = serializer.validated_data['refresh_interval']
            
            user_widget.save()
            
            return Response({'message': 'Widget configuration updated'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DashboardStatsViewSet(viewsets.ViewSet):
    """
    ViewSet para estadísticas generales del dashboard
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Estadísticas generales para el dashboard
        """
        from notifications.services import NotificationService
        from notifications.models import Notification
        
        try:
            # Estadísticas de notificaciones
            notifications_stats = {
                'total': Notification.objects.filter(user=request.user).count(),
                'unread': NotificationService.get_unread_count(request.user),
                'recent': NotificationService.get_recent_notifications(request.user, limit=5).count(),
            }
            
            # Estadísticas del dashboard
            dashboard = DashboardService.get_or_create_user_dashboard(request.user)
            dashboard_stats = {
                'total_widgets': UserWidget.objects.filter(user_dashboard=dashboard, is_visible=True).count(),
                'available_widgets': DashboardService.get_available_widgets(request.user).count(),
            }
            
            # Estadísticas del usuario
            user_stats = {
                'is_staff': request.user.is_staff,
                'is_active': request.user.is_active,
                'last_login': request.user.last_login,
            }
            
            return Response({
                'notifications': notifications_stats,
                'dashboard': dashboard_stats,
                'user': user_stats,
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error getting dashboard stats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )