from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.db.models import Count
from django.http import JsonResponse

from .models import Location, Department, JobPosition, WorkSchedule, OrganizationalAssignment
from .serializers import *

class LocationViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de ubicaciones"""
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'country', 'city']
    search_fields = ['name', 'code', 'address', 'city']
    
    def get_permissions(self):
        """Permisos diferentes según la acción"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        return Location.objects.prefetch_related('departments').order_by('name')


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de departamentos"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'location', 'parent', 'level']
    search_fields = ['name', 'code', 'description']
    
    def get_permissions(self):
        """Permisos diferentes según la acción"""
        if self.action in ['list', 'retrieve', 'tree', 'hierarchy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        return Department.objects.select_related('parent', 'location', 'manager').order_by('tree_id', 'order', 'name')
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Obtener árbol completo de departamentos"""
        root_departments = Department.objects.filter(parent__isnull=True, is_active=True)
        serializer = DepartmentTreeSerializer(root_departments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def hierarchy(self, request, pk=None):
        """Obtener jerarquía completa de un departamento"""
        department = self.get_object()
        
        data = {
            'department': DepartmentSerializer(department).data,
            'ancestors': DepartmentSerializer(department.get_ancestors(), many=True).data,
            'descendants': DepartmentTreeSerializer(department.get_descendants(), many=True).data,
            'siblings': DepartmentSerializer(
                Department.objects.filter(parent=department.parent, is_active=True).exclude(pk=department.pk),
                many=True
            ).data,
        }
        
        return Response(data)
    
    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Obtener empleados de un departamento (incluyendo sub-departamentos)"""
        department = self.get_object()
        
        try:
            # 🔥 CORRECCIÓN: Convertir a lista de IDs
            descendants = department.get_descendants(include_self=True)
            descendant_ids = [dept.id for dept in descendants]
            
            assignments = OrganizationalAssignment.objects.filter(
                department_id__in=descendant_ids, 
                is_active=True
            ).select_related('user', 'job_position')
            
            page = self.paginate_queryset(assignments)
            if page is not None:
                serializer = OrganizationalAssignmentSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = OrganizationalAssignmentSerializer(assignments, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Error obteniendo empleados: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JobPositionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de puestos de trabajo"""
    queryset = JobPosition.objects.all()
    serializer_class = JobPositionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'department', 'position_type', 'level', 'is_remote']
    search_fields = ['title', 'code', 'description']
    
    def get_permissions(self):
        """Permisos diferentes según la acción"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        return JobPosition.objects.select_related('department').prefetch_related('employees').order_by('department', 'level', 'title')
    
    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Obtener empleados en este puesto"""
        job_position = self.get_object()
        assignments = job_position.employees.filter(is_active=True).select_related('user', 'department')
        
        page = self.paginate_queryset(assignments)
        if page is not None:
            serializer = OrganizationalAssignmentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = OrganizationalAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)


class WorkScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de horarios laborales"""
    queryset = WorkSchedule.objects.all()
    serializer_class = WorkScheduleSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]  # Solo admin puede gestionar horarios
    filterset_fields = ['is_active', 'is_flexible']
    search_fields = ['name', 'code', 'description']
    
    def get_queryset(self):
        return WorkSchedule.objects.prefetch_related('departments', 'job_positions').order_by('name')


class OrganizationalAssignmentViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de asignaciones organizacionales"""
    queryset = OrganizationalAssignment.objects.all()
    serializer_class = OrganizationalAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'department', 'job_position']
    search_fields = ['user__email', 'employee_id', 'job_position__title']
    
    def get_permissions(self):
        """Permisos diferentes según la acción"""
        if self.action in ['list', 'retrieve', 'my_assignment']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        return OrganizationalAssignment.objects.select_related(
            'user', 'department', 'job_position', 'supervisor', 'work_schedule'
        ).order_by('department', 'job_position')
    
    @action(detail=False, methods=['get'])
    def my_assignment(self, request):
        """Obtener la asignación del usuario actual"""
        try:
            assignment = OrganizationalAssignment.objects.get(user=request.user, is_active=True)
            serializer = OrganizationalAssignmentSerializer(assignment)
            return Response(serializer.data)
        except OrganizationalAssignment.DoesNotExist:
            return Response(
                {'detail': 'No se encontró asignación organizacional activa'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def by_department(self, request):
        """Obtener asignaciones por departamento"""
        department_id = request.query_params.get('department_id')
        if not department_id:
            return Response(
                {'error': 'department_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            department = Department.objects.get(id=department_id)
            descendants = department.get_descendants(include_self=True)
            
            assignments = OrganizationalAssignment.objects.filter(
                department__in=descendants,
                is_active=True
            ).select_related('user', 'job_position')
            
            serializer = OrganizationalAssignmentSerializer(assignments, many=True)
            return Response(serializer.data)
            
        except Department.DoesNotExist:
            return Response(
                {'error': 'Departamento no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )


class OrganizationalStatsView(APIView):
    """Vista para estadísticas organizacionales"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener estadísticas generales de la organización"""
        
        # Estadísticas básicas
        stats = {
            'total_locations': Location.objects.filter(is_active=True).count(),
            'total_departments': Department.objects.filter(is_active=True).count(),
            'total_job_positions': JobPosition.objects.filter(is_active=True).count(),
            'total_assignments': OrganizationalAssignment.objects.count(),
            'active_assignments': OrganizationalAssignment.objects.filter(is_active=True).count(),
        }
        
        # Departamentos por nivel
        departments_by_level = Department.objects.filter(is_active=True).values('level').annotate(
            count=Count('id')
        ).order_by('level')
        stats['departments_by_level'] = {f'level_{item["level"]}': item['count'] for item in departments_by_level}
        
        # Puestos por tipo
        positions_by_type = JobPosition.objects.filter(is_active=True).values('position_type').annotate(
            count=Count('id')
        ).order_by('position_type')
        stats['positions_by_type'] = {item['position_type']: item['count'] for item in positions_by_type}
        
        return Response(stats)