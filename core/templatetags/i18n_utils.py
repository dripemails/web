from django import template
from django.conf import settings
from django.urls import resolve, reverse
from django.utils.translation import get_language

register = template.Library()

@register.simple_tag(takes_context=True)
def get_path_without_language(context):
    """
    Get the current path without the language prefix.
    This is useful for language switching forms.
    """
    request = context.get('request')
    if not request:
        return '/'
    
    path = request.path
    
    # Remove language prefix if it exists
    for lang_code, lang_name in settings.LANGUAGES:
        if path.startswith(f'/{lang_code}/'):
            path = path[len(f'/{lang_code}/'):]
            break
        elif path == f'/{lang_code}':
            path = '/'
            break
    
    # Ensure path starts with /
    if not path.startswith('/'):
        path = '/' + path
    
    return path 