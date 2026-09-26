"""
Custom template tags and filters for portal app.

Story 4.2: Article Search Functionality - highlight_search filter.
"""

import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="issue_label")
def issue_label(issue):
    """
    Generate issue label showing only populated fields.

    Delegates to Issue.label property for single source of truth.

    Usage: {{ issue|issue_label }}
    """
    return issue.label


#: ISO 639-1 (and a few common variants) -> Serbian language names.
LANGUAGE_NAMES = {
    "sr": "Srpski",
    "sr-latn": "Srpski (latinica)",
    "sr-cyrl": "Srpski (ćirilica)",
    "en": "Engleski",
    "de": "Nemački",
    "fr": "Francuski",
    "ru": "Ruski",
    "es": "Španski",
    "it": "Italijanski",
    "hr": "Hrvatski",
    "bs": "Bosanski",
    "sl": "Slovenački",
    "mk": "Makedonski",
    "bg": "Bugarski",
    "hu": "Mađarski",
    "ro": "Rumunski",
    "sq": "Albanski",
    "el": "Grčki",
    "tr": "Turski",
    "pt": "Portugalski",
    "pl": "Poljski",
    "cs": "Češki",
    "sk": "Slovački",
    "uk": "Ukrajinski",
    "zh": "Kineski",
    "ja": "Japanski",
    "ar": "Arapski",
    "la": "Latinski",
}


@register.filter(name="language_name")
def language_name(code):
    """
    Convert an ISO 639-1 language code to its full Serbian name.

    Falls back to the original (upper-cased) code when unknown, so nothing
    ever renders blank.

    Usage: {{ publication.language|language_name }}
    """
    if not code:
        return ""
    key = str(code).strip().lower()
    return LANGUAGE_NAMES.get(key, str(code).upper())


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
