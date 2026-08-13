from rest_framework import serializers

from .models import Book


class BookSerializer(serializers.ModelSerializer):
    """
    Serializer for book CRUD operations.
    """

    class Meta:
        model = Book
        fields = "__all__"

    def validate(self, attrs):
        """Ensure a library cannot report more available copies than it owns."""
        total_copies = attrs.get("total_copies", getattr(self.instance, "total_copies", None))
        available_copies = attrs.get(
            "available_copies", getattr(self.instance, "available_copies", None)
        )

        if available_copies is not None and total_copies is not None and available_copies > total_copies:
            raise serializers.ValidationError({
                "available_copies": "Available copies cannot exceed total copies."
            })

        return attrs
