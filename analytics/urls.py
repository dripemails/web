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
]