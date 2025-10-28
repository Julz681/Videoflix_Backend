from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # Accounts API (auth, activation, password reset, etc.)
    path("api/", include("accounts.api.urls")),

    # Videos API (listing, upload, streaming)
    path("api/", include("videos.api.urls")),

    # RQ dashboard for workers
    path("django-rq/", include("django_rq.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
