from rest_framework import serializers

from .models import BookSummary


class BookSummarySerializer(serializers.ModelSerializer):
    """
    Serializer for AI summaries.
    """

    class Meta:
        model = BookSummary

        fields = "__all__"