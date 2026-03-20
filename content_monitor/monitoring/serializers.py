from rest_framework import serializers

from monitoring.models import ContentItem, Flag, Keyword


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = ["id", "name", "created_at"]
        read_only_fields = ["id", "created_at"]


class ContentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentItem
        fields = ["id", "title", "source", "body", "last_updated", "imported_at"]
        read_only_fields = fields


class FlagSerializer(serializers.ModelSerializer):
    keyword_name = serializers.CharField(source="keyword.name", read_only=True)
    content_item_title = serializers.CharField(source="content_item.title", read_only=True)
    content_item_source = serializers.CharField(source="content_item.source", read_only=True)

    class Meta:
        model = Flag
        fields = [
            "id",
            "keyword",
            "keyword_name",
            "content_item",
            "content_item_title",
            "content_item_source",
            "score",
            "status",
            "content_snapshot_ts",
            "created_at",
            "reviewed_at",
        ]
        read_only_fields = [
            "id",
            "keyword",
            "keyword_name",
            "content_item",
            "content_item_title",
            "content_item_source",
            "score",
            "content_snapshot_ts",
            "created_at",
        ]


class FlagStatusUpdateSerializer(serializers.ModelSerializer):
    """Used only for PATCH /flags/{id}/ to update review status."""

    class Meta:
        model = Flag
        fields = ["status"]

    def validate_status(self, value):
        allowed = {Flag.Status.PENDING, Flag.Status.RELEVANT, Flag.Status.IRRELEVANT}
        if value not in allowed:
            raise serializers.ValidationError(
                f"Invalid status. Choose from: {', '.join(allowed)}"
            )
        return value

    def update(self, instance, validated_data):
        from django.utils import timezone

        instance.status = validated_data["status"]
        instance.reviewed_at = timezone.now()
        instance.save(update_fields=["status", "reviewed_at"])
        return instance
