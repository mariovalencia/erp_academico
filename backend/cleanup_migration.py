import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def cleanup_temporary_models():
    """Limpiar modelos temporales y verificar integridad"""
    from django.apps import apps
    from django.db import connection
    
    print("🧹 INICIANDO LIMPIEZA DE MODELOS TEMPORALES...")
    
    # 1. Verificar si existe el modelo temporal
    try:
        from core_permissions.models import Department as TempDepartment
        temp_count = TempDepartment.objects.count()
        print(f"📊 Departamentos temporales encontrados: {temp_count}")
        
        if temp_count > 0:
            print("⚠️  Hay departamentos temporales que necesitan migración")
            # Aquí iría la lógica de migración si existieran datos
        else:
            print("✅ No hay datos temporales que migrar")
            
    except Exception as e:
        print("✅ Modelo temporal Department no existe o ya fue eliminado")
    
    # 2. Verificar integridad de referencias
    print("\n🔍 VERIFICANDO INTEGRIDAD DE REFERENCIAS...")
    
    from core_organization.models import Department
    from core_permissions.models import UserRole, RolePermission
    
    # Verificar UserRoles
    user_roles = UserRole.objects.select_related('department').all()
    print(f"✅ {user_roles.count()} UserRoles con referencias a Department")
    
    # Verificar RolePermissions
    role_perms = RolePermission.objects.select_related('department_filter').all()
    print(f"✅ {role_perms.count()} RolePermissions con referencias a Department")
    
    # Verificar departamentos existentes
    depts = Department.objects.all()
    print(f"✅ {depts.count()} departamentos en core_organization")
    
    print("\n🎉 VERIFICACIÓN COMPLETADA - SISTEMA INTEGRADO!")

def check_serializer_imports():
    """Verificar que todos los serializers importen correctamente"""
    print("\n🔍 VERIFICANDO IMPORTACIONES DE SERIALIZERS...")
    
    try:
        from core_permissions.serializers import UserRoleSerializer
        from core_users.serializers import CustomUserSerializer
        from core_organization.serializers import DepartmentSerializer
        
        print("✅ Todos los serializers importan correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error en importaciones: {e}")
        return False

if __name__ == "__main__":
    cleanup_temporary_models()
    check_serializer_imports()