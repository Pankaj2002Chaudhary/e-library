from django.db import models
from django.conf import settings

from books.models import Book


class Review(models.Model):
    """
    Stores user ratings and reviews for books.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    # Rating between 1 and 5
    rating = models.PositiveSmallIntegerField()

    review_text = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        unique_together = (
            "user",
            "book"
        )

    def __str__(self):
        return (
            f"{self.user.email} - "
            f"{self.book.title}"
        )