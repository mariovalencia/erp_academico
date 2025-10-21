from rest_framework import serializers
from core_users.models import CustomUser, UserProfile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo CustomUser"""
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 
                 'timezone', 'language', 'is_active', 'is_verified', 'created_at']
        read_only_fields = ['id', 'created_at', 'is_verified']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personalizado para tokens JWT"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # 🔥 AGREGAR CLAIMS PERSONALIZADOS PARA SEGURIDAD
        token['email'] = user.email
        token['user_id'] = user.id
        token['is_verified'] = user.is_verified
        
        return token

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para el modelo UserProfile"""
    user = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'profile_picture', 'bio', 'date_of_birth',
                 'email_notifications', 'push_notifications', 'in_app_notifications',
                 'theme_preference', 'created_at']
        read_only_fields = ['id', 'created_at']