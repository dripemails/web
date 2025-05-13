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
    path('api/campaigns/create/', views.create_campaign, name='api-create'),
    path('api/campaigns/<uuid:campaign_id>/templates/order/', views.update_template_order, name='update-template-order'),
    path('api/campaigns/<uuid:campaign_id>/templates/<uuid:template_id>/timing/', views.update_template_timing, name='update-template-timing'),
]