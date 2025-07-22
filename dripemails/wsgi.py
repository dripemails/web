"""
WSGI config for dripemails project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dripemails.live')

application = get_wsgi_application()