
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    ResourceViewSet,
)


router = DefaultRouter()

router.register(
    r"categories",
    CategoryViewSet,
    basename="category",
)

router.register(
    r"resources",
    ResourceViewSet,
    basename="resource",
)


app_name = "resources"


urlpatterns = [
    path("", include(router.urls)),
]
