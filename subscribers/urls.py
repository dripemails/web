from django.urls import path
from . import views

app_name = 'subscribers'

urlpatterns = [
    path('subscribers/import/', views.import_subscribers, name='import'),
    path('subscribers/process-import/', views.process_import, name='process-import'),
    path('api/subscribers/import/', views.process_import, name='api-import'),
    path('api/lists/', views.ListListCreateAPIView.as_view(), name='list-list-create'),
    path('api/lists/<uuid:pk>/', views.ListRetrieveUpdateDestroyAPIView.as_view(), name='list-detail'),
    path('api/lists/<uuid:list_id>/subscribers/', views.SubscriberListCreateAPIView.as_view(), name='subscriber-list-create'),
    path('api/subscribers/<uuid:pk>/', views.SubscriberRetrieveUpdateDestroyAPIView.as_view(), name='subscriber-detail'),
]