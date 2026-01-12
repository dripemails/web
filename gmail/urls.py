from django.urls import path
from . import views

app_name = 'gmail'

urlpatterns = [
    # Gmail routes
    path('auth/url/', views.gmail_auth_url, name='auth-url'),
    path('callback/', views.gmail_callback, name='callback'),
    path('emails/', views.gmail_emails, name='emails'),
    path('disconnect/', views.gmail_disconnect, name='disconnect'),
    # IMAP routes
    path('imap/connect/', views.imap_connect, name='imap-connect'),
    path('imap/disconnect/', views.imap_disconnect, name='imap-disconnect'),
    path('imap/emails/', views.imap_emails, name='imap-emails'),
]

