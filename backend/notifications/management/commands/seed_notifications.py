# notifications/management/commands/seed_notifications.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.models import NotificationChannel, NotificationTemplate

class Command(BaseCommand):
    help = 'Crea datos iniciales para el sistema de notificaciones'
    
    def handle(self, *args, **options):
        self.stdout.write('Creando datos iniciales para notificaciones...')
        
        # Crear canales básicos
        channels_data = [
            {'code': 'email', 'name': 'Correo Electrónico', 'channel_type': 'email'},
            {'code': 'in_app', 'name': 'Notificación en App', 'channel_type': 'in_app'},
            {'code': 'push', 'name': 'Push Notification', 'channel_type': 'push'},
            {'code': 'sms', 'name': 'SMS', 'channel_type': 'sms'},
        ]
        
        channels = {}
        for channel_data in channels_data:
            channel, created = NotificationChannel.objects.get_or_create(
                code=channel_data['code'],
                defaults=channel_data
            )
            channels[channel.code] = channel
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Canal creado: {channel.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ Canal ya existe: {channel.name}'))
        
        # Crear plantillas básicas
        templates_data = [
            {
                'code': 'welcome_email',
                'name': 'Email de Bienvenida',
                'subject': 'Bienvenido a {{ app_name }}',
                'body': '''Hola {{ user_name }},

¡Bienvenido a {{ app_name }}! Estamos emocionados de tenerte con nosotros.

Tu cuenta ha sido creada exitosamente y ya puedes comenzar a usar todas las funcionalidades del sistema.

Saludos,
El equipo de {{ app_name }}''',
                'body_html': '''<h1>Bienvenido a {{ app_name }}</h1>
<p>Hola <strong>{{ user_name }}</strong>,</p>
<p>¡Bienvenido! Estamos emocionados de tenerte con nosotros.</p>
<p>Tu cuenta ha sido creada exitosamente y ya puedes comenzar a usar todas las funcionalidades del sistema.</p>
<br>
<p>Saludos,<br>
<strong>El equipo de {{ app_name }}</strong></p>'''
            },
            {
                'code': 'security_alert',
                'name': 'Alerta de Seguridad',
                'subject': 'Alerta de Seguridad - Actividad Sospechosa',
                'body': '''Hola {{ user_name }},

Hemos detectado actividad sospechosa en tu cuenta. 

- Evento: {{ event_type }}
- Fecha: {{ timestamp }}
- Dirección IP: {{ ip_address }}

Si no reconoces esta actividad, por favor cambia tu contraseña inmediatamente.

Saludos,
Equipo de Seguridad''',
                'body_html': '''<h2>🚨 Alerta de Seguridad</h2>
<p>Hola <strong>{{ user_name }}</strong>,</p>
<p>Hemos detectado actividad sospechosa en tu cuenta.</p>
<ul>
    <li><strong>Evento:</strong> {{ event_type }}</li>
    <li><strong>Fecha:</strong> {{ timestamp }}</li>
    <li><strong>Dirección IP:</strong> {{ ip_address }}</li>
</ul>
<p>Si no reconoces esta actividad, por favor cambia tu contraseña inmediatamente.</p>
<br>
<p><strong>Equipo de Seguridad</strong></p>'''
            },
            {
                'code': 'failed_login_attempt',
                'name': 'Intento de Login Fallido',
                'subject': 'Intento de acceso fallido a tu cuenta',
                'body': '''Hola {{ user_name }},

Se ha detectado un intento fallido de acceso a tu cuenta.

- Fecha: {{ timestamp }}
- IP: {{ ip_address }}

Si fuiste tú, puedes ignorar este mensaje. Si no reconoces este intento, por favor verifica la seguridad de tu cuenta.

Saludos,
Equipo de Seguridad''',
                'body_html': '''<h2>⚠️ Intento de acceso fallido</h2>
<p>Hola <strong>{{ user_name }}</strong>,</p>
<p>Se ha detectado un intento fallido de acceso a tu cuenta.</p>
<ul>
    <li><strong>Fecha:</strong> {{ timestamp }}</li>
    <li><strong>IP:</strong> {{ ip_address }}</li>
</ul>
<p>Si fuiste tú, puedes ignorar este mensaje. Si no reconoces este intento, por favor verifica la seguridad de tu cuenta.</p>
<br>
<p><strong>Equipo de Seguridad</strong></p>'''
            },
            {
                'code': 'new_user_registered',
                'name': 'Nuevo Usuario Registrado',
                'subject': 'Nuevo usuario registrado en el sistema',
                'body': '''Se ha registrado un nuevo usuario en el sistema.

- Email: {{ user_email }}
- Fecha de registro: {{ registration_date }}

Puedes revisar los detalles del usuario en el panel de administración.

Saludos,
Sistema''',
                'body_html': '''<h2>👤 Nuevo usuario registrado</h2>
<p>Se ha registrado un nuevo usuario en el sistema.</p>
<ul>
    <li><strong>Email:</strong> {{ user_email }}</li>
    <li><strong>Fecha de registro:</strong> {{ registration_date }}</li>
</ul>
<p>Puedes revisar los detalles del usuario en el panel de administración.</p>
<br>
<p><strong>Sistema</strong></p>'''
            },
            {
                'code': 'important_audit_event',
                'name': 'Evento Importante de Auditoría',
                'subject': 'Evento importante registrado en auditoría',
                'body': '''Se ha registrado un evento importante en el sistema de auditoría.

- Tipo de evento: {{ event_type }}
- Descripción: {{ description }}
- Usuario involucrado: {{ user_involved }}
- Fecha: {{ timestamp }}

Revisa el sistema de auditoría para más detalles.

Saludos,
Sistema de Auditoría''',
                'body_html': '''<h2>📊 Evento importante de auditoría</h2>
<p>Se ha registrado un evento importante en el sistema de auditoría.</p>
<ul>
    <li><strong>Tipo de evento:</strong> {{ event_type }}</li>
    <li><strong>Descripción:</strong> {{ description }}</li>
    <li><strong>Usuario involucrado:</strong> {{ user_involved }}</li>
    <li><strong>Fecha:</strong> {{ timestamp }}</li>
</ul>
<p>Revisa el sistema de auditoría para más detalles.</p>
<br>
<p><strong>Sistema de Auditoría</strong></p>'''
            },
        ]
        
        for template_data in templates_data:
            template, created = NotificationTemplate.objects.get_or_create(
                code=template_data['code'],
                defaults={
                    'name': template_data['name'],
                    'subject': template_data['subject'],
                    'body': template_data['body'],
                    'body_html': template_data.get('body_html', ''),
                }
            )
            
            if created:
                # Asignar canales por defecto (email e in_app para todas)
                template.channels.add(channels['email'], channels['in_app'])
                self.stdout.write(self.style.SUCCESS(f'✅ Plantilla creada: {template.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ Plantilla ya existe: {template.name}'))
        
        self.stdout.write(self.style.SUCCESS('🎉 Datos iniciales creados exitosamente!'))