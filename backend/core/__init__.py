import os
import sys

# Agregar el directorio actual al path para asegurar los imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from .celery_app import app as celery_app
except ImportError as e:
    print(f"Error importando celery: {e}")
    # Crear una app celery dummy para desarrollo
    from celery import Celery
    celery_app = Celery('erp_academico')
    print("✅ Celery app dummy creada para desarrollo")

__all__ = ('celery_app',)