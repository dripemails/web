from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from datetime import timedelta
import logging
import uuid
import sys
from analytics.models import UserProfile

logger = logging.getLogger(__name__)


def _is_celery_available():
    """Check if Celery broker is available."""
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        # Try to check if workers are available (this will fail if Redis is down)
        stats = inspect.stats()
        return stats is not None
    except Exception:
        # If any exception occurs, assume Celery is not available
        return False


def _send_test_email_sync(email_id, test_email, variables=None):
    """Send a test email synchronously (non-Celery version)."""
    from .models import Email
    
    try:
        email = Email.objects.select_related('campaign').get(id=email_id)
    except Email.DoesNotExist:
        logger.error(f"Email {email_id} not found")
        raise
    
    # Replace variables in content
    html_content = email.body_html
    text_content = email.body_text
    subject = email.subject
    
    if variables:
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            html_content = html_content.replace(placeholder, str(value))
            text_content = text_content.replace(placeholder, str(value))
            subject = subject.replace(placeholder, str(value))
    
    # Get user email for From address
    user_email = email.campaign.user.email
    
    # Check if user has valid SPF record
    user_profile, _ = UserProfile.objects.get_or_create(user=email.campaign.user)
    has_valid_spf = user_profile.spf_verified
    
    # Create and send email
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=user_email,
        to=[test_email]
    )
    # Only set Sender header if user doesn't have valid SPF record
    if not has_valid_spf:
        msg.extra_headers['Sender'] = settings.DEFAULT_FROM_EMAIL
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send()
        logger.info(f"Sent test email '{subject}' to {test_email}")
    except Exception as e:
        logger.error(f"Error sending test email to {test_email}: {str(e)}")
        raise


def _send_single_email_sync(email_id, subscriber_email, variables=None, request_id=None):
    """Send a single email synchronously (non-Celery version)."""
    from .models import Email, EmailEvent, EmailSendRequest
    request_obj = None
    if request_id:
        try:
            request_obj = EmailSendRequest.objects.get(id=request_id)
        except EmailSendRequest.DoesNotExist:
            request_obj = None
    
    try:
        email = Email.objects.select_related('campaign').get(id=email_id)
    except Email.DoesNotExist:
        logger.error(f"Email {email_id} not found")
        if request_obj:
            request_obj.status = 'failed'
            request_obj.error_message = f"Email {email_id} not found"
            request_obj.save(update_fields=['status', 'error_message', 'updated_at'])
        raise
    
    # Replace variables in content
    html_content = email.body_html
    text_content = email.body_text
    subject = email.subject
    
    if variables:
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            html_content = html_content.replace(placeholder, str(value))
            text_content = text_content.replace(placeholder, str(value))
            subject = subject.replace(placeholder, str(value))
    
    # Get user email for From address
    # Prefer user from request_obj if available, otherwise use campaign user
    if request_obj and request_obj.user:
        user_email = request_obj.user.email
        user = request_obj.user
    else:
        user_email = email.campaign.user.email
        user = email.campaign.user
    
    # Check if user has valid SPF record
    user_profile, _ = UserProfile.objects.get_or_create(user=user)
    has_valid_spf = user_profile.spf_verified
    
    # Create and send email
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=user_email,
        to=[subscriber_email]
    )
    # Only set Sender header if user doesn't have valid SPF record
    if not has_valid_spf:
        msg.extra_headers['Sender'] = settings.DEFAULT_FROM_EMAIL
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send()
        
        # Record the event
        EmailEvent.objects.create(
            email=email,
            subscriber_email=subscriber_email,
            event_type='sent'
        )
        
        # Update campaign metrics
        campaign = email.campaign
        campaign.sent_count += 1
        campaign.save(update_fields=['sent_count'])
        
        # Update send request status
        if request_obj:
            request_obj.status = 'sent'
            request_obj.error_message = ''
            request_obj.sent_at = timezone.now()
            request_obj.save(update_fields=['status', 'error_message', 'sent_at', 'updated_at'])
        
        logger.info(f"Sent single email '{subject}' to {subscriber_email}")
    except Exception as e:
        logger.error(f"Error sending single email to {subscriber_email}: {str(e)}")
        if request_obj:
            request_obj.status = 'failed'
            request_obj.error_message = str(e)
            request_obj.save(update_fields=['status', 'error_message', 'updated_at'])
        raise


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
    user_profile, created = UserProfile.objects.get_or_create(user=email.campaign.user)
    show_ads = not user_profile.has_verified_promo
    show_unsubscribe = not user_profile.send_without_unsubscribe
    
    # Get site information from request context
    from core.context_processors import site_detection
    # Create a mock request to get site info
    class MockRequest:
        def get_host(self):
            return settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'dripemails.org'
    
    site_info = site_detection(MockRequest())
    site_url = site_info['site_url']
    site_name = site_info['site_name']
    site_logo = site_info['site_logo']
    
    # Tracking pixel for open tracking
    tracking_id = uuid.uuid4()
    tracking_pixel = f'<img src="{site_url}/track/open/{tracking_id}/" width="1" height="1" alt=""/>'
    
    # Generate unsubscribe link
    unsubscribe_link = f"{site_url}/unsubscribe/{subscriber.uuid}/"
    
    # Prepare email with ads and unsubscribe link as needed
    html_content = email.body_html
    text_content = email.body_text
    
    # Add tracking pixel to HTML content
    html_content += tracking_pixel
    
    # Add ads if required
    if show_ads:
        
        ads_html = render_to_string('emails/ad_footer.html', {
            'site_url': site_url,
            'site_name': site_name,
            'site_logo': site_logo,
        })
        ads_text = f"This email was sent using {site_name} - Free email marketing automation\nWant to send emails without this footer? Share about {site_name} and remove this message: {site_url}/promo-verification/"
        html_content += ads_html
        text_content += f"\n\n{ads_text}"
    
    # Add unsubscribe link if required
    if show_unsubscribe:
        unsubscribe_html = f'<p style="font-size: 12px; color: #666; margin-top: 20px;">If you no longer wish to receive these emails, you can <a href="{unsubscribe_link}">unsubscribe here</a>.</p>'
        unsubscribe_text = f"\n\nIf you no longer wish to receive these emails, you can unsubscribe here: {unsubscribe_link}"
        html_content += unsubscribe_html
        text_content += unsubscribe_text
    
    # Get user email for From address
    user_email = email.campaign.user.email
    
    # Check if user has valid SPF record
    user_profile, _ = UserProfile.objects.get_or_create(user=email.campaign.user)
    has_valid_spf = user_profile.spf_verified
    
    # Create and send email
    msg = EmailMultiAlternatives(
        subject=email.subject,
        body=text_content,
        from_email=user_email,
        to=[subscriber.email]
    )
    # Only set Sender header if user doesn't have valid SPF record
    if not has_valid_spf:
        msg.extra_headers['Sender'] = settings.DEFAULT_FROM_EMAIL
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
            # Calculate when to send the next email
            wait_time = timedelta(**{next_email.wait_unit: next_email.wait_time})
            send_campaign_email.apply_async(
                args=[str(next_email.id), str(subscriber.id)],
                countdown=wait_time.total_seconds()
            )
            logger.info(f"Scheduled next email '{next_email.subject}' for {subscriber.email} in {next_email.wait_time} {next_email.wait_unit}")
    
    except Exception as e:
        logger.error(f"Error sending email to {subscriber.email}: {str(e)}")


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


@shared_task
def send_test_email(email_id, test_email, variables=None):
    """Send a test email to a specific address."""
    return _send_test_email_sync(email_id, test_email, variables)


@shared_task
def send_single_email(email_id, subscriber_email, variables=None, request_id=None):
    """Send a single email to a specific address."""
    return _send_single_email_sync(email_id, subscriber_email, variables, request_id=request_id)