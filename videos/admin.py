"""
Admin configuration for the Video model.

This module customizes how videos are displayed and filtered
in the Django admin interface.
"""

from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """
    Django admin configuration for the Video model.

    Features:
        - Displays key fields for quick overview.
        - Enables filtering by category, processed status, and creation date.
        - Adds a search bar for title, description, and category.
    """
    list_display = ("id", "title", "category", "processed", "created_at")
    list_filter = ("processed", "category", "created_at")
    search_fields = ("title", "description", "category")
