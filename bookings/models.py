
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from resources.models import Resource


class Booking(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    start_date = models.DateField()

    end_date = models.DateField()

    purpose = models.TextField()

    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_bookings",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    rejection_reason = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]

        indexes = [
            models.Index(
                fields=["status", "start_date", "end_date"],
                name="booking_status_dates_idx",
            ),
            models.Index(
                fields=["employee", "status"],
                name="booking_employee_status_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=models.F("start_date")),
                name="booking_valid_date_range",
            ),
        ]

    def clean(self):
        super().clean()

        errors = {}

        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                errors["end_date"] = (
                    "End date cannot be before start date."
                )

        if self._state.adding and self.start_date:
            if self.start_date < timezone.localdate():
                errors["start_date"] = (
                    "Booking cannot start in the past."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"Booking #{self.pk} - "
            f"{self.employee.username} - {self.status}"
        )


class BookingItem(models.Model):

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="items",
    )

    resource = models.ForeignKey(
        Resource,
        on_delete=models.PROTECT,
        related_name="booking_items",
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    class Meta:
        ordering = ["id"]

        constraints = [
            models.UniqueConstraint(
                fields=["booking", "resource"],
                name="unique_resource_per_booking",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=1),
                name="booking_item_quantity_positive",
            ),
        ]

    def clean(self):
        super().clean()

        if self.quantity is not None and self.quantity < 1:
            raise ValidationError({
                "quantity": "Quantity must be at least 1."
            })

        if self.resource_id and self.quantity:
            if self.quantity > self.resource.total_quantity:
                raise ValidationError({
                    "quantity": (
                        "Requested quantity exceeds "
                        "the resource's total quantity."
                    )
                })

    def __str__(self):
        return (
            f"{self.resource.name} "
            f"x {self.quantity}"
        )
