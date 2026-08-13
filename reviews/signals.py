from django.db.models import Avg

from .models import Review


def update_book_rating(book):

    avg_rating = (
        Review.objects
        .filter(book=book)
        .aggregate(
            Avg("rating")
        )["rating__avg"]
    )

    book.average_rating = (
        round(avg_rating, 2)
        if avg_rating
        else 0
    )

    book.save(
        update_fields=[
            "average_rating"
        ]
    )