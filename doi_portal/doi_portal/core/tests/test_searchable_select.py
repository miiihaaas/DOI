"""
Searchable selects (Tom Select) are wired centrally.

The behaviour itself lives in ``static/js/project.js`` (``initSearchableSelects``)
and is exercised with a jsdom harness outside the repo; these tests guard the
wiring: both base templates must ship the library, the skin and ``project.js``,
in an order that works with ``defer``.
"""

import re
from pathlib import Path

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.staticfiles import finders
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.test import RequestFactory

TOM_SELECT_VERSION = "2.6.2"
CDN = f"https://cdnjs.cloudflare.com/ajax/libs/tom-select/{TOM_SELECT_VERSION}"
LIB_JS = f"{CDN}/js/tom-select.base.min.js"
LIB_CSS = f"{CDN}/css/tom-select.bootstrap5.min.css"
SKIN_CSS = "css/searchable-select.css"
PROJECT_JS = "js/project.js"

BASE_TEMPLATES = ["base.html", "admin_base.html"]


def _source(name: str) -> str:
    return get_template(name).template.source


def _tag_containing(html: str, needle: str) -> str:
    """Return the full ``<link ...>`` / ``<script ...>`` tag that mentions needle."""
    for match in re.finditer(r"<(?:link|script)\b[^>]*>", html, flags=re.DOTALL):
        if needle in match.group(0):
            return match.group(0)
    msg = f"no <link>/<script> tag references {needle!r}"
    raise AssertionError(msg)


@pytest.mark.parametrize("template_name", BASE_TEMPLATES)
def test_base_template_includes_library_skin_and_project_js(template_name):
    source = _source(template_name)

    assert LIB_CSS in source
    assert LIB_JS in source
    assert SKIN_CSS in source
    assert PROJECT_JS in source


@pytest.mark.parametrize("template_name", BASE_TEMPLATES)
def test_library_tags_are_pinned_with_sri_and_deferred(template_name):
    source = _source(template_name)

    script = _tag_containing(source, LIB_JS)
    assert "defer" in script
    assert 'integrity="sha512-' in script
    assert 'crossorigin="anonymous"' in script

    stylesheet = _tag_containing(source, LIB_CSS)
    assert 'integrity="sha512-' in stylesheet
    assert 'crossorigin="anonymous"' in stylesheet


@pytest.mark.parametrize("template_name", BASE_TEMPLATES)
def test_load_order(template_name):
    """Deferred scripts run in document order: the library must precede project.js.

    The skin must come after the library stylesheet it overrides.
    """
    source = _source(template_name)

    project_js_tag = _tag_containing(source, "{% static 'js/project.js' %}")
    assert "defer" in project_js_tag
    assert source.index(LIB_JS) < source.index(project_js_tag)
    assert source.index(LIB_CSS) < source.index(SKIN_CSS)


@pytest.mark.parametrize("template_name", BASE_TEMPLATES)
def test_tags_live_in_the_overridable_blocks(template_name):
    """Children that extend the css/javascript blocks with block.super keep the tags."""
    source = _source(template_name)

    def block(name: str) -> str:
        start = source.index("{% block " + name + " %}")
        return source[start : source.index("{% endblock " + name + " %}")]

    css_block = block("css")
    js_block = block("javascript")
    assert LIB_CSS in css_block
    assert SKIN_CSS in css_block
    assert LIB_JS in js_block
    assert PROJECT_JS in js_block


def test_static_files_exist():
    assert finders.find(SKIN_CSS)
    assert finders.find(PROJECT_JS)


def test_project_js_exposes_the_central_initialiser():
    script = Path(finders.find(PROJECT_JS)).read_text(encoding="utf-8")

    assert "window.initSearchableSelects = initSearchableSelects" in script
    assert "var MIN_OPTIONS = 6;" in script
    assert "Nema rezultata" in script
    # HTMX partials are enhanced and cleaned up
    assert "htmx:load" in script
    assert "htmx:beforeCleanupElement" in script
    # the double-space warning shares the file and must stay
    assert "data-check-spaces" in script


@pytest.mark.django_db
def test_public_base_renders_the_tags_through_block_super():
    """portal/base.html overrides both blocks; it must still emit everything."""
    request = RequestFactory().get("/")
    request.user = AnonymousUser()

    html = render_to_string("portal/base.html", {"request": request}, request=request)

    assert LIB_CSS in html
    assert LIB_JS in html
    assert SKIN_CSS in html
    # tolerate hashed names from a manifest static storage
    project_js = re.search(r'<script\b[^>]*js/project[^"]*\.js"', html)
    assert project_js
    assert html.index(LIB_JS) < project_js.start()
