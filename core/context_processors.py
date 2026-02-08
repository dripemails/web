from datetime import datetime

def current_year(request):
    """Add current year to template context."""
    return {'current_year': datetime.now().year}


def site_detection(request):
    """Detect the site from the request URL and add site information to context."""
    host = request.get_host()
    
    # Determine site based on domain
    if 'dripemail.org' in host:
        site_domain = 'dripemail.org'
        site_url = 'https://dripemail.org'
        site_name = 'DripEmail.org'
        logo_file = 'logo_dripemail.org.png'
    else:
        # Default to dripemails.org
        site_domain = 'dripemails.org'
        site_url = 'https://dripemails.org'
        site_name = 'DripEmails.org'
        logo_file = 'logo_dripemails.org.png'
    
    return {
        'site_domain': site_domain,
        'site_url': site_url,
        'site_name': site_name,
        'site_logo': logo_file,
    }


def agent(request):
    """Add ?agent= query param to context (e.g. agent=mobile for agent-specific templates)."""
    return {'agent': (request.GET.get('agent') or '').strip()} 