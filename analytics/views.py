from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdminOrLibrarian
from .serializers import ActiveUserSerializer, BookAnalyticsSerializer
from .services import AnalyticsService


class DashboardSummaryView(APIView):
    """Return high-level platform statistics."""

    permission_classes = [IsAdminOrLibrarian]

    def get(self, request):
        return Response(AnalyticsService.dashboard_summary())


class MostBorrowedBooksView(APIView):
    """Return the ten most borrowed books."""

    permission_classes = [IsAdminOrLibrarian]

    def get(self, request):
        books = AnalyticsService.most_borrowed_books()
        return Response(BookAnalyticsSerializer(books, many=True).data)


class TopRatedBooksView(APIView):
    """Return the ten highest-rated books."""

    permission_classes = [IsAdminOrLibrarian]

    def get(self, request):
        books = AnalyticsService.top_rated_books()
        return Response(BookAnalyticsSerializer(books, many=True).data)


class ActiveUsersView(APIView):
    """Return the ten users with the most borrowing records."""

    permission_classes = [IsAdminOrLibrarian]

    def get(self, request):
        users = AnalyticsService.active_users()
        return Response(ActiveUserSerializer(users, many=True).data)


class GenreDistributionView(APIView):
    """Return book counts grouped by genre."""

    permission_classes = [IsAdminOrLibrarian]

    def get(self, request):
        return Response(AnalyticsService.genre_distribution())
