from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta


def activation_link_for(user) -> str:
    """
    Build the *frontend* activation link.

    Instead of pointing to /api/activate/<uid>/<token>/ directly,
    we send the user to the static frontend page /pages/auth/activate.html
    and include uid + token as query parameters.

    The frontend JS (initActivation()) will:
    - read uid/token from query params
    - call POST/GET to /api/activate/<uid>/<token>/ itself
    - update the UI accordingly
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    base = settings.FRONTEND_BASE_URL.rstrip("/")

    return (
        f"{base}/pages/auth/activate.html"
        f"?uid={uid}&token={token}"
    )


def password_reset_link_for(user) -> str:
    """
    Build the link for the password reset email.

    We send the user directly to confirm_password.html in the frontend,
    again passing uid+token via query params. The frontend JS will then
    do the POST /api/password_confirm/<uid>/<token>/ when the form submits.
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    frontend_base = settings.FRONTEND_BASE_URL.rstrip("/")

    return (
        f"{frontend_base}"
        f"/pages/auth/confirm_password.html"
        f"?uid={uid}&token={token}"
    )


def send_activation_email(user) -> None:
    """
    Send the 'Confirm your email' / account activation email.

    The button in the email links to the *frontend* page activate.html,
    which will use uid+token from the query string to call the backend
    /api/activate/<uid>/<token>/ internally via JS.
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
    Send the reset password email.
    The button links to password_reset_link_for(user),
    which now points directly to confirm_password.html
    with uid+token in the query string.
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
