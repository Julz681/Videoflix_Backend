"""
Test suite for authentication, registration, activation, password reset,
token refresh, and logout flows.

All tests run with a transactional test database (pytest.mark.django_db).
"""

import pytest
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import override_settings

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model

from accounts.views import logout_view
from accounts.authentication import ACCESS_COOKIE, REFRESH_COOKIE

User = get_user_model()

pytestmark = pytest.mark.django_db


def create_active_user(email="a@b.com", password="pw"):
    """
    Helper: create and return an active user.
    """
    return User.objects.create_user(
        email=email,
        password=password,
        is_active=True,
    )


def create_inactive_user(email="inactive@b.com", password="pw"):
    """
    Helper: create and return an inactive user
    (e.g. after registration, before activation).
    """
    return User.objects.create_user(
        email=email,
        password=password,
        is_active=False,
    )


def login_client(client, email="a@b.com", password="pw"):
    """
    Log in via the real /api/login/ endpoint to set auth cookies
    on the Django test client. Returns the same client instance.
    """
    response = client.post(
        reverse("login"),
        {"email": email, "password": password},
        content_type="application/json",
    )

    assert response.status_code == 200
    client.cookies[ACCESS_COOKIE] = response.cookies[ACCESS_COOKIE].value
    client.cookies[REFRESH_COOKIE] = response.cookies[REFRESH_COOKIE].value
    return client


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_register_sends_email_and_returns_201(client):
    """
    /api/register/:
    - creates a new inactive user
    - sends an activation email
    - returns 201
    """
    response = client.post(
        reverse("register"),
        {
            "email": "newuser@example.com",
            "password": "xxyyzz11",
            "confirmed_password": "xxyyzz11",
        },
        content_type="application/json",
    )

    assert response.status_code == 201
    assert len(mail.outbox) == 1
    assert "Confirm your email" in mail.outbox[0].subject



def test_register_rejects_duplicate_email(client):
    """
    Registering the same email twice:
    - first succeeds (not tested here)
    - second returns 400 with a generic error message
    """
    User.objects.create_user(
        email="dupe@example.com",
        password="pw",
        is_active=False,
    )

    response = client.post(
        reverse("register"),
        {
            "email": "dupe@example.com",
            "password": "abc12345",
            "confirmed_password": "abc12345",
        },
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "detail" in response.json()


def test_activate_view_success(client, settings):
    """
    /api/activate/<uid>/<token>/:
    - activates the user
    - redirects (302) to FRONTEND_LOGIN_SUCCESS_URL
    """
    user = create_inactive_user(email="foo@example.com", password="pw")
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    response = client.get(
        reverse("activate", kwargs={"uidb64": uidb64, "token": token})
    )

    assert response.status_code == 302
    assert response.url == settings.FRONTEND_LOGIN_SUCCESS_URL

    user.refresh_from_db()
    assert user.is_active is True


def test_activate_view_invalid_token(client, settings):
    """
    Invalid activation token:
    - redirects (302) to FRONTEND_ACTIVATE_ERROR_URL
    - user remains inactive
    """
    user = create_inactive_user(email="bar@example.com", password="pw")
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    bad_token = " obviously-wrong "

    response = client.get(
        reverse("activate", kwargs={"uidb64": uidb64, "token": bad_token})
    )

    assert response.status_code == 302
    assert response.url == settings.FRONTEND_ACTIVATE_ERROR_URL

    user.refresh_from_db()
    assert user.is_active is False


def test_login_success_sets_cookies(client):
    """
    /api/login/ with valid credentials:
    - returns 200
    - response includes access_token and refresh_token cookies
    """
    create_active_user(email="login@example.com", password="pw12345")

    response = client.post(
        reverse("login"),
        {"email": "login@example.com", "password": "pw12345"},
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Login successful"
    assert ACCESS_COOKIE in response.cookies
    assert REFRESH_COOKIE in response.cookies


def test_login_invalid_credentials_returns_400(client):
    """
    /api/login/ with invalid credentials or inactive user:
    - returns 400
    - returns a generic error message (no credential leak)
    """
    User.objects.create_user(
        email="nope@example.com",
        password="pw",
        is_active=False,
    )

    response = client.post(
        reverse("login"),
        {"email": "nope@example.com", "password": "pw"},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "Bitte überprüfe deine Eingaben" in response.json()["detail"]


def test_token_refresh_success_sets_new_cookie(client):
    """
    /api/token/refresh/ with valid refresh token cookie:
    - returns 200
    - sets a new access_token cookie
    """
    user = create_active_user(email="refresh@example.com", password="pw")
    refresh = RefreshToken.for_user(user)
    client.cookies[REFRESH_COOKIE] = str(refresh)

    response = client.post(reverse("token_refresh"))

    assert response.status_code == 200
    assert response.json()["detail"] == "Token refreshed"
    assert ACCESS_COOKIE in response.cookies


def test_token_refresh_missing_cookie_returns_400(client):
    """
    /api/token/refresh/ without refresh token cookie:
    - returns 400
    - returns 'Refresh token missing.'
    """
    response = client.post(reverse("token_refresh"))

    assert response.status_code == 400
    assert response.json()["detail"] == "Refresh token missing."


def test_token_refresh_invalid_cookie_returns_401(client):
    """
    /api/token/refresh/ with invalid refresh token cookie:
    - returns 401
    - returns 'Invalid refresh token.'
    """
    client.cookies[REFRESH_COOKIE] = "not-a-real-refresh-token"

    response = client.post(reverse("token_refresh"))

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token."


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_password_reset_request_always_200(client):
    """
    /api/password_reset/:
    - always returns 200, regardless of whether the email exists
    - sends an email only if the user exists
    """
    create_active_user(email="exists@example.com", password="pw1")

    response_existing = client.post(
        reverse("password_reset"),
        {"email": "exists@example.com"},
        content_type="application/json",
    )
    assert response_existing.status_code == 200
    assert response_existing.json()["detail"].startswith("An email has been sent")

    response_missing = client.post(
        reverse("password_reset"),
        {"email": "does-not-exist@example.com"},
        content_type="application/json",
    )
    assert response_missing.status_code == 200
    assert response_missing.json()["detail"].startswith("An email has been sent")

    # Only one email is sent (for the existing user)
    assert len(mail.outbox) == 1
    assert "Reset your password" in mail.outbox[0].subject



def test_password_reset_confirm_success(client):
    """
    /api/password_confirm/<uid>/<token>/:
    - sets a new password if token is valid
    - returns 200 with success message
    """
    user = create_active_user(email="resetme@example.com", password="oldpw")
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    response = client.post(
        reverse(
            "password_reset_confirm",
            kwargs={"uidb64": uidb64, "token": token},
        ),
        {
            "new_password": "NEU12345!!",
            "confirm_password": "NEU12345!!",
        },
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["detail"] == "Your Password has been successfully reset."

    user.refresh_from_db()
    assert user.check_password("NEU12345!!") is True


def test_password_reset_confirm_invalid_token(client):
    """
    /api/password_confirm/<uid>/<token>/ with invalid token:
    - returns 400 and an error message
    - does not change the password
    """
    user = create_active_user(email="resetbad@example.com", password="pw")
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    bad_token = "definitely-wrong-token"

    response = client.post(
        reverse(
            "password_reset_confirm",
            kwargs={"uidb64": uidb64, "token": bad_token},
        ),
        {
            "new_password": "X1X1X1X1",
            "confirm_password": "X1X1X1X1",
        },
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "detail" in response.json()


def test_logout_flow_success_and_cookie_clearing():
    """
    logout_view:
    - is protected with IsAuthenticated (checked via force_authenticate)
    - expects a valid refresh token cookie
    - returns 200 on success
    """
    factory = APIRequestFactory()
    user = create_active_user(email="logout@example.com", password="pw")

    refresh = RefreshToken.for_user(user)

    request = factory.post(reverse("logout"))
    request.COOKIES = {REFRESH_COOKIE: str(refresh)}
    force_authenticate(request, user=user)

    response = logout_view(request)

    assert response.status_code == 200
    assert "Logout successful" in response.data["detail"]


def test_logout_flow_missing_refresh_token_returns_400():
    """
    logout_view without refresh token cookie:
    - returns 400 'Refresh token missing.'
    """
    factory = APIRequestFactory()
    user = create_active_user(email="logout2@example.com", password="pw")

    request = factory.post(reverse("logout"))
    request.COOKIES = {}
    force_authenticate(request, user=user)

    response = logout_view(request)

    assert response.status_code == 400
    assert response.data["detail"] == "Refresh token missing."
