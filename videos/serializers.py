from rest_framework import serializers
from .models import Video


class VideoListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing videos (GET /api/video/).
    Includes a safe absolute thumbnail URL if available.
    """
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = (
            "id",
            "created_at",
            "title",
            "description",
            "thumbnail_url",
            "category",
        )

    def get_thumbnail_url(self, obj):
        """
        Return absolute thumbnail URL if available.
        Return empty string if thumbnail is missing or invalid.
        """
        try:
            if obj.thumbnail and getattr(obj.thumbnail, "url", None):
                request = self.context.get("request")
                url = obj.thumbnail.url
                return request.build_absolute_uri(url) if request else url
        except Exception:
            pass
        return ""


class VideoUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading a new video (POST /api/video/upload/).

    Enforces required fields:
    - title
    - category
    - video_file
    - thumbnail

    We intentionally make thumbnail required at the API layer even though the
    model allows blank/null. This guarantees that every created Video has a
    thumbnail, which the frontend expects.
    """

    class Meta:
        model = Video
        fields = (
            "title",
            "description",
            "category",
            "video_file",
            "thumbnail",
        )
        extra_kwargs = {
            "title": {"required": True},
            "category": {"required": True},
            "video_file": {"required": True},
            "thumbnail": {"required": True},
        }

    def validate(self, attrs):
        """
        Final safety check to ensure required upload fields are present.
        We do this explicitly so error messages are predictable.
        """
        missing = []

        if not attrs.get("title"):
            missing.append("title")
        if not attrs.get("category"):
            missing.append("category")
        if not attrs.get("video_file"):
            missing.append("video_file")
        if not attrs.get("thumbnail"):
            missing.append("thumbnail")

        if missing:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Missing required fields: "
                        + ", ".join(missing)
                    )
                }
            )

        return attrs
