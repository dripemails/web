from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import EmailEvent
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=EmailEvent)
def update_campaign_metrics(sender, instance, created, **kwargs):
    """
    Automatically update campaign metrics when an EmailEvent is created.
    This ensures analytics are always accurate regardless of how emails are sent.
    """
    if not created:
        return  # Only process new events
    
    campaign = instance.email.campaign
    
    if instance.event_type == 'sent':
        campaign.sent_count += 1
        campaign.save(update_fields=['sent_count'])
        logger.info(f"Campaign {campaign.id} sent_count incremented to {campaign.sent_count}")
        
    elif instance.event_type == 'opened':
        campaign.open_count += 1
        campaign.save(update_fields=['open_count'])
        logger.info(f"Campaign {campaign.id} open_count incremented to {campaign.open_count}")
        
    elif instance.event_type == 'clicked':
        campaign.click_count += 1
        campaign.save(update_fields=['click_count'])
        logger.info(f"Campaign {campaign.id} click_count incremented to {campaign.click_count}")
