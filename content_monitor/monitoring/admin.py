from django.contrib import admin

from monitoring.models import ContentItem, Flag, Keyword


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "created_at"]
    search_fields = ["name"]


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "source", "last_updated", "imported_at"]
    search_fields = ["title", "source"]
    list_filter = ["source"]


@admin.register(Flag)
class FlagAdmin(admin.ModelAdmin):
    list_display = ["id", "keyword", "content_item", "score", "status", "created_at", "reviewed_at"]
    list_filter = ["status", "keyword"]
    search_fields = ["keyword__name", "content_item__title"]
    readonly_fields = ["created_at", "reviewed_at", "content_snapshot_ts"]
