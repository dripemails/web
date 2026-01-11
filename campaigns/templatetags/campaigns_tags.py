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

