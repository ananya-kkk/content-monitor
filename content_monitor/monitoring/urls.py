from django.urls import path

from monitoring.views import (
    FlagDetailView,
    FlagListView,
    KeywordCreateView,
    KeywordListView,
    ScanView,
)

urlpatterns = [
    # Keywords
    path("keywords/", KeywordCreateView.as_view(), name="keyword-create"),
    path("keywords/list/", KeywordListView.as_view(), name="keyword-list"),

    # Scan
    path("scan/", ScanView.as_view(), name="scan"),

    # Flags
    path("flags/", FlagListView.as_view(), name="flag-list"),
    path("flags/<int:pk>/", FlagDetailView.as_view(), name="flag-detail"),
]
