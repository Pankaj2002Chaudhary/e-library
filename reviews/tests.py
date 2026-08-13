from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from books.models import Book
from .models import Review


class ReviewsApiTests(APITestCase):
    """Request-level coverage for all review endpoints and edge cases."""

    create_url = "/api/reviews/create/"

    def setUp(self):
        self.user = self.make_user("member@example.com", "9000000001")
        self.other_user = self.make_user("other@example.com", "9000000002")
        self.book = Book.objects.create(
            title="Review Book", author="Test Author", isbn="review-isbn-1",
            description="Test description", genre="Technology", publisher="Test Press",
            published_year=2024, language="English", total_copies=1, available_copies=1,
        )

    def make_user(self, email, contact_number):
        return User.objects.create_user(
            email=email, password="safe-pass-123", first_name="Test", last_name="User",
            contact_number=contact_number, street="1 Test Street", city="Test City",
            state="Test State", country="Test Country", postal_code="100001",
        )

    def ai_url(self, book_id=None):
        return f"/api/reviews/ai-review/{book_id or self.book.id}/"

    def book_reviews_url(self, book_id=None):
        return f"/api/reviews/book/{book_id or self.book.id}/"

    def review_payload(self, **overrides):
        payload = {"book": self.book.id, "rating": 5, "review_text": "Excellent book."}
        payload.update(overrides)
        return payload

    def test_create_requires_authentication(self):
        response = self.client.post(self.create_url, self.review_payload(), format="json")
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_create_review_sets_user_and_updates_book_average_rating(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.create_url, self.review_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        review = Review.objects.get(book=self.book, user=self.user)
        self.assertEqual(review.rating, 5)
        self.book.refresh_from_db()
        self.assertEqual(self.book.average_rating, 5.0)
        self.assertNotIn("password", response.data)

    def test_create_rejects_missing_book_and_duplicate_review(self):
        self.client.force_authenticate(self.user)
        for field in ("book", "rating", "review_text"):
            with self.subTest(field=field):
                payload = self.review_payload()
                payload.pop(field)
                response = self.client.post(self.create_url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)

        self.client.post(self.create_url, self.review_payload(), format="json")
        response = self.client.post(self.create_url, self.review_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rating_must_be_between_one_and_five(self):
        self.client.force_authenticate(self.user)
        for rating in (0, 6, -1, "invalid"):
            with self.subTest(rating=rating):
                response = self.client.post(
                    self.create_url, self.review_payload(rating=rating), format="json"
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("rating", response.data)

    def test_book_reviews_are_public_and_isolated_to_requested_book(self):
        Review.objects.create(user=self.user, book=self.book, rating=4, review_text="Good")
        other_book = Book.objects.create(
            title="Other Book", author="Other Author", isbn="review-isbn-2",
            description="Other description", genre="History", publisher="Test Press",
            published_year=2023, language="English", total_copies=1, available_copies=1,
        )
        Review.objects.create(user=self.other_user, book=other_book, rating=3, review_text="Okay")

        response = self.client.get(self.book_reviews_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["book"], self.book.id)

    @patch("reviews.views.AIReviewService.generate_review", return_value="Generated review draft")
    def test_ai_review_generates_draft_for_authenticated_user(self, generate):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.ai_url(), {"rating": 4, "notes": "Useful examples"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["generated_review"], "Generated review draft")
        generate.assert_called_once_with(self.book, 4, "Useful examples")

    @patch("reviews.views.AIReviewService.generate_review", side_effect=RuntimeError("provider failed"))
    def test_ai_review_provider_failure_returns_bad_gateway(self, generate):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.ai_url(), {"rating": 4, "notes": "Useful examples"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn("error", response.data)

    def test_ai_review_handles_auth_unknown_book_invalid_input_and_methods(self):
        response = self.client.post(self.ai_url(), {"rating": 4}, format="json")
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(self.ai_url(999999), format="json").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.get(self.ai_url()).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        for payload in ({}, {"rating": 0, "notes": "x"}, {"rating": 6, "notes": "x"}):
            with self.subTest(payload=payload):
                response = self.client.post(self.ai_url(), payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
