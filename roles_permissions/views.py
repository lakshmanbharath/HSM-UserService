from rest_framework import generics, status, filters, permissions
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Role, Module, UserModulePermission
from .serializers import (
    RoleSerializer,
    ModuleSerializer,
    UserModulePermissionSerializer,
)
from HSM_AI import utils
from HSM_AI.helper.pagination import CustomPagination


# ------------------- ROLE CRUD -------------------

# class RoleListCreateView(generics.ListCreateAPIView):
#     """
#     List all roles OR create a new one
#     """
#     serializer_class = RoleSerializer
#     permission_classes = [IsAuthenticated]

#     # authentication_classes = []
#     # permission_classes = []


#     def get_queryset(self):
#         # Only fetch active & not soft-deleted roles
#         return Role.objects.filter(is_deleted=False)

#     def list(self, request, *args, **kwargs):
#         try:
#             roles = self.get_queryset()
#             serializer = self.get_serializer(roles, many=True)
#             return utils.success_response(
#                 message="Roles fetched successfully.",
#                 # data={"roles": serializer.data},
#                 data= serializer.data,
#                 status_code=status.HTTP_200_OK
#             )
#         except Exception as e:
#             return utils.error_response("Failed to fetch roles.", str(e), 500, 500)


class RoleListCreateView(generics.ListCreateAPIView):
    """
    List all roles with pagination & search OR create a new one
    """

    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination  # ✅ Add pagination class
    """ For first time role creation we need to remove authentication """

    # authentication_classes = []
    # permission_classes = []
    def get_queryset(self):
        # Only fetch active & not soft-deleted roles
        queryset = Role.objects.filter(is_deleted=False).order_by("created_date")

        # ✅ search filter
        search_term = self.request.query_params.get("search", None)
        queryset = self.serializer_class.apply_search(queryset, search_term)

        return queryset

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                # DRF's get_paginated_response handles the data structure
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return utils.success_response(
                message="Roles fetched successfully.",
                data=serializer.data,
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return utils.error_response("Failed to fetch roles.", str(e), 500, 500)

    def create(self, request, *args, **kwargs):
        is_role_exist = Role.objects.filter(
            role_name__iexact=request.data.get("role_name"),
            is_deleted=False,
        ).exists()

        if is_role_exist:
            return utils.error_response(
                message="Role name already exists.", errors=None, status_code=400
            )

        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                role = serializer.save()
                return utils.success_response(
                    message="Role added successfully.",
                    data=self.get_serializer(role).data,
                    status_code=status.HTTP_200_OK,
                )

            # Check if role name already exists
            if "role_name" in serializer.errors and any(
                "already exists" in str(err).lower()
                for err in serializer.errors["role_name"]
            ):
                return utils.error_response(
                    message="Role name already exists.", errors=None, status_code=400
                )

            # Generic validation error
            return utils.error_response(
                message="Validation error.", errors=serializer.errors, status_code=400
            )

        except Exception as e:
            return utils.error_response("Failed to create role.", str(e), 500)


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, Update or Soft Delete a single role
    """

    serializer_class = RoleSerializer
    # permission_classes = [IsAuthenticated]
    authentication_classes = []
    permission_classes = []

    def get_queryset(self):
        # Only fetch not soft-deleted roles
        return Role.objects.filter(is_deleted=False)

    def retrieve(self, request, *args, **kwargs):
        try:
            role = self.get_object()
            serializer = self.get_serializer(role)
            return utils.success_response(
                message="Role fetched successfully.",
                data=serializer.data,
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return utils.error_response("Failed to fetch role.", str(e), 500, 500)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            role = self.get_object()  # DRF handles pk lookup automatically

            serializer = self.get_serializer(role, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                return utils.success_response(
                    message="Role updated successfully.",
                    data=serializer.data,
                    status_code=status.HTTP_200_OK,
                )

            if "role_name" in serializer.errors and any(
                "already exists" in str(err).lower()
                for err in serializer.errors["role_name"]
            ):
                return utils.error_response(
                    message="Role name already exists.", errors=None, status_code=400
                )

            return utils.error_response(
                message="Validation error.", errors=serializer.errors, status_code=400
            )

        except Exception as e:
            return utils.error_response("Failed to update role.", str(e), 500)

    # def update(self, request, *args, **kwargs):
    #     try:
    #         role = self.get_object()
    #         serializer = self.get_serializer(role, data=request.data, partial=True)
    #         if serializer.is_valid():
    #             serializer.save()
    #             return utils.success_response(
    #                 message="Role updated successfully.",
    #                 data=serializer.data,
    #                 status_code=status.HTTP_200_OK
    #             )

    #         # Handle duplicate role name
    #         if "role_name" in serializer.errors and any(
    #             "already exists" in str(err).lower() for err in serializer.errors["role_name"]
    #         ):
    #             return utils.error_response(
    #                 message="Role name already exists.",
    #                 errors=None,
    #                 status_code=400
    #             )

    #         # Generic validation error
    #         return utils.error_response(
    #             message="Validation error.",
    #             errors=serializer.errors,
    #             status_code=400
    #         )

    #     except Exception as e:
    #         return utils.error_response("Failed to update role.", str(e), 500)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete instead of actual delete
        """
        try:
            role = self.get_object()
            role.is_deleted = True
            role.save()
            return utils.success_response(
                message="Role removed successfully.",
                data={"id": str(role.id)},
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return utils.error_response("Failed to delete role.", str(e), 500, 500)


# ------------------- MODULE CRUD -------------------


class ModuleListCreateView(generics.ListCreateAPIView):
    serializer_class = ModuleSerializer
    # permission_classes = [IsAuthenticated]
    # authentication_classes = []
    # permission_classes = []
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Module.objects.filter(is_deleted=False).order_by("created_date")

        # ✅ search
        search_term = self.request.query_params.get("search", None)
        queryset = self.serializer_class.apply_search(queryset, search_term)

        # ✅ status filter (active / inactive)
        status_filter = self.request.query_params.get("status", None)
        if status_filter in ["active", "inactive"]:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return utils.success_response(
                message="Modules fetched successfully.",
                data=serializer.data,
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return utils.error_response("Failed to fetch modules.", str(e), 500, 500)

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                module = serializer.save()
                return utils.success_response(
                    message="Module created successfully.",
                    data=self.get_serializer(module).data,
                    status_code=status.HTTP_200_OK,
                )

            # Handle duplicate module name
            if "module_name" in serializer.errors and any(
                "already exists" in str(err).lower()
                for err in serializer.errors["module_name"]
            ):
                return utils.error_response(
                    message="Module name already exists.", errors=None, status_code=400
                )

            # Generic validation error
            return utils.error_response(
                message="Validation error.", errors=serializer.errors, status_code=400
            )

        except Exception as e:
            return utils.error_response("Failed to create module.", str(e), 500, 500)


class ModuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, Update or Soft Delete a single module
    """

    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Module.objects.filter(is_deleted=False)

    def retrieve(self, request, *args, **kwargs):
        try:
            module = self.get_object()
            serializer = self.get_serializer(module)
            return utils.success_response(
                message="Module fetched successfully.",
                data=serializer.data,  # same format as Role
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return utils.error_response("Failed to fetch module.", str(e), 500, 500)

    def update(self, request, *args, **kwargs):
        try:
            module = self.get_object()
            serializer = self.get_serializer(module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return utils.success_response(
                    message="Module updated successfully.",
                    data=serializer.data,
                    status_code=status.HTTP_200_OK,
                )

            # Handle duplicate module_name
            if "module_name" in serializer.errors and any(
                "already exists" in str(err).lower()
                for err in serializer.errors["module_name"]
            ):
                return utils.error_response(
                    message="Module name already exists.", errors=None, status_code=400
                )

            # Handle duplicate path
            if "path" in serializer.errors and any(
                "already exists" in str(err).lower()
                for err in serializer.errors["path"]
            ):
                return utils.error_response(
                    message="Module path already exists.", errors=None, status_code=400
                )

            return utils.error_response(
                message="Validation error.", errors=serializer.errors, status_code=400
            )

        except Exception as e:
            return utils.error_response("Failed to update module.", str(e), 500, 500)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete instead of actual delete
        """
        try:
            module = self.get_object()
            module.is_deleted = True
            module.save()
            return utils.success_response(
                message="Module removed successfully.",
                data={"id": str(module.id)},  # same format as Role
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return utils.error_response("Failed to delete module.", str(e), 500, 500)


# ------------------- USER MODULE PERMISSIONS CRUD -------------------


class MyPermissionsView(generics.GenericAPIView):
    serializer_class = UserModulePermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # fetch only active modules
        return UserModulePermission.objects.filter(
            user_id=self.request.user.id,
            module__status="active",  # ✅ filter
            module__is_deleted=False,
        )

    def get(self, request, *args, **kwargs):
        try:
            permissions = self.get_queryset()
            serializer = self.get_serializer(permissions, many=True)
            return utils.success_response(
                "Your permissions fetched successfully.", serializer.data, 200
            )
        except Exception as e:
            return utils.error_response(
                "Failed to fetch your permissions.", str(e), 500
            )

    def put(self, request, *args, **kwargs):
        return utils.error_response(
            "You are not allowed to update permissions.", {}, 403
        )


class UserPermissionsAdminView(generics.GenericAPIView):
    serializer_class = UserModulePermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self, user_id):
        return UserModulePermission.objects.filter(user_id=user_id)

    def get(self, request, user_id, *args, **kwargs):
        try:
            # if not request.user.is_superuser:
            #     return utils.error_response("Forbidden: Only super admin can fetch other user's permissions.", {}, 403)

            permissions = self.get_queryset(user_id)
            serializer = self.get_serializer(permissions, many=True)
            return utils.success_response(
                "User permissions fetched successfully.", serializer.data, 200
            )
        except Exception as e:
            return utils.error_response(
                "Failed to fetch user permissions.", str(e), 500
            )

    def put(self, request, user_id, *args, **kwargs):
        try:
            permissions_data = request.data.get("permissions", [])
            updated_permissions = []

            for perm_data in permissions_data:
                module_id = perm_data.get("module_id")
                if not module_id:
                    continue

                perm, created = UserModulePermission.objects.get_or_create(
                    user_id=user_id,
                    module_id=module_id,
                )

                # Only update the fields present in payload
                if "visible" in perm_data:
                    perm.visible = perm_data["visible"]

                perms = perm_data.get("permissions", {})
                if "create" in perms:
                    perm.can_create = perms["create"]
                if "read" in perms:
                    perm.can_read = perms["read"]
                if "update" in perms:
                    perm.can_update = perms["update"]
                if "delete" in perms:
                    perm.can_delete = perms["delete"]

                perm.save()
                updated_permissions.append(perm)

            serializer = self.get_serializer(updated_permissions, many=True)
            return utils.success_response(
                "User permissions updated successfully.", serializer.data, 200
            )

        except Exception as e:
            return utils.error_response(
                "Failed to update user permissions.", str(e), 500
            )


class UserModulePermissionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserModulePermissionSerializer

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        return UserModulePermission.objects.filter(user_id=user_id).select_related(
            "module"
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "status": 200,
                "message": "User permissions fetched successfully",
                "data": serializer.data,
            }
        )
