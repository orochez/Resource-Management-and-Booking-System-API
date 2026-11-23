
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from resources.models import Category, Resource
from .models import Booking, BookingItem


User = get_user_model()


class BookingAPITests(APITestCase):

    def setUp(self):
        self.today = timezone.localdate()
        self.start_date = self.today + timedelta(days=5)
        self.end_date = self.today + timedelta(days=7)

        self.employee = User.objects.create_user(
            username="booking_employee",
            email="employee@example.com",
            password="TestPassword123!",
            role="employee",
        )

        self.other_employee = User.objects.create_user(
            username="other_employee",
            email="other@example.com",
            password="TestPassword123!",
            role="employee",
        )

        self.manager = User.objects.create_user(
            username="booking_manager",
            email="manager@example.com",
            password="TestPassword123!",
            role="resource_manager",
        )

        self.admin_user = User.objects.create_superuser(
            username="booking_admin",
            email="admin@example.com",
            password="TestPassword123!",
            role="admin",
        )

        self.category = Category.objects.create(
            name="Electronics",
            description="Electronic equipment",
        )

        self.resource = Resource.objects.create(
            name="Epson Projector",
            description="Office projector",
            category=self.category,
            total_quantity=5,
            location="ICT Department",
            status=Resource.Status.ACTIVE,
        )

        self.booking_url = reverse(
            "bookings:booking-list"
        )

    def booking_payload(self):
        return {
            "start_date": str(self.start_date),
            "end_date": str(self.end_date),
            "purpose": "Departmental meeting",
            "items": [
                {
                    "resource": self.resource.id,
                    "quantity": 2,
                }
            ],
        }

    def create_booking(self, employee=None):
        booking = Booking.objects.create(
            employee=employee or self.employee,
            start_date=self.start_date,
            end_date=self.end_date,
            purpose="Departmental meeting",
        )

        BookingItem.objects.create(
            booking=booking,
            resource=self.resource,
            quantity=2,
        )

        return booking

    def detail_url(self, booking):
        return reverse(
            "bookings:booking-detail",
            args=[booking.id],
        )

    def action_url(self, booking, action):
        return reverse(
            f"bookings:booking-{action}",
            args=[booking.id],
        )

    # =====================================
    # BOOKING CREATION
    # =====================================

    def test_employee_can_create_booking(self):
        self.client.force_authenticate(user=self.employee)

        response = self.client.post(
            self.booking_url,
            self.booking_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        booking = Booking.objects.get(
            pk=response.data["id"]
        )

        self.assertEqual(
            booking.employee,
            self.employee,
        )

        self.assertEqual(
            booking.status,
            Booking.Status.PENDING,
        )

        self.assertEqual(booking.items.count(), 1)

    def test_unauthenticated_user_cannot_create_booking(self):
        response = self.client.post(
            self.booking_url,
            self.booking_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_booking_cannot_start_in_past(self):
        self.client.force_authenticate(user=self.employee)

        payload = self.booking_payload()
        payload["start_date"] = str(
            self.today - timedelta(days=1)
        )

        response = self.client.post(
            self.booking_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_end_date_cannot_precede_start_date(self):
        self.client.force_authenticate(user=self.employee)

        payload = self.booking_payload()
        payload["end_date"] = str(
            self.start_date - timedelta(days=1)
        )

        response = self.client.post(
            self.booking_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_booking_requires_items(self):
        self.client.force_authenticate(user=self.employee)

        payload = self.booking_payload()
        payload["items"] = []

        response = self.client.post(
            self.booking_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_booking_rejects_duplicate_resources(self):
        self.client.force_authenticate(user=self.employee)

        payload = self.booking_payload()
        payload["items"].append({
            "resource": self.resource.id,
            "quantity": 1,
        })

        response = self.client.post(
            self.booking_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_booking_rejects_excess_quantity(self):
        self.client.force_authenticate(user=self.employee)

        payload = self.booking_payload()
        payload["items"][0]["quantity"] = 10

        response = self.client.post(
            self.booking_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_booking_rejects_inactive_resource(self):
        self.client.force_authenticate(user=self.employee)

        self.resource.status = Resource.Status.INACTIVE
        self.resource.save()

        response = self.client.post(
            self.booking_url,
            self.booking_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # =====================================
    # BOOKING VISIBILITY
    # =====================================

    def test_employee_sees_only_own_bookings(self):
        self.create_booking(self.employee)
        self.create_booking(self.other_employee)

        self.client.force_authenticate(user=self.employee)

        response = self.client.get(self.booking_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(response.data["count"], 1)

    def test_employee_cannot_view_other_booking(self):
        booking = self.create_booking(self.other_employee)

        self.client.force_authenticate(user=self.employee)

        response = self.client.get(
            self.detail_url(booking)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_manager_can_view_all_bookings(self):
        self.create_booking(self.employee)
        self.create_booking(self.other_employee)

        self.client.force_authenticate(user=self.manager)

        response = self.client.get(self.booking_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(response.data["count"], 2)

    # =====================================
    # APPROVAL AND REJECTION
    # =====================================

    def test_manager_can_approve_booking(self):
        booking = self.create_booking()

        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            self.action_url(booking, "approve"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking.Status.APPROVED,
        )

        self.assertEqual(
            booking.reviewed_by,
            self.manager,
        )

    def test_employee_cannot_approve_booking(self):
        booking = self.create_booking()

        self.client.force_authenticate(user=self.employee)

        response = self.client.post(
            self.action_url(booking, "approve"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_manager_cannot_approve_own_booking(self):
        booking = self.create_booking(self.manager)

        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            self.action_url(booking, "approve"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_manager_can_reject_booking(self):
        booking = self.create_booking()

        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            self.action_url(booking, "reject"),
            {"reason": "Resource unavailable"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking.Status.REJECTED,
        )

        self.assertEqual(
            booking.rejection_reason,
            "Resource unavailable",
        )

    def test_rejection_requires_reason(self):
        booking = self.create_booking()

        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            self.action_url(booking, "reject"),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_approved_booking_cannot_be_approved_again(self):
        booking = self.create_booking()
        booking.status = Booking.Status.APPROVED
        booking.save()

        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            self.action_url(booking, "approve"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # =====================================
    # CANCELLATION
    # =====================================

    def test_employee_can_cancel_own_pending_booking(self):
        booking = self.create_booking()

        self.client.force_authenticate(user=self.employee)

        response = self.client.post(
            self.action_url(booking, "cancel"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking.Status.CANCELLED,
        )

    def test_employee_cannot_cancel_other_booking(self):
        booking = self.create_booking(self.other_employee)

        self.client.force_authenticate(user=self.employee)

        response = self.client.post(
            self.action_url(booking, "cancel"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_cancelled_booking_cannot_be_cancelled_again(self):
        booking = self.create_booking()
        booking.status = Booking.Status.CANCELLED
        booking.save()

        self.client.force_authenticate(user=self.employee)

        response = self.client.post(
            self.action_url(booking, "cancel"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # =====================================
    # COMPLETION
    # =====================================

    def test_employee_cannot_complete_booking(self):
        booking = self.create_booking()
        booking.status = Booking.Status.APPROVED
        booking.save()

        self.client.force_authenticate(user=self.employee)

        response = self.client.post(
            self.action_url(booking, "complete"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_manager_cannot_complete_future_booking(self):
        booking = self.create_booking()
        booking.status = Booking.Status.APPROVED
        booking.save()

        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            self.action_url(booking, "complete"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # =====================================
    # FILTERING
    # =====================================

    def test_filter_bookings_by_status(self):
        pending = self.create_booking()
        approved = self.create_booking(self.other_employee)
        approved.status = Booking.Status.APPROVED
        approved.save()

        self.client.force_authenticate(user=self.manager)

        response = self.client.get(
            self.booking_url,
            {"status": "pending"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["id"],
            pending.id,
        )

    def test_booking_cannot_be_deleted_through_api(self):
        booking = self.create_booking()

        self.client.force_authenticate(user=self.manager)

        response = self.client.delete(
            self.detail_url(booking)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
