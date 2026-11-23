
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    BookingViewSet,
    ResourceAvailabilityAPIView,
)


router = DefaultRouter()

router.register(
    r"bookings",
    BookingViewSet,
    basename="booking",
)


app_name = "bookings"


urlpatterns = [

    path(
        "availability/",
        ResourceAvailabilityAPIView.as_view(),
        name="resource-availability",
    ),

    path(
        "",
        include(router.urls),
    ),

]
