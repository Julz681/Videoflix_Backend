"""
Signal handlers for the 'videos' app.

Automatically enqueue background tasks (e.g., transcoding)
whenever a new video instance is created.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Video
import django_rq


@receiver(post_save, sender=Video)
def enqueue_transcode(sender, instance: Video, created: bool, **kwargs):
    """
    Enqueue a background transcoding job when a new video is uploaded.

    Trigger conditions:
        - The instance is newly created.
        - A video file has been uploaded.
        - The video has not been processed yet.

    The job is added to the default RQ queue as configured in settings.py.
    """
    if created and instance.video_file and not instance.processed:
        # Enqueue background transcoding task
        django_rq.enqueue("videos.tasks.transcode_video", instance.pk)
