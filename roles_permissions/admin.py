from django.contrib import admin
from .models import Role, Module, UserModulePermission

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("role_name", "created_date", "modified_date")
    search_fields = ("role_name",)
    readonly_fields = ("created_date", "modified_date")

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("module_name", "path", "status", "created_date")
    list_filter = ("status",)
    search_fields = ("module_name", "path")
    readonly_fields = ("created_date", "modified_date")

@admin.register(UserModulePermission)
class UserModulePermissionAdmin(admin.ModelAdmin):
    list_display = (
        "user", "module", "visible",
        "can_create", "can_read", "can_update", "can_delete"
    )
    list_filter = ("visible", "can_create", "can_read", "can_update", "can_delete")
    search_fields = ("user__email", "module__module_name")
    readonly_fields = ("created_date", "modified_date")
