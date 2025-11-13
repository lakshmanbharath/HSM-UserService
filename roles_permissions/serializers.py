from rest_framework import serializers
from .models import Role, Module, UserModulePermission
from django.db.models import Q

class SearchableMixin:
    """
    Reusable mixin to add search functionality inside a serializer.
    Usage:
        - Define `search_fields` in Meta
        - Call `apply_search(queryset, search_term)`
    """
    @classmethod
    def apply_search(cls, queryset, search_term):
        if not search_term:
            return queryset

        search_fields = getattr(cls.Meta, "search_fields", [])
        if not search_fields:
            return queryset

        query = Q()
        for field in search_fields:
            # ✅ ensures icontains runs even if field is nullable
            query |= Q(**{f"{field}__icontains": search_term})

        return queryset.filter(query)

class ModulePermissionSerializer(serializers.Serializer):
    module_id = serializers.UUIDField()
    visible = serializers.BooleanField(default=False)
    can_create = serializers.BooleanField(default=False)
    can_read = serializers.BooleanField(default=False)
    can_update = serializers.BooleanField(default=False)
    can_delete = serializers.BooleanField(default=False)

class RoleSerializer(SearchableMixin, serializers.ModelSerializer):
    module_permissions = ModulePermissionSerializer(many=True)

    class Meta:
        model = Role
        fields = ["id", "role_name", "module_permissions","created_date"]
        search_fields = ["role_name"]


    def create(self, validated_data):
        module_permissions = validated_data.pop("module_permissions", [])
        # ensure string UUIDs
        for perm in module_permissions:
            perm["module_id"] = str(perm.get("module_id"))
        return Role.objects.create(module_permissions=module_permissions, **validated_data)

    def update(self, instance, validated_data):
        instance.role_name = validated_data.get("role_name", instance.role_name)
        module_permissions = validated_data.get("module_permissions", instance.module_permissions)
        # ensure string UUIDs
        for perm in module_permissions:
            perm["module_id"] = str(perm.get("module_id"))
        instance.module_permissions = module_permissions
        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # extra safety: ensure module_id always comes out as string
        for perm in data.get("module_permissions", []):
            if "module_id" in perm:
                perm["module_id"] = str(perm["module_id"])
        return data

# class RoleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Role
#         fields = ['id', 'role_name']  # don’t expose is_deleted

#     def validate_role_name(self, value):
#         if Role.objects.filter(role_name__iexact=value, is_deleted=False).exists():
#             raise serializers.ValidationError("Role name already exists.")
#         return value

class ModuleSerializer(SearchableMixin, serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ["id", "module_name", "path", "description", "status"]
        search_fields = ["module_name", "description"]

    def validate_module_name(self, value):
        module_id = self.instance.id if self.instance else None
        qs = Module.objects.filter(module_name__iexact=value, is_deleted=False)
        if module_id:
            qs = qs.exclude(id=module_id)
        if qs.exists():
            raise serializers.ValidationError("Module name already exists.")
        return value

    # def validate_path(self, value):
    #     module_id = self.instance.id if self.instance else None
    #     qs = Module.objects.filter(path__iexact=value, is_deleted=False)
    #     if module_id:
    #         qs = qs.exclude(id=module_id)
    #     if qs.exists():
    #         raise serializers.ValidationError("Path already exists.")
    #     return value
    def validate_path(self, value):
        # ✅ ensure path always starts with "/"
        if not value.startswith("/"):
            value = f"/{value}"

        module_id = self.instance.id if self.instance else None
        qs = Module.objects.filter(path__iexact=value, is_deleted=False)
        if module_id:
            qs = qs.exclude(id=module_id)
        if qs.exists():
            raise serializers.ValidationError("Path already exists.")
        return value

class UserModulePermissionSerializer(serializers.ModelSerializer):
    userId = serializers.UUIDField(source="user_id", write_only=True)
    permissions = serializers.SerializerMethodField()
    module_id = serializers.UUIDField(source="module.id", read_only=True)
    module_name = serializers.CharField(source="module.module_name", read_only=True)
    module_status = serializers.CharField(source="module.status", read_only=True) 
    module_path = serializers.CharField(source="module.path", read_only=True) 

    class Meta:
        model = UserModulePermission
        fields = [
            'id', 'userId', 'module_id', 'module_name', 'module_path', 'module_status','visible', 'permissions'
        ]

    module_id = serializers.UUIDField(source='module.id', read_only=True)
    
    def get_permissions(self, obj):
        return {
            "create": obj.can_create,
            "read": obj.can_read,
            "update": obj.can_update,
            "delete": obj.can_delete
        }

    def create(self, validated_data):
        user_id = validated_data.pop("user_id")
        module_id = self.context['request'].data.get("module_id")
        permissions = self.context['request'].data.get("permissions", {})

        perm = UserModulePermission.objects.create(
            user_id=user_id,
            module_id=module_id,
            visible=validated_data.get("visible", False),
            can_create=permissions.get("create", False),
            can_read=permissions.get("read", False),
            can_update=permissions.get("update", False),
            can_delete=permissions.get("delete", False)
        )
        return perm

