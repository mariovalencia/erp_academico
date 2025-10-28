from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'locations', views.LocationViewSet, basename='locations')
router.register(r'departments', views.DepartmentViewSet, basename='departments')
router.register(r'job-positions', views.JobPositionViewSet, basename='job-positions')
router.register(r'work-schedules', views.WorkScheduleViewSet, basename='work-schedules')
router.register(r'assignments', views.OrganizationalAssignmentViewSet, basename='assignments')

# URLs para acciones personalizadas
department_urls = [
    path('tree/', views.DepartmentViewSet.as_view({'get': 'tree'}), name='departments-tree'),
]

assignment_urls = [
    path('my_assignment/', views.OrganizationalAssignmentViewSet.as_view({'get': 'my_assignment'}), name='my-assignment'),
    path('by_department/', views.OrganizationalAssignmentViewSet.as_view({'get': 'by_department'}), name='assignments-by-department'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', views.OrganizationalStatsView.as_view(), name='organization-stats'),
    path('departments/', include(department_urls)),
    path('assignments/', include(assignment_urls)),
]

app_name = 'core_organization'