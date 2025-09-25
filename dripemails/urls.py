from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from campaigns import views as campaign_views

# URL patterns that should NOT be prefixed with a language code
non_prefixed_urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')), # Provides 'set_language'
    # API endpoints (no language prefix needed)
    path('api/campaigns/', campaign_views.campaign_list_create, name='api-campaign-list-create'),
    path('api/campaigns/<uuid:campaign_id>/', campaign_views.campaign_detail, name='api-campaign-detail'),
    path('api/campaigns/<uuid:campaign_id>/activate/', campaign_views.activate_campaign, name='api-campaign-activate'),
    path('api/campaigns/<uuid:campaign_id>/deactivate/', campaign_views.deactivate_campaign, name='api-campaign-deactivate'),
    path('api/campaigns/<uuid:campaign_id>/emails/', campaign_views.email_list_create, name='api-email-list-create'),
    path('api/campaigns/<uuid:campaign_id>/emails/reorder/', campaign_views.reorder_emails, name='api-reorder-emails'),
    path('api/campaigns/<uuid:campaign_id>/emails/<uuid:email_id>/', campaign_views.email_detail, name='api-email-detail'),
    path('api/campaigns/<uuid:campaign_id>/emails/<uuid:email_id>/test/', campaign_views.test_email, name='api-test-email'),
    path('api/campaigns/<uuid:campaign_id>/emails/<uuid:email_id>/send/', campaign_views.send_email, name='api-send-email'),
    path('api/upload-contacts/', campaign_views.upload_contacts, name='api-upload-contacts'),
]

# URL patterns that SHOULD be prefixed with a language code
language_prefixed_urlpatterns = i18n_patterns(
    path('accounts/', include('allauth.urls')),
    path('', include('core.urls')),
    # Web views only (no API endpoints)
    path('campaigns/', include('campaigns.urls')),
    path('subscribers/', include('subscribers.urls')),
    path('', include('analytics.urls')),
    prefix_default_language=False
)

# Combine both lists
urlpatterns = non_prefixed_urlpatterns + language_prefixed_urlpatterns

# Add static and media files for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)