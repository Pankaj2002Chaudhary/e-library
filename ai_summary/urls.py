from django.urls import path

from .views import (
    GenerateSummaryView
)

urlpatterns = [

    path(
        "generate/<int:book_id>/",
        GenerateSummaryView.as_view(),
        name="generate-summary"
    ),
]