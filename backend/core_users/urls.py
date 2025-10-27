from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.CustomUserViewSet, basename='users')
router.register(r'profiles', views.UserProfileViewSet, basename='profiles')

urlpatterns = [
    path('', include(router.urls)),
]

app_name = 'core_users'