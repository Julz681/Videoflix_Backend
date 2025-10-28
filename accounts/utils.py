"""
Utility functions for generating activation and password reset links,
and sending the corresponding emails.

This module is responsible for:
- Building activation and password reset URLs
- Rendering email templates
- Sending transactional emails (HTML + plaintext fallback)
"""

from datetime import timedelta
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone


def activation_link_for(user) -> str:
    """
    Build the activation link that is sent in the "confirm your email" message.

    The link points to the Django backend /api/activate/<uid>/<token>/,
    NOT directly to the frontend. The backend view will:
    - validate the token
    - activate the user
    - redirect to the correct frontend success/failure URL

    Returns:
        str: Full backend activation URL, e.g.
             http://127.0.0.1:8000/api/activate/NA/abc123token/
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    base_url = settings.BACKEND_BASE_URL.rstrip("/")
    return f"{base_url}/api/activate/{uid}/{token}/"


def password_reset_link_for(user) -> str:
    """
    Build the password reset link that is sent in the "Reset your password" email.

    IMPORTANT:
    We do NOT link directly to the static frontend, because the frontend
    does not define dynamic routes like /password-reset/confirm/<uid>/<token>.

    Instead, we generate a backend URL:
        /api/password_reset_link/<uid>/<token>/

    The backend view `password_reset_redirect_view` will:
    - validate that uid/token are valid
    - then redirect the browser to the EXISTING frontend page
      /pages/auth/confirm_password.html?uid=...&token=...

    That way:
    - we don't have to change the frontend routing structure
    - the frontend still lands on `confirm_password.html`
    - and it receives uid/token via query parameters
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    base = settings.BACKEND_BASE_URL.rstrip("/")
    return f"{base}/api/password_reset_link/{uid}/{token}/"


def send_activation_email(user) -> None:
    """
    Send the 'Confirm your email' / activation message.

    The email includes:
    - A plain text fallback (for clients that block HTML)
    - An HTML version rendered from templates/email/activate.html

    The button in the email points to activation_link_for(user),
    which hits the backend and then redirects to the frontend login.
    """
    link = activation_link_for(user)

    subject = "Confirm your email – Videoflix"

    context = {
        "activation_url": link,
        "user": user,
    }

    html_body = render_to_string("email/activate.html", context)

    text_body = (
        "Dear {name},\n\n"
        "Thank you for registering with Videoflix.\n"
        "To complete your registration and verify your email address, "
        "please click the link below:\n\n"
        "{url}\n\n"
        "If you did not create an account, please disregard this email.\n\n"
        "Your Videoflix Team."
    ).format(
        name=user.first_name or "User",
        url=link,
    )

    send_mail(
        subject=subject,
        message=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_body,
    )


def send_password_reset_email(user) -> None:
    """
    Send the 'Reset your password' email.

    The email template (templates/email/reset_password.html) shows:
    - explanation text
    - a purple "Reset password" button
    - a 24h validity note
    - Videoflix branding

    The button URL comes from password_reset_link_for(user), which:
    - first hits the backend (/api/password_reset_link/<uid>/<token>/)
    - backend validates token
    - backend redirects to the existing static frontend page
      /pages/auth/confirm_password.html?uid=...&token=...

    We also include a plaintext fallback for maximum compatibility.
    """
    link = password_reset_link_for(user)

    subject = "Reset your password – Videoflix"

    context = {
        "reset_url": link,
        "user": user,
        "expires_at": timezone.now() + timedelta(hours=24),
    }

    html_body = render_to_string("email/reset_password.html", context)

    text_body = (
        "Hello,\n\n"
        "We recently received a request to reset your password. "
        "If you made this request, please use the link below:\n\n"
        "{url}\n\n"
        "Please note that for security reasons, this link is only valid for 24 hours.\n\n"
        "If you did not request a password reset, please ignore this email.\n\n"
        "Your Videoflix Team."
    ).format(url=link)

    send_mail(
        subject=subject,
        message=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_body,
    )
