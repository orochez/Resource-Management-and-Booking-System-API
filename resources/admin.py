
from django.contrib import admin

from .models import Category, Resource


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = ("name",)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "category",
        "total_quantity",
        "location",
        "status",
        "created_at",
    )

    list_filter = (
        "category",
        "status",
        "location",
    )

    search_fields = (
        "name",
        "description",
        "location",
    )

    list_editable = (
        "status",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("name",)
