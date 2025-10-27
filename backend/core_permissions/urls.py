from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'modules', views.PermissionModuleViewSet, basename='permission-modules')
router.register(r'permissions', views.GranularPermissionViewSet, basename='permissions')
router.register(r'roles', views.RoleViewSet, basename='roles')
router.register(r'user-roles', views.UserRoleViewSet, basename='user-roles')
router.register(r'role-templates', views.RoleTemplateViewSet, basename='role-templates')
router.register(r'departments', views.DepartmentViewSet, basename='departments')

urlpatterns = [
    path('', include(router.urls)),
    
    # URLs adicionales para utilidades
    path('utilities/sync-permissions/', views.PermissionUtilitiesView.as_view(), name='sync-permissions'),
    path('system/stats/', views.SystemPermissionsView.as_view(), name='system-stats'),
    
    # URLs para acciones específicas
    path('check-permission/', views.UserRoleViewSet.as_view({'post': 'check_permission'}), name='check-permission'),
    path('user-permissions/', views.UserRoleViewSet.as_view({'get': 'user_permissions'}), name='user-permissions'),
    path('assign-role/', views.UserRoleViewSet.as_view({'post': 'assign_role'}), name='assign-role'),
]

app_name = 'core_permissions'