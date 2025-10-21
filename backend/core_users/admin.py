from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser,UserProfile

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'created_at']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields':('email','password')}),
        ('Personal info', {'fields':('first_name', 'last_name', 'phone_number')}),
        ('Preferences',{'fields':('timezone','language')}),
        ('Permissions',{'fields':('is_active','is_staff','is_superuser','groups','user_permissions')}),
        ('Important Dates',{'fields':('last_login','created_at','updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes':('wide',),
            'fields':('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user','date_of_birth', 'theme_preference', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    list_filter = ['theme_preference', 'created_at']
    readonly_fields = ['created_at', 'updated_at']