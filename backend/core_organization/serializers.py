from rest_framework import serializers
from .models import Location, Department, JobPosition, WorkSchedule, OrganizationalAssignment
from core_users.serializers import CustomUserSerializer

class LocationSerializer(serializers.ModelSerializer):
    """Serializer para ubicaciones"""
    departments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Location
        fields = [
            'id', 'name', 'code', 'address', 'city', 'state', 'country',
            'postal_code', 'phone', 'email', 'is_active', 'departments_count',
            'latitude', 'longitude', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_departments_count(self, obj):
        return obj.departments.count()


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer para departamentos"""
    full_path = serializers.CharField(read_only=True)
    employee_count = serializers.SerializerMethodField()  # 🔥 CAMBIAR A METHOD FIELD
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    manager_email = serializers.CharField(source='manager.email', read_only=True)
    children_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'description', 'full_path', 'employee_count',
            'parent', 'parent_name', 'location', 'location_name',
            'manager', 'manager_email', 'email', 'phone',
            'is_active', 'order', 'level', 'children_count',
            'budget_code', 'cost_center', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'level']
    
    def get_children_count(self, obj):
        return obj.children.count()
    
    def get_employee_count(self, obj):
        """🔴 MÉTODO LAZY para employee_count"""
        try:
            from core_permissions.models import UserRole
            descendants = obj.get_descendants(include_self=True)
            descendant_ids = [dept.id for dept in descendants]
            return UserRole.objects.filter(department_id__in=descendant_ids).count()
        except Exception:
            return 0

class DepartmentTreeSerializer(serializers.ModelSerializer):
    """Serializer para árbol de departamentos"""
    children = serializers.SerializerMethodField()
    full_path = serializers.CharField(read_only=True)
    employee_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'description', 'full_path', 'employee_count',
            'is_active', 'level', 'children'
        ]
    
    def get_children(self, obj):
        """Obtener hijos recursivamente para el árbol"""
        children = obj.children.filter(is_active=True)
        return DepartmentTreeSerializer(children, many=True).data


class JobPositionSerializer(serializers.ModelSerializer):
    """Serializer para puestos de trabajo"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_full_path = serializers.CharField(source='department.full_path', read_only=True)
    filled_positions = serializers.IntegerField(read_only=True)
    position_type_display = serializers.CharField(source='get_position_type_display', read_only=True)
    
    class Meta:
        model = JobPosition
        fields = [
            'id', 'title', 'code', 'description', 'department', 'department_name', 'department_full_path',
            'position_type', 'position_type_display', 'level', 'filled_positions',
            'salary_grade', 'min_salary', 'max_salary', 'requirements', 'responsibilities',
            'is_active', 'is_remote', 'openings_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkScheduleSerializer(serializers.ModelSerializer):
    """Serializer para horarios laborales"""
    work_days_list = serializers.SerializerMethodField()
    total_weekly_hours = serializers.FloatField(read_only=True)
    departments_count = serializers.SerializerMethodField()
    job_positions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkSchedule
        fields = [
            'id', 'name', 'code', 'description', 'start_time', 'end_time',
            'break_start', 'break_end', 'work_days_list', 'total_weekly_hours',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'is_flexible', 'core_hours_start', 'core_hours_end',
            'departments', 'job_positions', 'departments_count', 'job_positions_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_work_days_list(self, obj):
        return obj.work_days
    
    def get_departments_count(self, obj):
        return obj.departments.count()
    
    def get_job_positions_count(self, obj):
        return obj.job_positions.count()


class OrganizationalAssignmentSerializer(serializers.ModelSerializer):
    """Serializer para asignaciones organizacionales"""
    user_detail = CustomUserSerializer(source='user', read_only=True)
    department_detail = DepartmentSerializer(source='department', read_only=True)
    job_position_detail = JobPositionSerializer(source='job_position', read_only=True)
    supervisor_email = serializers.CharField(source='supervisor.email', read_only=True)
    work_schedule_name = serializers.CharField(source='work_schedule.name', read_only=True)
    is_current = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = OrganizationalAssignment
        fields = [
            'id', 'user', 'user_detail', 'department', 'department_detail',
            'job_position', 'job_position_detail', 'employee_id', 'hire_date',
            'termination_date', 'supervisor', 'supervisor_email', 'work_schedule', 'work_schedule_name',
            'is_active', 'is_current', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganizationalStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas organizacionales"""
    total_locations = serializers.IntegerField()
    total_departments = serializers.IntegerField()
    total_job_positions = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    active_assignments = serializers.IntegerField()
    departments_by_level = serializers.DictField()
    positions_by_type = serializers.DictField()