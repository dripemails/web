"""Middleware for core app."""
import threading

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
