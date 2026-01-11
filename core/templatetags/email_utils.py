from django import template

register = template.Library()


@register.filter
def email_domain(email):
    """Extract the domain from an email address."""
    if not email or '@' not in str(email):
        return None
    return str(email).split('@')[1]

