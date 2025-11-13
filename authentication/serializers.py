import re
from django.db import transaction
from rest_framework import serializers
from .models import Users
from roles_permissions.models import UserModulePermission, Module

EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

# class UserSerializer(serializers.ModelSerializer):
#     id = serializers.UUIDField(read_only=True)
#     role_name = serializers.CharField(source="role.role_name", read_only=True)

#     class Meta:
#         model = Users
#         fields = [
#             "id",
#             "first_name",
#             "last_name",
#             "email",
#             "phone_number",
#             "country_code",
#             "password",
#             "role",
#             "role_name",
#             "status",
#             "is_deleted",
#         ]
#         extra_kwargs = {
#             "password": {"write_only": True},
#             "email": {"error_messages": {"required": "Email is required."}},
#             "first_name": {"error_messages": {"required": "First name is required."}},
#             "last_name": {"error_messages": {"required": "Last name is required."}},
#             "phone_number": {"error_messages": {"required": "Phone number is required."}},
#             "role": {"error_messages": {"required": "Role is required."}},
#         }

#     def validate_email(self, value):
#         if not re.match(EMAIL_REGEX, value):
#             raise serializers.ValidationError("Please enter a valid email address.")
#         return value

#     def create(self, validated_data):
#         email = validated_data["email"]
#         if Users.objects.filter(email=email, is_deleted=False).exists():
#             raise serializers.ValidationError({"email": "User already exists with this email."})

#         password = validated_data.pop("password")
#         user = Users(**validated_data)
#         user.set_password(password)  # hash password
#         user.save()
#         return user

#     def update(self, instance, validated_data):
#         if instance.is_deleted:
#             raise serializers.ValidationError({"detail": "Cannot update a soft-deleted user."})

#         password = validated_data.pop("password", None)

#         with transaction.atomic():
#             if password:
#                 instance.set_password(password)

#             for attr, value in validated_data.items():
#                 setattr(instance, attr, value)

#             instance.save()

#         return instance


class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    role_name = serializers.CharField(source="role.role_name", read_only=True)

    class Meta:
        model = Users
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "country_code",
            "password",
            "role",
            "role_name",
            "status",
            "is_deleted",
            "title",
        ]
        # === CHANGES MADE HERE ===
        extra_kwargs = {
            # 1. Make password NOT REQUIRED for PUT/PATCH requests
            "password": {
                "write_only": True,
                # Set required=False so it's not validated as required on PUT/PATCH
                "required": False,
            },
            # 2. Make email NOT REQUIRED for PUT/PATCH requests
            "email": {
                "required": False,  # Setting False makes it optional for updates
                "error_messages": {"required": "Email is required."},
            },
            # The rest of the fields should probably also be optional for PATCH requests.
            "first_name": {
                "required": False,
                "error_messages": {"required": "First name is required."},
            },
            "last_name": {
                "required": False,
                "error_messages": {"required": "Last name is required."},
            },
            "phone_number": {
                "required": False,
                "error_messages": {"required": "Phone number is required."},
            },
            "role": {
                "required": False,
                "error_messages": {"required": "Role is required."},
            },
            "country_code": {"required": False},  # Adding country_code for consistency
        }
        # =========================

    # ... validate_email remains the same ...
    def validate_email(self, value):
        if not re.match(EMAIL_REGEX, value):
            raise serializers.ValidationError("Please enter a valid email address.")
        return value

    # ... create method remains the same ...
    # def create(self, validated_data):
    #     # NOTE: Even with 'required: False' in extra_kwargs, password must be present
    #     # here, but DRF ensures it's passed from the request for POST.
    #     # If password is missing, a KeyError will occur, which you can catch
    #     # and re-raise as a validation error if necessary.

    #     email = validated_data["email"]
    #     if Users.objects.filter(email=email, is_deleted=False).exists():
    #         raise serializers.ValidationError({"email": "User already exists with this email."})

    #     password = validated_data.pop("password") # Will raise KeyError if missing on POST
    #     user = Users(**validated_data)
    #     user.set_password(password)  # hash password
    #     user.save()
    #     return user

    def create(self, validated_data):
        email = validated_data["email"]
        if Users.objects.filter(email=email, is_deleted=False).exists():
            raise serializers.ValidationError(
                {"email": "User already exists with this email."}
            )

        password = validated_data.pop("password")
        user = Users(**validated_data)
        user.set_password(password)
        user.save()

        # -------- Copy role permissions to UserModulePermission --------
        role = user.role
        role_permissions = role.module_permissions  # JSON list

        for perm in role_permissions:
            module_id = perm.get("module_id")
            if not module_id:
                continue

            UserModulePermission.objects.create(
                user=user,
                module_id=module_id,
                visible=perm.get("visible", False),
                can_create=perm.get("can_create", False),
                can_read=perm.get("can_read", False),
                can_update=perm.get("can_update", False),
                can_delete=perm.get("can_delete", False),
            )

        return user

    # ... update method remains the same and correctly handles the optional password ...
    def update(self, instance, validated_data):
        if instance.is_deleted and validated_data.get("is_deleted") is not False:
            raise serializers.ValidationError(
                {"detail": "Cannot update a soft-deleted user."}
            )

        # This correctly uses .pop("password", None) to handle its optional nature
        password = validated_data.pop("password", None)

        # NOTE: Email uniqueness check for updates
        email = validated_data.get("email")
        if (
            email
            and email != instance.email
            and Users.objects.filter(email=email, is_deleted=False).exists()
        ):
            raise serializers.ValidationError(
                {"email": "User already exists with this email."}
            )

        with transaction.atomic():
            if password:
                instance.set_password(password)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()

        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ForgotPasswordOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField()
