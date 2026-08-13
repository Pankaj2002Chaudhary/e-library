from rest_framework import serializers

from books.models import Book
from accounts.models import User


class BookAnalyticsSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Book

        fields = [
            "id",
            "title",
            "author",
            "average_rating",
            "borrow_count"
        ]


class ActiveUserSerializer(
    serializers.ModelSerializer
):

    borrow_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User

        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "borrow_count",
        ]
