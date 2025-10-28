"""
URL configuration for the accounts API.

Routes:
- registration & activation
- login / logout / token refresh
- password reset (request link, confirm new password)
- redirect helper for password reset link in email
"""

from django.urls import path
from accounts.api.views import (
    register_view,
    activate_view,
    login_view,
    logout_view,
    refresh_view,
    password_reset_request_view,
    password_reset_confirm_view,
    password_reset_redirect_view,
)

urlpatterns = [
    # Registration & email activation
    path("register/", register_view, name="register"),
    path("activate/<uidb64>/<token>/", activate_view, name="activate"),

    # Auth
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("token/refresh/", refresh_view, name="token_refresh"),

    # Password reset
    path("password_reset/", password_reset_request_view, name="password_reset"),
    path(
        "password_confirm/<uidb64>/<token>/",
        password_reset_confirm_view,
        name="password_reset_confirm",
    ),

    # Link from email -> redirect to frontend confirm_password.html
    path(
        "password_reset_link/<uidb64>/<token>/",
        password_reset_redirect_view,
        name="password_reset_link",
    ),
]
