from rest_framework import serializers
from .models import CustomUser, UserProfile

class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo CustomUser"""
    full_name = serializers.CharField(read_only=True)
    profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'timezone', 'language', 'is_verified',
            'is_active', 'is_staff', 'is_superuser',
            'profile_picture', 'created_at'
        ]
        read_only_fields = [
            'id', 'is_verified', 'is_staff', 'is_superuser', 
            'created_at', 'full_name'
        ]
    
    def get_profile_picture(self, obj):
        """Obtener la foto de perfil del usuario"""
        if hasattr(obj, 'profile') and obj.profile.profile_picture:
            return obj.profile.profile_picture.url
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para el modelo UserProfile"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_email', 'user_full_name',
            'profile_picture', 'bio', 'date_of_birth',
            'email_notifications', 'push_notifications', 'in_app_notifications',
            'theme_preference', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Serializer para creación de usuarios"""
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = CustomUser
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'timezone', 'language', 'password'
        ]
    
    def create(self, validated_data):
        """Crear usuario con contraseña encriptada"""
        password = validated_data.pop('password')
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        # Crear perfil automáticamente
        UserProfile.objects.create(user=user)
        
        return user


class CustomUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualización de usuarios"""
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone_number',
            'timezone', 'language', 'is_active'
        ]