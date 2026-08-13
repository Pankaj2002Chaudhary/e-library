from django.urls import path

from .views import (
    GenerateReviewView,
    CreateReviewView,
    BookReviewsView
)

urlpatterns = [

    path(
        "ai-review/<int:book_id>/",
        GenerateReviewView.as_view()
    ),

    path(
        "create/",
        CreateReviewView.as_view()
    ),

    path(
        "book/<int:book_id>/",
        BookReviewsView.as_view()
    ),
]