from rest_framework import serializers

from books.models import Book

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for book reviews.
    """

    class Meta:
        model = Review

        fields = "__all__"

        read_only_fields = [
            "user"
        ]

    rating = serializers.IntegerField(min_value=1, max_value=5)

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        book = attrs.get("book")

        if user and book and Review.objects.filter(user=user, book=book).exists():
            raise serializers.ValidationError({
                "non_field_errors": "You have already reviewed this book."
            })

        return attrs
