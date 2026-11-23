
from django.db import transaction
from django.utils import timezone

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import (
    viewsets,
    status,
    filters,
)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import (
    ValidationError,
    NotFound,
)
from rest_framework.views import APIView

from resources.models import Resource

from .models import Booking
from .serializers import (
    BookingSerializer,
    BookingRejectionSerializer,
    ResourceAvailabilityQuerySerializer,
)
from .permissions import IsBookingManager
from .services import (
    get_resource_availability,
    validate_booking_availability,
    ResourceAvailabilityError,
)


class BookingViewSet(viewsets.ModelViewSet):

    serializer_class = BookingSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    http_method_names = [
        "get",
        "post",
        "head",
        "options",
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "status",
        "start_date",
        "end_date",
    ]

    search_fields = [
        "purpose",
        "employee__username",
        "items__resource__name",
    ]

    ordering_fields = [
        "created_at",
        "start_date",
        "end_date",
    ]

    ordering = [
        "-created_at",
        "-id",
    ]

    def get_queryset(self):

        user = self.request.user

        queryset = Booking.objects.select_related(
            "employee",
            "reviewed_by",
        ).prefetch_related(
            "items__resource",
        )

        if user.is_superuser:
            return queryset

        if user.role in [
            "admin",
            "resource_manager",
        ]:
            return queryset

        return queryset.filter(
            employee=user
        )

    def get_permissions(self):

        if self.action in [
            "approve",
            "reject",
            "complete",
        ]:
            return [
                IsAuthenticated(),
                IsBookingManager(),
            ]

        return [
            IsAuthenticated(),
        ]

    @transaction.atomic
    @action(
        detail=True,
        methods=["post"],
        url_path="approve",
    )
    def approve(self, request, pk=None):

        # Check that this user can access the booking.
        booking = self.get_object()

        # Booking items are immutable through this API.
        # Lock all requested resources in a consistent
        # order to serialize competing approvals.
        resource_ids = sorted(
            set(
                booking.items.values_list(
                    "resource_id",
                    flat=True,
                )
            )
        )

        if not resource_ids:
            raise ValidationError({
                "detail": (
                    "Booking must contain at least "
                    "one resource."
                )
            })

        locked_resources = {}

        # Acquire locks one resource at a time in
        # ascending ID order to reduce deadlock risk.
        for resource_id in resource_ids:

            resource = (
                Resource.objects
                .select_for_update()
                .get(pk=resource_id)
            )

            locked_resources[resource_id] = resource

        # Lock and refresh the booking after acquiring
        # the resource locks.
        booking = (
            Booking.objects
            .select_for_update()
            .get(pk=booking.pk)
        )

        if booking.employee_id == request.user.id:
            raise ValidationError({
                "detail": (
                    "You cannot approve your own booking."
                )
            })

        if booking.status != Booking.Status.PENDING:
            raise ValidationError({
                "detail": (
                    "Only pending bookings can be approved."
                )
            })

        if booking.start_date < timezone.localdate():
            raise ValidationError({
                "detail": (
                    "Cannot approve a booking "
                    "whose start date is in the past."
                )
            })

        try:
            validate_booking_availability(
                booking=booking,
                locked_resources=locked_resources,
            )

        except ResourceAvailabilityError as exc:
            raise ValidationError({
                "detail": str(exc)
            })

        booking.status = Booking.Status.APPROVED
        booking.reviewed_by = request.user
        booking.reviewed_at = timezone.now()
        booking.rejection_reason = ""

        booking.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "rejection_reason",
                "updated_at",
            ]
        )

        return Response({
            "message": "Booking approved successfully.",
            "booking": self.get_serializer(booking).data,
        })

    @transaction.atomic
    @action(
        detail=True,
        methods=["post"],
        url_path="reject",
    )
    def reject(self, request, pk=None):

        serializer = BookingRejectionSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        booking = self.get_object()

        booking = (
            Booking.objects
            .select_for_update()
            .get(pk=booking.pk)
        )

        if booking.status != Booking.Status.PENDING:
            raise ValidationError({
                "detail": (
                    "Only pending bookings can be rejected."
                )
            })

        booking.status = Booking.Status.REJECTED
        booking.reviewed_by = request.user
        booking.reviewed_at = timezone.now()
        booking.rejection_reason = (
            serializer.validated_data["reason"]
        )

        booking.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "rejection_reason",
                "updated_at",
            ]
        )

        return Response({
            "message": "Booking rejected successfully.",
            "booking": self.get_serializer(booking).data,
        })

    @transaction.atomic
    @action(
        detail=True,
        methods=["post"],
        url_path="cancel",
    )
    def cancel(self, request, pk=None):

        booking = self.get_object()

        booking = (
            Booking.objects
            .select_for_update()
            .get(pk=booking.pk)
        )

        is_owner = (
            booking.employee_id == request.user.id
        )

        is_manager = (
            request.user.is_superuser
            or request.user.role in [
                "admin",
                "resource_manager",
            ]
        )

        if not is_owner and not is_manager:
            raise ValidationError({
                "detail": (
                    "You cannot cancel this booking."
                )
            })

        if booking.status not in [
            Booking.Status.PENDING,
            Booking.Status.APPROVED,
        ]:
            raise ValidationError({
                "detail": (
                    "This booking cannot be cancelled."
                )
            })

        if (
            booking.status == Booking.Status.APPROVED
            and booking.start_date <= timezone.localdate()
            and not is_manager
        ):
            raise ValidationError({
                "detail": (
                    "An approved booking that has started "
                    "must be cancelled by a manager."
                )
            })

        booking.status = Booking.Status.CANCELLED

        booking.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response({
            "message": "Booking cancelled successfully.",
            "booking": self.get_serializer(booking).data,
        })

    @transaction.atomic
    @action(
        detail=True,
        methods=["post"],
        url_path="complete",
    )
    def complete(self, request, pk=None):

        booking = self.get_object()

        booking = (
            Booking.objects
            .select_for_update()
            .get(pk=booking.pk)
        )

        if booking.status != Booking.Status.APPROVED:
            raise ValidationError({
                "detail": (
                    "Only approved bookings "
                    "can be completed."
                )
            })

        if booking.end_date > timezone.localdate():
            raise ValidationError({
                "detail": (
                    "Booking cannot be completed "
                    "before its end date."
                )
            })

        booking.status = Booking.Status.COMPLETED

        booking.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response({
            "message": "Booking completed successfully.",
            "booking": self.get_serializer(booking).data,
        })


class ResourceAvailabilityAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):

        serializer = ResourceAvailabilityQuerySerializer(
            data=request.query_params
        )

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            resource = Resource.objects.get(
                pk=data["resource_id"]
            )

        except Resource.DoesNotExist:
            raise NotFound(
                "The requested resource does not exist."
            )

        availability = get_resource_availability(
            resource=resource,
            start_date=data["start_date"],
            end_date=data["end_date"],
        )

        requested_quantity = data["quantity"]

        availability["requested_quantity"] = (
            requested_quantity
        )

        availability["can_book"] = (
            resource.status == Resource.Status.ACTIVE
            and requested_quantity
            <= availability["available_quantity"]
        )

        return Response(
            availability,
            status=status.HTTP_200_OK,
        )
