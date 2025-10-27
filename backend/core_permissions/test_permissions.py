# test_permissions.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core_permissions.models import PermissionModule, GranularPermission
from core_permissions.utils import PermissionManager

# Probar crear un permiso manualmente
def test_single_permission():
    module = PermissionModule.objects.get(code='academic')
    
    try:
        perm = GranularPermission.objects.create(
            module=module,
            functionality='Estudiantes',
            functionality_code='students',
            action='view',
            scope='all'
        )
        print(f"✅ Permiso creado: {perm.name}")
        print(f"   Código: {perm.permission_code}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Probar creación masiva
def test_bulk_permissions():
    academic_permissions = {
        'students': ['view', 'create'],
        'teachers': ['view'],
    }
    
    result = PermissionManager.create_module_permissions('academic', academic_permissions)
    print(f"✅ {len(result)} permisos creados exitosamente")
    for perm in result:
        print(f"   - {perm.permission_code}")

if __name__ == '__main__':
    print("🧪 Probando creación de permisos...")
    
    if test_single_permission():
        test_bulk_permissions()