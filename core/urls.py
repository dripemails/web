from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/dashboard/', views.dashboard_api, name='dashboard-api'),
    path('api/profile/settings/', views.profile_settings, name='profile-settings'),
]