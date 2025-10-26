"""
Test settings configuration for Django (used with pytest or local testing).

This module imports all default settings and overrides selected values for
a safe, lightweight test environment.
"""

from .settings import *  # Import all base settings


# -------------------------------------------------
# Database Configuration
# -------------------------------------------------
# Use SQLite instead of PostgreSQL for faster and isolated test runs.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.sqlite3",
    }
}


# -------------------------------------------------
# Email Backend
# -------------------------------------------------
# Use in-memory email backend so no real emails are sent during tests.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
