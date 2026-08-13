from django.db import models


class Book(models.Model):

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        OUT_OF_STOCK = "OUT_OF_STOCK", "Out of Stock"

    title = models.CharField(max_length=255)

    author = models.CharField(max_length=255)

    isbn = models.CharField(
        max_length=20,
        unique=True
    )

    description = models.TextField()

    genre = models.CharField(max_length=100)

    publisher = models.CharField(
        max_length=255
    )

    published_year = models.IntegerField()

    language = models.CharField(
        max_length=50,
        default="English"
    )

    total_copies = models.PositiveIntegerField()

    available_copies = models.PositiveIntegerField()

    borrow_count = models.PositiveIntegerField(
        default=0
    )

    average_rating = models.FloatField(
        default=0
    )

    cover_image = models.URLField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title

from django.conf import settings


class Wishlist(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            "user",
            "book"
        )