"""
Scoring rules (deterministic, easy to verify):

  - Exact keyword match in title  → 100
  - Partial keyword match in title → 70
  - Keyword appears only in body  →  40
  - No match                      →   0

"Exact match in title" means the keyword appears as a whole word boundary
(case-insensitive).  "Partial match in title" means the keyword string is
present somewhere in the title but is part of a larger word (e.g. keyword
"auto" inside "automation").

All comparisons are case-insensitive.
"""

import re


def _exact_word(keyword: str, text: str) -> bool:
    """Return True if keyword appears as a whole word in text."""
    pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"
    return bool(re.search(pattern, text, re.IGNORECASE))


def _partial(keyword: str, text: str) -> bool:
    """Return True if keyword string appears anywhere in text (case-insensitive)."""
    return keyword.lower() in text.lower()


def compute_score(keyword_name: str, title: str, body: str) -> int:
    """Return a score in {0, 40, 70, 100} for a (keyword, content) pair."""
    if _exact_word(keyword_name, title):
        return 100
    if _partial(keyword_name, title):
        return 70
    if _partial(keyword_name, body):
        return 40
    return 0
