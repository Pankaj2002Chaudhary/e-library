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
            "first_name": "Ada", "middle_name": "", "last_name": "Lovelace",
            "email": "ada@example.com", "contact_number": "9876543210",
            "street": "12 Example Street", "city": "London",
            "state": "Greater London", "country": "United Kingdom",
            "postal_code": "SW1A 1AA", "role": User.Role.MEMBER,
            "password": "safe-pass-123",
        }

    def post(self, payload=None, **kwargs):
        return self.client.post(
            self.url, self.payload if payload is None else payload, format="json", **kwargs
        )

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
        self.assertEqual(self.post(payload).status_code, status.HTTP_201_CREATED)

    def test_accepts_each_configured_role(self):
        for index, role in enumerate(User.Role.values, start=1):
            with self.subTest(role=role):
                payload = deepcopy(self.payload)
                payload.update(
                    role=role, email=f"{role.lower()}@example.com",
                    contact_number=f"99999{index:05d}",
                )
                response = self.post(payload)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(response.data["role"], role)

    def test_every_required_field_is_validated(self):
        required_fields = (
            "first_name", "last_name", "email", "contact_number", "street",
            "city", "state", "country", "postal_code", "password",
        )
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
        response = self.post(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        payload.update(email="grace@example.com", contact_number=self.payload["contact_number"])
        response = self.post(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("contact_number", response.data)

    def test_rejects_invalid_role_and_overlong_fields(self):
        payload = deepcopy(self.payload)
        payload.update(role="OWNER", first_name="A" * 101, postal_code="P" * 21)
        response = self.post(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ("role", "first_name", "postal_code"):
            self.assertIn(field, response.data)

    def test_only_post_is_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_rejects_malformed_json(self):
        response = self.client.generic("POST", self.url, data='{"email":', content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginApiTests(APITestCase):
    """Request-level coverage for the JWT login endpoint."""

    url = "/api/auth/login/"

    def setUp(self):
        self.password = "safe-pass-123"
        self.user = User.objects.create_user(
            email="ada@example.com", password=self.password, first_name="Ada",
            last_name="Lovelace", contact_number="9876543210", street="12 Example Street",
            city="London", state="Greater London", country="United Kingdom", postal_code="SW1A 1AA",
        )
        self.payload = {"email": self.user.email, "password": self.password}

    def post(self, payload=None):
        return self.client.post(self.url, self.payload if payload is None else payload, format="json")

    def test_returns_tokens_and_user_data_for_valid_credentials(self):
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["access"])
        self.assertTrue(response.data["refresh"])
        self.assertEqual(response.data["user"]["email"], self.user.email)
        self.assertNotIn("password", response.data["user"])

    def test_rejects_wrong_password_unknown_email_and_inactive_user(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        invalid_payloads = (
            {"email": self.user.email, "password": "wrong-password"},
            {"email": "unknown@example.com", "password": self.password},
            self.payload,
        )
        for payload in invalid_payloads:
            with self.subTest(email=payload["email"]):
                response = self.post(payload)
                self.assertIn(response.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED))
                self.assertNotIn("access", response.data)
                self.assertNotIn("refresh", response.data)

    def test_validates_missing_empty_and_null_credentials(self):
        for payload in ({}, {"email": self.user.email}, {"password": self.password}, {"email": "", "password": ""}, {"email": None, "password": None}):
            with self.subTest(payload=payload):
                self.assertEqual(self.post(payload).status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_malformed_json(self):
        response = self.client.generic("POST", self.url, data='{"email":', content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_post_is_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
