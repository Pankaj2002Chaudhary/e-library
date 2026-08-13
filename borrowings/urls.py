from django.urls import path

from .views import (
    BorrowBookView,
    ReturnBookView,
    BorrowHistoryView
)

urlpatterns = [

    path(
        "borrow/<int:book_id>/",
        BorrowBookView.as_view(),
        name="borrow-book"
    ),

    path(
        "return/<int:book_id>/",
        ReturnBookView.as_view(),
        name="return-book"
    ),

    path(
        "history/",
        BorrowHistoryView.as_view(),
        name="borrow-history"
    ),
]