import uuid
from django.db import models
from django.conf import settings


class BaseModel(models.Model):
    """
    Common fields for all models
    """
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)  # soft delete flag

    class Meta:
        abstract = True

# class Role(BaseModel):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     role_name = models.CharField(max_length=100, unique=True)

#     def __str__(self):
#         return self.role_name

class Role(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role_name = models.CharField(max_length=100, unique=True)

    # store module + permissions directly in JSON
    module_permissions = models.JSONField(default=list)
    # example value:
    # [
    #   {
    #     "module_id": "uuid1",
    #     "visible": true,
    #     "can_create": false,
    #     "can_read": true,
    #     "can_update": false,
    #     "can_delete": false
    #   },
    #   {...}
    # ]

    def __str__(self):
        return self.role_name

class Module(BaseModel):
    """
    Master list of modules (used to build sidebar)
    """
    STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module_name = models.CharField(max_length=100, unique=True)
    path = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)  
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="active"
    )

    def __str__(self):
        return f"{self.module_name} ({self.status})"

class UserModulePermission(BaseModel):
    """
    User-specific permissions for each module
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="module_permissions"
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="user_permissions"
    )

    visible = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_read = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'module')

    def __str__(self):
        return f"{self.user} → {self.module.module_name}"
