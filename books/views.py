from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework import filters

from django_filters.rest_framework import DjangoFilterBackend

from .models import Book
from .serializers import BookSerializer
from .permissions import IsAdminOrLibrarian
from .pagination import BookPagination


class BookViewSet(viewsets.ModelViewSet):
    """
    Manage library books.

    Features:
    - CRUD operations
    - Search
    - Filtering
    - Sorting
    """

    queryset = Book.objects.all()

    serializer_class = BookSerializer

    permission_classes = [IsAdminOrLibrarian]

    pagination_class = BookPagination

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    # Exact match filters
    filterset_fields = [
        "genre",
        "language",
        "status",
        "published_year",
    ]

    # Search across text fields
    search_fields = [
        "title",
        "author",
        "isbn",
    ]

    # Supported sorting fields
    ordering_fields = [
        "average_rating",
        "borrow_count",
        "published_year",
        "created_at",
    ]

    ordering = ["title"]