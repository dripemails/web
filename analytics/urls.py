from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('analytics/dashboard/', views.analytics_dashboard, name='dashboard'),
    path('analytics/campaigns/<uuid:campaign_id>/', views.campaign_analytics, name='campaign'),
    path('analytics/subscribers/<uuid:list_id>/', views.subscriber_analytics, name='subscribers'),
    path('track/open/<uuid:tracking_id>/', views.track_open, name='track-open'),
    path('track/click/<uuid:tracking_id>/', views.track_click, name='track-click'),
    path('profile/settings/', views.update_profile_settings, name='profile-settings'),
    # Footer management
    path('footers/', views.footer_list, name='footer_list'),
    path('footers/create/', views.footer_create, name='footer_create'),
    path('footers/<uuid:footer_id>/edit/', views.footer_edit, name='footer_edit'),
    path('footers/<uuid:footer_id>/delete/', views.footer_delete, name='footer_delete'),
    path('footers/<uuid:footer_id>/set-default/', views.footer_set_default, name='footer_set_default'),
]