
import django_filters

from .models import Resource


class ResourceFilter(django_filters.FilterSet):

    # Filter by category ID
    category = django_filters.NumberFilter(
        field_name="category_id"
    )

    # Filter by location
    location = django_filters.CharFilter(
        field_name="location",
        lookup_expr="icontains"
    )

    # Filter by resource status
    status = django_filters.ChoiceFilter(
        choices=Resource.Status.choices
    )

    # Filter by basic availability
    available = django_filters.BooleanFilter(
        method="filter_available"
    )

    # Minimum quantity
    min_quantity = django_filters.NumberFilter(
        field_name="total_quantity",
        lookup_expr="gte"
    )

    # Maximum quantity
    max_quantity = django_filters.NumberFilter(
        field_name="total_quantity",
        lookup_expr="lte"
    )

    class Meta:
        model = Resource

        fields = [
            "category",
            "location",
            "status",
            "available",
            "min_quantity",
            "max_quantity",
        ]

    def filter_available(self, queryset, name, value):

        if value:
            return queryset.filter(
                status=Resource.Status.ACTIVE,
                total_quantity__gte=1
            )

        return queryset.filter(
            status=Resource.Status.INACTIVE
        )
