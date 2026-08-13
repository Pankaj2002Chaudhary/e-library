from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from books.models import Book
from borrowings.models import BorrowRecord
from reviews.models import Review


class AnalyticsApiTests(APITestCase):
    """Edge-case and aggregation coverage for analytics dashboard APIs."""

    endpoints = (
        "/api/analytics/dashboard/",
        "/api/analytics/most-borrowed/",
        "/api/analytics/top-rated/",
        "/api/analytics/active-users/",
        "/api/analytics/genre-distribution/",
    )

    def setUp(self):
        self.admin = self.make_user("admin@example.com", "9000000001", User.Role.ADMIN)
        self.librarian = self.make_user("librarian@example.com", "9000000002", User.Role.LIBRARIAN)
        self.member = self.make_user("member@example.com", "9000000003", User.Role.MEMBER)

    def make_user(self, email, contact_number, role):
        return User.objects.create_user(
            email=email, password="safe-pass-123", first_name="Test", last_name="User",
            contact_number=contact_number, street="1 Test Street", city="Test City",
            state="Test State", country="Test Country", postal_code="100001", role=role,
        )

    def make_book(self, index, **overrides):
        values = {
            "title": f"Book {index}", "author": "Author", "isbn": f"analytics-{index}",
            "description": "Description", "genre": "Programming", "publisher": "Press",
            "published_year": 2024, "language": "English", "total_copies": 5,
            "available_copies": 5, "borrow_count": 0, "average_rating": 0,
        }
        values.update(overrides)
        return Book.objects.create(**values)

    def test_all_dashboard_endpoints_require_admin_or_librarian(self):
        for endpoint in self.endpoints:
            with self.subTest(endpoint=endpoint):
                anonymous = self.client.get(endpoint)
                self.assertIn(anonymous.status_code, (401, 403))

                self.client.force_authenticate(self.member)
                member_response = self.client.get(endpoint)
                self.assertEqual(member_response.status_code, status.HTTP_403_FORBIDDEN)
                self.client.force_authenticate(user=None)

    def test_all_dashboard_endpoints_allow_admin_and_librarian(self):
        for user in (self.admin, self.librarian):
            self.client.force_authenticate(user)
            for endpoint in self.endpoints:
                with self.subTest(role=user.role, endpoint=endpoint):
                    self.assertEqual(self.client.get(endpoint).status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=None)

    def test_dashboard_empty_database_returns_zero_counts_and_empty_lists(self):
        self.client.force_authenticate(self.admin)

        summary = self.client.get(self.endpoints[0])
        self.assertEqual(summary.data, {
            "total_books": 0,
            "total_users": 3,
            "total_borrowings": 0,
            "active_borrowings": 0,
        })
        self.assertEqual(self.client.get(self.endpoints[1]).data, [])
        self.assertEqual(self.client.get(self.endpoints[2]).data, [])
        self.assertEqual(self.client.get(self.endpoints[3]).data, [])
        self.assertEqual(self.client.get(self.endpoints[4]).data, [])

    def test_dashboard_summary_counts_only_borrowed_as_active(self):
        book = self.make_book(1)
        BorrowRecord.objects.create(user=self.member, book=book, status=BorrowRecord.Status.BORROWED)
        returned = self.make_book(2)
        BorrowRecord.objects.create(user=self.member, book=returned, status=BorrowRecord.Status.RETURNED)
        self.client.force_authenticate(self.admin)

        response = self.client.get(self.endpoints[0])

        self.assertEqual(response.data["total_books"], 2)
        self.assertEqual(response.data["total_borrowings"], 2)
        self.assertEqual(response.data["active_borrowings"], 1)

    def test_most_borrowed_and_top_rated_are_sorted_and_capped(self):
        for index in range(12):
            self.make_book(index, borrow_count=index, average_rating=index / 2)
        self.client.force_authenticate(self.admin)

        borrowed = self.client.get(self.endpoints[1]).data
        rated = self.client.get(self.endpoints[2]).data

        self.assertEqual(len(borrowed), 10)
        self.assertEqual(borrowed[0]["borrow_count"], 11)
        self.assertEqual(len(rated), 10)
        self.assertEqual(rated[0]["average_rating"], 5.5)

    def test_ties_have_deterministic_title_order(self):
        self.make_book(1, title="Alpha", borrow_count=5, average_rating=4)
        self.make_book(2, title="Beta", borrow_count=5, average_rating=4)
        self.client.force_authenticate(self.admin)

        borrowed = self.client.get(self.endpoints[1]).data
        rated = self.client.get(self.endpoints[2]).data

        self.assertEqual([item["title"] for item in borrowed], ["Alpha", "Beta"])
        self.assertEqual([item["title"] for item in rated], ["Alpha", "Beta"])

    def test_active_users_includes_borrow_count_and_excludes_password(self):
        book = self.make_book(1)
        BorrowRecord.objects.create(user=self.member, book=book)
        self.client.force_authenticate(self.admin)

        response = self.client.get(self.endpoints[3])

        member = next(item for item in response.data if item["email"] == self.member.email)
        self.assertEqual(member["borrow_count"], 1)
        self.assertNotIn("password", member)

    def test_genre_distribution_groups_and_sorts_counts(self):
        self.make_book(1, genre="Programming")
        self.make_book(2, genre="Programming")
        self.make_book(3, genre="History")
        self.client.force_authenticate(self.admin)

        response = self.client.get(self.endpoints[4])

        self.assertEqual(response.data, [
            {"genre": "Programming", "total": 2},
            {"genre": "History", "total": 1},
        ])

    def test_dashboard_endpoints_reject_non_get_methods(self):
        self.client.force_authenticate(self.admin)
        for endpoint in self.endpoints:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(
                    self.client.post(endpoint, {}, format="json").status_code,
                    status.HTTP_405_METHOD_NOT_ALLOWED,
                )
