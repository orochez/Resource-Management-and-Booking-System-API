
from rest_framework import serializers

from .models import Category, Resource


class CategorySerializer(serializers.ModelSerializer):

    resource_count = serializers.IntegerField(
        read_only=True,
        default=0,
    )

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
            "resource_count",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "resource_count",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        name = value.strip()

        if not name:
            raise serializers.ValidationError(
                "Category name cannot be empty."
            )

        queryset = Category.objects.filter(
            name__iexact=name
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "A category with this name already exists."
            )

        return name


class ResourceSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    is_available = serializers.BooleanField(
        read_only=True,
    )

    available_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Resource

        fields = [
            "id",
            "name",
            "description",
            "category",
            "category_name",
            "total_quantity",
            "available_quantity",
            "location",
            "status",
            "is_available",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "category_name",
            "available_quantity",
            "is_available",
            "created_at",
            "updated_at",
        ]

    def get_available_quantity(self, obj):
        """
        Provisional unreserved inventory.

        Date-specific booking availability will
        replace this calculation in Step 5.
        """
        if obj.status == Resource.Status.INACTIVE:
            return 0

        return obj.total_quantity

    def validate_name(self, value):
        name = value.strip()

        if not name:
            raise serializers.ValidationError(
                "Resource name cannot be empty."
            )

        return name

    def validate_location(self, value):
        location = value.strip()

        if not location:
            raise serializers.ValidationError(
                "Location cannot be empty."
            )

        return location

    def validate_total_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Total quantity must be at least 1."
            )

        return value

    def validate(self, attrs):
        category = attrs.get("category")

        if category is not None and not Category.objects.filter(
            pk=category.pk
        ).exists():
            raise serializers.ValidationError({
                "category": "Invalid category."
            })

        return attrs
