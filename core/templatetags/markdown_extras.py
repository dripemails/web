from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def markdownify(text):
    """Convert markdown text to HTML."""
    try:
        import markdown
        
        md = markdown.Markdown(extensions=[
            'fenced_code',
            'tables', 
            'toc',
            'nl2br',  # Convert newlines to <br>
            'codehilite',  # Syntax highlighting for code blocks
        ])
        html = md.convert(str(text))
        return mark_safe(html)
    except ImportError:
        # If markdown is not installed, return text as-is with basic formatting
        # This at least preserves spacing
        return mark_safe(str(text).replace('\n', '<br>\n'))

