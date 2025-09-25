from django.urls import path
from . import views

app_name = 'subscribers'

urlpatterns = [
    # Web views
    path('subscribers/import/', views.import_subscribers, name='import'),
    path('subscribers/lists/', views.list_list_create, name='list-list-create'),
    path('subscribers/lists/<uuid:pk>/', views.list_detail, name='list-detail'),
    
    # API endpoints
    path('api/lists/', views.list_list_create, name='api-list-list-create'),
    path('api/lists/<uuid:pk>/', views.list_detail, name='api-list-detail'),
    path('api/subscribers/', views.subscriber_list_create, name='list-create'),
    path('api/subscribers/<uuid:pk>/', views.subscriber_detail, name='detail'),
    path('api/subscribers/import/', views.process_import, name='process-import'),
    path('api/subscribers/validate-file/', views.validate_file, name='validate-file'),
]