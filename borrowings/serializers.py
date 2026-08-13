from rest_framework import serializers

from .models import BorrowRecord


class BorrowRecordSerializer(serializers.ModelSerializer):

    book_title = serializers.ReadOnlyField(
        source="book.title"
    )

    class Meta:
        model = BorrowRecord

        fields = "__all__"

        read_only_fields = [
            "user",
            "borrowed_at",
            "due_date",
            "returned_at",
            "status",
        ]