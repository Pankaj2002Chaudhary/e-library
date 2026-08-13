from django.db.models import Count

from accounts.models import User
from books.models import Book
from borrowings.models import BorrowRecord


class AnalyticsService:
    """Build read-only, bounded analytics for the dashboard."""

    @staticmethod
    def dashboard_summary():
        return {
            "total_books": Book.objects.count(),
            "total_users": User.objects.count(),
            "total_borrowings": BorrowRecord.objects.count(),
            "active_borrowings": BorrowRecord.objects.filter(
                status=BorrowRecord.Status.BORROWED
            ).count(),
        }

    @staticmethod
    def most_borrowed_books():
        return Book.objects.order_by("-borrow_count", "title", "id")[:10]

    @staticmethod
    def top_rated_books():
        return Book.objects.order_by("-average_rating", "title", "id")[:10]

    @staticmethod
    def active_users():
        return (
            User.objects.annotate(borrow_count=Count("borrow_records"))
            .filter(borrow_count__gt=0)
            .order_by("-borrow_count", "email", "id")[:10]
        )

    @staticmethod
    def genre_distribution():
        return list(
            Book.objects.values("genre")
            .annotate(total=Count("id"))
            .order_by("-total", "genre")
        )
