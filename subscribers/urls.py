from django.urls import path
from . import views

app_name = 'subscribers'

urlpatterns = [
    # Web views
    path('subscribers/import/', views.import_subscribers, name='import'),
    path('subscribers/process-import/', views.process_import, name='process-import'),
    
    # API endpoints
    path('api/subscribers/validate-file/', views.validate_file, name='validate-file'),
]