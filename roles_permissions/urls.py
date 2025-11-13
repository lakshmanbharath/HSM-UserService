from django.urls import path
from .views import (
    RoleListCreateView,
    RoleDetailView,
    ModuleListCreateView,
    ModuleDetailView,
    MyPermissionsView,
    UserPermissionsAdminView,
    UserModulePermissionListView
)

urlpatterns = [
    # -------- Roles --------
    path("roles/", RoleListCreateView.as_view(), name="role-list-create"),
    path("roles/<uuid:pk>/", RoleDetailView.as_view(), name="role-detail"),

    # -------- Modules --------
    path("modules/", ModuleListCreateView.as_view(), name="module-list-create"),
    path("modules/<uuid:pk>/", ModuleDetailView.as_view(), name="module-detail"),

    # -------- User Permissions --------
    path("my-permissions/", MyPermissionsView.as_view(), name="my-permissions"),
    path("user-permissions/<uuid:user_id>/", UserPermissionsAdminView.as_view(), name="user-permissions-admin"),
    path('users/permissions/<uuid:user_id>/', UserModulePermissionListView.as_view(), name='user-permissions'),


    
]
