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
from .utils import (
    send_activation_email,
    send_password_reset_email,
)
from .authentication import (
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

    try:
        # Create an inactive user
        user = User.objects.create_user(
            email=email,
            password=password,
            is_active=False,
        )
    except Exception:
        # Duplicate or invalid data (e.g. existing email)
        return Response(
            {"detail": "Bitte überprüfe deine Eingaben und versuche es erneut."},
            status=status.HTTP_400_BAD_REQUEST,
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
    Activate user via link sent in email.
    Redirects to frontend on success or failure.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        # Validate the token
        valid = bool(
            user
            and default_token_generator.check_token(user, token)
        )

        if valid:
            user.is_active = True
            user.save(update_fields=["is_active"])

    except Exception:
        valid = False

    # Redirect URLs configurable via settings
    success_url = getattr(
        settings,
        "FRONTEND_LOGIN_SUCCESS_URL",
        "http://127.0.0.1:5500/pages/auth/login.html?activated=1",
    )
    error_url = getattr(
        settings,
        "FRONTEND_ACTIVATE_ERROR_URL",
        "http://127.0.0.1:5500/pages/auth/register.html?activation=failed",
    )

    return HttpResponseRedirect(success_url if valid else error_url)


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

    Response example:
    {
        "detail": "Login successful",
        "user": {
            "id": ...,
            "username": "user@example.com"
        }
    }
    """
    data = LoginSerializer(data=request.data)
    data.is_valid(raise_exception=True)

    email = data.validated_data["email"].lower()
    password = data.validated_data["password"]

    # Authenticate against the Django user model
    user = authenticate(username=email, password=password)

    if not user or not user.is_active:
        # Inactive or invalid credentials
        return Response(
            {"detail": "Bitte überprüfe deine Eingaben und versuche es erneut."},
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

    Response example:
    {
        "detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."
    }
    """
    refresh_token_raw = request.COOKIES.get(REFRESH_COOKIE)
    if not refresh_token_raw:
        # No token cookie provided
        return Response(
            {"detail": "Refresh token missing."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Blacklist token to invalidate it
        RefreshToken(refresh_token_raw).blacklist()
    except TokenError:
        # Already invalid or malformed
        pass

    # Build logout response and clear cookies
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

    Response example:
    {
        "detail": "Token refreshed",
        "access": "new_access_token"
    }
    """
    refresh_token_raw = request.COOKIES.get(REFRESH_COOKIE)
    if not refresh_token_raw:
        return Response(
            {"detail": "Refresh token missing."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Generate a new access token
        new_access_token = str(RefreshToken(refresh_token_raw).access_token)
    except TokenError:
        # Invalid or expired refresh token
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

    # Set new access cookie
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
            # Never reveal if user exists or not
            pass

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
        # Decode user ID and validate token
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save new password securely
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        return Response(
            {"detail": "Your Password has been successfully reset."},
            status=status.HTTP_200_OK,
        )

    except Exception:
        # Invalid user ID or malformed request
        return Response(
            {"detail": "Invalid request."},
            status=status.HTTP_400_BAD_REQUEST,
        )
