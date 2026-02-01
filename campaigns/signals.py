from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import EmailEvent, Campaign, Email
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_default_campaign(sender, instance, created, **kwargs):
    """
    Create a default campaign with a default email template when a new user is created.
    """
    if not created:
        return  # Only process new users
    
    # Check if user already has a "Default" campaign to avoid duplicates
    if Campaign.objects.filter(user=instance, name="Default").exists():
        return
    
    try:
        # Create the default campaign
        default_campaign = Campaign.objects.create(
            user=instance,
            name="Default",
            description="Default campaign created automatically on signup",
            is_active=True
        )
        
        # Create the default email template
        Email.objects.create(
            campaign=default_campaign,
            subject="Hi {{first_name}}, did you have any questions?",
            body_html="<p>Hi {{first_name}}, did you have any questions?</p>",
            body_text="Hi {{first_name}}, did you have any questions?",
            wait_time=1,
            wait_unit='days',
            order=0
        )
        
        logger.info(f"Created default campaign and email template for user {instance.id}")
    except Exception as e:
        logger.error(f"Error creating default campaign for user {instance.id}: {str(e)}", exc_info=True)


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
        
    elif instance.event_type == 'bounced':
        campaign.bounce_count += 1
        campaign.save(update_fields=['bounce_count'])
        logger.info(f"Campaign {campaign.id} bounce_count incremented to {campaign.bounce_count}")
        
    elif instance.event_type == 'unsubscribed':
        campaign.unsubscribe_count += 1
        campaign.save(update_fields=['unsubscribe_count'])
        logger.info(f"Campaign {campaign.id} unsubscribe_count incremented to {campaign.unsubscribe_count}")
        
    elif instance.event_type == 'complained':
        campaign.complaint_count += 1
        campaign.save(update_fields=['complaint_count'])
        logger.info(f"Campaign {campaign.id} complaint_count incremented to {campaign.complaint_count}")
