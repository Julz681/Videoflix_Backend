"""
URL configuration for the videos API.

Routes:
- GET /api/video/                        -> list videos
- POST /api/video/upload/                -> upload new video
- GET /api/video/<id>/<res>/index.m3u8   -> HLS manifest
- GET /api/video/<id>/<res>/<segment>/   -> HLS segment
"""

from django.urls import path
from videos.api.views import (
    video_list_view,
    video_upload_view,
    hls_manifest_view,
    hls_segment_view,
)

urlpatterns = [
    path("video/", video_list_view, name="video_list"),
    path("video/upload/", video_upload_view, name="video_upload"),
    path(
        "video/<int:movie_id>/<str:resolution>/index.m3u8",
        hls_manifest_view,
        name="hls_manifest",
    ),
    path(
        "video/<int:movie_id>/<str:resolution>/<str:segment>/",
        hls_segment_view,
        name="hls_segment",
    ),
]
