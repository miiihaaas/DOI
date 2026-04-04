"""
Template tags and filters for contextual terminology.

Usage:
    {% load terminology %}
    {{ "article_plural"|term:pub_type }}
    {% article_count_label issue.article_count pub_type %}
"""

from django import template

from doi_portal.core.terminology import get_article_count_label, get_term

register = template.Library()


@register.filter
def term(term_key, publication_type):
    """Filter: {{ "article"|term:pub_type }}"""
    return get_term(term_key, publication_type)


@register.simple_tag
def article_count_label(count, publication_type):
    """Tag: {% article_count_label issue.article_count pub_type %}"""
    return get_article_count_label(count, publication_type)
