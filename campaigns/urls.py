from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    # Web views only (API endpoints are handled in main URLs)
    path('create/', views.campaign_create, name='create'),
    path('<uuid:campaign_id>/edit/', views.campaign_edit, name='edit'),
    path('template/<uuid:campaign_id>/', views.campaign_template, name='template'),
    path('template/', views.campaign_template, name='new-template'),
]