"""
Serializers for the 'videos' app.

Provides lightweight representations for listing and uploading videos.
Includes automatic thumbnail URL resolution and validation for uploads.
"""

from rest_framework import serializers
from .models import Video


class VideoListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing videos via /api/video/.
    Includes a computed field for the thumbnail URL that safely
    resolves to an absolute URI when a request context is present.
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
        Return an absolute thumbnail URL if available; otherwise an empty string.

        Handles cases where no request context or thumbnail file is present.
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
    Serializer for uploading new videos (multipart/form-data).
    The post-save signal triggers automatic transcoding.
    """

    class Meta:
        model = Video
        fields = ("title", "description", "category", "video_file")
        extra_kwargs = {
            "title": {"required": True},
            "video_file": {"required": True},
        }
