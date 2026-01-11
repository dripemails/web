from django.urls import path
from . import views

app_name = 'gmail'

urlpatterns = [
    path('auth/url/', views.gmail_auth_url, name='auth-url'),
    path('callback/', views.gmail_callback, name='callback'),
    path('emails/', views.gmail_emails, name='emails'),
    path('disconnect/', views.gmail_disconnect, name='disconnect'),
]

