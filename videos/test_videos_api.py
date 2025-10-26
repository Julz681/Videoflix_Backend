"""
Test suite for the 'videos' app.

Covers:
- Video list access control
- Authenticated video listing
- Secure HLS manifest / segment serving
- Path traversal protection
- Video upload behavior (including queuing of transcoding tasks)

All tests run against the test database (pytest.mark.django_db) and
use temporary MEDIA_ROOT overrides where file I/O is involved.
"""

import os
from pathlib import Path
import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from django.conf import settings
from django.http import Http404

from rest_framework.test import APIRequestFactory, force_authenticate

from django.contrib.auth import get_user_model

from videos.models import Video
from videos.views import (
    video_list_view,
    hls_manifest_view,
    hls_segment_view,
    safe_hls_path,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


def create_active_user(email="a@b.com", password="pw"):
    """
    Create and return an active user (CustomUser).
    """
    return User.objects.create_user(
        email=email,
        password=password,
        is_active=True,
    )


def login_client(client, email="a@b.com", password="pw"):
    """
    Log in using the real /api/login/ view so the test client receives
    valid JWT cookies (access_token, refresh_token).
    """
    r = client.post(
        reverse("login"),
        {"email": email, "password": password},
        content_type="application/json",
    )
    assert r.status_code == 200
    client.cookies["access_token"] = r.cookies["access_token"].value
    client.cookies["refresh_token"] = r.cookies["refresh_token"].value
    return client


def auth_client_fixture(client):
    """
    Convenience helper:
    - create active user
    - log that user in
    - return authenticated client with cookies set
    """
    create_active_user(email="a@b.com", password="pw")
    return login_client(client, email="a@b.com", password="pw")


def test_video_list_requires_auth(client):
    """
    /api/video/ should reject unauthenticated requests.
    View is protected via IsAuthenticated, so response should
    be HTTP 401 or 403 depending on configuration.
    """
    r = client.get(reverse("video_list"))
    assert r.status_code in (401, 403)


def test_video_list_returns_data_for_authenticated_user(client):
    """
    /api/video/ should return 200 and a serialized list of videos
    when accessed with valid auth cookies.
    """
    client = auth_client_fixture(client)

    Video.objects.create(
        title="My Movie",
        description="Test Desc",
        category="Drama",
        hls_dir="hls/1",
        processed=True,
    )

    r = client.get(reverse("video_list"))
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["title"] == "My Movie"
    assert body[0]["category"] == "Drama"


@override_settings(MEDIA_ROOT="/tmp/test_media_root_videoflix")
def test_hls_manifest_and_segment_ok(tmp_path, client, monkeypatch, settings):
    """
    Simulate existing HLS output on disk.

    Checks:
    - Resolution alias '480p' should resolve to '360p' internally.
    - Manifest (/index.m3u8) is served with correct content type.
    - TS segment is streamed with correct MIME type.
    """
    # Point MEDIA_ROOT to a temp dir
    settings.MEDIA_ROOT = tmp_path

    # Authenticated client
    client = auth_client_fixture(client)

    # Create fake HLS structure: MEDIA_ROOT/hls/1/360p/{index.m3u8,000.ts}
    base_dir = tmp_path / "hls" / "1" / "360p"
    base_dir.mkdir(parents=True)
    (base_dir / "index.m3u8").write_text("#EXTM3U")
    (base_dir / "000.ts").write_bytes(b"abc")

    # DB entry that refers to that HLS dir
    Video.objects.create(
        id=1,
        title="Streamable",
        description="",
        category="Action",
        hls_dir="hls/1",
        processed=True,
    )

    # Request .m3u8 manifest
    r_manifest = client.get(
        reverse("hls_manifest", kwargs={"movie_id": 1, "resolution": "480p"})
    )
    assert r_manifest.status_code == 200
    assert r_manifest["Content-Type"] == "application/vnd.apple.mpegurl"

    # Request .ts segment
    r_segment = client.get(
        reverse(
            "hls_segment",
            kwargs={
                "movie_id": 1,
                "resolution": "480p",
                "segment": "000.ts",
            },
        )
    )
    assert r_segment.status_code == 200
    assert r_segment["Content-Type"] == "video/MP2T"
    assert b"abc" in b"".join(r_segment.streaming_content)


@override_settings(MEDIA_ROOT="/tmp/test_media_root_videoflix")
def test_hls_manifest_404_for_missing_file(tmp_path, client, settings):
    """
    If index.m3u8 does not exist for the requested video/resolution,
    the manifest endpoint should return 404.
    """
    settings.MEDIA_ROOT = tmp_path
    client = auth_client_fixture(client)

    # No index.m3u8 is created here on purpose
    Video.objects.create(
        id=2,
        title="Broken",
        description="",
        category="Drama",
        hls_dir="hls/2",
        processed=True,
    )

    r_manifest = client.get(
        reverse("hls_manifest", kwargs={"movie_id": 2, "resolution": "480p"})
    )
    assert r_manifest.status_code == 404


@override_settings(MEDIA_ROOT="/tmp/test_media_root_videoflix")
def test_hls_segment_404_for_directory_traversal_attempt(tmp_path, client, settings):
    """
    Attempt to request a file outside the allowed HLS directory.

    Note:
    - The URLconf for <segment> does not allow '/' in the segment.
      So we simulate traversal using '..' chunks but no slashes.
    - Expected behavior: the view should return 404
      (either because the file is refused or not found).
    """
    settings.MEDIA_ROOT = tmp_path
    client = auth_client_fixture(client)

    # Create a DB entry to make sure the view actually resolves the video
    Video.objects.create(
        id=3,
        title="Secure",
        description="",
        category="SciFi",
        hls_dir="hls/3",
        processed=True,
    )

    # "Malicious" filename without '/' so reverse() still works
    bad_segment = "..__..__etc_passwd"

    r = client.get(
        reverse(
            "hls_segment",
            kwargs={
                "movie_id": 3,
                "resolution": "480p",
                "segment": bad_segment,
            },
        )
    )

    assert r.status_code == 404


def test_safe_hls_path_refuses_escape(tmp_path, settings):
    """
    Unit test for safe_hls_path().

    - Valid request should produce an in-bounds absolute path.
    - Invalid (escape) request should raise Http404.
    """
    settings.MEDIA_ROOT = tmp_path

    # Set up a valid base directory to mirror expected layout
    base_dir = tmp_path / "hls" / "10" / "360p"
    base_dir.mkdir(parents=True)

    # Safe path should include hls/10/360p/index.m3u8
    p_ok = safe_hls_path(10, "480p", "index.m3u8")
    assert "hls/10/360p/index.m3u8" in p_ok.replace("\\", "/")

    # Unsafe path should raise Http404
    with pytest.raises(Http404):
        safe_hls_path(10, "480p", "../../../secret.txt")


@override_settings(MEDIA_ROOT="/tmp/test_media_root_videoflix")
def test_video_upload_creates_video_and_enqueues(monkeypatch, tmp_path, client, settings):
    """
    /api/video/upload/ should:
    - accept multipart/form-data
    - return 201
    - create a Video instance
    - enqueue the transcoding task (via django_rq.enqueue)

    We monkeypatch django_rq.enqueue to avoid actually invoking ffmpeg.
    """
    settings.MEDIA_ROOT = tmp_path

    # Authenticate client
    client = auth_client_fixture(client)

    # Monkeypatch the RQ enqueue call to assert scheduling behavior
    def fake_enqueue(func_path, pk):
        # Ensure the correct background task would have been queued
        assert func_path == "videos.tasks.transcode_video"
        assert isinstance(pk, int)

    monkeypatch.setattr("videos.signals.django_rq.enqueue", fake_enqueue)

    # Build a dummy uploaded file to simulate video upload
    dummy_video = SimpleUploadedFile(
        "testvideo.mp4",
        b"fake-video-content",
        content_type="video/mp4",
    )

    r = client.post(
        reverse("video_upload"),
        {
            "title": "Upload Title",
            "description": "Some desc",
            "category": "Drama",
            "video_file": dummy_video,
        },
        format="multipart",
    )

    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["processed"] is False  # newly uploaded videos are not yet processed

    assert Video.objects.count() == 1
    v = Video.objects.first()
    assert v.title == "Upload Title"

    # The uploaded file should now exist on disk in MEDIA_ROOT
    assert Path(v.video_file.path).exists()
