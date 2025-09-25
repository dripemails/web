from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    # Web views only (API endpoints are handled in main URLs)
    path('campaigns/create/', views.campaign_create, name='create'),
    path('campaigns/<uuid:campaign_id>/edit/', views.campaign_edit, name='edit'),
    path('campaigns/template/<uuid:campaign_id>/', views.campaign_template, name='template'),
    path('campaigns/template/', views.campaign_template, name='new-template'),
]