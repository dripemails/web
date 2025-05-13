from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='core-home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('pricing/', views.pricing, name='pricing'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('promo-verification/', views.promo_verification, name='promo_verification'),
]