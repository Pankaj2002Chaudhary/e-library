from django.db.models import Count

from books.models import Book
from borrowings.models import BorrowRecord


class RecommendationService:
    """Build efficient, read-only book recommendation querysets."""

    @staticmethod
    def get_personalized_books(user):
        """Recommend unborrowed books from the user's most-read genres."""
        preferred_genres = (
            BorrowRecord.objects.filter(user=user)
            .values("book__genre")
            .annotate(borrow_frequency=Count("id"))
            .order_by("-borrow_frequency", "book__genre")
            .values("book__genre")
        )
        borrowed_book_ids = BorrowRecord.objects.filter(user=user).values("book_id")

        return (
            Book.objects.filter(genre__in=preferred_genres)
            .exclude(pk__in=borrowed_book_ids)
            .order_by("-average_rating", "-borrow_count", "title", "id")[:10]
        )

    @staticmethod
    def get_also_borrowed_books(book_id):
        """Return books most frequently borrowed by readers of one book."""
        # Validate the target before deriving its borrowing cohort.
        Book.objects.get(pk=book_id)

        reader_ids = BorrowRecord.objects.filter(book_id=book_id).values("user_id")

        return (
            Book.objects.filter(borrow_records__user_id__in=reader_ids)
            .exclude(pk=book_id)
            .annotate(co_borrow_count=Count("borrow_records"))
            .order_by("-co_borrow_count", "-average_rating", "-borrow_count", "title", "id")[:10]
        )

    @staticmethod
    def get_trending_books():
        """Return the ten most borrowed and best-rated books."""
        return Book.objects.order_by(
            "-borrow_count", "-average_rating", "title", "id"
        )[:10]
