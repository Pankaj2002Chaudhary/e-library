from django.urls import path

from .views import (
    AlsoBorrowedBooksView,
    PersonalizedRecommendationsView,
    TrendingBooksView,
)


urlpatterns = [
    path(
        "personalized/",
        PersonalizedRecommendationsView.as_view(),
        name="personalized-recommendations",
    ),
    path(
        "also-borrowed/<int:book_id>/",
        AlsoBorrowedBooksView.as_view(),
        name="also-borrowed-books",
    ),
    path(
        "trending/",
        TrendingBooksView.as_view(),
        name="trending-books",
    ),
]
