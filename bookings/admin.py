
from django.contrib import admin

from .models import Booking, BookingItem


class BookingItemInline(admin.TabularInline):

    model = BookingItem

    extra = 0

    readonly_fields = [
        "resource",
        "quantity",
    ]

    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "employee",
        "start_date",
        "end_date",
        "status",
        "reviewed_by",
        "created_at",
    ]

    list_filter = [
        "status",
        "start_date",
        "end_date",
        "created_at",
    ]

    search_fields = [
        "employee__username",
        "purpose",
        "items__resource__name",
    ]

    readonly_fields = [
        "employee",
        "start_date",
        "end_date",
        "purpose",
        "status",
        "reviewed_by",
        "reviewed_at",
        "rejection_reason",
        "created_at",
        "updated_at",
    ]

    inlines = [
        BookingItemInline,
    ]

    ordering = [
        "-created_at",
        "-id",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BookingItem)
class BookingItemAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "booking",
        "resource",
        "quantity",
    ]

    list_filter = [
        "resource",
    ]

    search_fields = [
        "booking__employee__username",
        "resource__name",
    ]

    readonly_fields = [
        "booking",
        "resource",
        "quantity",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
