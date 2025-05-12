from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from datetime import timedelta
import logging
import uuid

logger = logging.getLogger(__name__)

@shared_task
def send_campaign_emails(campaign_id):
    """
    Process the campaign and schedule emails to subscribers.
    This task is triggered when a campaign is activated.
    """
    from .models import Campaign, Email, EmailEvent
    from subscribers.models import Subscriber
    
    try:
        campaign = Campaign.objects.get(id=campaign_id, is_active=True)
    except Campaign.DoesNotExist:
        logger.error(f"Campaign with id {campaign_id} not found or not active")
        return
    
    # Get all subscribers in the list
    subscribers = campaign.subscriber_list.subscribers.filter(is_active=True)
    if not subscribers.exists():
        logger.warning(f"No active subscribers found for campaign {campaign.name}")
        return
    
    # Get first email in sequence
    first_email = campaign.emails.order_by('order').first()
    if not first_email:
        logger.warning(f"No emails found in campaign {campaign.name}")
        return
    
    # Schedule the first email for each subscriber
    for subscriber in subscribers:
        # Check if this subscriber has already received emails from this campaign
        if not EmailEvent.objects.filter(
            email__campaign=campaign, 
            subscriber_email=subscriber.email,
            event_type='sent'
        ).exists():
            # Schedule the first email
            send_campaign_email.delay(
                email_id=str(first_email.id),
                subscriber_id=str(subscriber.id)
            )
    
    logger.info(f"Scheduled first email of campaign {campaign.name} for {subscribers.count()} subscribers")


@shared_task
def send_campaign_email(email_id, subscriber_id):
    """Send a specific campaign email to a specific subscriber."""
    from .models import Email, EmailEvent
    from subscribers.models import Subscriber
    
    try:
        email = Email.objects.select_related('campaign').get(id=email_id)
        subscriber = Subscriber.objects.get(id=subscriber_id, is_active=True)
    except (Email.DoesNotExist, Subscriber.DoesNotExist):
        logger.error(f"Email {email_id} or Subscriber {subscriber_id} not found")
        return
    
    # Make sure the campaign is still active
    if not email.campaign.is_active:
        logger.info(f"Campaign {email.campaign.name} is no longer active. Skipping email.")
        return
    
    # Check if subscriber is still in the list and active
    if not subscriber.is_active or subscriber not in email.campaign.subscriber_list.subscribers.all():
        logger.info(f"Subscriber {subscriber.email} is no longer active or in the list. Skipping email.")
        return
    
    # Get user profile for ad settings
    user_profile = email.campaign.user.profile
    show_ads = not user_profile.has_verified_promo
    show_unsubscribe = not user_profile.send_without_unsubscribe
    
    # Tracking pixel for open tracking
    tracking_id = uuid.uuid4()
    tracking_pixel = f'<img src="{settings.SITE_URL}/track/open/{tracking_id}/" width="1" height="1" alt=""/>'
    
    # Generate unsubscribe link
    unsubscribe_link = f"{settings.SITE_URL}/unsubscribe/{subscriber.uuid}/"
    
    # Prepare email with ads and unsubscribe link as needed
    html_content = email.body_html
    text_content = email.body_text
    
    # Add tracking pixel to HTML content
    html_content += tracking_pixel
    
    # Add ads if required
    if show_ads:
        ads_html = render_to_string('emails/ad_footer.html')
        ads_text = "This email is powered by DripEmails.org - Free email marketing automation"
        html_content += ads_html
        text_content += f"\n\n{ads_text}"
    
    # Add unsubscribe link if required
    if show_unsubscribe:
        unsubscribe_html = f'<p style="font-size: 12px; color: #666; margin-top: 20px;">If you no longer wish to receive these emails, you can <a href="{unsubscribe_link}">unsubscribe here</a>.</p>'
        unsubscribe_text = f"\n\nIf you no longer wish to receive these emails, you can unsubscribe here: {unsubscribe_link}"
        html_content += unsubscribe_html
        text_content += unsubscribe_text
    
    # Create and send email
    msg = EmailMultiAlternatives(
        subject=email.subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[subscriber.email]
    )
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send()
        
        # Record the event
        EmailEvent.objects.create(
            email=email,
            subscriber_email=subscriber.email,
            event_type='sent'
        )
        
        # Update campaign metrics
        campaign = email.campaign
        campaign.sent_count += 1
        campaign.save(update_fields=['sent_count'])
        
        logger.info(f"Sent email '{email.subject}' to {subscriber.email}")
        
        # Schedule the next email in sequence if one exists
        next_email = email.campaign.emails.filter(order__gt=email.order).order_by('order').first()
        if next_email:
            # Calculate delay based on wait time and unit
            if next_email.wait_unit == 'hours':
                delay = timedelta(hours=next_email.wait_time)
            else:  # days
                delay = timedelta(days=next_email.wait_time)
            
            # Schedule the next email
            send_campaign_email.apply_async(
                args=[str(next_email.id), str(subscriber.id)],
                eta=timezone.now() + delay
            )
            
            logger.info(f"Scheduled next email '{next_email.subject}' for {subscriber.email} in {next_email.wait_time} {next_email.wait_unit}")
    
    except Exception as e:
        logger.error(f"Failed to send email to {subscriber.email}: {str(e)}")


@shared_task
def process_email_open(tracking_id, subscriber_email):
    """Process email open event."""
    from .models import EmailEvent, Campaign
    
    try:
        # Find the sent event with the same tracking ID
        sent_event = EmailEvent.objects.get(
            id=tracking_id, 
            event_type='sent',
            subscriber_email=subscriber_email
        )
        
        # Create an open event
        EmailEvent.objects.create(
            email=sent_event.email,
            subscriber_email=subscriber_email,
            event_type='opened'
        )
        
        # Update campaign metrics
        campaign = sent_event.email.campaign
        campaign.open_count += 1
        campaign.save(update_fields=['open_count'])
        
        logger.info(f"Recorded open event for {subscriber_email}")
    
    except EmailEvent.DoesNotExist:
        logger.error(f"No matching sent event found for tracking ID {tracking_id}")
    except Exception as e:
        logger.error(f"Failed to process email open: {str(e)}")


@shared_task
def process_email_click(tracking_id, subscriber_email, link_url):
    """Process email click event."""
    from .models import EmailEvent, Campaign
    
    try:
        # Find the sent event with the same tracking ID
        sent_event = EmailEvent.objects.get(
            id=tracking_id, 
            event_type='sent',
            subscriber_email=subscriber_email
        )
        
        # Create a click event
        EmailEvent.objects.create(
            email=sent_event.email,
            subscriber_email=subscriber_email,
            event_type='clicked',
            link_clicked=link_url
        )
        
        # Update campaign metrics
        campaign = sent_event.email.campaign
        campaign.click_count += 1
        campaign.save(update_fields=['click_count'])
        
        logger.info(f"Recorded click event for {subscriber_email} on {link_url}")
    
    except EmailEvent.DoesNotExist:
        logger.error(f"No matching sent event found for tracking ID {tracking_id}")
    except Exception as e:
        logger.error(f"Failed to process email click: {str(e)}")