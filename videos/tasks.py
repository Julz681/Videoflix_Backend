"""
Background task utilities for transcoding uploaded videos into HLS format.

This module:
- Generates multiple resolution variants (360p, 720p, 1080p)
- Produces .m3u8 playlists and .ts segments
- Extracts a thumbnail frame
- Updates the Video model with HLS paths and processing status
"""

import os
import subprocess
from pathlib import Path
from django.conf import settings
from django.core.files import File
from django.db import transaction
from .models import Video


# -------------------------------------------------
# Helper functions (≤14 lines each)
# -------------------------------------------------

def run(cmd: list[str]) -> None:
    """
    Execute a shell command using subprocess with error checking.

    Args:
        cmd (list[str]): Command and arguments to execute.
    """
    subprocess.run(cmd, check=True)


def m3u8_target_dir(base: Path, res: str) -> Path:
    """
    Create and return the output directory for a given resolution.

    Args:
        base (Path): Base output directory for the video.
        res (str): Resolution name (e.g., '720p').

    Returns:
        Path: Created or existing resolution subdirectory.
    """
    p = base / res
    p.mkdir(parents=True, exist_ok=True)
    return p


# -------------------------------------------------
# Main transcoding task
# -------------------------------------------------

@transaction.atomic
def transcode_video(video_id: int) -> None:
    """
    Transcode a video into multiple HLS variants (360p/720p/1080p)
    and extract a thumbnail image.

    Workflow:
        - Generates HLS outputs under MEDIA_ROOT/hls/<id>/<res>/
        - Creates index.m3u8 + TS segments per resolution
        - Extracts a thumbnail frame at 3 seconds
        - Updates the Video instance with HLS directory and thumbnail

    Args:
        video_id (int): ID of the Video model instance to process.
    """
    video = Video.objects.select_for_update().get(pk=video_id)
    if not video.video_file:
        return  # Nothing to process

    input_path = Path(video.video_file.path)
    out_base = Path(settings.MEDIA_ROOT) / "hls" / str(video.id)
    out_base.mkdir(parents=True, exist_ok=True)

    # Video resolutions and bitrates
    variants = {
        "360p":  {"height": 360,  "vb": "800k"},
        "720p":  {"height": 720,  "vb": "2500k"},
        "1080p": {"height": 1080, "vb": "4500k"},
    }

    # Generate HLS outputs for each resolution
    for res, cfg in variants.items():
        o = m3u8_target_dir(out_base, res)
        # scale=-2:height preserves aspect ratio (width multiple of 2)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", f"scale=-2:{cfg['height']}",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-c:a", "aac", "-ar", "48000", "-b:a", "128k",
            "-b:v", cfg["vb"],
            "-hls_time", "4",
            "-hls_playlist_type", "vod",
            "-hls_segment_filename", str(o / "%03d.ts"),
            str(o / "index.m3u8"),
        ]
        run(cmd)

    # Generate thumbnail at 3 seconds
    thumb_path = out_base / "thumb.jpg"
    run(["ffmpeg", "-y", "-ss", "3", "-i", str(input_path), "-frames:v", "1", str(thumb_path)])

    # Update video model with generated data
    video.hls_dir = f"hls/{video.id}"
    if thumb_path.exists():
        with open(thumb_path, "rb") as fh:
            video.thumbnail.save(f"thumb_{video.id}.jpg", File(fh), save=False)
    video.processed = True
    video.save(update_fields=["hls_dir", "thumbnail", "processed"])
