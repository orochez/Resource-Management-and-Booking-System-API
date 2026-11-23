
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


# ==========================================
# CATEGORY MODEL
# ==========================================

class Category(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


# ==========================================
# RESOURCE MODEL
# ==========================================

class Resource(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    name = models.CharField(
        max_length=150,
    )

    description = models.TextField(
        blank=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="resources",
    )

    total_quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    location = models.CharField(
        max_length=200,
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_quantity__gte=1),
                name="resource_quantity_minimum_one",
            ),
        ]

        indexes = [
            models.Index(
                fields=["category", "status"],
                name="resource_category_status_idx",
            ),
            models.Index(
                fields=["location"],
                name="resource_location_idx",
            ),
        ]

    def clean(self):
        super().clean()

        if self.total_quantity is not None and self.total_quantity < 1:
            raise ValidationError({
                "total_quantity": (
                    "Total quantity must be at least 1."
                )
            })

    def __str__(self):
        return f"{self.name} ({self.total_quantity})"

    @property
    def is_available(self):
        return (
            self.status == self.Status.ACTIVE
            and self.total_quantity > 0
        )
