from django import template
from campaigns.models import Campaign

register = template.Library()

@register.simple_tag
def get_campaigns_for_lists(lists, user):
    """Get all campaigns for the given lists that belong to the user."""
    campaign_ids = set()
    campaigns = []
    
    for list_obj in lists:
        for campaign in list_obj.campaigns.filter(user=user):
            if campaign.id not in campaign_ids:
                campaign_ids.add(campaign.id)
                campaigns.append(campaign)
    
    return campaigns


@register.filter
def render_email_variables(content, send_request):
    """Replace email template variables with actual values from the send request."""
    if not content:
        return content
    
    # Get variables from send_request
    variables = send_request.variables or {}
    
    # Add sender_email if not already in variables
    if 'sender_email' not in variables:
        if send_request.user:
            variables['sender_email'] = send_request.user.email
        else:
            variables['sender_email'] = send_request.campaign.user.email
    
    # Add subscriber information if not in variables
    if send_request.subscriber:
        if 'first_name' not in variables:
            variables['first_name'] = send_request.subscriber.first_name or ''
        if 'last_name' not in variables:
            variables['last_name'] = send_request.subscriber.last_name or ''
        if 'full_name' not in variables:
            full_name = f"{send_request.subscriber.first_name or ''} {send_request.subscriber.last_name or ''}".strip()
            variables['full_name'] = full_name or send_request.subscriber.email
        if 'email' not in variables:
            variables['email'] = send_request.subscriber.email
    else:
        # Use subscriber_email if no subscriber object
        if 'email' not in variables:
            variables['email'] = send_request.subscriber_email
    
    # Replace variables in content
    rendered_content = content
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        rendered_content = rendered_content.replace(placeholder, str(value))
    
    return rendered_content
