"""
Main URL configuration for the Videoflix Django project.

This file routes URLs to their respective apps:
- Admin interface
- Accounts (authentication, registration, password handling)
- Videos (streaming and upload)
- Django-RQ dashboard for background tasks

In development mode, media files are also served directly from Django.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Django admin panel
    path("admin/", admin.site.urls),

    # User authentication, registration, password reset, and token endpoints
    path("api/", include("accounts.urls")),

    # Video management, streaming, and upload endpoints
    path("api/", include("videos.urls")),

    # Django-RQ job queue monitoring dashboard
    path("django-rq/", include("django_rq.urls")),
]

# Serve media files locally during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
