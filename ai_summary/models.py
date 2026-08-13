from django.db import models

from books.models import Book


class BookSummary(models.Model):
    """
    Stores generated AI summaries for books.
    """

    class SummaryType(models.TextChoices):
        SHORT = "SHORT", "Short"
        DETAILED = "DETAILED", "Detailed"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    # Book for which summary was generated
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="summaries"
    )

    # Type of generated summary
    summary_type = models.CharField(
        max_length=20,
        choices=SummaryType.choices
    )

    # Generated summary text
    summary = models.TextField(
        blank=True
    )

    # Current generation state
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    generated_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        unique_together = (
            "book",
            "summary_type"
        )

    def __str__(self):
        return (
            f"{self.book.title} "
            f"({self.summary_type})"
        )