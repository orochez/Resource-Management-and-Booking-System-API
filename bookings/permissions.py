
from rest_framework.permissions import BasePermission


class IsBookingManager(BasePermission):
    """
    Allow only administrators and resource managers
    to approve, reject, and complete bookings.
    """

    message = (
        "Only administrators and resource managers "
        "can perform this action."
    )

    def has_permission(self, request, view):

        user = request.user

        if not user or not user.is_authenticated:
            return False

        if not user.is_active:
            return False

        if user.is_superuser:
            return True

        return user.role in [
            "admin",
            "resource_manager",
        ]


class IsBookingOwnerOrManager(BasePermission):
    """
    Allow booking owners to access their own bookings.

    Administrators and resource managers can
    access all bookings.
    """

    message = (
        "You do not have permission "
        "to access this booking."
    )

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
        )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):

        user = request.user

        if not user.is_active:
            return False

        if user.is_superuser:
            return True

        if user.role in [
            "admin",
            "resource_manager",
        ]:
            return True

        return obj.employee_id == user.id
