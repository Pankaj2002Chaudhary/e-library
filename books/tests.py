from copy import deepcopy

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from .models import Book


class BooksApiTests(APITestCase):
    """End-to-end request coverage for the documented Books API."""

    list_url = "/api/books/"

    def setUp(self):
        self.admin = self.create_user("admin@example.com", "9000000001", User.Role.ADMIN)
        self.librarian = self.create_user("librarian@example.com", "9000000002", User.Role.LIBRARIAN)
        self.member = self.create_user("member@example.com", "9000000003", User.Role.MEMBER)
        self.payload = {
            "title": "Clean Code", "author": "Robert Martin", "isbn": "isbn-001",
            "description": "Software craftsmanship.", "genre": "Programming",
            "publisher": "Example Press", "published_year": 2024, "language": "English",
            "total_copies": 4, "available_copies": 4, "borrow_count": 0,
            "average_rating": 4.0, "status": Book.Status.AVAILABLE,
        }

    def create_user(self, email, contact_number, role):
        return User.objects.create_user(
            email=email, password="safe-pass-123", first_name="Test", last_name="User",
            contact_number=contact_number, street="1 Test Street", city="Test City",
            state="Test State", country="Test Country", postal_code="100001", role=role,
        )

    def create_book(self, **overrides):
        values = deepcopy(self.payload)
        values.update(overrides)
        return Book.objects.create(**values)

    def detail_url(self, book):
        return f"{self.list_url}{book.pk}/"

    def test_create_requires_admin_or_librarian(self):
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, status.HTTP_403_FORBIDDEN)

        for user, isbn in ((self.admin, "isbn-002"), (self.librarian, "isbn-003")):
            with self.subTest(role=user.role):
                data = deepcopy(self.payload)
                data["isbn"] = isbn
                self.client.force_authenticate(user)
                response = self.client.post(self.list_url, data, format="json")
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(response.data["isbn"], isbn)

    def test_get_all_books_and_get_single_book_are_public(self):
        book = self.create_book()

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], book.id)

        response = self.client.get(self.detail_url(book))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], book.title)

    def test_update_book_requires_privileged_role_and_updates_data(self):
        book = self.create_book()
        self.client.force_authenticate(self.member)
        self.assertEqual(
            self.client.put(self.detail_url(book), self.payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )

        data = deepcopy(self.payload)
        data.update(title="Refactored", isbn="isbn-updated", available_copies=3)
        self.client.force_authenticate(self.librarian)
        response = self.client.put(self.detail_url(book), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Refactored")
        self.assertEqual(response.data["available_copies"], 3)

    def test_delete_book_requires_privileged_role_and_deletes(self):
        book = self.create_book()
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.delete(self.detail_url(book)).status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(self.detail_url(book)).status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(pk=book.pk).exists())

    def test_searches_title_author_and_isbn(self):
        title = self.create_book(title="Clean Architecture", isbn="isbn-101")
        author = self.create_book(title="Compilers", author="Grace Hopper", isbn="isbn-102")
        isbn = self.create_book(title="Algorithms", isbn="978-clean-103")

        for query, expected in (("architecture", title), ("grace", author), ("clean-103", isbn)):
            with self.subTest(query=query):
                response = self.client.get(self.list_url, {"search": query})
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["count"], 1)
                self.assertEqual(response.data["results"][0]["id"], expected.id)

    def test_filters_by_genre_language_and_published_year(self):
        matching = self.create_book(title="Python", isbn="isbn-201")
        self.create_book(title="French Python", isbn="isbn-202", language="French")
        self.create_book(title="History", isbn="isbn-203", genre="History", published_year=2023)

        for params in ({"genre": "Programming"}, {"language": "English"}, {"published_year": 2024}):
            with self.subTest(params=params):
                response = self.client.get(self.list_url, params)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn(matching.id, [result["id"] for result in response.data["results"]])

    def test_orders_by_highest_average_rating(self):
        highest = self.create_book(title="Highest", isbn="isbn-301", average_rating=4.9)
        self.create_book(title="Lower", isbn="isbn-302", average_rating=3.1)

        response = self.client.get(self.list_url, {"ordering": "-average_rating"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["id"], highest.id)

    def test_create_rejects_missing_invalid_and_duplicate_fields(self):
        self.client.force_authenticate(self.admin)
        required_fields = (
            "title", "author", "isbn", "description", "genre", "publisher",
            "published_year", "total_copies", "available_copies",
        )
        for field in required_fields:
            with self.subTest(missing=field):
                payload = deepcopy(self.payload)
                payload.pop(field)
                response = self.client.post(self.list_url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)

        self.create_book()
        payload = deepcopy(self.payload)
        payload.update(
            total_copies=-1, available_copies=-1, status="LOST",
            cover_image="not-a-url",
        )
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ("isbn", "total_copies", "available_copies", "status", "cover_image"):
            self.assertIn(field, response.data)

    def test_rejects_malformed_json_and_unsupported_methods(self):
        self.client.force_authenticate(self.admin)
        response = self.client.generic("POST", self.list_url, data='{"title":', content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(self.list_url, [self.payload], format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

        book = self.create_book()
        self.assertEqual(self.client.put(self.list_url, self.payload, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.post(self.detail_url(book), self.payload, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_returns_404_for_unknown_book_and_invalid_page(self):
        self.assertEqual(self.client.get(f"{self.list_url}999999/").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.get(self.list_url, {"page": 0}).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.get(self.list_url, {"page": "bad"}).status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_filter_is_rejected_and_unknown_ordering_is_ignored(self):
        self.create_book()
        response = self.client.get(self.list_url, {"published_year": "not-a-number"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(self.list_url, {"ordering": "not_a_book_field"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_page_size_is_capped_at_100(self):
        for index in range(101):
            self.create_book(title=f"Book {index}", isbn=f"cap-{index}")

        response = self.client.get(self.list_url, {"page_size": 1000})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 101)
        self.assertEqual(len(response.data["results"]), 100)

    def test_detects_missing_inventory_consistency_validation(self):
        """A failing test reveals whether available copies can exceed total copies."""
        self.client.force_authenticate(self.admin)
        payload = deepcopy(self.payload)
        payload.update(isbn="inventory-001", total_copies=1, available_copies=2)

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("available_copies", response.data)
