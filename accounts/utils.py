"""
Utility functions for generating activation and password reset links
and sending corresponding emails for user account management.
"""

from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string


def activation_link_for(user) -> str:
    """
    Build a backend activation link containing a base64 user ID and token.

    Args:
        user (User): Django user instance.

    Returns:
        str: Full backend activation URL.
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    base_url = settings.BACKEND_BASE_URL.rstrip("/")
    return f"{base_url}/api/activate/{uid}/{token}/"


def password_reset_link_for(user) -> str:
    """
    Build a frontend password reset link used in reset emails.

    Args:
        user (User): Django user instance.

    Returns:
        str: Full frontend password reset confirmation URL.
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_BASE_URL}/password-reset/confirm/{uid}/{token}"


def send_activation_email(user) -> None:
    """
    Send an activation email with both text and HTML content.

    Args:
        user (User): Newly registered, inactive user.
    """
    link = activation_link_for(user)
    subject = "Aktiviere deinen Videoflix-Account"
    html_body = render_to_string("email/activate.html", {"activation_url": link, "user": user})
    send_mail(
        subject=subject,
        message=f"Klicke zur Aktivierung: {link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_body,
    )


def send_password_reset_email(user) -> None:
    """
    Send a password reset email containing a one-time reset link.

    Args:
        user (User): Active user requesting a password reset.
    """
    link = password_reset_link_for(user)
    send_mail(
        subject="Passwort zurücksetzen – Videoflix",
        message=f"Passwort zurücksetzen: {link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
