"""
Sidebar navigation tests: active-item matching and menu composition.

Covers the rules in ``core/templatetags/menu_tags.py``:
- "Kontrolna tabla" is active only on the dashboard home (exact match)
- items that share a URL are told apart by the query string
- nested system pages highlight the most specific item only
- exactly one item is highlighted at a time
"""

import re
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from doi_portal.core.menu import MENU_ITEMS
from doi_portal.core.menu import get_menu_for_user
from doi_portal.core.templatetags.menu_tags import resolve_active_key
from doi_portal.publishers.models import Publisher

User = get_user_model()

ARTICLES = "/dashboard/articles/"
AUDIT = "/dashboard/audit-log/"

ITEMS = [
    {"key": "dashboard", "path": "/dashboard/", "query": {}, "exact": True},
    {
        "key": "my_drafts",
        "path": ARTICLES,
        "query": {"status": "DRAFT", "mine": "1"},
        "exact": False,
    },
    {
        "key": "pending_review",
        "path": ARTICLES,
        "query": {"status": "REVIEW"},
        "exact": False,
    },
    {"key": "articles", "path": ARTICLES, "query": {}, "exact": False},
    {"key": "audit_log", "path": AUDIT, "query": {}, "exact": False},
    {"key": "deleted_items", "path": f"{AUDIT}deleted/", "query": {}, "exact": False},
    {"key": "gdpr_requests", "path": f"{AUDIT}gdpr/", "query": {}, "exact": False},
    {
        "key": "system_health",
        "path": f"{AUDIT}system/health/",
        "query": {},
        "exact": False,
    },
    {"key": "system_settings", "path": None, "query": {}, "exact": False},
]


class TestResolveActiveKey:
    """Unit tests for the matching rules (no database)."""

    @pytest.mark.parametrize(
        ("path", "query", "expected"),
        [
            # (a) dashboard is exact-match only
            ("/dashboard/", {}, "dashboard"),
            ("/dashboard/publications/", {}, None),
            ("/dashboard/crossref/issues/1/", {}, None),
            # (b) same URL, different query string
            (ARTICLES, {}, "articles"),
            (ARTICLES, {"status": "DRAFT", "mine": "1"}, "my_drafts"),
            # all drafts of the publisher (no "mine") are just the article list
            (ARTICLES, {"status": "DRAFT"}, "articles"),
            (ARTICLES, {"mine": "1"}, "articles"),
            (ARTICLES, {"status": "REVIEW", "mine": "1"}, "pending_review"),
            (ARTICLES, {"status": "REVIEW"}, "pending_review"),
            (ARTICLES, {"status": "PUBLISHED"}, "articles"),
            (ARTICLES, {"status": "DRAFT", "mine": "1", "page": "2"}, "my_drafts"),
            (ARTICLES, {"status": "DRAFT", "mine": "1", "q": "voda"}, "my_drafts"),
            (ARTICLES, {"issue": "7"}, "articles"),
            # nested article pages belong to "Članci", never to the filtered links
            (f"{ARTICLES}12/", {}, "articles"),
            (f"{ARTICLES}12/edit/", {"status": "DRAFT"}, "articles"),
            # (c) most specific match wins under /dashboard/audit-log/
            (AUDIT, {}, "audit_log"),
            (f"{AUDIT}15/", {}, "audit_log"),
            (f"{AUDIT}deleted/", {}, "deleted_items"),
            (f"{AUDIT}gdpr/", {}, "gdpr_requests"),
            (f"{AUDIT}gdpr/3/", {}, "gdpr_requests"),
            (f"{AUDIT}system/health/", {}, "system_health"),
            # unrelated path
            ("/users/manage/", {}, None),
        ],
    )
    def test_most_specific_item_wins(self, path, query, expected):
        assert resolve_active_key(ITEMS, path, query) == expected

    def test_prefix_match_respects_path_segments(self):
        """'/dashboard/articles-archive/' must not activate '/dashboard/articles/'."""
        items = [{"key": "articles", "path": "/dashboard/articles", "query": {}}]
        assert resolve_active_key(items, "/dashboard/articles-archive/") is None
        assert resolve_active_key(items, "/dashboard/articles/4/") == "articles"

    def test_item_without_url_never_matches(self):
        items = [{"key": "system_settings", "path": None, "query": {}}]
        assert resolve_active_key(items, "/dashboard/") is None

    def test_query_item_missing_from_menu_falls_back_to_plain_item(self):
        """No 'Na pregledu' entry (Bibliotekar): ?status=REVIEW highlights 'Članci'."""
        items = [item for item in ITEMS if item["key"] != "pending_review"]
        assert resolve_active_key(items, ARTICLES, {"status": "REVIEW"}) == "articles"


def _make_user(email: str, role: str | None = None, **extra):
    user = User.objects.create_user(email=email, password="testpass123!", **extra)  # noqa: S106
    if role:
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
    return user


def _active_labels(html: str) -> list[str]:
    """Labels of sidebar links carrying the 'active' class."""
    pattern = re.compile(
        r'<a class="sidebar-link sidebar-menu-item active"[^>]*>.*?'
        r'<span class="sidebar-link__label">(.*?)</span>',
        re.DOTALL,
    )
    return pattern.findall(html)


@pytest.mark.django_db
class TestSidebarActiveItemRendered:
    """The rendered sidebar highlights exactly one item."""

    @pytest.fixture
    def superadmin_client(self, client: Client) -> Client:
        client.force_login(_make_user("nav-super@test.com", is_superuser=True))
        return client

    @pytest.mark.parametrize(
        ("url_name", "query", "expected"),
        [
            ("dashboard", "", "Kontrolna tabla"),
            ("articles:list", "", "Članci"),
            ("articles:list", "?status=DRAFT&mine=1", "Moji nacrti"),
            ("articles:list", "?status=DRAFT", "Članci"),
            ("articles:list", "?mine=1", "Članci"),
            ("articles:list", "?status=REVIEW", "Na pregledu"),
            ("articles:list", "?status=READY", "Članci"),
            ("publications:list", "", "Publikacije"),
            ("core:audit-log-list", "", "Revizioni log"),
            ("core:deleted-items", "", "Obrisane stavke"),
            ("core:gdpr-request-list", "", "GDPR zahtevi"),
            ("core:gdpr-request-create", "", "GDPR zahtevi"),
            ("core:system-health", "", "Zdravlje sistema"),
            ("core:sentry-test", "", "Sentry test"),
            ("wizard:conference-start", "", "Registracija konferencije"),
        ],
    )
    def test_single_active_item(self, superadmin_client, url_name, query, expected):
        response = superadmin_client.get(reverse(url_name) + query)
        assert response.status_code == HTTPStatus.OK
        assert _active_labels(response.content.decode("utf-8")) == [expected]

    def test_filtered_links_carry_their_query_string(self, superadmin_client):
        content = superadmin_client.get(reverse("dashboard")).content.decode("utf-8")
        list_url = reverse("articles:list")
        assert f'href="{list_url}?status=DRAFT&amp;mine=1"' in content
        assert f'href="{list_url}?status=REVIEW"' in content
        assert f'href="{list_url}"' in content

    def test_active_item_has_aria_current(self, superadmin_client):
        content = superadmin_client.get(reverse("dashboard")).content.decode("utf-8")
        assert content.count('aria-current="page"') >= 1
        assert re.search(
            r'<a class="sidebar-link sidebar-menu-item active"\s+'
            r'href="/dashboard/" aria-current="page"',
            content,
        )

    def test_unavailable_item_is_not_a_link(self, superadmin_client):
        """'Podešavanja sistema' stays in the menu but is rendered as unavailable."""
        content = superadmin_client.get(reverse("dashboard")).content.decode("utf-8")
        match = re.search(
            r"<(\w+) class=\"sidebar-link sidebar-menu-item is-unavailable\"[^>]*>"
            r"(.*?)</\1>",
            content,
            re.DOTALL,
        )
        assert match is not None
        assert match.group(1) == "span"
        assert "Podešavanja sistema" in match.group(2)
        assert 'aria-disabled="true"' in match.group(0)


@pytest.mark.django_db
class TestMenuComposition:
    """Menu configuration: wizard entry and query targets."""

    def test_filtered_items_have_query_targets(self):
        assert MENU_ITEMS["my_drafts"]["query"] == {"status": "DRAFT", "mine": "1"}
        assert MENU_ITEMS["pending_review"]["query"] == {"status": "REVIEW"}
        assert "query" not in MENU_ITEMS["articles"]

    def test_wizard_visible_for_admin_roles(self):
        user = _make_user("nav-admin@test.com", role="Administrator")
        keys = [item["key"] for item in get_menu_for_user(user)]
        assert "conference_wizard" in keys
        assert keys.index("conference_wizard") < keys.index("publishers")

    def test_wizard_hidden_for_urednik_without_publisher(self):
        """Mirrors wizard_start, which raises PermissionDenied in this case."""
        user = _make_user("nav-urednik@test.com", role="Urednik")
        keys = [item["key"] for item in get_menu_for_user(user)]
        assert "conference_wizard" not in keys
        assert "articles" in keys

    def test_wizard_visible_for_bibliotekar_with_publisher(self):
        user = _make_user("nav-bibl@test.com", role="Bibliotekar")
        user.publisher = Publisher.objects.create(name="Nav Test Publisher")
        user.save()
        keys = [item["key"] for item in get_menu_for_user(user)]
        assert "conference_wizard" in keys
