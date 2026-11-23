
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        RESOURCE_MANAGER = "resource_manager", "Resource Manager"
        EMPLOYEE = "employee", "Employee"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        db_index=True,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_resource_manager(self):
        return (
            self.role == self.Role.RESOURCE_MANAGER
            or self.is_superuser
        )

    @property
    def is_admin_user(self):
        return self.is_superuser or (
            self.is_staff and self.role == self.Role.ADMIN
        )
