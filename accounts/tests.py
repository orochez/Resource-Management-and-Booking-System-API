
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

class AuthenticationAPITests(APITestCase):

    def setUp(self):
        self.employee = User.objects.create_user(
            username="testemployee",
            email="testemployee@example.com",
            password="TestPassword123!",
            role=User.Role.EMPLOYEE,
        )

        self.admin_user = User.objects.create_superuser(
            username="testadmin",
            email="testadmin@example.com",
            password="TestPassword123!",
            role=User.Role.ADMIN,
        )

    def login(self, username, password):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": username,
                "password": password,
            },
            format="json",
        )
        return response

    def test_registration_defaults_to_employee(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newemployee",
                "email": "newemployee@example.com",
                "password": "SecurePassword123!",
                "password_confirm": "SecurePassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        user = User.objects.get(
            username="newemployee"
        )

        self.assertEqual(
            user.role,
            User.Role.EMPLOYEE,
        )

        self.assertNotIn("password", response.data)

    def test_registration_rejects_duplicate_email(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "anotheremployee",
                "email": "testemployee@example.com",
                "password": "SecurePassword123!",
                "password_confirm": "SecurePassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_login_returns_jwt_tokens(self):
        response = self.login(
            "testemployee",
            "TestPassword123!",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)

    def test_profile_requires_authentication(self):
        response = self.client.get(
            reverse("accounts:profile")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_employee_cannot_access_admin_users(self):
        response = self.login(
            "testemployee",
            "TestPassword123!",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {response.data['access']}"
            )
        )

        response = self.client.get(
            reverse("accounts:user_list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_access_users(self):
        response = self.login(
            "testadmin",
            "TestPassword123!",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {response.data['access']}"
            )
        )

        response = self.client.get(
            reverse("accounts:user_list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_employee_cannot_change_role(self):
        response = self.login(
            "testemployee",
            "TestPassword123!",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {response.data['access']}"
            )
        )

        response = self.client.patch(
            reverse("accounts:profile"),
            {"role": User.Role.ADMIN},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.employee.refresh_from_db()

        self.assertEqual(
            self.employee.role,
            User.Role.EMPLOYEE,
        )

    def test_logout_blacklists_refresh_token(self):
        response = self.login(
            "testemployee",
            "TestPassword123!",
        )

        access = response.data["access"]
        refresh = response.data["refresh"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access}"
        )

        logout_response = self.client.post(
            reverse("accounts:logout"),
            {"refresh": refresh},
            format="json",
        )

        self.assertEqual(
            logout_response.status_code,
            status.HTTP_200_OK,
        )

        refresh_response = self.client.post(
            reverse("accounts:token_refresh"),
            {"refresh": refresh},
            format="json",
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )