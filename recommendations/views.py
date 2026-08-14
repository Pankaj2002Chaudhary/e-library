from django.http import Http404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book

from .serializers import RecommendationSerializer
from .services import RecommendationService


class PersonalizedRecommendationsView(APIView):
    """Return recommendations tailored to the authenticated reader."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        books = RecommendationService.get_personalized_books(request.user)
        return Response(RecommendationSerializer(books, many=True).data)


class AlsoBorrowedBooksView(APIView):
    """Return books commonly borrowed by readers of the selected book."""

    permission_classes = [AllowAny]

    def get(self, request, book_id):
        try:
            books = RecommendationService.get_also_borrowed_books(book_id)
        except Book.DoesNotExist:
            raise Http404("Book not found.")

        return Response(RecommendationSerializer(books, many=True).data)


class TrendingBooksView(APIView):
    """Return the current top ten books by usage and rating."""

    permission_classes = [AllowAny]

    def get(self, request):
        books = RecommendationService.get_trending_books()
        return Response(RecommendationSerializer(books, many=True).data)
