from django.apps import AppConfig


class CampaignsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaigns'
    
    def ready(self):
        """Import signals when the app is ready."""
        import campaigns.signals