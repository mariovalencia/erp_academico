from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from mptt.models import MPTTModel, TreeForeignKey

CustomUser = get_user_model()

class Location(models.Model):
    """
    Ubicaciones físicas (oficinas, sucursales, edificios)
    """
    name = models.CharField(_('location name'), max_length=100)
    code = models.CharField(_('location code'), max_length=50, unique=True)
    address = models.TextField(_('address'), blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    state = models.CharField(_('state/province'), max_length=100, blank=True)
    country = models.CharField(_('country'), max_length=100, default='El Salvador')
    postal_code = models.CharField(_('postal code'), max_length=20, blank=True)
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    email = models.EmailField(_('email'), blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    
    # Coordenadas geográficas
    latitude = models.DecimalField(
        _('latitude'), 
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    longitude = models.DecimalField(
        _('longitude'), 
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'core_organization_locations'
        verbose_name = _('location')
        verbose_name_plural = _('locations')
        ordering = ['name']

    def __str__(self):
        return self.name


class Department(MPTTModel):
    """
    Departamentos/Áreas con estructura jerárquica
    """
    name = models.CharField(_('department name'), max_length=100)
    code = models.CharField(_('department code'), max_length=50, unique=True)
    description = models.TextField(_('description'), blank=True)
    
    # Jerarquía
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('parent department')
    )
    
    # Ubicación física
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departments',
        verbose_name=_('location')
    )
    
    # Metadatos
    is_active = models.BooleanField(_('active'), default=True)
    order = models.PositiveIntegerField(_('order'), default=0)
    
    # Contacto
    manager = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name=_('department manager')
    )
    email = models.EmailField(_('department email'), blank=True)
    phone = models.CharField(_('department phone'), max_length=20, blank=True)
    
    # Presupuesto y recursos
    budget_code = models.CharField(_('budget code'), max_length=50, blank=True)
    cost_center = models.CharField(_('cost center'), max_length=50, blank=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'core_organization_departments'
        verbose_name = _('department')
        verbose_name_plural = _('departments')
        ordering = ['tree_id', 'order', 'name']

    class MPTTMeta:
        order_insertion_by = ['order', 'name']

    def __str__(self):
        return self.name
    
    @property
    def full_path(self):
        """
        Ruta completa del departamento en la jerarquía
        """
        ancestors = self.get_ancestors(include_self=True)
        return ' / '.join([dept.name for dept in ancestors])
    
    @property
    def employee_count(self):
        """
        Número de empleados en este departamento (incluyendo sub-departamentos)
        CORREGIDO: Usar lista de IDs en lugar del QuerySet directamente
        """
        from core_permissions.models import UserRole
        
        try:
            # 🔥 CORRECCIÓN: Convertir a lista de IDs
            descendants = self.get_descendants(include_self=True)
            descendant_ids = [dept.id for dept in descendants]
            
            return UserRole.objects.filter(department_id__in=descendant_ids).count()
        except Exception as e:
            # En caso de error, retornar 0 y loggear el error
            print(f"⚠️ Error calculando employee_count para departamento {self.id}: {e}")
            return 0

class JobPosition(models.Model):
    """
    Puestos de trabajo en la organización
    """
    POSITION_TYPE_CHOICES = [
        ('executive', _('Executive')),
        ('management', _('Management')),
        ('professional', _('Professional')),
        ('technical', _('Technical')),
        ('administrative', _('Administrative')),
        ('support', _('Support')),
        ('intern', _('Intern')),
    ]
    
    title = models.CharField(_('job title'), max_length=100)
    code = models.CharField(_('position code'), max_length=50, unique=True)
    description = models.TextField(_('description'), blank=True)
    
    # Departamento al que pertenece el puesto
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='positions',
        verbose_name=_('department')
    )
    
    # Tipo y nivel del puesto
    position_type = models.CharField(
        _('position type'),
        max_length=20,
        choices=POSITION_TYPE_CHOICES,
        default='professional'
    )
    level = models.PositiveIntegerField(_('job level'), default=1)
    
    # Información de compensación
    salary_grade = models.CharField(_('salary grade'), max_length=20, blank=True)
    min_salary = models.DecimalField(
        _('minimum salary'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    max_salary = models.DecimalField(
        _('maximum salary'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Requisitos
    requirements = models.TextField(_('requirements'), blank=True)
    responsibilities = models.TextField(_('responsibilities'), blank=True)
    
    # Metadatos
    is_active = models.BooleanField(_('active'), default=True)
    is_remote = models.BooleanField(_('remote position'), default=False)
    openings_count = models.PositiveIntegerField(_('number of openings'), default=1)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'core_organization_job_positions'
        verbose_name = _('job position')
        verbose_name_plural = _('job positions')
        ordering = ['department', 'level', 'title']

    def __str__(self):
        return f"{self.title} - {self.department.name}"
    
    @property
    def filled_positions(self):
        """
        Número de posiciones ocupadas
        """
        return self.employees.count()


class WorkSchedule(models.Model):
    """
    Horarios laborales por departamento o puesto
    """
    name = models.CharField(_('schedule name'), max_length=100)
    code = models.CharField(_('schedule code'), max_length=50, unique=True)
    description = models.TextField(_('description'), blank=True)
    
    # Horario estándar
    start_time = models.TimeField(_('start time'))
    end_time = models.TimeField(_('end time'))
    break_start = models.TimeField(_('break start'), null=True, blank=True)
    break_end = models.TimeField(_('break end'), null=True, blank=True)
    
    # Días laborales
    monday = models.BooleanField(_('Monday'), default=True)
    tuesday = models.BooleanField(_('Tuesday'), default=True)
    wednesday = models.BooleanField(_('Wednesday'), default=True)
    thursday = models.BooleanField(_('Thursday'), default=True)
    friday = models.BooleanField(_('Friday'), default=True)
    saturday = models.BooleanField(_('Saturday'), default=False)
    sunday = models.BooleanField(_('Sunday'), default=False)
    
    # Flexibilidad
    is_flexible = models.BooleanField(_('flexible schedule'), default=False)
    core_hours_start = models.TimeField(_('core hours start'), null=True, blank=True)
    core_hours_end = models.TimeField(_('core hours end'), null=True, blank=True)
    
    # Aplicación
    departments = models.ManyToManyField(
        Department,
        related_name='work_schedules',
        blank=True,
        verbose_name=_('departments')
    )
    job_positions = models.ManyToManyField(
        JobPosition,
        related_name='work_schedules',
        blank=True,
        verbose_name=_('job positions')
    )
    
    is_active = models.BooleanField(_('active'), default=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'core_organization_work_schedules'
        verbose_name = _('work schedule')
        verbose_name_plural = _('work schedules')
        ordering = ['name']

    def __str__(self):
        return self.name
    
    @property
    def work_days(self):
        """
        Días laborales como lista
        """
        days = []
        if self.monday: days.append(_('Monday'))
        if self.tuesday: days.append(_('Tuesday'))
        if self.wednesday: days.append(_('Wednesday'))
        if self.thursday: days.append(_('Thursday'))
        if self.friday: days.append(_('Friday'))
        if self.saturday: days.append(_('Saturday'))
        if self.sunday: days.append(_('Sunday'))
        return days
    
    @property
    def total_weekly_hours(self):
        """
        Total de horas laborales por semana
        """
        from datetime import datetime, timedelta
        
        work_days_count = sum([
            self.monday, self.tuesday, self.wednesday,
            self.thursday, self.friday, self.saturday, self.sunday
        ])
        
        # Calcular horas por día
        start_dt = datetime.combine(datetime.today(), self.start_time)
        end_dt = datetime.combine(datetime.today(), self.end_time)
        
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        
        daily_hours = (end_dt - start_dt).seconds / 3600
        
        # Restar tiempo de break si existe
        if self.break_start and self.break_end:
            break_start_dt = datetime.combine(datetime.today(), self.break_start)
            break_end_dt = datetime.combine(datetime.today(), self.break_end)
            
            if break_end_dt < break_start_dt:
                break_end_dt += timedelta(days=1)
            
            break_hours = (break_end_dt - break_start_dt).seconds / 3600
            daily_hours -= break_hours
        
        return round(daily_hours * work_days_count, 2)


class OrganizationalAssignment(models.Model):
    """
    Asignación de usuarios a la estructura organizacional
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='organizational_assignment',
        verbose_name=_('user')
    )
    
    # Asignación principal
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name=_('department')
    )
    job_position = models.ForeignKey(
        JobPosition,
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name=_('job position')
    )
    
    # Información de empleado
    employee_id = models.CharField(
        _('employee ID'),
        max_length=50,
        unique=True,
        blank=True,
        null=True
    )
    hire_date = models.DateField(_('hire date'), null=True, blank=True)
    termination_date = models.DateField(_('termination date'), null=True, blank=True)
    
    # Jefe directo
    supervisor = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        verbose_name=_('supervisor')
    )
    
    # Horario asignado
    work_schedule = models.ForeignKey(
        WorkSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments',
        verbose_name=_('work schedule')
    )
    
    # Estado
    is_active = models.BooleanField(_('active assignment'), default=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'core_organization_assignments'
        verbose_name = _('organizational assignment')
        verbose_name_plural = _('organizational assignments')
        ordering = ['department', 'job_position']

    def __str__(self):
        return f"{self.user.email} - {self.job_position.title}"
    
    @property
    def is_current(self):
        """
        Verificar si la asignación está activa actualmente
        """
        from django.utils import timezone
        today = timezone.now().date()
        
        if not self.is_active:
            return False
        
        if self.termination_date and self.termination_date < today:
            return False
        
        return True