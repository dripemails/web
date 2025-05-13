from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

# URL patterns that should NOT be prefixed with a language code
non_prefixed_urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')), # Provides 'set_language'
]

# URL patterns that SHOULD be prefixed with a language code
language_prefixed_urlpatterns = i18n_patterns(
    path('accounts/', include('allauth.urls')),
    path('', include('core.urls')),
    path('', include('campaigns.urls')),
    path('', include('subscribers.urls')),
    path('', include('analytics.urls')),
    prefix_default_language=False
)

# Combine both lists
urlpatterns = non_prefixed_urlpatterns + language_prefixed_urlpatterns

# Add static and media files for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)