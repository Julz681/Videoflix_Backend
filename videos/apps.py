"""
Django application configuration for the 'videos' app.

This configuration ensures that video-related signals are registered
when the application starts — for example, to trigger transcoding
after a file upload.
"""

from django.apps import AppConfig


class VideosConfig(AppConfig):
    """
    Configuration class for the 'videos' Django application.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "videos"

    def ready(self):
        """
        Register signals when the app is ready.
        This ensures video processing tasks (e.g., transcoding)
        are triggered automatically after uploads.
        """
        from . import signals  # noqa: F401
