"""
Utilities for collecting IPv4 and IPv6 addresses from HTTP requests.
"""
import ipaddress


def get_client_ips(request):
    """
    Extract client IPv4 and/or IPv6 from request.

    Uses X-Forwarded-For (first/client address) when behind a proxy,
    otherwise REMOTE_ADDR. A single request typically has one or the other.

    Returns:
        tuple: (ipv4_str or None, ipv6_str or None)
    """
    if request is None:
        return None, None
    raw = None
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        # "client, proxy1, proxy2" -> first is client
        raw = xff.split(',')[0].strip()
    if not raw:
        raw = request.META.get('REMOTE_ADDR')
    if not raw:
        return None, None
    try:
        addr = ipaddress.ip_address(raw)
    except ValueError:
        return None, None
    if isinstance(addr, ipaddress.IPv4Address):
        return str(addr), None
    return None, str(addr)
