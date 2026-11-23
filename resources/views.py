
from django.db import transaction
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from rest_framework import (
    viewsets,
    filters,
    status,
)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from django_filters.rest_framework import DjangoFilterBackend

from bookings.services import (
    validate_resource_change,
    ResourceAvailabilityError,
)

from .models import Category, Resource
from .serializers import (
    CategorySerializer,
    ResourceSerializer,
)
from .filters import ResourceFilter
from .permissions import IsResourceManagerOrReadOnly


class CategoryViewSet(viewsets.ModelViewSet):

    serializer_class = CategorySerializer

    permission_classes = [
        IsAuthenticated,
        IsResourceManagerOrReadOnly,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ["name"]

    search_fields = [
        "name",
        "description",
    ]

    ordering_fields = [
        "name",
        "created_at",
    ]

    def get_queryset(self):
        return Category.objects.annotate(
            resource_count=Count("resources")
        ).order_by("name")

    def perform_destroy(self, instance):
        if instance.resources.exists():
            raise ValidationError({
                "detail": (
                    "Cannot delete a category "
                    "containing resources."
                )
            })

        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError({
                "detail": (
                    "This category is still in use."
                )
            })


class ResourceViewSet(viewsets.ModelViewSet):

    serializer_class = ResourceSerializer

    permission_classes = [
        IsAuthenticated,
        IsResourceManagerOrReadOnly,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_class = ResourceFilter

    search_fields = [
        "name",
        "description",
        "location",
        "category__name",
    ]

    ordering_fields = [
        "name",
        "total_quantity",
        "location",
        "created_at",
    ]

    ordering = ["name", "id"]

    def get_queryset(self):
        return Resource.objects.select_related(
            "category"
        ).order_by("name", "id")

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        # Lock before reading and validating stock.
        instance = Resource.objects.select_for_update().get(
            pk=self.get_object().pk
        )

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)

        new_quantity = serializer.validated_data.get(
            "total_quantity",
            instance.total_quantity,
        )
        new_status = serializer.validated_data.get(
            "status",
            instance.status,
        )

        try:
            validate_resource_change(
                resource=instance,
                new_quantity=new_quantity,
                new_status=new_status,
                today=timezone.localdate(),
            )
        except ResourceAvailabilityError as exc:
            raise ValidationError({
                "detail": str(exc)
            })

        serializer.save()

        return Response(serializer.data)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @transaction.atomic
    @action(
        detail=True,
        methods=["post"],
        url_path="deactivate",
    )
    def deactivate(self, request, pk=None):
        instance = Resource.objects.select_for_update().get(
            pk=self.get_object().pk
        )

        try:
            validate_resource_change(
                resource=instance,
                new_quantity=instance.total_quantity,
                new_status=Resource.Status.INACTIVE,
                today=timezone.localdate(),
            )
        except ResourceAvailabilityError as exc:
            raise ValidationError({
                "detail": str(exc)
            })

        instance.status = Resource.Status.INACTIVE
        instance.save(
            update_fields=["status", "updated_at"]
        )

        return Response({
            "message": "Resource deactivated successfully.",
            "resource": self.get_serializer(instance).data,
        })

    @transaction.atomic
    @action(
        detail=True,
        methods=["post"],
        url_path="activate",
    )
    def activate(self, request, pk=None):
        instance = Resource.objects.select_for_update().get(
            pk=self.get_object().pk
        )

        instance.status = Resource.Status.ACTIVE
        instance.save(
            update_fields=["status", "updated_at"]
        )

        return Response({
            "message": "Resource activated successfully.",
            "resource": self.get_serializer(instance).data,
        })

    @transaction.atomic
    def perform_destroy(self, instance):
        locked = Resource.objects.select_for_update().get(
            pk=instance.pk
        )

        if locked.booking_items.exists():
            raise ValidationError({
                "detail": (
                    "Cannot delete a resource with booking "
                    "history. Deactivate it instead."
                )
            })

        try:
            locked.delete()
        except ProtectedError:
            raise ValidationError({
                "detail": (
                    "This resource is referenced "
                    "by another record."
                )
            })
