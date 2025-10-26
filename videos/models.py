"""
Model definition for uploaded and processed video content.

Each Video instance represents an uploaded media file that can be
transcoded into HLS format and associated with a generated thumbnail.
"""

from django.db import models


class Video(models.Model):
    """
    Represents a single uploaded video and its processing state.
    Includes metadata, file paths, and transcoding-related fields.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)

    # Original uploaded file (required for transcoding)
    video_file = models.FileField(upload_to="videos/original/", blank=True, null=True)

    # Automatically generated thumbnail image
    thumbnail = models.ImageField(upload_to="thumbnail/", blank=True, null=True)

    # Base directory for HLS output (e.g., "hls/42")
    hls_dir = models.CharField(max_length=255, blank=True)

    # Indicates whether transcoding has been successfully completed
    processed = models.BooleanField(default=False)

    def __str__(self):
        """Return the video title for admin and string representation."""
        return self.title
