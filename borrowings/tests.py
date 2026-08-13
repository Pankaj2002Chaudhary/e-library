from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from books.models import Book
from .models import BorrowRecord


class BorrowingsApiTests(APITestCase):
    """Request-level coverage for borrowing, returning, and history APIs."""

    history_url = "/api/borrowings/history/"

    def setUp(self):
        self.user = self.make_user("member@example.com", "9000000001")
        self.other_user = self.make_user("other@example.com", "9000000002")
        self.book = self.make_book()

    def make_user(self, email, contact_number):
        return User.objects.create_user(
            email=email, password="safe-pass-123", first_name="Test", last_name="Member",
            contact_number=contact_number, street="1 Test Street", city="Test City",
            state="Test State", country="Test Country", postal_code="100001",
        )

    def make_book(self, **overrides):
        data = {
            "title": "Borrowable Book", "author": "Test Author", "isbn": "borrow-isbn-001",
            "description": "Test description", "genre": "Programming", "publisher": "Test Press",
            "published_year": 2024, "language": "English", "total_copies": 2,
            "available_copies": 2, "status": Book.Status.AVAILABLE,
        }
        data.update(overrides)
        return Book.objects.create(**data)

    def borrow_url(self, book_id=None):
        return f"/api/borrowings/borrow/{book_id or self.book.id}/"

    def return_url(self, book_id=None):
        return f"/api/borrowings/return/{book_id or self.book.id}/"

    def test_all_endpoints_require_authentication(self):
        for method, url in ((self.client.post, self.borrow_url()), (self.client.post, self.return_url()), (self.client.get, self.history_url)):
            with self.subTest(url=url):
                response = method(url)
                self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_borrow_creates_record_and_updates_inventory(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(self.borrow_url())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "Book borrowed successfully")
        record = BorrowRecord.objects.get(user=self.user, book=self.book)
        self.assertEqual(record.status, BorrowRecord.Status.BORROWED)
        self.assertIsNotNone(record.due_date)
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 1)
        self.assertEqual(self.book.borrow_count, 1)

    def test_borrow_rejects_unknown_duplicate_and_out_of_stock_books(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(self.borrow_url(999999)).status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(self.client.post(self.borrow_url()).status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.post(self.borrow_url()).status_code, status.HTTP_400_BAD_REQUEST)

        no_copies = self.make_book(isbn="borrow-isbn-002", total_copies=0, available_copies=0)
        response = self.client.post(self.borrow_url(no_copies.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "No copies available")

    def test_return_updates_record_and_restores_inventory(self):
        self.client.force_authenticate(self.user)
        self.client.post(self.borrow_url())

        response = self.client.post(self.return_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        record = BorrowRecord.objects.get(user=self.user, book=self.book)
        self.assertEqual(record.status, BorrowRecord.Status.RETURNED)
        self.assertIsNotNone(record.returned_at)
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 2)

    def test_return_rejects_unknown_or_not_active_borrow(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(self.return_url(999999)).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.post(self.return_url()).status_code, status.HTTP_404_NOT_FOUND)

        self.client.post(self.borrow_url())
        self.client.post(self.return_url())
        self.assertEqual(self.client.post(self.return_url()).status_code, status.HTTP_404_NOT_FOUND)

    def test_history_returns_only_current_users_records_with_book_details(self):
        BorrowRecord.objects.create(user=self.user, book=self.book)
        other_book = self.make_book(isbn="borrow-isbn-003")
        BorrowRecord.objects.create(user=self.other_user, book=other_book)
        self.client.force_authenticate(self.user)

        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["book"], self.book.id)
        self.assertEqual(response.data[0]["book_title"], self.book.title)
        self.assertNotIn("password", response.data[0])

    def test_only_post_is_allowed_for_borrow_and_return(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(self.borrow_url()).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.get(self.return_url()).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_user_can_borrow_again_after_return_and_inventory_remains_correct(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(self.borrow_url()).status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.post(self.return_url()).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(self.borrow_url()).status_code, status.HTTP_201_CREATED)

        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 1)
        self.assertEqual(self.book.borrow_count, 2)
        self.assertEqual(BorrowRecord.objects.filter(user=self.user, book=self.book).count(), 2)

    def test_multiple_users_can_borrow_distinct_available_copies(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(self.borrow_url()).status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.client.post(self.borrow_url()).status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.post(self.borrow_url()).status_code, status.HTTP_400_BAD_REQUEST)

        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 0)
        self.assertEqual(self.book.borrow_count, 2)

    def test_return_does_not_exceed_total_copies_when_inventory_is_corrupt(self):
        """A return must not make availability exceed physical inventory."""
        BorrowRecord.objects.create(user=self.user, book=self.book)
        self.book.available_copies = self.book.total_copies
        self.book.save(update_fields=["available_copies"])
        self.client.force_authenticate(self.user)

        response = self.client.post(self.return_url())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.book.refresh_from_db()
        self.assertLessEqual(self.book.available_copies, self.book.total_copies)

    def test_history_has_deterministic_newest_first_ordering(self):
        first = BorrowRecord.objects.create(user=self.user, book=self.book)
        second_book = self.make_book(isbn="borrow-isbn-004")
        second = BorrowRecord.objects.create(user=self.user, book=second_book)
        self.client.force_authenticate(self.user)

        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in response.data], [second.id, first.id])
