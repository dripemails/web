from django.urls import path
from . import views

app_name = 'subscribers'

urlpatterns = [
    path('lists/', views.ListListCreateAPIView.as_view(), name='list-list-create'),
    path('lists/<uuid:pk>/', views.ListRetrieveUpdateDestroyAPIView.as_view(), name='list-detail'),
    path('lists/<uuid:list_id>/subscribers/', views.SubscriberListCreateAPIView.as_view(), name='subscriber-list-create'),
    path('subscribers/<uuid:pk>/', views.SubscriberRetrieveUpdateDestroyAPIView.as_view(), name='subscriber-detail'),
    path('subscribers/import/', views.import_subscribers, name='import-subscribers'),
    path('subscribers/export/<uuid:list_id>/', views.export_subscribers, name='export-subscribers'),
    path('unsubscribe/<uuid:subscriber_uuid>/', views.unsubscribe, name='unsubscribe'),
    path('confirm-subscription/<uuid:subscriber_uuid>/', views.confirm_subscription, name='confirm-subscription'),
]