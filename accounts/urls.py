"""
URL configuration for the accounts app.

Defines all authentication and user management routes such as registration,
activation, login, logout, token refresh, and password reset.
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
)

urlpatterns = [
    # User registration and activation
    path("register/", register_view, name="register"),
    path("activate/<uidb64>/<token>/", activate_view, name="activate"),

    # Authentication and session management
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("token/refresh/", refresh_view, name="token_refresh"),

    # Password reset flow
    path("password_reset/", password_reset_request_view, name="password_reset"),
    path(
        "password_confirm/<uidb64>/<token>/",
        password_reset_confirm_view,
        name="password_reset_confirm",
    ),
]
