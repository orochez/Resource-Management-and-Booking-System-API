
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
        "date_joined",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    ordering = ("-date_joined",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Organisation Information",
            {
                "fields": (
                    "role",
                    "phone_number",
                ),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Organisation Information",
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "phone_number",
                ),
            },
        ),
    )

    readonly_fields = (
        "date_joined",
        "last_login",
        "created_at",
        "updated_at",
    )
