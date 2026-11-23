
from rest_framework.permissions import BasePermission

from .models import User


class IsAdminRole(BasePermission):

    message = "Administrator access is required."

    def has_permission(self, request, view):

        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (
                user.is_superuser
                or (
                    user.is_staff
                    and user.role == User.Role.ADMIN
                )
            )
        )


class IsResourceManager(BasePermission):

    message = "Resource Manager access is required."

    def has_permission(self, request, view):

        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (
                user.is_superuser
                or (
                    user.is_staff
                    and user.role == User.Role.ADMIN
                )
                or user.role == User.Role.RESOURCE_MANAGER
            )
        )


class IsEmployee(BasePermission):

    message = "Employee access is required."

    def has_permission(self, request, view):

        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (
                user.is_superuser
                or (
                    user.is_staff
                    and user.role == User.Role.ADMIN
                )
                or user.role == User.Role.EMPLOYEE
            )
        )
