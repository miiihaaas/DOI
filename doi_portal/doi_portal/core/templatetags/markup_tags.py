"""Template tags for markup rendering in Django templates."""

from django import template
from django.utils.safestring import mark_safe

from doi_portal.core.markup import markup_to_html, strip_markup as _strip_markup

register = template.Library()


@register.filter(name="render_markup")
def render_markup(value):
    """Convert markup to HTML and mark as safe."""
    return mark_safe(markup_to_html(value))


@register.filter(name="strip_markup")
def strip_markup_filter(value):
    """Remove markup delimiters, return plain text."""
    return _strip_markup(value)
