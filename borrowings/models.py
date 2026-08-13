from django.db import models
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

from books.models import Book


class BorrowRecord(models.Model):
    """
    Stores borrowing history and book access records.
    """

    class Status(models.TextChoices):
        BORROWED = "BORROWED", "Borrowed"
        RETURNED = "RETURNED", "Returned"
        OVERDUE = "OVERDUE", "Overdue"

    # User who borrowed the book
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrow_records"
    )

    # Borrowed book
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="borrow_records"
    )

    borrowed_at = models.DateTimeField(auto_now_add=True)

    # Expected return date
    due_date = models.DateTimeField()

    returned_at = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.BORROWED
    )

    def save(self, *args, **kwargs):

        # Set default borrowing period
        if not self.pk:
            self.due_date = timezone.now() + timedelta(days=14)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.book.title}"