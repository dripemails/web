"""
SEO template tags for generating comprehensive meta tags.
"""
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

# Comprehensive keyword list for drip emails and email marketing
EMAIL_MARKETING_KEYWORDS = [
    # Primary keywords
    "drip email",
    "drip emails",
    "drip email marketing",
    "drip email campaign",
    "drip email campaigns",
    "email drip campaign",
    "email drip campaigns",
    "automated email",
    "automated emails",
    "automated email marketing",
    "email automation",
    "email marketing automation",
    "email marketing",
    "email campaigns",
    "email campaign",
    "email marketing software",
    "email marketing platform",
    "email marketing tool",
    "email marketing tools",
    # Variations and synonyms
    "drip marketing",
    "email sequence",
    "email sequences",
    "email series",
    "automated email sequence",
    "email nurture sequence",
    "lead nurturing",
    "email nurture",
    "nurture campaign",
    "nurture campaigns",
    "welcome series",
    "onboarding emails",
    "email onboarding",
    "customer onboarding",
    # Technical terms
    "email drip software",
    "drip email software",
    "email automation software",
    "email marketing automation software",
    "email marketing platform",
    "email service provider",
    "ESP",
    "email marketing service",
    "bulk email",
    "bulk email service",
    "transactional emails",
    "marketing emails",
    # Action-based keywords
    "send drip emails",
    "create drip campaign",
    "email marketing campaign",
    "email marketing strategy",
    "email marketing solution",
    "email marketing services",
    "email marketing agency",
    "email marketing company",
    # Feature-focused keywords
    "email scheduling",
    "schedule emails",
    "scheduled emails",
    "email analytics",
    "email tracking",
    "email open rates",
    "email click rates",
    "email subscriber management",
    "subscriber management",
    "email list management",
    "email segmentation",
    "email personalization",
    "personalized emails",
    # Industry-specific
    "SaaS email marketing",
    "small business email marketing",
    "startup email marketing",
    "ecommerce email marketing",
    "B2B email marketing",
    "B2C email marketing",
    # Free/affordable keywords
    "free email marketing",
    "free email marketing software",
    "free drip email software",
    "affordable email marketing",
    "cheap email marketing",
    "email marketing free",
    # Comparison keywords
    "best email marketing software",
    "best drip email software",
    "email marketing alternative",
    "mailchimp alternative",
    "constant contact alternative",
    "sendinblue alternative",
    "getresponse alternative",
    # Long-tail keywords
    "how to create drip email campaign",
    "how to set up email automation",
    "email marketing for beginners",
    "email marketing best practices",
    "email marketing tips",
    "improve email open rates",
    "increase email engagement",
    "email marketing ROI",
    # Related concepts
    "newsletter",
    "newsletters",
    "email newsletter",
    "email newsletters",
    "newsletter marketing",
    "email marketing list",
    "email list",
    "subscriber list",
    "email subscribers",
    "email audience",
]

@register.simple_tag
def get_seo_keywords(page_keywords=None):
    """
    Generate SEO keywords string. Can be customized per page.
    
    Args:
        page_keywords: Optional list of page-specific keywords to add
    
    Returns:
        Comma-separated keyword string
    """
    keywords = EMAIL_MARKETING_KEYWORDS.copy()
    if page_keywords:
        if isinstance(page_keywords, str):
            keywords.extend([k.strip() for k in page_keywords.split(',')])
        else:
            keywords.extend(page_keywords)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower not in seen:
            seen.add(keyword_lower)
            unique_keywords.append(keyword)
    
    return ', '.join(unique_keywords[:50])  # Limit to 50 keywords

@register.simple_tag
def get_site_url():
    """Get the site URL from settings."""
    from django.contrib.sites.models import Site
    try:
        current_site = Site.objects.get_current()
        protocol = 'https' if getattr(settings, 'USE_HTTPS', False) else 'http'
        return f"{protocol}://{current_site.domain}"
    except:
        return getattr(settings, 'SITE_URL', 'https://dripemails.org')

