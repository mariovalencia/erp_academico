from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core_permissions.models import (
    PermissionModule, GranularPermission, Role, 
    RoleTemplate, UserRole
)
from core_permissions.utils import PermissionManager, RoleTemplateManager

CustomUser = get_user_model()

class Command(BaseCommand):
    help = 'Carga datos iniciales para el sistema de permisos'
    
    def handle(self, *args, **options):
        self.stdout.write('🌱 Sembrando datos iniciales de permisos...')
        
        # 1. Crear módulos básicos
        modules_data = [
            ('academic', 'Académico', 'Gestion académica y cursos'),
            ('financial', 'Financiero', 'Gestión financiera y pagos'),
            ('users', 'Usuarios', 'Gestión de usuarios y perfiles'),
            ('reports', 'Reportes', 'Reportes y analytics'),
            ('system', 'Sistema', 'Configuración del sistema'),
        ]
        
        for code, name, desc in modules_data:
            module, created = PermissionModule.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': desc,
                    'icon': 'folder'
                }
            )
            if created:
                self.stdout.write(f'✅ Módulo creado: {name}')
        
        # 2. Crear permisos para módulo académico
        academic_permissions = {
            'students': ['view', 'create', 'edit', 'delete', 'export'],
            'teachers': ['view', 'create', 'edit', 'delete'],
            'courses': ['view', 'create', 'edit', 'delete', 'manage'],
            'grades': ['view', 'create', 'edit', 'approve'],
            'schedules': ['view', 'create', 'edit'],
        }
        
        created_perms = PermissionManager.create_module_permissions(
            'academic', academic_permissions
        )
        self.stdout.write(f'✅ {len(created_perms)} permisos académicos creados')
        
        # 3. Crear plantilla universitaria
        template = RoleTemplateManager.create_university_template()
        self.stdout.write(f'✅ Plantilla universitaria creada: {template.name}')
        
        # 4. Asignar permisos a roles
        self._assign_role_permissions()
        
        self.stdout.write('🎉 Datos iniciales de permisos sembrados exitosamente!')
    
    def _assign_role_permissions(self):
        """Asigna permisos específicos a cada rol"""
        
        # Permisos para Estudiante
        student_perms = [
            'academic.courses.view.own',
            'academic.grades.view.own',
            'academic.schedules.view.own',
        ]
        
        # Permisos para Docente  
        teacher_perms = [
            'academic.courses.view.all',
            'academic.courses.edit.own',
            'academic.students.view.department',
            'academic.grades.create.own',
            'academic.grades.edit.own',
        ]
        
        # Asignar permisos a roles
        role_permissions = {
            'estudiante': student_perms,
            'docente': teacher_perms,
        }
        
        for role_code, perm_codes in role_permissions.items():
            try:
                role = Role.objects.get(code=role_code)
                result = PermissionManager.bulk_assign_permissions_to_role(role, perm_codes)
                self.stdout.write(f'✅ {len(result["assigned"])} permisos asignados a {role.name}')
            except Role.DoesNotExist:
                self.stdout.write(f'⚠️ Rol {role_code} no encontrado')