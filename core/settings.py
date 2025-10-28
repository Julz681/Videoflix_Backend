"""
Core Django settings for the Videoflix project.

This configuration is environment-driven (via .env) and tailored for
local development with Docker, PostgreSQL, Redis, Mailhog, and
JWT-based auth in HttpOnly cookies.

Key things this file ensures:
- CORS is enabled so the frontend on :5500 can call the API on :8000
- Cookies (JWT) can be sent cross-origin in development
- Activation / password reset flows redirect back into the static frontend
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -------------------------------------------------
# Base paths and security
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-@#x5h3zj!g+8g1v@2^b6^9$8&f1r7g$@t3v!p4#=g0r5qzj4m3"
)
DEBUG = True

# -------------------------------------------------
# Hosts and trusted origins
# -------------------------------------------------
ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1"
).split(",")

# Browser security model: frontend is served e.g. from 127.0.0.1:5500,
# it will POST/GET against 127.0.0.1:8000. We must trust that origin
# for things like CSRF (if we ever re-enable CSRF on some views).
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:4200,http://127.0.0.1:4200,http://localhost:5500,http://127.0.0.1:5500"
).split(",")

# -------------------------------------------------
# Installed applications
# -------------------------------------------------
INSTALLED_APPS = [
    # Django built-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party packages
    "corsheaders",  # must be installed for cross-origin frontend->backend requests
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt.token_blacklist",
    "django_rq",

    # Local apps
    "accounts",
    "videos",
]

# -------------------------------------------------
# Middleware configuration
# -------------------------------------------------
# IMPORTANT ORDER:
# - corsheaders.middleware.CorsMiddleware MUST be high in the list
#   and specifically before CommonMiddleware.
# - We leave CSRF disabled for API via custom middleware DisableCSRFForAPI
#   (your project already chose this path because auth is cookie-JWT).
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # Handle CORS as early as possible
    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",

    # CSRF is intentionally not using Django's default CsrfViewMiddleware.
    # Instead you ship a custom middleware that skips CSRF checks for /api/*.
    # Keep this to avoid breaking your cookie-based JWT auth flow.
    # "django.middleware.csrf.CsrfViewMiddleware",
    "core.middleware.DisableCSRFForAPI",

    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

# -------------------------------------------------
# Template configuration
# -------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# -------------------------------------------------
# Database (PostgreSQL via Docker)
# -------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "videoflix_db"),
        "USER": os.environ.get("DB_USER", "videoflix_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "supersecretpassword"),
        "HOST": os.environ.get("DB_HOST", "db"),
        "PORT": os.environ.get("DB_PORT", 5432),
    }
}

# -------------------------------------------------
# Redis cache and RQ (task queue) configuration
# -------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_LOCATION", "redis://redis:6379/1"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "videoflix",
    }
}

RQ_QUEUES = {
    "default": {
        "HOST": os.environ.get("REDIS_HOST", "redis"),
        "PORT": int(os.environ.get("REDIS_PORT", 6379)),
        "DB": int(os.environ.get("REDIS_DB", 0)),
        "DEFAULT_TIMEOUT": 900,
        "REDIS_CLIENT_KWARGS": {},
    },
}

# -------------------------------------------------
# Authentication and password validation
# -------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -------------------------------------------------
# Static and media files
# -------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------
# Django REST Framework configuration (JWT via cookies)
# -------------------------------------------------
REST_FRAMEWORK = {
    # We authenticate using the HttpOnly JWT cookies you set in login_view / refresh_view.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.CookieJWTAuthentication",
    ],
    # In your current code you explicitly control permissions per-view.
    # We'll keep the global default permissive so tests keep passing.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

# -------------------------------------------------
# Cookie / session security for development
# -------------------------------------------------
# We're in dev on http://, not https://, so these flags are False.
# In production you'd put True and also use 'SameSite=None' for cross-site cookies.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# SameSite defaults (Django default is 'Lax'); that works for most dev flows,
# and matches what CookieJWTAuthentication expects.
SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SAMESITE = os.environ.get("CSRF_COOKIE_SAMESITE", "Lax")

# -------------------------------------------------
# Email configuration (Mailhog in Docker)
# -------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "mailhog")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 1025))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "False") == "True"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False") == "True"
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "no-reply@videoflix.local"
)

# -------------------------------------------------
# Frontend and backend URLs (used in utils.py for emails / redirects)
# -------------------------------------------------
# The static frontend (your HTML files) is served locally by Live Server on :5500.
FRONTEND_BASE_URL = os.environ.get(
    "FRONTEND_BASE_URL",
    "http://127.0.0.1:5500"
)

# After successful account activation we tell the frontend to show login with ?activated=1
FRONTEND_LOGIN_SUCCESS_URL = os.environ.get(
    "FRONTEND_LOGIN_SUCCESS_URL",
    "http://127.0.0.1:5500/pages/auth/login.html?activated=1"
)

# On activation error, we want to land on the *existing* frontend page "activate.html"
# and let its JS/UI display "Activation failed".
FRONTEND_ACTIVATE_ERROR_URL = os.environ.get(
    "FRONTEND_ACTIVATE_ERROR_URL",
    "http://127.0.0.1:5500/pages/auth/activate.html?error=1"
)

# The backend base URL (used when building activation/reset links that first hit backend redirect views)
BACKEND_BASE_URL = os.environ.get(
    "BACKEND_BASE_URL",
    "http://127.0.0.1:8000"
)

# -------------------------------------------------
# CORS configuration
# -------------------------------------------------
# Your frontend runs on http://127.0.0.1:5500 (or localhost:5500).
# Your backend runs on http://127.0.0.1:8000.
# Different origin -> browser blocks fetch unless CORS is allowed.
#
# We explicitly allow those dev origins and allow credentials,
# because we rely on HttpOnly cookies for auth.
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

# -------------------------------------------------
# Custom user model
# -------------------------------------------------
AUTH_USER_MODEL = "accounts.CustomUser"
