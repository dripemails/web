from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from campaigns import views as campaign_views
from analytics import views as analytics_views
from subscribers import views as subscriber_views
from core import views as core_views

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
    path('api/campaigns/<uuid:campaign_id>/generate-email/', campaign_views.generate_email_with_ai, name='api-generate-email'),
    path('api/campaigns/revise-email/', campaign_views.revise_email_with_ai, name='api-revise-email'),
    path('api/campaigns/search-templates/', campaign_views.search_templates, name='api-search-templates'),
    path('api/upload-contacts/', campaign_views.upload_contacts, name='api-upload-contacts'),
    # Analytics API endpoints (no language prefix needed)
    path('api/footers/create/', analytics_views.footer_create_api, name='api-footer-create'),
    path('api/regenerate-key/', analytics_views.regenerate_api_key, name='api-regenerate-key'),
    # Subscribers API endpoints (no language prefix needed)
    path('api/subscribers/lists/', subscriber_views.list_list_create, name='api-subscriber-list-create'),
    path('api/subscribers/lists/<uuid:pk>/', subscriber_views.list_detail, name='api-subscriber-list-detail'),
    path('api/subscribers/', subscriber_views.subscriber_list_create, name='api-subscriber-create'),
    path('api/subscribers/<uuid:pk>/', subscriber_views.subscriber_detail, name='api-subscriber-detail'),
    path('api/subscribers/import/', subscriber_views.process_import, name='api-subscriber-import'),
    path('api/subscribers/validate-file/', subscriber_views.validate_file, name='api-subscriber-validate-file'),
    # Core API endpoints (no language prefix needed)
    path('api/send-email/', core_views.send_email_api, name='api-send-email'),
    path('api/send-email/requests/', core_views.send_email_requests_list, name='api-send-email-requests'),
    path('api/send-email/requests/<uuid:request_id>/send-now/', core_views.send_email_request_send_now, name='api-send-email-request-send-now'),
    path('api/send-email/requests/<uuid:request_id>/unsubscribe/', core_views.send_email_request_unsubscribe, name='api-send-email-request-unsubscribe'),
]

# URL patterns that SHOULD be prefixed with a language code
language_prefixed_urlpatterns = i18n_patterns(
    # Profile page - must come before allauth.urls to override default profile redirect
    path('accounts/profile/', core_views.profile, name='account_profile'),
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
    # Use django.contrib.staticfiles to serve from STATICFILES_DIRS in development
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()