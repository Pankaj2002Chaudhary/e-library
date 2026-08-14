from rest_framework import serializers

from books.models import Book


class RecommendationSerializer(serializers.ModelSerializer):
    """Expose the compact book data needed by recommendation clients."""

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "genre",
            "average_rating",
            "borrow_count",
        ]
