
from django.contrib import admin
from django.urls import path, include


urlpatterns = [

    # Django Admin
    path(
        "admin/",
        admin.site.urls,
    ),

    # Authentication API
    path(
        "api/auth/",
        include("accounts.urls"),
    ),

    # Resource Management API
    path(
        "api/",
        include("resources.urls"),
    ),

    # Booking Management API
    path(
        "api/",
        include("bookings.urls"),
    ),

]
