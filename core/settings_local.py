"""
Local development settings for Videoflix.

This settings module is intended for running the project on a normal laptop
(without Docker, without PostgreSQL, without Redis).

It overrides the production-/docker-oriented defaults from core.settings:
- Uses SQLite instead of PostgreSQL
- Uses local memory cache instead of Redis
- Stores emails in memory (no real SMTP required)
"""

from .settings import *  # Import everything from the main settings
import os
from pathlib import Path

# -------------------------------------------------------------------
# Database: use local SQLite instead of PostgreSQL
# -------------------------------------------------------------------
# This allows anyone (e.g. reviewers / instructors) to run the project
# without having a running Postgres container named "db".
BASE_DIR = Path(__file__).resolve().parent.parent

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "dev.sqlite3",
    }
}

# -------------------------------------------------------------------
# Cache / RQ: replace Redis with local memory cache
# -------------------------------------------------------------------
# The real settings.py expects Redis at host "redis".
# For local runs (without docker-compose) that host doesn't exist.
# We switch to a built-in Django local memory cache so the app can start.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "videoflix-local",
    }
}

# django_rq / RQ_QUEUES refers to Redis in `core.settings`.
# For local runs without Redis, this would normally break when
# somebody actually tries to start a worker.
# It's safe to keep RQ_QUEUES defined as-is for the web app,
# because the normal `runserver` path won't spawn rqworker.
# (No override needed unless your instructors actually run rqworker.)

# -------------------------------------------------------------------
# Email backend: in-memory instead of real SMTP
# -------------------------------------------------------------------
# In Docker you use Mailhog / SMTP. Locally that's not available.
# The locmem backend just stores sent emails in django.core.mail.outbox
# instead of trying to deliver them.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# -------------------------------------------------------------------
# Security / Debug
# -------------------------------------------------------------------
DEBUG = True

# We allow localhost by default for manual testing in browser.
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# -------------------------------------------------------------------
# Note for reviewers:
# To run the project locally without Docker:
#
#   1. Set the settings module:
#      PowerShell (Windows):
#          $env:DJANGO_SETTINGS_MODULE = "core.settings_local"
#
#      macOS/Linux:
#          export DJANGO_SETTINGS_MODULE=core.settings_local
#
#   2. Run migrations and start dev server:
#          python manage.py migrate
#          python manage.py runserver
#
# This does NOT require Postgres, Redis, or Mailhog.
# -------------------------------------------------------------------
