from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin
from .models import Location, Department, JobPosition, WorkSchedule, OrganizationalAssignment

CustomUser = get_user_model()

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'city', 'country', 'is_active', 
        'created_at'
    ]
    list_filter = [
        'is_active', 'country', 'city', 'created_at'
    ]
    search_fields = [
        'name', 'code', 'address', 'city', 'state', 'country'
    ]
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name', 'code', 'is_active'
            )
        }),
        (_('Address'), {
            'fields': (
                'address', 'city', 'state', 'country', 'postal_code'
            )
        }),
        (_('Contact'), {
            'fields': ('phone', 'email')
        }),
        (_('Geographic Coordinates'), {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Department)
class DepartmentAdmin(DraggableMPTTAdmin):
    list_display = [
        'tree_actions', 'indented_title', 'code', 'manager', 
        'location', 'employee_count', 'is_active', 'created_at'
    ]
    list_display_links = ['indented_title']
    list_filter = [
        'is_active', 'location', 'created_at'
    ]
    search_fields = [
        'name', 'code', 'manager__email',
        'manager__first_name', 'manager__last_name'
    ]
    list_editable = ['is_active']
    readonly_fields = [
        'created_at', 'updated_at', 'employee_count', 'full_path'
    ]
    raw_id_fields = ['parent', 'location', 'manager']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name', 'code', 'description', 'is_active', 'order'
            )
        }),
        (_('Hierarchy'), {
            'fields': ('parent',)
        }),
        (_('Location & Contact'), {
            'fields': (
                'location', 'manager', 'email', 'phone'
            )
        }),
        (_('Budget & Resources'), {
            'fields': ('budget_code', 'cost_center'),
            'classes': ('collapse',)
        }),
        (_('Statistics'), {
            'fields': ('employee_count', 'full_path'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def indented_title(self, instance):
        return format_html(
            '<div style="text-indent:{}px">{}</div>',
            instance._mpttfield('level') * self.mptt_level_indent,
            instance.name
        )
    indented_title.short_description = _('Department Name')
    
    def employee_count(self, obj):
        return obj.employee_count
    employee_count.short_description = _('Employees')

@admin.register(JobPosition)
class JobPositionAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'code', 'department', 'position_type', 
        'level', 'filled_positions', 'openings_count', 
        'is_active', 'created_at'
    ]
    list_filter = [
        'is_active', 'position_type', 'level', 'department', 
        'is_remote', 'created_at'
    ]
    search_fields = [
        'title', 'code', 'department__name',
        'requirements', 'responsibilities'
    ]
    list_editable = ['is_active', 'openings_count']
    readonly_fields = ['created_at', 'updated_at', 'filled_positions']
    raw_id_fields = ['department']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'title', 'code', 'description', 'department',
                'position_type', 'level', 'is_active'
            )
        }),
        (_('Compensation'), {
            'fields': (
                'salary_grade', 'min_salary', 'max_salary'
            ),
            'classes': ('collapse',)
        }),
        (_('Job Details'), {
            'fields': (
                'requirements', 'responsibilities', 
                'is_remote', 'openings_count'
            )
        }),
        (_('Statistics'), {
            'fields': ('filled_positions',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def filled_positions(self, obj):
        return obj.filled_positions
    filled_positions.short_description = _('Filled Positions')

@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'start_time', 'end_time', 
        'total_weekly_hours', 'is_flexible', 'is_active', 
        'created_at'
    ]
    list_filter = [
        'is_active', 'is_flexible', 'created_at'
    ]
    search_fields = [
        'name', 'code', 'description'
    ]
    list_editable = ['is_active']
    readonly_fields = [
        'created_at', 'updated_at', 'work_days', 'total_weekly_hours'
    ]
    # 🔥 CORRECCIÓN: Eliminado filter_horizontal para departments y job_positions
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name', 'code', 'description', 'is_active'
            )
        }),
        (_('Schedule Details'), {
            'fields': (
                'start_time', 'end_time',
                'break_start', 'break_end'
            )
        }),
        (_('Work Days'), {
            'fields': (
                'monday', 'tuesday', 'wednesday', 'thursday',
                'friday', 'saturday', 'sunday'
            )
        }),
        (_('Flexibility'), {
            'fields': (
                'is_flexible', 'core_hours_start', 'core_hours_end'
            ),
            'classes': ('collapse',)
        }),
        (_('Application'), {
            'fields': ('departments', 'job_positions')
        }),
        (_('Statistics'), {
            'fields': ('work_days', 'total_weekly_hours'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def work_days(self, obj):
        return ", ".join(obj.work_days) if obj.work_days else _("No days selected")
    work_days.short_description = _('Work Days')
    
    def total_weekly_hours(self, obj):
        return f"{obj.total_weekly_hours} hrs"
    total_weekly_hours.short_description = _('Weekly Hours')

@admin.register(OrganizationalAssignment)
class OrganizationalAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'employee_id', 'department', 'job_position',
        'supervisor', 'hire_date', 'is_current', 'is_active',
        'created_at'
    ]
    list_filter = [
        'is_active', 'department', 'job_position', 
        'hire_date', 'created_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'employee_id', 'department__name', 'job_position__title',
        'supervisor__email', 'supervisor__first_name', 'supervisor__last_name'
    ]
    list_editable = ['is_active']
    readonly_fields = [
        'created_at', 'updated_at', 'is_current'
    ]
    raw_id_fields = [
        'user', 'department', 'job_position', 
        'supervisor', 'work_schedule'
    ]
    
    fieldsets = (
        (_('Assignment Details'), {
            'fields': (
                'user', 'employee_id', 'department', 'job_position'
            )
        }),
        (_('Employment Information'), {
            'fields': (
                'hire_date', 'termination_date', 'supervisor'
            )
        }),
        (_('Schedule'), {
            'fields': ('work_schedule',)
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_current')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_current(self, obj):
        return obj.is_current
    is_current.boolean = True
    is_current.short_description = _('Current Assignment')