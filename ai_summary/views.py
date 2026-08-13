from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests

from books.models import Book

from .summary_manager import SummaryManager


class GenerateSummaryView(APIView):
    """
    Generate or retrieve
    AI-generated summaries.
    """

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        book_id
    ):

        summary_type = (
            request.query_params
            .get(
                "type",
                "SHORT"
            )
            .upper()
        )

        if summary_type not in [
            "SHORT",
            "DETAILED"
        ]:

            return Response(
                {
                    "error":
                    "type must be SHORT or DETAILED"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            book = Book.objects.get(
                id=book_id
            )

        except Book.DoesNotExist:

            return Response(
                {
                    "error":
                    "Book not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            result = SummaryManager.get_or_generate(book, summary_type)
        except requests.RequestException:
            return Response(
                {"error": "Summary service is temporarily unavailable. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception:
            return Response(
                {"error": "Unable to generate the summary right now. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if (
            result["status"]
            == "PROCESSING"
        ):

            return Response(
                {
                    "message": "Summary generation already in progress.",
                    "retry_after": 5,
                },
                status=status.HTTP_202_ACCEPTED
            )

        return Response(
            {
                "summary_type":
                summary_type,

                "cached":
                result["cached"],

                "summary":
                result["summary"]
            }
        )
