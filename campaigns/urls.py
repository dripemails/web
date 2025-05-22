from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    # Web views
    path('campaigns/create/', views.campaign_create, name='create'),
    path('campaigns/<uuid:campaign_id>/edit/', views.campaign_edit, name='edit'),
    path('campaigns/template/<uuid:campaign_id>/', views.campaign_template, name='template'),
    path('campaigns/template/', views.campaign_template, name='new-template'),
    
    # API endpoints
    path('api/campaigns/', views.campaign_list_create, name='list-create'),
    path('api/campaigns/<uuid:campaign_id>/', views.campaign_detail, name='detail'),
    path('api/campaigns/<uuid:campaign_id>/activate/', views.activate_campaign, name='activate'),
    path('api/campaigns/<uuid:campaign_id>/deactivate/', views.deactivate_campaign, name='deactivate'),
    path('api/campaigns/<uuid:campaign_id>/emails/', views.email_list_create, name='email-list-create'),
    path('api/campaigns/<uuid:campaign_id>/emails/<uuid:email_id>/', views.email_detail, name='email-detail'),
    path('api/campaigns/<uuid:campaign_id>/emails/<uuid:email_id>/test/', views.test_email, name='test-email'),
    path('api/campaigns/<uuid:campaign_id>/emails/<uuid:email_id>/send/', views.send_email, name='send-email'),
    path('api/upload-contacts/', views.upload_contacts, name='upload_contacts'),
]