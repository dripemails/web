"""Middleware for core app."""
import threading

from django.conf import settings
from django.utils.cache import patch_vary_headers

_thread_locals = threading.local()


def get_current_request():
    """Return the current HTTP request from thread-local storage, or None."""
    return getattr(_thread_locals, 'request', None)


class RequestStorageMiddleware:
    """Store the current request in thread-local storage for use in signals etc."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        try:
            return self.get_response(request)
        finally:
            if hasattr(_thread_locals, 'request'):
                del _thread_locals.request


class FrameAncestorsMiddleware:
    """
    Allow this site to be embedded in iframes from the mobile wrapper (and other
    allowed origins) by setting Content-Security-Policy frame-ancestors and
    removing X-Frame-Options so the browser does not block embedding.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        allowed = getattr(settings, 'FRAME_ANCESTORS_ALLOWED', None)
        if not allowed:
            return response
        # Remove X-Frame-Options so CSP frame-ancestors can allow embedding
        if 'X-Frame-Options' in response:
            del response['X-Frame-Options']
        # frame-ancestors lists who can embed this page in a frame
        ancestors = ' '.join(allowed)
        try:
            csp = response['Content-Security-Policy']
        except KeyError:
            csp = ''
        if csp and not csp.strip().endswith(';'):
            csp = csp.rstrip() + '; '
        response['Content-Security-Policy'] = csp + f"frame-ancestors {ancestors};"
        return response


class NoCacheAuthPagesMiddleware:
    """Force no-cache headers on auth pages to avoid stale CSRF tokens.

    Applies to login and signup/register pages (including localized URLs).
    """

    AUTH_URL_NAMES = {
        'account_login',
        'account_signup',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        resolver_match = getattr(request, 'resolver_match', None)
        url_name = resolver_match.url_name if resolver_match else None
        path = (request.path or '').lower().rstrip('/')

        is_auth_page = (
            url_name in self.AUTH_URL_NAMES or
            path.endswith('/accounts/login') or
            path.endswith('/accounts/signup') or
            path.endswith('/accounts/register')
        )

        if is_auth_page:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            patch_vary_headers(response, ('Cookie',))

        return response
