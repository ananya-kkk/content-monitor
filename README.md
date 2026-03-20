# Content Monitoring & Flagging System

A Django + DRF backend that ingests content, matches it against user-defined keywords, and supports a human review workflow with suppression logic.

---

## Quick start

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd content_monitor

# 2. Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4. (Optional) Create a superuser for the admin panel
python manage.py createsuperuser

# 5. Start the development server
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/`.  
The Django admin is available at `http://127.0.0.1:8000/admin/`.

---

## Running tests

```bash
python manage.py test tests --verbosity=2
```

19 tests covering the matcher, suppression rule, and every API endpoint.

---

## Content source

**Mock dataset** is used (documented choice).  
`monitoring/services/mock_source.py` contains 10 hardcoded articles covering topics like Django, Python, automation, and data pipelines — enough to exercise all scoring tiers and the suppression rule without requiring external API keys.

To add a real source (e.g. NewsAPI), implement a new function in `mock_source.py` and wire it into `scanner.py`'s `_fetch_content()`.

---

## API reference

### `POST /keywords/`
Create a keyword to monitor.

```bash
curl -s -X POST http://127.0.0.1:8000/keywords/ \
  -H "Content-Type: application/json" \
  -d '{"name": "django"}'
```

Response `201`:
```json
{"id": 1, "name": "django", "created_at": "2026-03-20T10:00:00Z"}
```

---

### `GET /keywords/list/`
List all configured keywords.

```bash
curl -s http://127.0.0.1:8000/keywords/list/
```

---

### `POST /scan/`
Trigger a scan against the content source. Creates, updates, or suppresses flags for every (keyword × content item) pair.

```bash
curl -s -X POST http://127.0.0.1:8000/scan/ \
  -H "Content-Type: application/json" \
  -d '{"source": "mock"}'
```

Response `200`:
```json
{
  "source": "mock",
  "content_items_processed": 10,
  "flags_created": 6,
  "flags_updated": 0,
  "flags_suppressed": 0
}
```

---

### `GET /flags/`
List generated flags.

```bash
# All flags
curl -s http://127.0.0.1:8000/flags/

# Filter by status
curl -s "http://127.0.0.1:8000/flags/?status=pending"

# Filter by keyword id
curl -s "http://127.0.0.1:8000/flags/?keyword=1"

# Filter by minimum score
curl -s "http://127.0.0.1:8000/flags/?min_score=70"
```

Response:
```json
[
  {
    "id": 1,
    "keyword": 1,
    "keyword_name": "django",
    "content_item": 1,
    "content_item_title": "Learn Django Fast",
    "content_item_source": "mock",
    "score": 100,
    "status": "pending",
    "content_snapshot_ts": "2026-03-20T10:00:00Z",
    "created_at": "2026-03-20T10:00:05Z",
    "reviewed_at": null
  }
]
```

---

### `PATCH /flags/{id}/`
Update the review status of a flag.

```bash
# Mark as relevant
curl -s -X PATCH http://127.0.0.1:8000/flags/1/ \
  -H "Content-Type: application/json" \
  -d '{"status": "relevant"}'

# Mark as irrelevant (will be suppressed on future scans unless content changes)
curl -s -X PATCH http://127.0.0.1:8000/flags/1/ \
  -H "Content-Type: application/json" \
  -d '{"status": "irrelevant"}'
```

---

### `GET /flags/{id}/`
Retrieve a single flag by id.

```bash
curl -s http://127.0.0.1:8000/flags/1/
```

---

## Full walkthrough (copy-paste)

```bash
# Add keywords
curl -s -X POST http://127.0.0.1:8000/keywords/ -H "Content-Type: application/json" -d '{"name": "python"}'
curl -s -X POST http://127.0.0.1:8000/keywords/ -H "Content-Type: application/json" -d '{"name": "django"}'
curl -s -X POST http://127.0.0.1:8000/keywords/ -H "Content-Type: application/json" -d '{"name": "automation"}'
curl -s -X POST http://127.0.0.1:8000/keywords/ -H "Content-Type: application/json" -d '{"name": "data pipeline"}'

# Run a scan
curl -s -X POST http://127.0.0.1:8000/scan/ -H "Content-Type: application/json" -d '{"source": "mock"}'

# Review flags
curl -s http://127.0.0.1:8000/flags/

# Mark flag 1 as irrelevant
curl -s -X PATCH http://127.0.0.1:8000/flags/1/ -H "Content-Type: application/json" -d '{"status": "irrelevant"}'

# Scan again — flag 1 remains suppressed (content unchanged)
curl -s -X POST http://127.0.0.1:8000/scan/ -H "Content-Type: application/json" -d '{"source": "mock"}'
```

---

## Scoring rules

| Match type                       | Score |
|----------------------------------|-------|
| Exact keyword match in title     | 100   |
| Partial keyword match in title   | 70    |
| Keyword appears only in body     | 40    |
| No match                         | 0 (no flag created) |

"Exact" means the keyword appears as a whole word (word-boundary regex, case-insensitive).  
"Partial" means the keyword string is present anywhere in the title but is part of a larger word.

---

## Suppression logic

This is the core business rule (spec §6).

Each `Flag` stores a `content_snapshot_ts` — a copy of `ContentItem.last_updated` at the time the flag was last evaluated.

On every scan:

1. If a flag exists with `status = irrelevant` **and** `content_item.last_updated == flag.content_snapshot_ts` → the item has not changed → **skip it** (increment `flags_suppressed`).
2. If `content_item.last_updated > flag.content_snapshot_ts` → the content changed after it was dismissed → **reset to pending** with the new score and updated snapshot.

This means a reviewer's "irrelevant" decision is respected until the underlying article is actually updated.

---

## Project structure

```
content_monitor/
├── content_monitor/          # Django project config
│   ├── settings.py
│   └── urls.py
├── monitoring/               # Core application
│   ├── models.py             # Keyword, ContentItem, Flag
│   ├── serializers.py        # DRF serializers
│   ├── views.py              # Thin views, no business logic
│   ├── urls.py
│   ├── admin.py
│   └── services/
│       ├── matcher.py        # Pure scoring logic (no Django imports)
│       ├── mock_source.py    # Mock dataset
│       └── scanner.py        # Scan orchestration + suppression
├── tests/
│   └── test_all.py           # 19 tests
├── manage.py
└── requirements.txt
```

---

## Assumptions and trade-offs

| Decision | Rationale |
|----------|-----------|
| Mock dataset over live API | Keeps the project self-contained and runnable without API keys. A real source can be added by implementing `_fetch_content()` in `scanner.py`. |
| `unique_together (title, source)` on ContentItem | Simplest stable identity for deduplication. A real system might use a URL or external id. |
| `content_snapshot_ts` on Flag | Stores the `last_updated` value at evaluation time, so suppression comparison is a simple timestamp equality check rather than re-fetching content. |
| SQLite | Adequate for local development; swap to Postgres by changing `DATABASES` in settings. |
| No authentication | Out of scope for this assignment. In production, add DRF token or session auth. |
| No Celery | Scan is triggered synchronously via `POST /scan/`. Celery would be the natural next step for large-scale or scheduled scanning. |
| Score only stored on flag | Computed fresh on each scan; if the score changes (body changed but title didn't), the flag is updated. |
