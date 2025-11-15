from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardWidgetViewSet, 
    UserDashboardViewSet, 
    UserWidgetViewSet,
    DashboardStatsViewSet
)

router = DefaultRouter()
router.register(r'widgets', DashboardWidgetViewSet, basename='dashboard-widget')
router.register(r'my-dashboard', UserDashboardViewSet, basename='user-dashboard')
router.register(r'my-widgets', UserWidgetViewSet, basename='user-widget')
router.register(r'stats', DashboardStatsViewSet, basename='dashboard-stats')

urlpatterns = [
    path('', include(router.urls)),
]