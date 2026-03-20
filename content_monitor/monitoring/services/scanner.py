"""
Scanner service
===============
Responsibilities:
  1. Fetch content records from the chosen source (mock by default).
  2. Upsert ContentItem rows (create or update; detect last_updated changes).
  3. For every (keyword, content_item) pair, compute a score.
  4. Apply suppression logic before creating/updating flags.
  5. Return a summary dict for the API response.

Suppression rule (spec §6)
--------------------------
If a Flag exists with status=irrelevant AND the content item has NOT changed
since it was last evaluated (content_snapshot_ts == content_item.last_updated),
skip that pair — do not surface it again.

If the content item HAS changed (new last_updated > content_snapshot_ts), the
flag is reset to pending with the updated score and the new snapshot timestamp,
so it can be reviewed again.

All database work is wrapped in a single atomic transaction so a partial failure
leaves the database clean.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from monitoring.models import ContentItem, Flag, Keyword
from monitoring.services.matcher import compute_score
from monitoring.services.mock_source import MOCK_ARTICLES


def _parse_dt(value: str | datetime) -> datetime:
    """Parse an ISO-8601 string into an aware datetime, or pass through."""
    if isinstance(value, datetime):
        return value if value.tzinfo else timezone.make_aware(value)
    dt = parse_datetime(value)
    if dt is None:
        raise ValueError(f"Cannot parse datetime: {value!r}")
    return dt if dt.tzinfo else timezone.make_aware(dt)


def _fetch_content(source: str) -> list[dict[str, Any]]:
    """Return raw content records for the given source identifier."""
    if source == "mock":
        return MOCK_ARTICLES
    raise ValueError(f"Unknown source {source!r}. Supported: 'mock'.")


@transaction.atomic
def run_scan(source: str = "mock") -> dict[str, Any]:
    """
    Run a full scan cycle and return a summary.

    Returns
    -------
    {
        "source": str,
        "content_items_processed": int,
        "flags_created": int,
        "flags_updated": int,
        "flags_suppressed": int,
    }
    """
    raw_records = _fetch_content(source)
    keywords = list(Keyword.objects.all())

    if not keywords:
        return {
            "source": source,
            "content_items_processed": len(raw_records),
            "flags_created": 0,
            "flags_updated": 0,
            "flags_suppressed": 0,
            "detail": "No keywords configured. Add keywords first.",
        }

    created = updated = suppressed = 0

    for record in raw_records:
        last_updated = _parse_dt(record["last_updated"])

        # --- Upsert ContentItem ---
        item, item_created = ContentItem.objects.get_or_create(
            title=record["title"],
            source=record["source"],
            defaults={
                "body": record["body"],
                "last_updated": last_updated,
            },
        )
        if not item_created and item.last_updated != last_updated:
            # Content changed — update the stored record.
            item.body = record["body"]
            item.last_updated = last_updated
            item.save(update_fields=["body", "last_updated"])

        # --- Score + flag lifecycle for each keyword ---
        for keyword in keywords:
            score = compute_score(keyword.name, item.title, item.body)
            if score == 0:
                continue  # No match at all — nothing to flag.

            try:
                flag = Flag.objects.get(keyword=keyword, content_item=item)
            except Flag.DoesNotExist:
                flag = None

            if flag is None:
                # New flag.
                Flag.objects.create(
                    keyword=keyword,
                    content_item=item,
                    score=score,
                    status=Flag.Status.PENDING,
                    content_snapshot_ts=last_updated,
                )
                created += 1
            elif flag.status == Flag.Status.IRRELEVANT:
                if item.last_updated > flag.content_snapshot_ts:
                    # Content changed after it was dismissed → resurface.
                    flag.score = score
                    flag.status = Flag.Status.PENDING
                    flag.content_snapshot_ts = last_updated
                    flag.reviewed_at = None
                    flag.save(update_fields=["score", "status", "content_snapshot_ts", "reviewed_at"])
                    updated += 1
                else:
                    # Content unchanged → stay suppressed.
                    suppressed += 1
            else:
                # Flag exists but is pending or relevant — refresh score.
                if flag.score != score:
                    flag.score = score
                    flag.content_snapshot_ts = last_updated
                    flag.save(update_fields=["score", "content_snapshot_ts"])
                    updated += 1

    return {
        "source": source,
        "content_items_processed": len(raw_records),
        "flags_created": created,
        "flags_updated": updated,
        "flags_suppressed": suppressed,
    }
