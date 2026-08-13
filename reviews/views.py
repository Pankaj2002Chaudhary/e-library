from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

from books.models import Book

from .models import Review
from .serializers import ReviewSerializer
from .services import AIReviewService
from .signals import update_book_rating


class GenerateReviewView(APIView):
    """Generate an AI-assisted review draft."""

    permission_classes = [IsAuthenticated]

    def post(self, request, book_id):
        rating = request.data.get("rating")
        notes = request.data.get("notes")

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response(
                {"error": "Book not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if rating is None:
            return Response(
                {"rating": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rating = int(rating)
        except (TypeError, ValueError):
            return Response(
                {"rating": "Rating must be an integer from 1 to 5."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not 1 <= rating <= 5:
            return Response(
                {"rating": "Rating must be between 1 and 5."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            review = AIReviewService.generate_review(book, rating, notes)
        except requests.RequestException:
            return Response(
                {"error": "Review service is temporarily unavailable. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception:
            return Response(
                {"error": "Unable to generate a review right now. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"generated_review": review})


class CreateReviewView(generics.CreateAPIView):
    """Create a book review for the authenticated user."""

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        try:
            review = serializer.save(user=self.request.user)
        except IntegrityError as exc:
            raise ValidationError({
                "non_field_errors": "You have already reviewed this book."
            }) from exc

        update_book_rating(review.book)


class BookReviewsView(generics.ListAPIView):
    """List reviews for a book."""

    serializer_class = ReviewSerializer

    def get_queryset(self):
        if not Book.objects.filter(pk=self.kwargs["book_id"]).exists():
            from rest_framework.exceptions import NotFound

            raise NotFound("Book not found.")

        return Review.objects.filter(book_id=self.kwargs["book_id"]).select_related("user")
