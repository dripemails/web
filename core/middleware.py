"""Middleware for core app."""
import threading

from django.conf import settings

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
        response.pop('X-Frame-Options', None)
        # frame-ancestors lists who can embed this page in a frame
        ancestors = ' '.join(allowed)
        csp = response.get('Content-Security-Policy', '')
        if csp and not csp.strip().endswith(';'):
            csp = csp.rstrip() + '; '
        response['Content-Security-Policy'] = csp + f"frame-ancestors {ancestors};"
        return response
