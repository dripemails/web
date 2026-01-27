from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Subscriber
from campaigns.models import Campaign, Email, EmailEvent
import logging

logger = logging.getLogger(__name__)


@receiver(m2m_changed, sender=Subscriber.lists.through)
def send_first_campaign_email_on_list_add(sender, instance, action, pk_set, **kwargs):
    """
    When a subscriber is added to a list, check if that list is used by any active campaigns
    and send the first email in those campaigns to the subscriber.
    
    This handles both single subscriber additions and bulk imports.
    """
    # Only process when subscribers are added to lists (not removed)
    if action != 'post_add':
        return
    
    # Get the lists that were added
    if not pk_set:
        return
    
    from .models import List
    added_lists = List.objects.filter(id__in=pk_set)
    
    # Find all active campaigns that use these lists
    campaigns = Campaign.objects.filter(
        subscriber_list__in=added_lists,
        is_active=True
    ).select_related('subscriber_list').prefetch_related('emails')
    
    if not campaigns.exists():
        return
    
    # Process each campaign
    for campaign in campaigns:
        # Only process if the subscriber is actually in the campaign's list
        # Check if the campaign's list ID is in the pk_set of added lists
        if not campaign.subscriber_list or campaign.subscriber_list.id not in pk_set:
            continue
        
        # Get the first email in the campaign (lowest order)
        first_email = campaign.emails.order_by('order').first()
        if not first_email:
            logger.debug(f"No emails found in campaign {campaign.name}")
            continue
        
        # Check if subscriber has already received emails from this campaign
        if EmailEvent.objects.filter(
            email__campaign=campaign,
            subscriber_email=instance.email,
            event_type='sent'
        ).exists():
            logger.debug(f"Subscriber {instance.email} has already received emails from campaign {campaign.name}")
            continue
        
        # Only send if subscriber is active
        if not instance.is_active:
            logger.debug(f"Subscriber {instance.email} is not active, skipping campaign email")
            continue
        
        # Send the first email using the campaign task
        try:
            from campaigns.tasks import send_campaign_email
            
            # Build variables from subscriber
            variables = {}
            if instance.first_name:
                variables['first_name'] = instance.first_name
            if instance.last_name:
                variables['last_name'] = instance.last_name
            variables['email'] = instance.email
            
            # Send the first email
            send_campaign_email(
                email_id=str(first_email.id),
                subscriber_id=str(instance.id),
                variables=variables
            )
            
            logger.info(
                f"Sent first email from campaign '{campaign.name}' to subscriber {instance.email} "
                f"after being added to list '{campaign.subscriber_list.name}'"
            )
        except Exception as e:
            logger.error(
                f"Error sending first campaign email to {instance.email} for campaign {campaign.name}: {str(e)}",
                exc_info=True
            )
