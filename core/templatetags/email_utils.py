from django import template
from django.utils import timezone
from django.utils.dateformat import format
import pytz

register = template.Library()


@register.filter
def email_domain(email):
    """Extract the domain from an email address."""
    if not email or '@' not in str(email):
        return None
    return str(email).split('@')[1]


@register.filter
def timezone_format(dt, user_timezone_str='UTC'):
    """
    Convert a datetime to the user's preferred timezone and format it.
    
    Usage: {{ datetime|timezone_format:user_timezone }}
    Format: "M d, Y g:i A" (e.g., "Jan 18, 2026 2:08 PM")
    """
    if not dt:
        return ''
    
    try:
        # Parse the user's timezone
        user_tz = pytz.timezone(user_timezone_str)
    except (pytz.UnknownTimeZoneError, AttributeError):
        # Fallback to UTC if timezone is invalid
        user_tz = pytz.UTC
    
    # Convert datetime to user's timezone
    if timezone.is_naive(dt):
        # If naive, assume it's in UTC and make it aware
        dt = timezone.make_aware(dt, pytz.UTC)
    
    # Convert to user's timezone
    local_dt = timezone.localtime(dt, user_tz)
    
    # Format: "M d, Y g:i A" (e.g., "Jan 18, 2026 2:08 PM")
    return format(local_dt, 'M d, Y g:i A')

