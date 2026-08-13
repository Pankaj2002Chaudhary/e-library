from django.db import transaction
from rest_framework import generics
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from books.models import Book
from .models import BorrowRecord
from .serializers import BorrowRecordSerializer

class BorrowBookView(APIView):
    """
    Allows members to borrow available books.
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, book_id):

        user = request.user

        try:
            # Lock row to prevent concurrent borrowing issues
            book = Book.objects.select_for_update().get(
                id=book_id
            )

        except Book.DoesNotExist:
            return Response(
                {"error": "Book not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Prevent multiple active borrows of same book
        already_borrowed = BorrowRecord.objects.filter(
            user=user,
            book=book,
            status=BorrowRecord.Status.BORROWED
        ).exists()

        if already_borrowed:
            return Response(
                {"error": "Book already borrowed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ensure at least one copy is available
        if book.available_copies <= 0:
            return Response(
                {"error": "No copies available"},
                status=status.HTTP_400_BAD_REQUEST
            )

        BorrowRecord.objects.create(
            user=user,
            book=book
        )

        # Update book inventory statistics
        book.available_copies -= 1
        book.borrow_count += 1
        book.save()

        return Response(
            {"message": "Book borrowed successfully"},
            status=status.HTTP_201_CREATED
        )




class ReturnBookView(APIView):
    """
    Marks a borrowed book as returned.
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, book_id):

        try:
            # Fetch active borrowing record
            record = BorrowRecord.objects.select_for_update().select_related(
                "book"
            ).get(
                user=request.user,
                book_id=book_id,
                status=BorrowRecord.Status.BORROWED
            )

        except BorrowRecord.DoesNotExist:
            return Response(
                {"error": "No active borrow found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Lock the inventory row before restoring a copy. This prevents two
        # simultaneous returns from increasing availability twice.
        book = Book.objects.select_for_update().get(pk=record.book_id)
        if book.available_copies >= book.total_copies:
            return Response(
                {"error": "Book inventory is already at total capacity"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Close borrowing record and restore one available copy.
        record.status = BorrowRecord.Status.RETURNED
        record.returned_at = timezone.now()
        record.save(update_fields=["status", "returned_at"])

        book.available_copies += 1
        book.save(update_fields=["available_copies"])

        return Response(
            {"message": "Book returned successfully"}
        )

class BorrowHistoryView(generics.ListAPIView):
    """
    Returns borrowing history of the logged-in user.
    """

    serializer_class = BorrowRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Fetch history with book details
        return BorrowRecord.objects.filter(
            user=self.request.user
        ).select_related("book").order_by("-borrowed_at", "-id")
