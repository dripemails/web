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
    path('promo-verification/', views.promo_verification, name='promo_verification'),
    # Feature pages
    path('features/drip-campaigns/', views.feature_drip_campaigns, name='feature_drip_campaigns'),
    path('features/email-scheduling/', views.feature_email_scheduling, name='feature_email_scheduling'),
    path('features/analytics/', views.feature_analytics, name='feature_analytics'),
    path('features/subscriber-management/', views.feature_subscriber_management, name='feature_subscriber_management'),
    path('features/email-templates/', views.feature_email_templates, name='feature_email_templates'),
    # Resource pages
    path('resources/documentation/', views.resource_documentation, name='resource_documentation'),
    # Documentation subpages
    path('resources/documentation/getting-started/', views.docs_getting_started, name='docs_getting_started'),
    path('resources/documentation/campaigns/', views.docs_campaigns, name='docs_campaigns'),
    path('resources/documentation/subscribers/', views.docs_subscribers, name='docs_subscribers'),
    path('resources/documentation/templates/', views.docs_templates, name='docs_templates'),
    path('resources/documentation/analytics/', views.docs_analytics, name='docs_analytics'),
    path('resources/documentation/ai-features/', views.docs_ai_features, name='docs_ai_features'),
    path('resources/documentation/smtp-server/', views.docs_smtp_server, name='docs_smtp_server'),
    path('resources/documentation/deployment/', views.docs_deployment, name='docs_deployment'),
    path('resources/documentation/deployment/prerequisites/', views.docs_deployment_prerequisites, name='docs_deployment_prerequisites'),
    path('resources/documentation/deployment/installation/', views.docs_deployment_installation, name='docs_deployment_installation'),
    path('resources/documentation/deployment/configuration/', views.docs_deployment_configuration, name='docs_deployment_configuration'),
    path('resources/documentation/deployment/production/', views.docs_deployment_production, name='docs_deployment_production'),
    path('resources/documentation/deployment/troubleshooting/', views.docs_deployment_troubleshooting, name='docs_deployment_troubleshooting'),
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