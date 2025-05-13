from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    path('campaigns/create/', views.campaign_create, name='create'),
    path('campaigns/template/<uuid:campaign_id>/', views.campaign_template, name='template'),
    path('campaigns/template/', views.campaign_template, name='new-template'),
    path('api/campaigns/create/', views.create_campaign, name='api-create'),
    path('api/campaigns/<uuid:campaign_id>/emails/', views.EmailListCreateAPIView.as_view(), name='email-list-create'),
    path('api/campaigns/<uuid:campaign_id>/emails/<uuid:pk>/', views.EmailRetrieveUpdateDestroyAPIView.as_view(), name='email-detail'),
    path('api/campaigns/<uuid:campaign_id>/activate/', views.activate_campaign, name='campaign-activate'),
    path('api/campaigns/<uuid:campaign_id>/deactivate/', views.deactivate_campaign, name='campaign-deactivate'),
]