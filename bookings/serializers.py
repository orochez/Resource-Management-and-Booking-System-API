
from django.db import transaction
from django.utils import timezone
from django.utils import timezone
from rest_framework import serializers

from resources.models import Resource

from .models import Booking, BookingItem


class BookingItemSerializer(serializers.ModelSerializer):

    resource_name = serializers.CharField(
        source="resource.name",
        read_only=True,
    )

    class Meta:
        model = BookingItem

        fields = [
            "id",
            "resource",
            "resource_name",
            "quantity",
        ]

        read_only_fields = [
            "id",
            "resource_name",
        ]


class BookingSerializer(serializers.ModelSerializer):

    employee_username = serializers.CharField(
        source="employee.username",
        read_only=True,
    )

    reviewed_by_username = serializers.CharField(
        source="reviewed_by.username",
        read_only=True,
        allow_null=True,
    )

    items = BookingItemSerializer(
        many=True,
    )

    class Meta:
        model = Booking

        fields = [
            "id",
            "employee",
            "employee_username",
            "start_date",
            "end_date",
            "purpose",
            "status",
            "items",
            "reviewed_by",
            "reviewed_by_username",
            "reviewed_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "employee",
            "employee_username",
            "status",
            "reviewed_by",
            "reviewed_by_username",
            "reviewed_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):

        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        items = attrs.get("items", [])

        if start_date and start_date < timezone.localdate():
            raise serializers.ValidationError({
                "start_date": (
                    "Booking cannot start in the past."
                )
            })

        if start_date and end_date:
            if end_date < start_date:
                raise serializers.ValidationError({
                    "end_date": (
                        "End date cannot be before start date."
                    )
                })

        if not items:
            raise serializers.ValidationError({
                "items": (
                    "At least one resource is required."
                )
            })

        resource_ids = []

        for item in items:

            resource = item["resource"]
            quantity = item["quantity"]

            if resource.id in resource_ids:
                raise serializers.ValidationError({
                    "items": (
                        "A resource cannot appear twice "
                        "in the same booking."
                    )
                })

            resource_ids.append(resource.id)

            if resource.status != Resource.Status.ACTIVE:
                raise serializers.ValidationError({
                    "items": (
                        f"{resource.name} is inactive."
                    )
                })

            if quantity < 1:
                raise serializers.ValidationError({
                    "items": (
                        "Quantity must be at least 1."
                    )
                })

            if quantity > resource.total_quantity:
                raise serializers.ValidationError({
                    "items": (
                        f"Requested quantity for "
                        f"{resource.name} exceeds stock."
                    )
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):

        items_data = validated_data.pop("items")

        request = self.context["request"]

        booking = Booking.objects.create(
            employee=request.user,
            status=Booking.Status.PENDING,
            **validated_data,
        )

        for item in items_data:
            BookingItem.objects.create(
                booking=booking,
                resource=item["resource"],
                quantity=item["quantity"],
            )

        return booking


class BookingRejectionSerializer(serializers.Serializer):

    reason = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=1000,
    )



class ResourceAvailabilityQuerySerializer(
    serializers.Serializer
):
    resource_id = serializers.IntegerField(
        min_value=1
    )

    start_date = serializers.DateField()

    end_date = serializers.DateField()

    quantity = serializers.IntegerField(
        min_value=1,
        required=False,
        default=1,
    )

    def validate(self, attrs):

        start_date = attrs["start_date"]
        end_date = attrs["end_date"]

        if end_date < start_date:
            raise serializers.ValidationError({
                "end_date": (
                    "End date cannot be before start date."
                )
            })

        if start_date < timezone.localdate():
            raise serializers.ValidationError({
                "start_date": (
                    "Availability must be checked "
                    "for today or a future date."
                )
            })

        return attrs
