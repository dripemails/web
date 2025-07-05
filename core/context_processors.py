from datetime import datetime

def current_year(request):
    """Add current year to template context."""
    return {'current_year': datetime.now().year} 