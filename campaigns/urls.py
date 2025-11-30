from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    # Web views only (API endpoints are handled in main URLs)
    path('create/', views.campaign_create, name='create'),
    path('<uuid:campaign_id>/edit/', views.campaign_edit, name='edit'),
    path('template/<uuid:campaign_id>/', views.campaign_template, name='template'),
    path('template/', views.campaign_template, name='new-template'),
    # Simple pages ported from streamlit utilities
    path('abtest/', views.abtest_view, name='abtest'),
    path('drafts/', views.drafts_view, name='drafts'),
    path('analysis/', views.campaign_analysis_view, name='analysis'),
]