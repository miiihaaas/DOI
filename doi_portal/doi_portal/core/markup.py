"""
Lightweight markup parser for scientific text formatting.

Supports inline markup for titles, subtitles, and abstracts:
- _text_ → italic
- **text** → bold
- ~text~ → subscript
- ^text^ → superscript
- „text" → Unicode quotes (pass-through)

Three output modes:
- HTML: for landing page rendering
- Crossref XML: face markup (<i>, <b>, <sub>, <sup>) for title/subtitle
- JATS XML: JATS inline markup for abstract within <jats:abstract><jats:p>
"""

import html
import re

# Regex patterns — bold MUST be processed before italic
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC_RE = re.compile(r"(?<!\w)_([^_]+)_(?!\w)")
_SUP_RE = re.compile(r"\^([^^]+)\^")
_SUB_RE = re.compile(r"~([^~]+)~")


def markup_to_html(text: str | None) -> str:
    """Convert markup to HTML (<em>, <strong>, <sub>, <sup>)."""
    if not text:
        return ""
    # HTML escape first for XSS prevention
    t = html.escape(text)
    # Bold before italic
    t = _BOLD_RE.sub(r"<strong>\1</strong>", t)
    t = _ITALIC_RE.sub(r"<em>\1</em>", t)
    t = _SUP_RE.sub(r"<sup>\1</sup>", t)
    t = _SUB_RE.sub(r"<sub>\1</sub>", t)
    return t


def _xml_escape(text: str) -> str:
    """Escape XML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def markup_to_crossref_xml(text: str | None) -> str:
    """Convert markup to Crossref face markup (<i>, <b>, <sub>, <sup>).

    Used for title, subtitle, original_language_title, original_language_subtitle.
    """
    if not text:
        return ""
    t = _xml_escape(text)
    t = _BOLD_RE.sub(r"<b>\1</b>", t)
    t = _ITALIC_RE.sub(r"<i>\1</i>", t)
    t = _SUP_RE.sub(r"<sup>\1</sup>", t)
    t = _SUB_RE.sub(r"<sub>\1</sub>", t)
    return t


def markup_to_jats_xml(text: str | None) -> str:
    """Convert markup to JATS inline markup for abstract.

    Used EXCLUSIVELY for abstract within <jats:abstract><jats:p> where
    Crossref face markup tags (<i>, <b>) are NOT valid.
    JATS standard requires JATS-specific tags.
    """
    if not text:
        return ""
    t = _xml_escape(text)
    t = _BOLD_RE.sub(r"<jats:bold>\1</jats:bold>", t)
    t = _ITALIC_RE.sub(r"<jats:italic>\1</jats:italic>", t)
    t = _SUP_RE.sub(r"<jats:sup>\1</jats:sup>", t)
    t = _SUB_RE.sub(r"<jats:sub>\1</jats:sub>", t)
    return t


def strip_markup(text: str | None) -> str:
    """Remove markup delimiters, return plain text for search/meta."""
    if not text:
        return ""
    t = _BOLD_RE.sub(r"\1", text)
    t = _ITALIC_RE.sub(r"\1", t)
    t = _SUP_RE.sub(r"\1", t)
    t = _SUB_RE.sub(r"\1", t)
    return t
