from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from books.models import Book
from borrowings.models import BorrowRecord


class RecommendationApiTests(APITestCase):
    """Request-level coverage for the recommendation endpoints."""

    def setUp(self):
        self.member = self.make_user("member@example.com", "9000000001")
        self.other_member = self.make_user("other@example.com", "9000000002")
        self.third_member = self.make_user("third@example.com", "9000000003")

        self.python_book = self.make_book(1, "Programming", 5.0, 1)
        self.recommended_book = self.make_book(2, "Programming", 4.8, 8)
        self.history_book = self.make_book(3, "History", 4.9, 20)
        self.co_borrowed_book = self.make_book(4, "Design", 4.0, 2)

    def make_user(self, email, contact_number):
        return User.objects.create_user(
            email=email,
            password="safe-pass-123",
            first_name="Test",
            last_name="Reader",
            contact_number=contact_number,
            street="1 Test Street",
            city="Test City",
            state="Test State",
            country="Test Country",
            postal_code="100001",
        )

    def make_book(self, index, genre, average_rating, borrow_count):
        return Book.objects.create(
            title=f"Book {index}",
            author="Test Author",
            isbn=f"recommendation-{index}",
            description="Test description",
            genre=genre,
            publisher="Test Press",
            published_year=2024,
            language="English",
            total_copies=5,
            available_copies=5,
            average_rating=average_rating,
            borrow_count=borrow_count,
        )

    def test_personalized_recommendations_require_auth_and_exclude_history(self):
        BorrowRecord.objects.create(user=self.member, book=self.python_book)

        self.assertIn(
            self.client.get("/api/recommendations/personalized/").status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

        self.client.force_authenticate(self.member)
        response = self.client.get("/api/recommendations/personalized/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([book["id"] for book in response.data], [self.recommended_book.id])

    def test_personalized_recommendations_return_empty_for_a_new_reader(self):
        self.client.force_authenticate(self.member)

        response = self.client.get("/api/recommendations/personalized/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_personalized_recommendations_are_limited_and_sorted(self):
        BorrowRecord.objects.create(user=self.member, book=self.python_book)
        for index in range(10, 22):
            self.make_book(index, "Programming", index / 10, index)

        self.client.force_authenticate(self.member)
        response = self.client.get("/api/recommendations/personalized/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)
        self.assertNotIn(self.python_book.id, [book["id"] for book in response.data])
        ordering_values = [
            (book["average_rating"], book["borrow_count"])
            for book in response.data
        ]
        self.assertEqual(ordering_values, sorted(ordering_values, reverse=True))

    def test_also_borrowed_counts_books_from_the_same_reader_cohort(self):
        BorrowRecord.objects.create(user=self.member, book=self.python_book)
        BorrowRecord.objects.create(user=self.member, book=self.co_borrowed_book)
        BorrowRecord.objects.create(user=self.other_member, book=self.python_book)
        BorrowRecord.objects.create(user=self.other_member, book=self.co_borrowed_book)
        BorrowRecord.objects.create(user=self.third_member, book=self.history_book)

        response = self.client.get(
            f"/api/recommendations/also-borrowed/{self.python_book.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([book["id"] for book in response.data], [self.co_borrowed_book.id])

    def test_also_borrowed_orders_by_co_borrow_frequency(self):
        less_common_book = self.make_book(7, "Design", 5.0, 100)
        BorrowRecord.objects.create(user=self.member, book=self.python_book)
        BorrowRecord.objects.create(user=self.member, book=self.co_borrowed_book)
        BorrowRecord.objects.create(user=self.member, book=less_common_book)
        BorrowRecord.objects.create(user=self.other_member, book=self.python_book)
        BorrowRecord.objects.create(user=self.other_member, book=self.co_borrowed_book)

        response = self.client.get(
            f"/api/recommendations/also-borrowed/{self.python_book.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [book["id"] for book in response.data],
            [self.co_borrowed_book.id, less_common_book.id],
        )

    def test_also_borrowed_returns_empty_when_no_reader_has_borrowed_the_book(self):
        response = self.client.get(
            f"/api/recommendations/also-borrowed/{self.python_book.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_trending_books_are_sorted_by_borrow_count_then_rating(self):
        tied_higher_rating = self.make_book(5, "Science", 4.9, 20)
        tied_lower_rating = self.make_book(6, "Science", 4.0, 20)

        response = self.client.get("/api/recommendations/trending/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [book["id"] for book in response.data[:3]],
            [self.history_book.id, tied_higher_rating.id, tied_lower_rating.id],
        )

    def test_trending_books_are_public_and_limited_to_ten(self):
        for index in range(20, 31):
            self.make_book(index, "Science", 4.0, index)

        response = self.client.get("/api/recommendations/trending/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)
        self.assertEqual(response.data[0]["borrow_count"], 30)

    def test_also_borrowed_returns_404_for_unknown_book(self):
        response = self.client.get("/api/recommendations/also-borrowed/999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
