"""
Custom template tags and filters for portal app.

Story 4.2: Article Search Functionality - highlight_search filter.
"""

import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="highlight_search")
def highlight_search(text, query):
    """
    Highlight search term in text by wrapping matches in <mark> tags.

    Case-insensitive. HTML-escapes input before wrapping to prevent XSS.

    Usage: {{ article.title|highlight_search:query }}
    """
    if not query or not text:
        return text or ""

    # Escape HTML first (XSS prevention)
    escaped_text = escape(str(text))
    escaped_query = escape(str(query))

    # Case-insensitive replacement with <mark> wrapper
    pattern = re.compile(re.escape(escaped_query), re.IGNORECASE)
    highlighted = pattern.sub(
        lambda m: f"<mark>{m.group()}</mark>",
        escaped_text,
    )
    return mark_safe(highlighted)
