from django.urls import path

from .views import (
    DashboardSummaryView,
    MostBorrowedBooksView,
    TopRatedBooksView,
    ActiveUsersView,
    GenreDistributionView
)

urlpatterns = [

    path(
        "dashboard/",
        DashboardSummaryView.as_view()
    ),

    path(
        "most-borrowed/",
        MostBorrowedBooksView.as_view()
    ),

    path(
        "top-rated/",
        TopRatedBooksView.as_view()
    ),

    path(
        "active-users/",
        ActiveUsersView.as_view()
    ),

    path(
        "genre-distribution/",
        GenreDistributionView.as_view()
    ),
]