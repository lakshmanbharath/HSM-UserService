from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db import transaction
from django.core.exceptions import ImproperlyConfigured

class RolesPermissionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "roles_permissions"

    def ready(self):
        """
        Bootstrap default data after migrations.
        """
        try:
            from roles_permissions.models import Module, Role, UserModulePermission
            from authentication.models import Users
        except ImproperlyConfigured:
            return
        except Exception:
            return

        def bootstrap(sender, **kwargs):
            try:
                with transaction.atomic():
                    print(">>> Running bootstrap after migrations <<<")

                    # 1️⃣ Create default modules
                    modules_data = [
                        {"module_name": "Dashboard", "path": "/dashboard", "description": "Main overview"},
                        {"module_name": "Users", "path": "/users", "description": "Manage application users"},
                        {"module_name": "Customer", "path": "/customer", "description": "Manage customers"},
                        {"module_name": "Modules", "path": "/modules", "description": "Manage modules"},
                        {"module_name": "Roles", "path": "/roles", "description": "Manage user roles"},
                        {"module_name": "Projects", "path": "/projects", "description": "Manage projects"},
                    ]

                    module_objs = []
                    for m in modules_data:
                        obj, created = Module.objects.get_or_create(
                            module_name=m["module_name"],
                            defaults=m
                        )
                        module_objs.append(obj)
                        if created:
                            print(f"✅ Created module: {m['module_name']}")
                        else:
                            print(f"ℹ️ Module already exists: {m['module_name']}")

                    # 2️⃣ Create Super Admin role
                    role_name = "Super Admin"
                    role, created = Role.objects.get_or_create(role_name=role_name)
                    if created or not role.module_permissions:
                        role.module_permissions = [
                            {
                                "module_id": str(m.id),
                                "visible": True,
                                "can_create": True,
                                "can_read": True,
                                "can_update": True,
                                "can_delete": True,
                            }
                            for m in module_objs
                        ]
                        role.save()
                        print(f"✅ Created role: {role_name}")
                    else:
                        print(f"ℹ️ Role already exists: {role_name}")

                    # 3️⃣ Create Super Admin user
                    super_email = "admin@yopmail.com"
                    super_password = "Admin@123"

                    if not Users.objects.filter(email=super_email, is_deleted=False).exists():
                        super_admin = Users.objects.create(
                            email=super_email,
                            first_name="Super",
                            last_name="Admin",
                            phone_number="9999999999",
                            country_code="+91",
                            role=role
                        )
                        super_admin.set_password(super_password)
                        super_admin.save()
                        print(f"✅ Super Admin user created: {super_email}")

                        # Copy role permissions → UserModulePermission
                        for perm in role.module_permissions:
                            UserModulePermission.objects.get_or_create(
                                user=super_admin,
                                module_id=perm["module_id"],
                                defaults={
                                    "visible": perm.get("visible", True),
                                    "can_create": perm.get("can_create", True),
                                    "can_read": perm.get("can_read", True),
                                    "can_update": perm.get("can_update", True),
                                    "can_delete": perm.get("can_delete", True),
                                },
                            )
                        print("✅ Role permissions assigned to Super Admin user")
                    else:
                        print(f"ℹ️ Super Admin user already exists: {super_email}")

            except Exception as e:
                print(f"❌ Bootstrap failed: {e}")

        # Connect bootstrap to post_migrate signal
        post_migrate.connect(bootstrap, sender=self)

# from django.apps import AppConfig
# from django.db import transaction
# from django.db.models.signals import post_migrate


# class RolesPermissionsConfig(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "roles_permissions"

#     def ready(self):
#         from django.core.exceptions import ImproperlyConfigured
#         try:
#             from roles_permissions.models import Module, Role, UserModulePermission
#             from authentication.models import Users
#         except ImproperlyConfigured:
#             return

#         def bootstrap(sender, **kwargs):
#             print(">>> Running bootstrap after migrations <<<")
#             try:
#                 with transaction.atomic():
#                     # 1. Create default modules
#                     modules_data = [
#                         {"module_name": "Dashboard", "path": "/dashboard", "description": "Main overview"},
#                         {"module_name": "Users", "path": "/users", "description": "Manage application users"},
#                         {"module_name": "Customers", "path": "/customers", "description": "Manage customers"},
#                         {"module_name": "Modules", "path": "/modules", "description": "Manage modules"},
#                         {"module_name": "Roles", "path": "/roles", "description": "Manage user roles"},
#                         {"module_name": "Projects", "path": "/projects", "description": "Manage projects"},
#                     ]

#                     module_objs = []
#                     for m in modules_data:
#                         obj, created = Module.objects.get_or_create(
#                             module_name=m["module_name"],
#                             defaults=m
#                         )
#                         if created:
#                             print(f"✅ Created module: {m['module_name']}")
#                         module_objs.append(obj)

#                     # 2. Create Super Admin role
#                     role_name = "Super Admin"
#                     role, created = Role.objects.get_or_create(role_name=role_name)
#                     if created:
#                         print("✅ Created role: Super Admin")
#                     if created or not role.module_permissions:
#                         role.module_permissions = [
#                             {
#                                 "module_id": str(m.id),
#                                 "visible": True,
#                                 "can_create": True,
#                                 "can_read": True,
#                                 "can_update": True,
#                                 "can_delete": True,
#                             }
#                             for m in module_objs
#                         ]
#                         role.save()
#                         print("✅ Attached full permissions to Super Admin role")

#                     # 3. Create super admin user
#                     super_email = "admin@yopmail.com"
#                     super_password = "Admin@123"

#                     if not Users.objects.filter(email=super_email, is_deleted=False).exists():
#                         kwargs = {
#                             "email": super_email,
#                             "password": super_password,
#                             "first_name": "Super",
#                             "last_name": "Admin",
#                             "phone_number": "9999999999",
#                             "country_code": "+91",
#                             "role": role,
#                         }
#                         if "username" in [f.name for f in Users._meta.get_fields()]:
#                             kwargs["username"] = "superadmin"

#                         super_admin = Users.objects.create_superuser(**kwargs)
#                         print(f"✅ Super Admin created with email {super_email}")

#                         # Copy role permissions → UserModulePermission
#                         for perm in role.module_permissions:
#                             UserModulePermission.objects.get_or_create(
#                                 user=super_admin,
#                                 module_id=perm["module_id"],
#                                 defaults={
#                                     "visible": perm.get("visible", True),
#                                     "can_create": perm.get("can_create", True),
#                                     "can_read": perm.get("can_read", True),
#                                     "can_update": perm.get("can_update", True),
#                                     "can_delete": perm.get("can_delete", True),
#                                 },
#                             )
#                         print("✅ Super Admin permissions initialized")
#                     else:
#                         print(f"ℹ️ Super Admin already exists ({super_email}), skipping creation")

#             except Exception as e:
#                 print(f"❌ Bootstrap failed: {e}")

#         # Attach only once migrations are done
#         post_migrate.connect(bootstrap, sender=self)

# # from django.apps import AppConfig
# # from django.db.utils import OperationalError, ProgrammingError
# # from django.db import transaction
# # from django.core.exceptions import ImproperlyConfigured


# # class RolesPermissionsConfig(AppConfig):
# #     default_auto_field = "django.db.models.BigAutoField"
# #     name = "roles_permissions"

# #     def ready(self):
# #         """
# #         Bootstrap default data (modules, role, super admin)
# #         Runs once when server starts.
# #         """
# #         try:
# #             # Import models inside ready() to avoid import cycles
# #             from roles_permissions.models import Module, Role, UserModulePermission
# #             from authentication.models import Users  # adjust path if needed
# #         except ImproperlyConfigured:
# #             # If settings or models are not ready yet (first migrate), skip
# #             return
# #         except Exception:
# #             # Other import issues (during migration phase)
# #             return

# #         try:
# #             with transaction.atomic():
# #                 # 1. Create default modules
# #                 modules_data = [
# #                     {"module_name": "Dashboard", "path": "/dashboard", "description": "Main overview"},
# #                     {"module_name": "Users", "path": "/users", "description": "Manage application users"},
# #                     {"module_name": "Customers", "path": "/customers", "description": "Manage customers"},
# #                     {"module_name": "Modules", "path": "/modules", "description": "Manage modules"},
# #                     {"module_name": "Roles", "path": "/roles", "description": "Manage user roles"},
# #                     {"module_name": "Projects", "path": "/projects", "description": "Manage projects"},
# #                 ]

# #                 module_objs = []
# #                 for m in modules_data:
# #                     obj, _ = Module.objects.get_or_create(
# #                         module_name=m["module_name"],
# #                         defaults=m
# #                     )
# #                     module_objs.append(obj)

# #                 # 2. Create Super Admin role
# #                 role_name = "Super Admin"
# #                 role, created = Role.objects.get_or_create(role_name=role_name)
# #                 if created or not role.module_permissions:
# #                     role.module_permissions = [
# #                         {
# #                             "module_id": str(m.id),
# #                             "visible": True,
# #                             "can_create": True,
# #                             "can_read": True,
# #                             "can_update": True,
# #                             "can_delete": True,
# #                         }
# #                         for m in module_objs
# #                     ]
# #                     role.save()

# #                 # 3. Create super admin user
# #                 super_email = "admin@yopmail.com"
# #                 super_password = "Admin@123"

# #                 if not Users.objects.filter(email=super_email, is_deleted=False).exists():
# #                     # handle both cases: AbstractUser (needs username) OR AbstractBaseUser (email only)
# #                     kwargs = {
# #                         "email": super_email,
# #                         "password": super_password,
# #                         "first_name": "Super",
# #                         "last_name": "Admin",
# #                         "phone_number": "9999999999",
# #                         "country_code": "+91",
# #                         "role": role,
# #                     }

# #                     # if the model has "username" field, provide it
# #                     if "username" in [f.name for f in Users._meta.get_fields()]:
# #                         kwargs["username"] = "superadmin"

# #                     super_admin = Users.objects.create_superuser(**kwargs)

# #                     # Copy role permissions → UserModulePermission
# #                     for perm in role.module_permissions:
# #                         UserModulePermission.objects.get_or_create(
# #                             user=super_admin,
# #                             module_id=perm["module_id"],
# #                             defaults={
# #                                 "visible": perm.get("visible", True),
# #                                 "can_create": perm.get("can_create", True),
# #                                 "can_read": perm.get("can_read", True),
# #                                 "can_update": perm.get("can_update", True),
# #                                 "can_delete": perm.get("can_delete", True),
# #                             },
# #                         )
# #         except (OperationalError, ProgrammingError):
# #             # Database might not be ready on first migrate
# #             pass


# # class RolesPermissionsConfig(AppConfig):
# #     default_auto_field = 'django.db.models.BigAutoField'
# #     name = 'roles_permissions'
