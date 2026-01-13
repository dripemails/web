from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from datetime import timedelta
import logging
import uuid
import sys
import re
from analytics.models import UserProfile

logger = logging.getLogger(__name__)


def _html_to_plain_text(html_content):
    """Convert HTML to plain text, preserving URLs from links."""
    if not html_content:
        return ""
    
    # Replace <a href="URL">text</a> with "text (URL)" if URL is different from text
    def replace_link(match):
        url = match.group(1)
        text = match.group(2)
        # If the link text is different from URL or doesn't contain the full URL, append the URL
        if url.lower() not in text.lower() or not text.startswith('http'):
            return f"{text} ({url})"
        return text
    
    # Pattern to match <a> tags with href
    link_pattern = re.compile(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
    html_content = link_pattern.sub(replace_link, html_content)
    
    # Replace <br> and <br/> with newlines
    html_content = re.sub(r'<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)
    
    # Replace </p>, </div>, </h1-6> with double newlines
    html_content = re.sub(r'</(p|div|h[1-6]|li)>', '\n\n', html_content, flags=re.IGNORECASE)
    
    # Replace <li> with bullet point
    html_content = re.sub(r'<li[^>]*>', '\n• ', html_content, flags=re.IGNORECASE)
    
    # Remove all other HTML tags
    html_content = re.sub(r'<[^>]+>', '', html_content)
    
    # Decode HTML entities
    html_content = html_content.replace('&nbsp;', ' ')
    html_content = html_content.replace('&amp;', '&')
    html_content = html_content.replace('&lt;', '<')
    html_content = html_content.replace('&gt;', '>')
    html_content = html_content.replace('&quot;', '"')
    
    # Clean up extra whitespace and newlines
    html_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', html_content)
    html_content = re.sub(r'[ \t]+', ' ', html_content)
    
    return html_content.strip()


def _replace_hr_with_separator(html_content, tracking_id, subscriber_email, base_url=None):
    """Replace <hr/> tags with decorative separator image that also tracks opens."""
    from django.conf import settings
    from core.context_processors import site_detection
    import re
    
    # Get base URL - prefer provided base_url, then try site detection, then DEFAULT_URL, then fallback
    if base_url:
        site_base_url = base_url
    else:
        # Try to detect site from settings
        try:
            class MockRequest:
                def get_host(self):
                    return settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'dripemails.org'
            
            site_info = site_detection(MockRequest())
            site_base_url = site_info['site_url']
        except Exception:
            # Fall back to DEFAULT_URL or SITE_URL
            site_base_url = getattr(settings, 'DEFAULT_URL', None) or getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    # Ensure base_url doesn't end with a slash (we'll add it in the path)
    site_base_url = site_base_url.rstrip('/')
    
    # URL-encode the email and include it in the path instead of query string
    from urllib.parse import quote
    encoded_email = quote(subscriber_email, safe='')
    # Clean URL that doesn't mention tracking or pixel - looks like a regular image
    separator_url = f"{site_base_url}/analytics/message_split.gif?t={tracking_id}&e={encoded_email}"
    
    # Create decorative separator image (looks like an HR line, not a tracking pixel)
    # This is a visible separator that also tracks opens
    separator_img = f'<img src="{separator_url}" alt="" style="display:block; width:100%; height:2px; border:none; margin:20px 0; background:linear-gradient(to right, transparent, #e2e8f0, transparent);" />'
    
    # Replace all <hr> and <hr/> tags with the separator
    # Match various HR tag formats: <hr>, <hr/>, <hr />, <HR>, etc.
    hr_pattern = re.compile(r'<hr\s*/?>', re.IGNORECASE)
    html_content = hr_pattern.sub(separator_img, html_content)
    
    # If no HR tags were found, inject separator before closing body tag for tracking
    if not hr_pattern.search(html_content):
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{separator_img}</body>')
        else:
            html_content += separator_img
    
    return html_content


def _wrap_links_with_tracking(html_content, tracking_id, subscriber_email, base_url=None):
    """Wrap all links in HTML content with tracking redirects."""
    from django.conf import settings
    from core.context_processors import site_detection
    import re
    from urllib.parse import quote
    
    # Get base URL - prefer provided base_url, then try site detection, then DEFAULT_URL, then fallback
    if base_url:
        tracking_base_url = base_url
    else:
        # Try to detect site from settings
        try:
            class MockRequest:
                def get_host(self):
                    return settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'dripemails.org'
            
            site_info = site_detection(MockRequest())
            tracking_base_url = site_info['site_url']
        except Exception:
            # Fall back to DEFAULT_URL or SITE_URL
            tracking_base_url = getattr(settings, 'DEFAULT_URL', None) or getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    # Ensure base_url doesn't end with a slash (we'll add it in the path)
    tracking_base_url = tracking_base_url.rstrip('/')
    
    # Pattern to find <a> tags with href attributes
    link_pattern = re.compile(r'<a([^>]*?)href=["\']([^"\'>]+)["\']([^>]*?)>', re.IGNORECASE)
    
    def replace_link(match):
        before_href = match.group(1)
        original_url = match.group(2)
        after_href = match.group(3)
        
        # Skip if it's already a tracking link, mailto, or anchor link
        if original_url.startswith(('#', 'mailto:', tracking_base_url)):
            return match.group(0)
        
        # Create tracking URL
        tracking_url = f"{tracking_base_url}/analytics/track/click/{tracking_id}/?email={subscriber_email}&url={quote(original_url)}"
        
        return f'<a{before_href}href="{tracking_url}"{after_href}>'
    
    return link_pattern.sub(replace_link, html_content)


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
        error_msg = f"Email {email_id} not found"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Replace variables in content
    html_content = email.body_html or ""
    text_content = email.body_text or ""
    subject = email.subject or "Test Email"
    
    if variables:
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            html_content = html_content.replace(placeholder, str(value))
            text_content = text_content.replace(placeholder, str(value))
            subject = subject.replace(placeholder, str(value))
    
    # Ensure we have at least some content
    if not html_content and not text_content:
        error_msg = "Email has no content (both body_html and body_text are empty)"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # If we have HTML content but no text content, convert HTML to plain text
    if html_content and not text_content:
        text_content = _html_to_plain_text(html_content)
    
    # Create and send email
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content or "This is a test email.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[test_email]
        )
        if html_content:
            msg.attach_alternative(html_content, "text/html")
        
        msg.send()
        logger.info(f"Sent test email '{subject}' to {test_email}")
    except Exception as e:
        error_msg = f"Error sending test email to {test_email}: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


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
        logger.info(f"Sending email {email_id} for campaign: {email.campaign.id} - {email.campaign.name}")
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
    
    # Create the sent event first to get tracking ID
    sent_event = EmailEvent.objects.create(
        email=email,
        subscriber_email=subscriber_email,
        event_type='sent'
    )
    tracking_id = str(sent_event.id)
    logger.info(f"Created EmailEvent {tracking_id} for email {email.id}, campaign {email.campaign.id}, subscriber {subscriber_email}")
    
    # Get site information for tracking URLs
    from core.context_processors import site_detection
    class MockRequest:
        def get_host(self):
            return settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'dripemails.org'
    
    site_info = site_detection(MockRequest())
    site_url = site_info['site_url']
    
    # Replace HR tags with separator image and wrap links
    html_content = _replace_hr_with_separator(html_content, tracking_id, subscriber_email, base_url=site_url)
    html_content = _wrap_links_with_tracking(html_content, tracking_id, subscriber_email, base_url=site_url)
    
    # If we have HTML content but no text content, convert HTML to plain text
    if html_content and not text_content:
        text_content = _html_to_plain_text(html_content)
    
    # Add email footer if one is assigned
    if email.footer:
        footer_html = email.footer.html_content
        # Replace variables in footer if needed
        if variables:
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                footer_html = footer_html.replace(placeholder, str(value))
        html_content += footer_html
        # Convert footer HTML to text for plain text version using proper HTML to text conversion
        footer_text = _html_to_plain_text(footer_html)
        if footer_text:
            text_content += f"\n\n{footer_text}"
    
    # Get user email and name for From address
    # Prefer user from request_obj if available, otherwise use campaign user
    if request_obj and request_obj.user:
        user_email = request_obj.user.email
        user = request_obj.user
    else:
        user_email = email.campaign.user.email
        user = email.campaign.user
    
    # Get user profile for full_name and SPF
    user_profile, _ = UserProfile.objects.get_or_create(user=user)
    has_valid_spf = user_profile.spf_verified
    full_name = user_profile.full_name or ''
    
    # Format From header: "Full Name <email@example.com>" or just email if no name
    if full_name:
        from_email_header = f"{full_name} <{user_email}>"
    else:
        from_email_header = user_email
    show_ads = not user_profile.has_verified_promo
    show_unsubscribe = not user_profile.send_without_unsubscribe
    
    # Get site information for unsubscribe links and tracking (already done above, reuse)
    site_name = site_info['site_name']
    site_logo = site_info['site_logo']
    
    # Get subscriber UUID for unsubscribe link
    subscriber_uuid = None
    if request_obj and request_obj.subscriber:
        subscriber_uuid = request_obj.subscriber.uuid
    else:
        # Try to find subscriber by email
        from subscribers.models import Subscriber
        try:
            subscriber = Subscriber.objects.filter(email=subscriber_email).first()
            if subscriber:
                subscriber_uuid = subscriber.uuid
        except Exception:
            pass
    
    # Add unsubscribe link to email content if enabled
    if show_unsubscribe and subscriber_uuid:
        unsubscribe_url = f"{site_url}/unsubscribe/{subscriber_uuid}/"
        
        # Format user address for footer (required by CAN-SPAM, GDPR, etc.)
        address_lines = []
        # Add full name first if available
        if user_profile.full_name:
            address_lines.append(user_profile.full_name)
        if user_profile.address_line1:
            address_lines.append(user_profile.address_line1)
        if user_profile.address_line2:
            address_lines.append(user_profile.address_line2)
        city_state = []
        if user_profile.city:
            city_state.append(user_profile.city)
        if user_profile.state:
            city_state.append(user_profile.state)
        if city_state:
            address_lines.append(', '.join(city_state))
        postal_country = []
        if user_profile.postal_code:
            postal_country.append(user_profile.postal_code)
        if user_profile.country:
            postal_country.append(user_profile.country)
        if postal_country:
            address_lines.append(' '.join(postal_country))
        
        address_html = ''
        address_text = ''
        if address_lines:
            address_html = '<p style="font-size: 11px; color: #999; margin-top: 10px; line-height: 1.4;">' + '<br>'.join(address_lines) + '</p>'
            address_text = '\n' + '\n'.join(address_lines)
        
        # Add to HTML content with separator
        unsubscribe_html = f'<hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;"><p style="font-size: 12px; color: #666; margin-top: 20px;">If you no longer wish to receive these emails, you can <a href="{unsubscribe_url}">unsubscribe here</a>.</p>{address_html}'
        html_content += unsubscribe_html
        # Add to text content with separator
        unsubscribe_text = f"\n\n--\n\nIf you no longer wish to receive these emails, you can unsubscribe here: {unsubscribe_url}{address_text}"
        text_content += unsubscribe_text
    
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
    
    # Create and send email
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email_header,
        to=[subscriber_email],
        bcc=[user_email]  # BCC the user so they can see emails being sent
    )
    # Only set Sender header if user doesn't have valid SPF record
    if not has_valid_spf:
        msg.extra_headers['Sender'] = settings.DEFAULT_FROM_EMAIL
    
    # Add List-Unsubscribe headers if unsubscribe is enabled
    if show_unsubscribe and subscriber_uuid:
        unsubscribe_url = f"{site_url}/unsubscribe/{subscriber_uuid}/"
        msg.extra_headers['List-Unsubscribe'] = f"<{unsubscribe_url}>"
        msg.extra_headers['List-Unsubscribe-Post'] = "List-Unsubscribe=One-Click"
    
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send()
        
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
        
        # Schedule the next email in the campaign sequence
        try:
            schedule_next_email_in_sequence(email, request_obj, subscriber_email, variables)
        except Exception as next_email_error:
            # Log but don't fail the current email send if scheduling next email fails
            logger.warning(f"Failed to schedule next email in sequence: {str(next_email_error)}")
    except Exception as e:
        logger.error(f"Error sending single email to {subscriber_email}: {str(e)}")
        if request_obj:
            request_obj.status = 'failed'
            request_obj.error_message = str(e)
            request_obj.save(update_fields=['status', 'error_message', 'updated_at'])
        raise


def schedule_next_email_in_sequence(current_email, request_obj, subscriber_email, variables):
    """
    Schedule the next email in the campaign sequence after an email is sent.
    
    Args:
        current_email: The Email object that was just sent
        request_obj: The EmailSendRequest object for the email that was sent
        subscriber_email: The email address of the subscriber
        variables: Variables dictionary for personalization
    """
    from .models import Email, EmailSendRequest
    from subscribers.models import Subscriber
    from datetime import timedelta
    
    # Get the campaign and current email order
    campaign = current_email.campaign
    
    # Find the next email in the sequence (by order)
    next_email = Email.objects.filter(
        campaign=campaign,
        order__gt=current_email.order
    ).order_by('order').first()
    
    if not next_email:
        logger.debug(f"No next email found in campaign '{campaign.name}' after email order {current_email.order}")
        return
    
    # Get the subscriber object
    subscriber = None
    if request_obj and request_obj.subscriber:
        subscriber = request_obj.subscriber
    else:
        # Try to find subscriber by email
        try:
            subscriber = Subscriber.objects.filter(email=subscriber_email).first()
        except Exception:
            pass
    
    if not subscriber:
        logger.warning(f"Could not find subscriber for email {subscriber_email} to schedule next email")
        return
    
    # Calculate scheduled time based on next email's wait_time and wait_unit
    # Use 0 as default if wait_time is None, but allow 0 to mean immediate sending
    wait_time = next_email.wait_time if next_email.wait_time is not None else 0
    wait_unit = next_email.wait_unit or 'days'
    
    send_delay = timedelta(0)
    if wait_time > 0:
        if wait_unit == 'seconds':
            send_delay = timedelta(seconds=wait_time)
        elif wait_unit == 'minutes':
            send_delay = timedelta(minutes=wait_time)
        elif wait_unit == 'hours':
            send_delay = timedelta(hours=wait_time)
        elif wait_unit == 'days':
            send_delay = timedelta(days=wait_time)
        elif wait_unit == 'weeks':
            send_delay = timedelta(weeks=wait_time)
        elif wait_unit == 'months':
            send_delay = timedelta(days=wait_time * 30)
    
    scheduled_for = timezone.now() + send_delay
    
    # Get user from request_obj or campaign
    user = request_obj.user if request_obj else campaign.user
    
    # Create EmailSendRequest for the next email
    next_send_request = EmailSendRequest.objects.create(
        user=user,
        campaign=campaign,
        email=next_email,
        subscriber=subscriber,
        subscriber_email=subscriber_email,
        variables=variables or {},
        scheduled_for=scheduled_for,
        status='pending'
    )
    
    logger.info(f"Scheduled next email '{next_email.subject}' (order {next_email.order}) in campaign '{campaign.name}' "
                f"for {subscriber_email} to be sent at {scheduled_for}")


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
            # Send the first email immediately
            send_campaign_email(
                email_id=str(first_email.id),
                subscriber_id=str(subscriber.id)
            )
    
    logger.info(f"Scheduled first email of campaign {campaign.name} for {subscribers.count()} subscribers")


def send_campaign_email(email_id, subscriber_id, variables=None):
    """Send a specific campaign email to a specific subscriber."""
    from .models import Email, EmailEvent
    from subscribers.models import Subscriber
    
    try:
        email = Email.objects.select_related('campaign').get(id=email_id)
    except Email.DoesNotExist:
        logger.error(f"Email {email_id} not found")
        return
    
    try:
        subscriber = Subscriber.objects.get(id=subscriber_id, is_active=True)
    except Subscriber.DoesNotExist:
        logger.error(f"Subscriber {subscriber_id} not found or not active")
        return
    
    # Make sure the campaign is still active
    if not email.campaign.is_active:
        logger.info(f"Campaign {email.campaign.name} is no longer active. Skipping email.")
        return
    
    # Check if subscriber is still in the list and active
    if not subscriber.is_active or subscriber not in email.campaign.subscriber_list.subscribers.all():
        logger.info(f"Subscriber {subscriber.email} is no longer active or in the list. Skipping email.")
        return
    
    # Build variables from subscriber if not provided
    if variables is None:
        variables = {}
    
    # Always include subscriber data in variables (subscriber data takes precedence)
    if not variables.get('first_name') and subscriber.first_name:
        variables['first_name'] = subscriber.first_name
    if not variables.get('last_name') and subscriber.last_name:
        variables['last_name'] = subscriber.last_name
    if not variables.get('email'):
        variables['email'] = subscriber.email
    
    # Get user profile for ad settings
    user_profile, created = UserProfile.objects.get_or_create(user=email.campaign.user)
    show_ads = not user_profile.has_verified_promo
    show_unsubscribe = not user_profile.send_without_unsubscribe
    
    # Create the sent event first to get tracking ID
    sent_event = EmailEvent.objects.create(
        email=email,
        subscriber_email=subscriber.email,
        event_type='sent'
    )
    tracking_id = str(sent_event.id)
    
    # Get site information for tracking and unsubscribe links
    from core.context_processors import site_detection
    class MockRequest:
        def get_host(self):
            return settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'dripemails.org'
    
    site_info = site_detection(MockRequest())
    site_url = site_info['site_url']
    site_name = site_info['site_name']
    site_logo = site_info['site_logo']
    
    # Generate URLs (clean, no mention of tracking or pixel)
    from urllib.parse import quote
    encoded_email = quote(subscriber.email, safe='')
    unsubscribe_link = f"{site_url}/unsubscribe/{subscriber.uuid}/"
    
    # Prepare email with tracking and replace variables
    html_content = email.body_html
    text_content = email.body_text
    subject = email.subject
    
    # Replace variables in content
    if variables:
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            html_content = html_content.replace(placeholder, str(value)) if html_content else html_content
            text_content = text_content.replace(placeholder, str(value)) if text_content else text_content
            subject = subject.replace(placeholder, str(value)) if subject else subject
    
    # Replace HR tags with separator image and wrap all links with tracking
    html_content = _replace_hr_with_separator(html_content, tracking_id, subscriber.email, base_url=site_url)
    html_content = _wrap_links_with_tracking(html_content, tracking_id, subscriber.email, base_url=site_url)
    
    # Add email footer if one is assigned
    if email.footer:
        footer_html = email.footer.html_content
        # Replace variables in footer if needed
        if variables:
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                footer_html = footer_html.replace(placeholder, str(value))
        html_content += footer_html
        # Convert footer HTML to text for plain text version using proper HTML to text conversion
        footer_text = _html_to_plain_text(footer_html)
        if footer_text:
            text_content += f"\n\n{footer_text}"
    
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
        # Format user address for footer (required by CAN-SPAM, GDPR, etc.)
        address_lines = []
        # Add full name first if available
        if user_profile.full_name:
            address_lines.append(user_profile.full_name)
        if user_profile.address_line1:
            address_lines.append(user_profile.address_line1)
        if user_profile.address_line2:
            address_lines.append(user_profile.address_line2)
        city_state = []
        if user_profile.city:
            city_state.append(user_profile.city)
        if user_profile.state:
            city_state.append(user_profile.state)
        if city_state:
            address_lines.append(', '.join(city_state))
        postal_country = []
        if user_profile.postal_code:
            postal_country.append(user_profile.postal_code)
        if user_profile.country:
            postal_country.append(user_profile.country)
        if postal_country:
            address_lines.append(' '.join(postal_country))
        
        address_html = ''
        address_text = ''
        if address_lines:
            address_html = '<p style="font-size: 11px; color: #999; margin-top: 10px; line-height: 1.4;">' + '<br>'.join(address_lines) + '</p>'
            address_text = '\n' + '\n'.join(address_lines)
        
        unsubscribe_html = f'<hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;"><p style="font-size: 12px; color: #666; margin-top: 20px;">If you no longer wish to receive these emails, you can <a href="{unsubscribe_link}">unsubscribe here</a>.</p>{address_html}'
        unsubscribe_text = f"\n\n--\n\nIf you no longer wish to receive these emails, you can unsubscribe here: {unsubscribe_link}{address_text}"
        html_content += unsubscribe_html
        text_content += unsubscribe_text
    
    # Get user email and name for From address
    user_email = email.campaign.user.email
    
    # Check if user has valid SPF record
    user_profile, _ = UserProfile.objects.get_or_create(user=email.campaign.user)
    has_valid_spf = user_profile.spf_verified
    
    # Get full_name for From header
    full_name = user_profile.full_name or ''
    
    # Format From header: "Full Name <email@example.com>" or just email if no name
    if full_name:
        from_email_header = f"{full_name} <{user_email}>"
    else:
        from_email_header = user_email
    
    # Create and send email
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email_header,
        to=[subscriber.email],
        bcc=[user_email]  # BCC the user so they can see emails being sent
    )
    # Only set Sender header if user doesn't have valid SPF record
    if not has_valid_spf:
        msg.extra_headers['Sender'] = settings.DEFAULT_FROM_EMAIL
    
    # Add List-Unsubscribe headers if unsubscribe is enabled
    if show_unsubscribe:
        msg.extra_headers['List-Unsubscribe'] = f"<{unsubscribe_link}>"
        msg.extra_headers['List-Unsubscribe-Post'] = "List-Unsubscribe=One-Click"
    
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send()
        
        # Update campaign metrics (event was already created before sending)
        campaign = email.campaign
        campaign.sent_count += 1
        campaign.save(update_fields=['sent_count'])
        
        logger.info(f"Sent email '{subject}' to {subscriber.email}")
        
        # Schedule the next email in sequence if one exists
        next_email = email.campaign.emails.filter(order__gt=email.order).order_by('order').first()
        if next_email:
            # Calculate when to send the next email
            wait_time_val = next_email.wait_time or 0
            wait_unit_val = next_email.wait_unit or 'days'
            
            send_delay = timedelta(0)
            if wait_unit_val == 'seconds':
                send_delay = timedelta(seconds=wait_time_val)
            elif wait_unit_val == 'minutes':
                send_delay = timedelta(minutes=wait_time_val)
            elif wait_unit_val == 'hours':
                send_delay = timedelta(hours=wait_time_val)
            elif wait_unit_val == 'days':
                send_delay = timedelta(days=wait_time_val)
            elif wait_unit_val == 'weeks':
                send_delay = timedelta(weeks=wait_time_val)
            elif wait_unit_val == 'months':
                send_delay = timedelta(days=wait_time_val * 30)
            
            scheduled_for = timezone.now() + send_delay
            
            # Use EmailSendRequest to schedule the next email
            from .models import EmailSendRequest
            EmailSendRequest.objects.create(
                user=email.campaign.user,
                campaign=email.campaign,
                email=next_email,
                subscriber=subscriber,
                subscriber_email=subscriber.email,
                variables=variables or {},
                scheduled_for=scheduled_for,
                status='pending'
            )
            logger.info(f"Scheduled next email '{next_email.subject}' for {subscriber.email} in {next_email.wait_time} {next_email.wait_unit}")
    
    except Exception as e:
        logger.error(f"Error sending email to {subscriber.email}: {str(e)}")


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
        
        # Check if open event already exists to avoid duplicates
        existing_open = EmailEvent.objects.filter(
            email=sent_event.email,
            subscriber_email=subscriber_email,
            event_type='opened'
        ).exists()
        
        if not existing_open:
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
        else:
            logger.debug(f"Open event already exists for {subscriber_email}, skipping duplicate")
    
    except EmailEvent.DoesNotExist:
        logger.error(f"No matching sent event found for tracking ID {tracking_id}")
    except Exception as e:
        logger.error(f"Failed to process email open: {str(e)}")


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
        
        # Always create click events (even if duplicate link clicks) for accurate tracking
        EmailEvent.objects.create(
            email=sent_event.email,
            subscriber_email=subscriber_email,
            event_type='clicked',
            link_clicked=link_url
        )
        
        # Update campaign metrics (count each click)
        campaign = sent_event.email.campaign
        campaign.click_count += 1
        campaign.save(update_fields=['click_count'])
        
        logger.info(f"Recorded click event for {subscriber_email} on {link_url}")
    
    except EmailEvent.DoesNotExist:
        logger.error(f"No matching sent event found for tracking ID {tracking_id}")
    except Exception as e:
        logger.error(f"Failed to process email click: {str(e)}")


def send_test_email(email_id, test_email, variables=None):
    """Send a test email to a specific address."""
    return _send_test_email_sync(email_id, test_email, variables)


def send_single_email(email_id, subscriber_email, variables=None, request_id=None):
    """Send a single email to a specific address."""
    return _send_single_email_sync(email_id, subscriber_email, variables, request_id=request_id)