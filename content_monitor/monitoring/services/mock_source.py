"""
Mock content dataset used as the default import source.

Each record mirrors the ContentItem fields: title, source, body, last_updated.
The last_updated values are intentionally varied so that suppression logic
can be exercised even with mock data.
"""

from django.utils import timezone

MOCK_ARTICLES = [
    {
        "title": "Learn Django Fast",
        "body": "Django is a powerful Python web framework that encourages rapid development.",
        "source": "mock",
        "last_updated": "2026-03-20T10:00:00Z",
    },
    {
        "title": "Getting started with Python",
        "body": "Python is beginner-friendly and widely used in data science and automation.",
        "source": "mock",
        "last_updated": "2026-03-20T11:00:00Z",
    },
    {
        "title": "Cooking Tips for Beginners",
        "body": "Best recipes and kitchen tricks for those just starting out.",
        "source": "mock",
        "last_updated": "2026-03-20T12:00:00Z",
    },
    {
        "title": "Building a data pipeline with Apache Airflow",
        "body": "Orchestrate your data pipeline using DAGs and Python operators.",
        "source": "mock",
        "last_updated": "2026-03-20T13:00:00Z",
    },
    {
        "title": "Automation in modern DevOps",
        "body": "Infrastructure automation reduces human error and speeds up deployments.",
        "source": "mock",
        "last_updated": "2026-03-20T14:00:00Z",
    },
    {
        "title": "Understanding REST APIs",
        "body": "REST is an architectural style used to build scalable web services.",
        "source": "mock",
        "last_updated": "2026-03-20T15:00:00Z",
    },
    {
        "title": "Django REST Framework deep-dive",
        "body": "DRF makes it trivial to expose Django models as JSON endpoints.",
        "source": "mock",
        "last_updated": "2026-03-20T16:00:00Z",
    },
    {
        "title": "10 Python tricks you didn't know",
        "body": "Improve your Python code with list comprehensions, generators, and more.",
        "source": "mock",
        "last_updated": "2026-03-20T17:00:00Z",
    },
    {
        "title": "Sports news roundup",
        "body": "Weekend fixtures and results from football, cricket, and tennis.",
        "source": "mock",
        "last_updated": "2026-03-20T18:00:00Z",
    },
    {
        "title": "Introduction to machine learning",
        "body": "Machine learning automates the process of building analytical models.",
        "source": "mock",
        "last_updated": "2026-03-20T19:00:00Z",
    },
]
