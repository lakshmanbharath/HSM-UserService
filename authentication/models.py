import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Users(AbstractUser, BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID
    username = None  # Remove username field from AbstractUser
    email = models.EmailField(unique=True)

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    country_code = models.CharField(max_length=10, default="+91")
    title = models.CharField(max_length=255, blank=True, null=True)

    role = models.ForeignKey(
        "roles_permissions.Role",
        on_delete=models.CASCADE,
        related_name="users",
    )

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="active")
    is_deleted = models.BooleanField(default=False)

    # OTP fields
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "phone_number",
        "role",
        "country_code",
    ]

    def __str__(self):
        return f"{self.email} ({self.role or 'No Role'})"

    def is_otp_valid(self, otp):
        if not self.otp_code or not self.otp_created_at:
            return False
        if self.otp_code != otp:
            return False
        return timezone.now() <= self.otp_created_at + timedelta(minutes=15)

    def clear_otp(self):
        self.otp_code = None
        self.otp_created_at = None
        self.save()


class EmailTemplate(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100, unique=True
    )  # Unique identifier for the template
    subject = models.CharField(max_length=200)
    html_body = models.TextField()


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
