from django.db import models
from django.utils import timezone


class Keyword(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class ContentItem(models.Model):
    title = models.CharField(max_length=500)
    source = models.CharField(max_length=100)
    body = models.TextField()
    last_updated = models.DateTimeField()
    imported_at = models.DateTimeField(default=timezone.now)

    class Meta:
        # A title+source pair uniquely identifies a content item for deduplication.
        unique_together = ("title", "source")

    def __str__(self):
        return f"[{self.source}] {self.title}"


class Flag(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RELEVANT = "relevant", "Relevant"
        IRRELEVANT = "irrelevant", "Irrelevant"

    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE, related_name="flags")
    content_item = models.ForeignKey(
        ContentItem, on_delete=models.CASCADE, related_name="flags"
    )
    score = models.IntegerField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    # Snapshot of last_updated at the time we last evaluated this flag.
    # Used to detect whether the content item changed since it was marked irrelevant.
    content_snapshot_ts = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("keyword", "content_item")

    def __str__(self):
        return f"Flag({self.keyword.name!r} × {self.content_item.title!r}) → {self.status}"
