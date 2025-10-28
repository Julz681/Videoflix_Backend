"""
Views handling user registration, activation, authentication,
token management, and password reset for the Videoflix accounts app.
"""

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseRedirect
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
)
from ..utils import (
    send_activation_email,
    send_password_reset_email,
)
from ..authentication import (
    mint_tokens_for,
    set_jwt_cookies,
    clear_jwt_cookies,
    REFRESH_COOKIE,
)

User = get_user_model()


# -------------------------------------------------
# Registration / Activation
# -------------------------------------------------

@csrf_exempt
@api_view(["POST"])
@authentication_classes([])            # No authentication required
@permission_classes([AllowAny])        # Public endpoint
def register_view(request):
    """
    Register a new user (inactive by default) and send an activation email.

    Response example:
    {
        "user": { "id": ..., "email": ... },
        "token": "activation_token"
    }
    """
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data["email"].lower()
    password = serializer.validated_data["password"]

    # Reject duplicate email explicitly to avoid half-created users
    if User.objects.filter(email=email).exists():
        return Response(
            {"detail": "This email address is already registered."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create an inactive user (must activate via email link)
    user = User.objects.create_user(
        email=email,
        password=password,
        is_active=False,
    )

    # Send activation email to user
    send_activation_email(user)

    return Response(
        {
            "user": {
                "id": user.id,
                "email": user.email,
            },
            "token": "activation_token",
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@authentication_classes([])            # Public GET endpoint
@permission_classes([AllowAny])
def activate_view(request, uidb64, token):
    """
    Frontend calls this after the user landed on activate.html with uid/token.

    Old flow:
      - We used to redirect with HttpResponseRedirect.

    New flow:
      - We return JSON instead, because the frontend page already handles
        showing a spinner, a success/fail message, and then redirecting
        to login.html after some delay.

    IMPORTANT for UX:
      - We ALWAYS return HTTP 200 so that fetch(...).then(...) in the
        frontend is treated as "success" instead of falling into .catch().
      - We include `"status": "ok"` or `"status": "error"` in the JSON
        so the frontend *could* distinguish if it wants.
    """
    user_was_activated = False
    error_reason = None

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        # Validate token
        if default_token_generator.check_token(user, token):
            # If token is valid, activate the user (idempotent)
            if not user.is_active:
                user.is_active = True
                user.save(update_fields=["is_active"])
            user_was_activated = True
        else:
            error_reason = "invalid_token"
    except Exception:
        error_reason = "invalid_request"

    # Where should the frontend send the user next?
    target_login_url = getattr(
        settings,
        "FRONTEND_LOGIN_SUCCESS_URL",
        "http://127.0.0.1:5500/pages/auth/login.html?activated=1",
    )

    # Build a frontend-friendly payload.
    # NOTE: HTTP status is ALWAYS 200, even if activation failed,
    # so the frontend doesn't fall into its 'network error' branch.
    if user_was_activated:
        return Response(
            {
                "status": "ok",
                "message": "Account successfully activated.",
                "redirect_after_ms": getattr(
                    settings, "ACTIVATION_REDIRECT_DELAY_MS", 2500
                ),
                "redirect_to": target_login_url,
            },
            status=status.HTTP_200_OK,
        )
    else:
        return Response(
            {
                "status": "error",
                "message": "Activation failed.",
                "reason": error_reason or "unknown",
                "redirect_after_ms": getattr(
                    settings, "ACTIVATION_REDIRECT_DELAY_MS", 2500
                ),
                "redirect_to": target_login_url,
            },
            status=status.HTTP_200_OK,
        )


@api_view(["GET"])
@authentication_classes([])     # public
@permission_classes([AllowAny])
def password_reset_redirect_view(request, uidb64, token):
    """
    User clicked the 'Reset password' link in the email.

    We validate uid/token.
    If valid: redirect the browser to the existing static frontend page
    /pages/auth/confirm_password.html?uid=...&token=...
    If invalid: redirect to login with an error flag.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        if not default_token_generator.check_token(user, token):
            raise Exception("Invalid token")

        frontend_ok = (
            f"{settings.FRONTEND_BASE_URL.rstrip('/')}"
            f"/pages/auth/confirm_password.html"
            f"?uid={uidb64}&token={token}"
        )
        return HttpResponseRedirect(frontend_ok)

    except Exception:
        frontend_fail = (
            f"{settings.FRONTEND_BASE_URL.rstrip('/')}"
            f"/pages/auth/login.html?reset=invalid"
        )
        return HttpResponseRedirect(frontend_fail)


# -------------------------------------------------
# Login / Logout / Token Refresh
# -------------------------------------------------

@csrf_exempt
@api_view(["POST"])
@authentication_classes([])            # Public endpoint
@permission_classes([AllowAny])
def login_view(request):
    """
    Log in a user and set JWT cookies (access + refresh).
    """
    data = LoginSerializer(data=request.data)
    data.is_valid(raise_exception=True)

    email = data.validated_data["email"].lower()
    password = data.validated_data["password"]

    user = authenticate(username=email, password=password)

    if not user or not user.is_active:
        return Response(
            {"detail": "Please check your credentials and try again."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Mint new JWT tokens for this user
    access, refresh = mint_tokens_for(user)

    # Build response and set cookies
    resp = Response(
        {
            "detail": "Login successful",
            "user": {
                "id": user.id,
                "username": user.email,
            },
        },
        status=status.HTTP_200_OK,
    )

    set_jwt_cookies(resp, access, refresh)
    return resp


@csrf_exempt
@api_view(["POST"])
@authentication_classes([])            # Manual authentication via cookies
@permission_classes([AllowAny])        # Open endpoint per specification
def logout_view(request):
    """
    Logout the current user:
    - blacklist the refresh token
    - clear authentication cookies
    """
    refresh_token_raw = request.COOKIES.get(REFRESH_COOKIE)
    if not refresh_token_raw:
        return Response(
            {"detail": "Refresh token missing."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        RefreshToken(refresh_token_raw).blacklist()
    except TokenError:
        # Already invalid or malformed
        pass

    resp = Response(
        {
            "detail": (
                "Logout successful! All tokens will be deleted. "
                "Refresh token is now invalid."
            )
        },
        status=status.HTTP_200_OK,
    )
    clear_jwt_cookies(resp)
    return resp


@csrf_exempt
@api_view(["POST"])
@authentication_classes([])            # Public; uses cookies only
@permission_classes([AllowAny])
def refresh_view(request):
    """
    Refresh access token using the refresh token cookie.
    Sets a new access_token as HttpOnly cookie.
    """
    refresh_token_raw = request.COOKIES.get(REFRESH_COOKIE)
    if not refresh_token_raw:
        return Response(
            {"detail": "Refresh token missing."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        new_access_token = str(RefreshToken(refresh_token_raw).access_token)
    except TokenError:
        return Response(
            {"detail": "Invalid refresh token."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    resp = Response(
        {
            "detail": "Token refreshed",
            "access": "new_access_token",
        },
        status=status.HTTP_200_OK,
    )

    set_jwt_cookies(resp, new_access_token, None)
    return resp


# -------------------------------------------------
# Password Reset
# -------------------------------------------------

@csrf_exempt
@api_view(["POST"])
@authentication_classes([])            # Public endpoint
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """
    Always returns 200.
    Sends a reset email if a user with the provided email exists.
    """
    email = request.data.get("email", "").lower()

    if email:
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(user)
        except User.DoesNotExist:
            pass  # do not leak existence

    return Response(
        {"detail": "An email has been sent to reset your password."},
        status=status.HTTP_200_OK,
    )


@csrf_exempt
@api_view(["POST"])
@authentication_classes([])            # Public endpoint
@permission_classes([AllowAny])
def password_reset_confirm_view(request, uidb64, token):
    """
    Set a new password for the user if the token and uid are valid.
    """
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        return Response(
            {"detail": "Your Password has been successfully reset."},
            status=status.HTTP_200_OK,
        )

    except Exception:
        return Response(
            {"detail": "Invalid request."},
            status=status.HTTP_400_BAD_REQUEST,
        )
