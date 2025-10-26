"""
Middleware that disables CSRF protection for API endpoints.

Useful in setups where authentication is handled via JWT tokens in HttpOnly cookies
instead of Django's CSRF tokens. This should be applied with caution, ideally only
in trusted API contexts.
"""

from django.utils.deprecation import MiddlewareMixin


class DisableCSRFForAPI(MiddlewareMixin):
    """
    Middleware to bypass CSRF checks for requests starting with /api/.

    Note:
        - Intended for REST APIs using token-based authentication.
        - Should not be used if standard Django session authentication is active.
    """

    def process_request(self, request):
        """
        Disable CSRF enforcement for API routes by setting the internal
        Django flag `_dont_enforce_csrf_checks` to True.
        """
        if request.path.startswith("/api/"):
            setattr(request, "_dont_enforce_csrf_checks", True)
