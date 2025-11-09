from django.urls import path
from . import views

app_name = 'subscribers'

urlpatterns = [
    # Web views (no 'subscribers/' prefix since it's added in main urls.py)
    path('', views.subscriber_directory, name='list'),
    path('import/', views.import_subscribers, name='import'),
    path('lists/', views.list_list_create, name='list-list-create'),
    path('lists/<uuid:pk>/', views.list_detail, name='list-detail'),
    
    # API endpoints (moved to main urls.py as non-prefixed patterns)
]