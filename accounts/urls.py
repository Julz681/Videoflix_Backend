"""
URL configuration for the accounts app.

Defines all authentication and user management routes such as:
- registration & activation
- login / logout / token refresh
- password reset (request link, redirect link, confirm new password)
"""

from django.urls import path
from .views import (
    register_view,
    activate_view,
    login_view,
    logout_view,
    refresh_view,
    password_reset_request_view,
    password_reset_confirm_view,
    password_reset_redirect_view,  # NEW
)

urlpatterns = [
    # -----------------------------
    # User registration and activation
    # -----------------------------
    path("register/", register_view, name="register"),
    path("activate/<uidb64>/<token>/", activate_view, name="activate"),

    # -----------------------------
    # Authentication and session management
    # -----------------------------
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("token/refresh/", refresh_view, name="token_refresh"),

    # -----------------------------
    # Password reset flow
    # -----------------------------

    # 1. User enters email -> we send reset email (always returns 200)
    path("password_reset/", password_reset_request_view, name="password_reset"),

    # 2. User clicks the link in the email.
    #    This does NOT go directly to the frontend.
    #    Instead, it hits our backend, we validate uid/token,
    #    and then we redirect the browser to the existing frontend page
    #    /pages/auth/confirm_password.html?uid=...&token=...
    path(
        "password_reset_link/<uidb64>/<token>/",
        password_reset_redirect_view,
        name="password_reset_link",
    ),

    # 3. Frontend submits the new password here (POST with new_password + confirm_password)
    path(
        "password_confirm/<uidb64>/<token>/",
        password_reset_confirm_view,
        name="password_reset_confirm",
    ),
]
