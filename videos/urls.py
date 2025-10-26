"""
URL configuration for the 'videos' app.

Defines REST API endpoints for:
- Listing available videos
- Uploading new videos
- Serving HLS manifests and video segments
"""

from django.urls import path
from .views import (
    video_list_view,
    video_upload_view,
    hls_manifest_view,
    hls_segment_view,
)

urlpatterns = [
    # -------------------------------------------------
    # Video listing
    # -------------------------------------------------
    # GET /api/video/
    path(
        "video/",
        video_list_view,
        name="video_list",
    ),

    # -------------------------------------------------
    # Video upload
    # -------------------------------------------------
    # POST /api/video/upload/
    path(
        "video/upload/",
        video_upload_view,
        name="video_upload",
    ),

    # -------------------------------------------------
    # HLS streaming endpoints
    # -------------------------------------------------
    # Master/variant playlist (index.m3u8)
    # GET /api/video/<movie_id>/<resolution>/index.m3u8
    path(
        "video/<int:movie_id>/<str:resolution>/index.m3u8",
        hls_manifest_view,
        name="hls_manifest",
    ),

    # Individual HLS segment (.ts)
    # GET /api/video/<movie_id>/<str:resolution>/<segment>/
    path(
        "video/<int:movie_id>/<str:resolution>/<str:segment>/",
        hls_segment_view,
        name="hls_segment",
    ),
]
