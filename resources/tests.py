
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Resource


User = get_user_model()


class ResourceAPITests(APITestCase):

    def setUp(self):

        self.admin_user = User.objects.create_superuser(
            username="testadmin",
            email="admin@example.com",
            password="TestPassword123!",
            role="admin",
        )

        self.manager = User.objects.create_user(
            username="testmanager",
            email="manager@example.com",
            password="TestPassword123!",
            role="resource_manager",
        )

        self.employee = User.objects.create_user(
            username="testemployee",
            email="employee@example.com",
            password="TestPassword123!",
            role="employee",
        )

        self.category = Category.objects.create(
            name="Electronics",
            description="Electronic equipment",
        )

        self.resource = Resource.objects.create(
            name="Projector",
            description="Meeting room projector",
            category=self.category,
            total_quantity=5,
            location="ICT Department",
            status=Resource.Status.ACTIVE,
        )

        self.category_url = reverse(
            "resources:category-list"
        )

        self.resource_url = reverse(
            "resources:resource-list"
        )

    def resource_payload(self):
        return {
            "name": "Laptop",
            "description": "Office laptop",
            "category": self.category.id,
            "total_quantity": 10,
            "location": "Main Office",
            "status": "active",
        }

    # =====================================
    # CATEGORY TESTS
    # =====================================

    def test_manager_can_create_category(self):

        self.client.force_authenticate(
            user=self.manager
        )

        response = self.client.post(
            self.category_url,
            {
                "name": "Furniture",
                "description": "Office furniture",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_employee_cannot_create_category(self):

        self.client.force_authenticate(
            user=self.employee
        )

        response = self.client.post(
            self.category_url,
            {
                "name": "Furniture",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_employee_can_view_categories(self):

        self.client.force_authenticate(
            user=self.employee
        )

        response = self.client.get(
            self.category_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_category_with_resources_cannot_be_deleted(self):

        self.client.force_authenticate(
            user=self.admin_user
        )

        url = reverse(
            "resources:category-detail",
            args=[self.category.id],
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # =====================================
    # RESOURCE TESTS
    # =====================================

    def test_manager_can_create_resource(self):

        self.client.force_authenticate(
            user=self.manager
        )

        response = self.client.post(
            self.resource_url,
            self.resource_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_employee_cannot_create_resource(self):

        self.client.force_authenticate(
            user=self.employee
        )

        response = self.client.post(
            self.resource_url,
            self.resource_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_employee_can_view_resources(self):

        self.client.force_authenticate(
            user=self.employee
        )

        response = self.client.get(
            self.resource_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_unauthenticated_user_cannot_view_resources(self):

        response = self.client.get(
            self.resource_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_manager_can_update_resource(self):

        self.client.force_authenticate(
            user=self.manager
        )

        url = reverse(
            "resources:resource-detail",
            args=[self.resource.id],
        )

        response = self.client.patch(
            url,
            {"location": "Conference Room"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.resource.refresh_from_db()

        self.assertEqual(
            self.resource.location,
            "Conference Room",
        )

    def test_resource_quantity_cannot_be_zero(self):

        self.client.force_authenticate(
            user=self.manager
        )

        url = reverse(
            "resources:resource-detail",
            args=[self.resource.id],
        )

        response = self.client.patch(
            url,
            {"total_quantity": 0},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_manager_can_deactivate_resource(self):

        self.client.force_authenticate(
            user=self.manager
        )

        url = reverse(
            "resources:resource-deactivate",
            args=[self.resource.id],
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.resource.refresh_from_db()

        self.assertEqual(
            self.resource.status,
            Resource.Status.INACTIVE,
        )

    def test_manager_can_activate_resource(self):

        self.resource.status = Resource.Status.INACTIVE
        self.resource.save()

        self.client.force_authenticate(
            user=self.manager
        )

        url = reverse(
            "resources:resource-activate",
            args=[self.resource.id],
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.resource.refresh_from_db()

        self.assertEqual(
            self.resource.status,
            Resource.Status.ACTIVE,
        )
