from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('pricing/', views.pricing, name='pricing'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('send-contact/', views.send_contact, name='send-contact'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('settings/', views.account_settings, name='settings'),
    path('promo-verification/', views.promo_verification, name='promo_verification'),
    # Feature pages
    path('features/drip-campaigns/', views.feature_drip_campaigns, name='feature_drip_campaigns'),
    path('features/email-scheduling/', views.feature_email_scheduling, name='feature_email_scheduling'),
    path('features/analytics/', views.feature_analytics, name='feature_analytics'),
    path('features/subscriber-management/', views.feature_subscriber_management, name='feature_subscriber_management'),
    path('features/email-templates/', views.feature_email_templates, name='feature_email_templates'),
    # Resource pages
    path('resources/documentation/', views.resource_documentation, name='resource_documentation'),
    path('resources/tutorials/', views.resource_tutorials, name='resource_tutorials'),
    path('resources/api-reference/', views.resource_api_reference, name='resource_api_reference'),
    path('resources/community/', views.resource_community, name='resource_community'),
    # Community resource pages
    path('resources/community/user-forum/', views.community_user_forum, name='community_user_forum'),
    path('resources/community/feature-requests/', views.community_feature_requests, name='community_feature_requests'),
    path('resources/community/success-stories/', views.community_success_stories, name='community_success_stories'),
    path('resources/community/social/', views.community_social, name='community_social'),
    # Blog
    path('resources/blog/', views.blog_index, name='blog_index'),
    path('resources/blog/<slug:slug>/', views.blog_post_detail, name='blog_post_detail'),
]