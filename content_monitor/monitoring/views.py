from rest_framework import generics, mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.models import Flag, Keyword
from monitoring.serializers import (
    FlagSerializer,
    FlagStatusUpdateSerializer,
    KeywordSerializer,
)
from monitoring.services.scanner import run_scan


# ---------------------------------------------------------------------------
# POST /keywords/
# ---------------------------------------------------------------------------

class KeywordCreateView(generics.CreateAPIView):
    """Create a new keyword to monitor."""

    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer


# ---------------------------------------------------------------------------
# GET /keywords/  (bonus: list existing keywords for convenience)
# ---------------------------------------------------------------------------

class KeywordListView(generics.ListAPIView):
    queryset = Keyword.objects.order_by("name")
    serializer_class = KeywordSerializer


# ---------------------------------------------------------------------------
# POST /scan/
# ---------------------------------------------------------------------------

class ScanView(APIView):
    """
    Trigger a scan.

    Optional JSON body:
        { "source": "mock" }   (default: "mock")
    """

    def post(self, request):
        source = request.data.get("source", "mock")
        try:
            summary = run_scan(source=source)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(summary, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# GET /flags/
# ---------------------------------------------------------------------------

class FlagListView(generics.ListAPIView):
    """
    List flags.

    Query parameters:
        status  — filter by status (pending / relevant / irrelevant)
        keyword — filter by keyword id
        min_score — filter by minimum score
    """

    serializer_class = FlagSerializer

    def get_queryset(self):
        qs = Flag.objects.select_related("keyword", "content_item").order_by("-score", "-created_at")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        keyword_id = self.request.query_params.get("keyword")
        if keyword_id:
            qs = qs.filter(keyword_id=keyword_id)

        min_score = self.request.query_params.get("min_score")
        if min_score:
            try:
                qs = qs.filter(score__gte=int(min_score))
            except ValueError:
                pass

        return qs


# ---------------------------------------------------------------------------
# PATCH /flags/{id}/
# ---------------------------------------------------------------------------

class FlagDetailView(generics.RetrieveUpdateAPIView):
    """
    GET  /flags/{id}/   — retrieve a single flag
    PATCH /flags/{id}/  — update status (pending / relevant / irrelevant)
    """

    queryset = Flag.objects.select_related("keyword", "content_item")

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return FlagStatusUpdateSerializer
        return FlagSerializer

    def update(self, request, *args, **kwargs):
        # Enforce PATCH-only (no full PUT replacement).
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)
