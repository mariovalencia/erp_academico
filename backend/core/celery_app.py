# backend/core/celery_app.py - AGREGAR NUEVAS TAREAS
import os
from celery import Celery
from celery.schedules import crontab

# Establecer la configuración de Django por defecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('erp_academico')

# Usar la configuración de Django para Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configuración de tareas periódicas
app.conf.beat_schedule = {
    # Procesar notificaciones pendientes cada 5 minutos
    'process-pending-notifications-every-5-minutes': {
        'task': 'notifications.tasks.process_pending_notifications',
        'schedule': crontab(minute='*/5'),
    },
    
    # Limpiar notificaciones antiguas cada día a las 2:00 AM
    'cleanup-old-notifications-daily': {
        'task': 'notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # Enviar resumen diario a las 6:00 PM
    'send-daily-summary': {
        'task': 'notifications.tasks.send_daily_notifications_summary', 
        'schedule': crontab(hour=18, minute=0),
    },
    
    # Reintentar notificaciones fallidas cada hora
    'retry-failed-notifications-hourly': {
        'task': 'notifications.tasks.retry_failed_notifications',
        'schedule': crontab(minute=0),  # Cada hora en el minuto 0
    },
}

# Auto-descubrir tasks en todas las apps de Django
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')