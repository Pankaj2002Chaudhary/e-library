from copy import deepcopy

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class RegisterApiTests(APITestCase):
    """Request-level coverage for the public registration endpoint."""

    url = reverse("register")

    def setUp(self):
        self.payload = {
            "first_name": "Ada",
            "middle_name": "",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "contact_number": "9876543210",
            "street": "12 Example Street",
            "city": "London",
            "state": "Greater London",
            "country": "United Kingdom",
            "postal_code": "SW1A 1AA",
            "role": User.Role.MEMBER,
            "password": "safe-pass-123",
        }

    def post(self, payload=None, **kwargs):
        return self.client.post(self.url, payload or self.payload, format="json", **kwargs)

    def test_registers_member_and_never_returns_password(self):
        response = self.post()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        user = User.objects.get(email=self.payload["email"])
        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertNotEqual(user.password, self.payload["password"])

    def test_optional_middle_name_may_be_omitted(self):
        payload = deepcopy(self.payload)
        payload.pop("middle_name")

        response = self.post(payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_accepts_each_configured_role(self):
        for role in User.Role.values:
            with self.subTest(role=role):
                payload = deepcopy(self.payload)
                payload["role"] = role
                payload["email"] = f"{role.lower()}@example.com"
                payload["contact_number"] = f"99999{len(User.objects.all()) + 1:05d}"

                response = self.post(payload)

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(response.data["role"], role)

    def test_every_required_field_is_validated(self):
        required_fields = [
            "first_name", "last_name", "email", "contact_number", "street",
            "city", "state", "country", "postal_code", "password",
        ]
        for field in required_fields:
            with self.subTest(field=field):
                payload = deepcopy(self.payload)
                payload.pop(field)

                response = self.post(payload)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)

    def test_rejects_invalid_email_and_short_password(self):
        payload = deepcopy(self.payload)
        payload.update(email="not-an-email", password="short")

        response = self.post(payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("password", response.data)

    def test_rejects_duplicate_email_and_contact_number(self):
        self.post()
        payload = deepcopy(self.payload)
        payload["contact_number"] = "1234567890"

        email_response = self.post(payload)
        self.assertEqual(email_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", email_response.data)

        payload["email"] = "grace@example.com"
        payload["contact_number"] = self.payload["contact_number"]
        contact_response = self.post(payload)
        self.assertEqual(contact_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("contact_number", contact_response.data)

    def test_rejects_invalid_role_and_overlong_fields(self):
        payload = deepcopy(self.payload)
        payload["role"] = "OWNER"
        payload["first_name"] = "A" * 101
        payload["postal_code"] = "P" * 21

        response = self.post(payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.data)
        self.assertIn("first_name", response.data)
        self.assertIn("postal_code", response.data)

    def test_only_post_is_allowed(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_rejects_malformed_json(self):
        response = self.client.generic(
            "POST", self.url, data='{"email":', content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
