from datetime import datetime

from django.conf import settings


def current_year(request):
    """Add current year to template context."""
    return {'current_year': datetime.now().year}


def _normalize_host(host):
    """Strip port and lowercase for comparison."""
    return (host or '').split(':')[0].lower()


def _resolve_site_for_request(request):
    """
    Pick the django.contrib.sites Site row that matches this request's host.
    Falls back to get_current() (SITE_ID) when no row matches.
    """
    from django.contrib.sites.models import Site

    host = _normalize_host(request.get_host())
    if not host:
        return Site.objects.get_current()

    site = Site.objects.filter(domain__iexact=host).first()
    if site:
        return site

    for site in Site.objects.exclude(domain=''):
        d = _normalize_host(site.domain)
        if not d:
            continue
        if host == d or host == f'www.{d}' or d == f'www.{host}':
            return site
        if host.endswith('.' + d) and len(host) > len(d) + 1:
            return site

    return Site.objects.get_current()


def site_detection(request):
    """Add site info from the database Site model (matched to request host when possible)."""
    site = _resolve_site_for_request(request)
    domain = site.domain.split(':')[0]
    site_domain = domain
    site_name = site.name

    use_https = getattr(settings, 'USE_HTTPS', None)
    if use_https is None:
        use_https = not getattr(settings, 'DEBUG', True)

    # Some call sites pass a lightweight MockRequest (only get_host()).
    # Use request.is_secure() only when it exists.
    is_secure_fn = getattr(request, 'is_secure', None)
    is_secure = is_secure_fn() if callable(is_secure_fn) else False
    scheme = 'https' if use_https or is_secure else 'http'
    site_url = f'{scheme}://{domain}'

    # Static asset follows domain; local dev (e.g. Site.domain localhost:8000) uses production logo asset
    logo_domain = domain.lower()
    if _normalize_host(site.domain) == 'localhost':
        logo_domain = 'dripemails.org'
    site_logo = f'logo_{logo_domain}.png'

    return {
        'site_domain': site_domain,
        'site_url': site_url,
        'site_name': site_name,
        'site_logo': site_logo,
    }


def agent(request):
    """Add ?agent= query param to context (e.g. agent=mobile for agent-specific templates)."""
    return {'agent': (request.GET.get('agent') or '').strip()}
