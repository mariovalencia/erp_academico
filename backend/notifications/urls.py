# notifications/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, UserNotificationPreferenceViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'preferences', UserNotificationPreferenceViewSet, basename='preference')

urlpatterns = [
    path('', include(router.urls)),
]