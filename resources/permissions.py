
from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.permissions import IsAdminRole, IsResourceManager


class IsResourceManagerOrReadOnly(BasePermission):
    """
    Authenticated users can read resources.
    Admins and Resource Managers can modify them.
    """

    message = (
        "Only Admins and Resource Managers "
        "can modify resources."
    )

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if not user.is_active:
            return False

        if request.method in SAFE_METHODS:
            return True

        return IsResourceManager().has_permission(
            request, view
        )
