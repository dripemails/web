from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    path('campaigns/', views.CampaignListCreateAPIView.as_view(), name='campaign-list-create'),
    path('campaigns/<uuid:pk>/', views.CampaignRetrieveUpdateDestroyAPIView.as_view(), name='campaign-detail'),
    path('campaigns/<uuid:campaign_id>/emails/', views.EmailListCreateAPIView.as_view(), name='email-list-create'),
    path('campaigns/<uuid:campaign_id>/emails/<uuid:pk>/', views.EmailRetrieveUpdateDestroyAPIView.as_view(), name='email-detail'),
    path('campaigns/<uuid:campaign_id>/activate/', views.activate_campaign, name='campaign-activate'),
    path('campaigns/<uuid:campaign_id>/deactivate/', views.deactivate_campaign, name='campaign-deactivate'),
    path('campaigns/<uuid:pk>/edit/', views.campaign_edit_view, name='campaign-edit'),
]