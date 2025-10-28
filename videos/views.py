"""
Views for the 'videos' app.

Provides API endpoints for:
- Listing available videos
- Uploading new videos
- Securely serving HLS manifests (.m3u8) and segments (.ts)
"""

import os
from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from .models import Video
from .serializers import VideoListSerializer, VideoUploadSerializer


# -------------------------------------------------
# Resolution mapping
# -------------------------------------------------
# Maps frontend resolutions to available directories.
# Example: frontend requests "480p" → maps to "360p".
# Other resolutions are passed through as-is.
RESOLUTION_MAP = {
    "480p": "360p",
    "360p": "360p",
    "720p": "720p",
    "1080p": "1080p",
}


def _normalize_resolution(requested_resolution: str) -> str:
    """
    Normalize the requested resolution to a real HLS directory name.

    Args:
        requested_resolution (str): Resolution string from the URL (e.g., "480p").

    Returns:
        str: Mapped resolution directory name (e.g., "360p").

    Raises:
        Http404: If the resolution is unknown.
    """
    norm = RESOLUTION_MAP.get(requested_resolution)
    if not norm:
        raise Http404("Unknown resolution")
    return norm


def safe_hls_path(video_id: int, resolution: str, filename: str) -> str:
    """
    Build a secure absolute file path for an HLS asset (manifest or segment).

    Security logic:
        - Maps the given resolution via RESOLUTION_MAP.
        - Constructs MEDIA_ROOT/hls/<video_id>/<mapped_resolution>/<filename>.
        - Validates that the resolved path stays within MEDIA_ROOT/hls.

    Args:
        video_id (int): ID of the video.
        resolution (str): Requested resolution (e.g., "480p").
        filename (str): File name (e.g., "index.m3u8" or "001.ts").

    Returns:
        str: Absolute, safe path to the requested file.

    Raises:
        Http404: If the path escapes the allowed directory.
    """
    real_resolution = _normalize_resolution(resolution)
    base = os.path.join(settings.MEDIA_ROOT, "hls", str(video_id), real_resolution)
    path = os.path.normpath(os.path.join(base, filename))

    # Ensure no directory traversal is possible
    if not path.startswith(os.path.normpath(base)):
        raise Http404()

    return path


# -------------------------------------------------
# Video listing endpoint
# -------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def video_list_view(request):
    """
    GET /api/video/

    Returns a list of all videos ordered by creation date (newest first).

    Response fields:
        - id
        - created_at
        - title
        - description
        - thumbnail_url
        - category
    """
    qs = Video.objects.all().order_by("-created_at")
    ser = VideoListSerializer(qs, many=True, context={"request": request})
    return Response(ser.data, status=status.HTTP_200_OK)


# -------------------------------------------------
# HLS manifest and segment endpoints
# -------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def hls_manifest_view(request, movie_id: int, resolution: str):
    """
    GET /api/video/<movie_id>/<resolution>/index.m3u8

    Example:
        /api/video/1/480p/index.m3u8

    Maps 480p → 360p internally if needed,
    reads the manifest file, and returns it with the correct content type.
    """
    path = safe_hls_path(movie_id, resolution, "index.m3u8")
    if not os.path.exists(path):
        raise Http404("Manifest not found")

    return FileResponse(
        open(path, "rb"),
        content_type="application/vnd.apple.mpegurl",
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def hls_segment_view(request, movie_id: int, resolution: str, segment: str):
    """
    GET /api/video/<movie_id>/<resolution>/<segment>/

    Example:
        /api/video/1/480p/000.ts

    Uses the same resolution mapping and security validation
    as `hls_manifest_view`.
    """
    path = safe_hls_path(movie_id, resolution, segment)
    if not os.path.exists(path):
        raise Http404("Segment not found")

    return FileResponse(
        open(path, "rb"),
        content_type="video/MP2T",
    )


# -------------------------------------------------
# Video upload endpoint
# -------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def video_upload_view(request):
    """
    POST /api/video/upload/

    Expects multipart/form-data with REQUIRED fields:
        - title          (str)
        - category       (str)
        - video_file     (file; the original video)
        - thumbnail      (image; manual upload is mandatory)

    Optional:
        - description    (str)

    Behavior:
        - Validates that video_file AND thumbnail are provided.
          If either is missing, returns 400.
        - Saves the Video instance.
        - post_save signal enqueues transcoding via RQ worker
          (videos.tasks.transcode_video), which will later generate HLS output
          under MEDIA_ROOT/hls/<id>/...
    """
    ser = VideoUploadSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    video = ser.save()

    return Response(
        {
            "id": video.id,
            "processed": video.processed,
        },
        status=status.HTTP_201_CREATED,
    )
