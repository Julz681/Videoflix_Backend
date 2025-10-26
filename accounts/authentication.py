"""
Custom JWT authentication and cookie management for Django REST Framework.

This module provides helper functions to mint, set, and clear JWT tokens 
stored in HttpOnly cookies, as well as a custom authentication class that 
reads and validates these tokens for authenticated requests.
"""

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication

# ---------------------------------------------------------------------------
# Constants for JWT cookie names and configuration
# ---------------------------------------------------------------------------

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"

# Common keyword arguments for setting secure cookies
COOKIE_KW = {
    "httponly": True,
    "samesite": "Lax",
    "secure": False,  # Set to True in production with HTTPS
    "path": "/",
}


# ---------------------------------------------------------------------------
# Token Utility Functions
# ---------------------------------------------------------------------------

def mint_tokens_for(user):
    """
    Generate a new access and refresh token pair for the given user.

    Args:
        user (User): Django user instance.

    Returns:
        tuple[str, str]: Access token and refresh token as string values.
    """
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def set_jwt_cookies(response, access, refresh=None):
    """
    Set JWT tokens in HttpOnly cookies on the provided response.

    Args:
        response (Response): DRF Response object.
        access (str): Encoded access token.
        refresh (str, optional): Encoded refresh token. Defaults to None.
    """
    response.set_cookie(ACCESS_COOKIE, access, **COOKIE_KW)
    if refresh:
        response.set_cookie(REFRESH_COOKIE, refresh, **COOKIE_KW)


def clear_jwt_cookies(response):
    """
    Remove JWT cookies from the response, effectively logging out the user.

    Args:
        response (Response): DRF Response object.
    """
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


# ---------------------------------------------------------------------------
# Custom Authentication Class
# ---------------------------------------------------------------------------

class CookieJWTAuthentication(BaseAuthentication):
    """
    Custom authentication class that validates JWT tokens stored in cookies.

    This class reads the access token from the request's HttpOnly cookie and
    validates it using Django REST Framework SimpleJWT. If valid, the user is
    authenticated; otherwise, an AuthenticationFailed exception is raised.
    """

    def authenticate(self, request):
        """
        Authenticate the request using the JWT access token stored in cookies.

        Args:
            request (Request): Incoming REST framework request.

        Returns:
            tuple(User, Token) | tuple(AnonymousUser, None):
                Authenticated user and validated token, or an anonymous user
                if no token is found.
        """
        raw_token = request.COOKIES.get(ACCESS_COOKIE)
        if not raw_token:
            return AnonymousUser(), None

        jwt_auth = JWTAuthentication()
        try:
            validated_token = jwt_auth.get_validated_token(raw_token)
            user = jwt_auth.get_user(validated_token)
            return user, validated_token
        except (InvalidToken, TokenError):
            raise exceptions.AuthenticationFailed("Unauthenticated")
