from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """
    Manager personalizado para CustomUser donde el email es el campo de identificación.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Crea y guarda un usuario con el email y password proporcionados.
        """
        if not email:
            raise ValueError('El email debe ser proporcionado')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con el email y password proporcionados.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado para el Core Empresarial.
    Reemplaza el modelo User por defecto de Django.
    """
    #AGREGAR EL MANAGER PERSONALIZADO
    objects = CustomUserManager()

    # Remover el campo username y usar email como identificador principal
    username = None
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )
    
    # Campos adicionales para el core empresarial
    phone_number = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        null=True
    )
    timezone = models.CharField(
        _('timezone'),
        max_length=50,
        default='America/El_Salvador'
    )
    language = models.CharField(
        _('language'),
        max_length=10,
        default='es'
    )
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Designates whether this user has verified their email.')
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # SOBRESCRIBIR los campos groups y user_permissions con related_name único
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="customuser_set",  # 🔥 NOMBRE ÚNICO
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="customuser_set",  # 🔥 NOMBRE ÚNICO
        related_query_name="customuser",
    )
    
    # Configuración para usar email como campo de autenticación
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'core_users'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

class UserProfile(models.Model):
    """
    Perfil extendido para información adicional del usuario.
    Separado del modelo principal para mantener CustomUser limpio.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Información de perfil
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='profiles/',
        blank=True,
        null=True
    )
    bio = models.TextField(_('biography'), blank=True)
    date_of_birth = models.DateField(_('date of birth'), blank=True, null=True)
    
    # Preferencias de notificación
    email_notifications = models.BooleanField(_('email notifications'), default=True)
    push_notifications = models.BooleanField(_('push notifications'), default=True)
    in_app_notifications = models.BooleanField(_('in-app notifications'), default=True)
    
    # Configuraciones de sistema
    theme_preference = models.CharField(
        _('theme preference'),
        max_length=10,
        choices=[
            ('light', _('Light')),
            ('dark', _('Dark')),
            ('auto', _('Auto'))
        ],
        default='auto'
    )
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'core_user_profiles'
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
    
    def __str__(self):
        return f"Profile of {self.user.email}"