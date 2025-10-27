from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction

from .models import CustomUser, UserProfile
from .serializers import (
    CustomUserSerializer, CustomUserCreateSerializer,
    CustomUserUpdateSerializer, UserProfileSerializer
)

class CustomUserViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de usuarios"""
    queryset = CustomUser.objects.all()
    
    def get_permissions(self):
        """Permisos diferentes según la acción"""
        if self.action == 'me':
            permission_classes = [IsAuthenticated]  # 🔥 CUALQUIER usuario autenticado
        elif self.action in ['create', 'update', 'partial_update', 'destroy', 'list']:
            permission_classes = [IsAuthenticated, IsAdminUser]  # 🔥 Solo admin
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action == 'create':
            return CustomUserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CustomUserUpdateSerializer
        return CustomUserSerializer
    
    def get_queryset(self):
        """Optimizar queries con select_related"""
        return CustomUser.objects.select_related('profile').order_by('-created_at')
    
    @action(detail=True, methods=['get', 'put'])
    def profile(self, request, pk=None):
        """Gestionar perfil del usuario"""
        user = self.get_object()
        
        if request.method == 'GET':
            profile, created = UserProfile.objects.get_or_create(user=user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            profile, created = UserProfile.objects.get_or_create(user=user)
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Obtener información del usuario actual"""
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'put'])
    def profile(self, request, pk=None):
        """Gestionar perfil del usuario"""
        user = self.get_object()
        
        # 🔥 PERMISO: Usuarios solo pueden ver su propio perfil, admins pueden ver todos
        if not request.user.is_staff and request.user != user:
            return Response(
                {'error': 'No tienes permisos para ver este perfil'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            profile, created = UserProfile.objects.get_or_create(user=user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            profile, created = UserProfile.objects.get_or_create(user=user)
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de perfiles de usuario"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Los usuarios solo pueden ver su propio perfil"""
        if self.request.user.is_staff:
            return UserProfile.objects.select_related('user').all()
        return UserProfile.objects.filter(user=self.request.user)
