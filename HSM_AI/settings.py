from pathlib import Path
from decouple import config
import os
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")

# DEBUG = config('DEBUG')
DEBUG = config("DEBUG", cast=bool)

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "https://sdeiaiml.com:9034",
]

""" Azure storage Details """
AZURE_STORAGE_CONNECTION_STRING = config("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER_NAME = config("AZURE_STORAGE_CONTAINER_NAME")
AZURE_STORAGE_ACCOUNT_URL = config("AZURE_STORAGE_ACCOUNT_URL")

""" Azure Open AI Details """
AZURE_OPENAI_ENDPOINT = config("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = config("AZURE_OPENAI_KEY")
AZURE_OPENAI_DEPLOYMENT_NAME = config("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = config("AZURE_OPENAI_API_VERSION")

""" Azure OCR """
AZURE_OCR_KEY = config("AZURE_OCR_KEY")
AZURE_OCR_ENDPOINT = config("AZURE_OCR_ENDPOINT")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "storages",
    "drf_yasg",
    "authentication",
    "roles_permissions.apps.RolesPermissionsConfig",  # Defined it herer to run this app for creating a default super admin
    "django_celery_beat",
    # "provider",
    # 'roles_permissions', #this is main application which should run but we used 'roles_permissions.apps.RolesPermissionsConfig'
    # "projects",
    # "uploader",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 'HSM_AI.middleware.aes_middleware.AESMiddleware',
    # 'HSM_AI.middleware.logging_middleware.APILoggingMiddleware',
]

ROOT_URLCONF = "HSM_AI.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "HSM_AI.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_NAME"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": config("POSTGRES_HOST"),
        "PORT": config("POSTGRES_PORT"),
    }
}


CORS_ALLOW_ALL_ORIGINS = True


CORS_ALLOW_HEADERS = [
    "content-type",
    "authorization",
    "x-csrftoken",
    "accept",
    "accept-language",
    "origin",
    "user-agent",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# REST_FRAMEWORK = {
#         'DEFAULT_AUTHENTICATION_CLASSES': (
#             'rest_framework_simplejwt.authentication.JWTAuthentication',
#         ),
# }
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "EXCEPTION_HANDLER": "HSM_AI.utils.custom_exception_handler",
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=2),
}

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "/static/"

STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# # Email Configuration for Gmail
# EMAIL_BACKEND = config('EMAIL_BACKEND')
# EMAIL_HOST = config('EMAIL_HOST')
# EMAIL_PORT = config('EMAIL_PORT')
# EMAIL_USE_TLS = config('EMAIL_USE_TLS')
# EMAIL_HOST_USER = config('EMAIL_HOST_USER')  # Replace with your Gmail address
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')  # Replace with your Gmail app password

# # Default From Email
# DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

AUTH_USER_MODEL = "authentication.Users"

# AWS S3 settings
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME")
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

# Microsoft Azure Oauth SSO
MICROSOFT_CLIENT_ID = config("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = config("MICROSOFT_CLIENT_SECRET")
MICROSOFT_REDIRECT_URI = config("MICROSOFT_REDIRECT_URI")

# Dropbox Oauth SSO
DROPBOX_CLIENT_ID = config("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = config("DROPBOX_CLIENT_SECRET")
DROPBOX_REDIRECT_URI = config("DROPBOX_REDIRECT_URI")

# Azure SharePoint Oauth SSO
SHAREPOINT_CLIENT_ID = config("SHAREPOINT_CLIENT_ID")
SHAREPOINT_CLIENT_SECRET = config("SHAREPOINT_CLIENT_SECRET")
SHAREPOINT_TENANT_ID = config("SHAREPOINT_TENANT_ID")
SHAREPOINT_REDIRECT_URI = config("SHAREPOINT_REDIRECT_URI")
SHAREPOINT_AUTHORITY = config("SHAREPOINT_AUTHORITY")
SHAREPOINT_SCOPES = config("SHAREPOINT_SCOPES")


CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

GROQ_API_KEY = config("GROQ_API_KEY")
# OPENAI_API_KEY = config("OPENAI_API_KEY")

# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "json": {
#             "format": (
#                 '{{'
#                 '"time": "{asctime}", '
#                 '"level": "{levelname}", '
#                 '"logger": "{name}", '
#                 '"message": "{message}", '
#                 '"structured": "{structured}"'
#                 '}}'
#             ),
#             "style": "{",
#         },
#     },
#     "handlers": {
#         "console": {
#             "class": "logging.StreamHandler",
#             "formatter": "json",
#         },
#     },
#     "root": {
#         "handlers": ["console"],
#         "level": "INFO",
#     },
# }
