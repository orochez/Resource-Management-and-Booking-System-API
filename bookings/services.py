
from collections import defaultdict
from datetime import timedelta

from django.db.models import Q

from resources.models import Resource
from .models import Booking, BookingItem


class ResourceAvailabilityError(Exception):
    pass


def _approved_items(resource, start_date, end_date, exclude_booking_id=None):
    queryset = BookingItem.objects.filter(
        resource_id=resource.pk,
        booking__status=Booking.Status.APPROVED,
        booking__start_date__lte=end_date,
        booking__end_date__gte=start_date,
    ).select_related("booking")

    if exclude_booking_id is not None:
        queryset = queryset.exclude(
            booking_id=exclude_booking_id
        )

    return queryset


def get_peak_reserved_quantity(
    resource,
    start_date,
    end_date,
    exclude_booking_id=None,
):
    """
    Calculate peak simultaneous reservations.

    Dates are inclusive. Uses a sweep-line
    algorithm rather than summing all bookings
    that overlap the requested period.
    """
    if end_date < start_date:
        raise ValueError(
            "End date cannot be before start date."
        )

    events = defaultdict(int)

    items = _approved_items(
        resource,
        start_date,
        end_date,
        exclude_booking_id,
    )

    for item in items:
        start = max(
            item.booking.start_date,
            start_date,
        )
        end = min(
            item.booking.end_date,
            end_date,
        )

        events[start.toordinal()] += item.quantity
        events[end.toordinal() + 1] -= item.quantity

    current = 0
    peak = 0

    for day in sorted(events):
        current += events[day]
        peak = max(peak, current)

    return peak


def get_reserved_quantity(
    resource,
    start_date,
    end_date,
    exclude_booking_id=None,
):
    """
    Compatibility function for existing code.
    Returns peak simultaneous reservations.
    """
    return get_peak_reserved_quantity(
        resource,
        start_date,
        end_date,
        exclude_booking_id,
    )


def get_resource_availability(
    resource,
    start_date,
    end_date,
    exclude_booking_id=None,
):
    reserved = get_peak_reserved_quantity(
        resource,
        start_date,
        end_date,
        exclude_booking_id,
    )

    available = max(
        resource.total_quantity - reserved,
        0,
    )

    if resource.status != Resource.Status.ACTIVE:
        available = 0

    return {
        "resource_id": resource.pk,
        "resource_name": resource.name,
        "status": resource.status,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_quantity": resource.total_quantity,
        "reserved_quantity": reserved,
        "available_quantity": available,
        "is_available": available > 0,
    }


def validate_booking_availability(
    booking,
    locked_resources,
):
    """
    Called while holding resource row locks.
    """
    items = list(
        booking.items.all()
    )

    if not items:
        raise ResourceAvailabilityError(
            "Booking must contain at least one resource."
        )

    for item in items:
        resource = locked_resources.get(
            item.resource_id
        )

        if resource is None:
            raise ResourceAvailabilityError(
                "Requested resource is not locked."
            )

        if resource.status != Resource.Status.ACTIVE:
            raise ResourceAvailabilityError(
                f"{resource.name} is inactive."
            )

        if item.quantity < 1:
            raise ResourceAvailabilityError(
                "Booking quantities must be positive."
            )

        if item.quantity > resource.total_quantity:
            raise ResourceAvailabilityError(
                f"{resource.name}: requested quantity "
                "exceeds total stock."
            )

        availability = get_resource_availability(
            resource,
            booking.start_date,
            booking.end_date,
            exclude_booking_id=booking.pk,
        )

        if item.quantity > availability["available_quantity"]:
            raise ResourceAvailabilityError(
                f"Insufficient availability for "
                f"{resource.name}. "
                f"Requested: {item.quantity}; "
                f"Available: "
                f"{availability['available_quantity']}."
            )

    return True


def validate_resource_change(
    resource,
    new_quantity,
    new_status,
    today,
):
    """
    Validate changes to a resource while its
    database row is locked.

    Future approved bookings must remain valid.
    """
    if new_quantity < 1:
        raise ResourceAvailabilityError(
            "Resource quantity must be at least 1."
        )

    approved_items = BookingItem.objects.filter(
        resource_id=resource.pk,
        booking__status=Booking.Status.APPROVED,
        booking__end_date__gte=today,
    ).select_related("booking")

    events = defaultdict(int)
    has_future_allocation = False

    for item in approved_items:
        has_future_allocation = True

        start = max(
            item.booking.start_date,
            today,
        )
        end = item.booking.end_date

        events[start.toordinal()] += item.quantity
        events[end.toordinal() + 1] -= item.quantity

    if (
        new_status == Resource.Status.INACTIVE
        and has_future_allocation
    ):
        raise ResourceAvailabilityError(
            "Cannot deactivate this resource while "
            "current or future approved bookings exist. "
            "Cancel or complete those bookings first."
        )

    current = 0
    peak = 0

    for day in sorted(events):
        current += events[day]
        peak = max(peak, current)

    if new_quantity < peak:
        raise ResourceAvailabilityError(
            f"Cannot reduce {resource.name} to "
            f"{new_quantity} units. Existing approved "
            f"bookings require up to {peak} units "
            "simultaneously."
        )

    return True
