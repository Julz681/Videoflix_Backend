from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """
    Admin configuration for Video entries.

    - Ensures editors can see if a video has been processed.
    - Exposes thumbnail and video_file in the form.
    - Makes it easy to filter by category or processing state.
    """

    list_display = (
        "id",
        "title",
        "category",
        "processed",
        "created_at",
    )
    list_filter = (
        "processed",
        "category",
        "created_at",
    )
    search_fields = (
        "title",
        "description",
        "category",
    )

    # Fields visible in the edit form
    fields = (
        "title",
        "description",
        "category",
        "video_file",
        "thumbnail",
        "processed",
        "hls_dir",
        "created_at",
    )
    readonly_fields = (
        "created_at",
        "hls_dir",
        "processed",
    )
