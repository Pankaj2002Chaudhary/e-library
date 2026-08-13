from unittest.mock import patch

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from books.models import Book
from .models import BookSummary


class GenerateSummaryApiTests(APITestCase):
    """Request-level coverage for POST /api/ai/generate/<book_id>/."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email="member@example.com", password="safe-pass-123", first_name="Test",
            last_name="User", contact_number="9000000001", street="1 Test Street",
            city="Test City", state="Test State", country="Test Country", postal_code="100001",
        )
        self.book = Book.objects.create(
            title="Test Book", author="Test Author", isbn="summary-isbn-1",
            description="A book used for summary tests.", genre="Technology", publisher="Test Press",
            published_year=2024, language="English", total_copies=1, available_copies=1,
        )

    def url(self, book_id=None):
        return f"/api/ai/generate/{book_id or self.book.id}/"

    def test_requires_authentication_and_post_method(self):
        response = self.client.post(self.url(), {"unused": True}, format="json")
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(self.url()).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch("ai_summary.summary_manager.AISummaryService.generate_summary", return_value="Short summary")
    def test_generates_short_summary_persists_it_and_caches_second_request(self, generate):
        self.client.force_authenticate(self.user)

        first = self.client.post(self.url(), {"ignored": True}, format="json")
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data, {"summary_type": "SHORT", "cached": False, "summary": "Short summary"})
        self.assertEqual(generate.call_count, 1)
        summary = BookSummary.objects.get(book=self.book, summary_type=BookSummary.SummaryType.SHORT)
        self.assertEqual(summary.status, BookSummary.Status.COMPLETED)
        self.assertEqual(summary.summary, "Short summary")

        second = self.client.post(self.url(), format="json")
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(second.data, {"summary_type": "SHORT", "cached": True, "summary": "Short summary"})
        generate.assert_called_once()

    @patch("ai_summary.summary_manager.AISummaryService.generate_summary", return_value="Detailed summary")
    def test_detailed_summary_is_separate_from_short_summary(self, generate):
        self.client.force_authenticate(self.user)
        self.client.post(self.url(), {"type": "short"}, format="json")
        detailed = self.client.post(f"{self.url()}?type=detailed", format="json")

        self.assertEqual(detailed.status_code, status.HTTP_200_OK)
        self.assertEqual(detailed.data["summary_type"], "DETAILED")
        self.assertFalse(detailed.data["cached"])
        self.assertEqual(BookSummary.objects.filter(book=self.book).count(), 2)
        self.assertEqual(generate.call_count, 2)

    def test_returns_202_when_summary_is_already_processing(self):
        BookSummary.objects.create(
            book=self.book, summary_type=BookSummary.SummaryType.SHORT,
            status=BookSummary.Status.PROCESSING,
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(self.url(), format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["message"], "Summary generation already in progress.")
        self.assertEqual(response.data["retry_after"], 5)

    def test_rejects_invalid_type_and_unknown_book(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(f"{self.url()}?type=long", format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(self.url(999999), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("ai_summary.summary_manager.AISummaryService.generate_summary", side_effect=TimeoutError("AI unavailable"))
    def test_ai_failure_marks_summary_failed_without_leaving_processing_lock(self, generate):
        self.client.force_authenticate(self.user)
        self.client.raise_request_exception = False

        response = self.client.post(self.url(), format="json")

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        summary = BookSummary.objects.get(book=self.book, summary_type=BookSummary.SummaryType.SHORT)
        self.assertEqual(summary.status, BookSummary.Status.FAILED)

    @patch("ai_summary.summary_manager.AISummaryService.generate_summary", return_value="Recovered summary")
    def test_retries_a_previously_failed_summary(self, generate):
        BookSummary.objects.create(
            book=self.book, summary_type=BookSummary.SummaryType.SHORT,
            status=BookSummary.Status.FAILED,
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(self.url(), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["cached"])
        summary = BookSummary.objects.get(book=self.book, summary_type=BookSummary.SummaryType.SHORT)
        self.assertEqual(summary.status, BookSummary.Status.COMPLETED)
        self.assertEqual(summary.summary, "Recovered summary")
        generate.assert_called_once()
