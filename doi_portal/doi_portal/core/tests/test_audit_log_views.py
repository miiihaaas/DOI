"""
Tests for Audit Log Viewer views (Story 6.2).

Tests cover:
- Permission/access control (AC#6)
- List view with filtering and search (AC#1, #2, #3, #5)
- Detail view with changes display (AC#4)
- HTMX partial rendering
- Menu visibility
"""

import json

import pytest
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import reverse

from auditlog.models import LogEntry

from doi_portal.users.tests.factories import UserFactory


@pytest.fixture
def superadmin_user(db):
    """Create a superadmin user."""
    user = UserFactory(email="superadmin@test.com", is_superuser=True)
    return user


@pytest.fixture
def admin_user(db):
    """Create an Administrator user."""
    user = UserFactory(email="admin@test.com")
    group, _ = Group.objects.get_or_create(name="Administrator")
    user.groups.add(group)
    return user


@pytest.fixture
def urednik_user(db):
    """Create an Urednik user."""
    user = UserFactory(email="urednik@test.com")
    group, _ = Group.objects.get_or_create(name="Urednik")
    user.groups.add(group)
    return user


@pytest.fixture
def bibliotekar_user(db):
    """Create a Bibliotekar user."""
    user = UserFactory(email="bibliotekar@test.com")
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user.groups.add(group)
    return user


@pytest.fixture
def user_content_type(db):
    """Get User content type."""
    from doi_portal.users.models import User
    return ContentType.objects.get_for_model(User)


@pytest.fixture
def sample_log_entries(db, superadmin_user, user_content_type):
    """Create sample LogEntry records for testing."""
    entries = []
    for i in range(5):
        entry = LogEntry.objects.create(
            content_type=user_content_type,
            object_pk=str(i + 1),
            object_id=i + 1,
            object_repr=f"Test Object {i + 1}",
            action=LogEntry.Action.CREATE,
            changes=json.dumps({"name": ["", f"Test {i + 1}"]}),
            actor=superadmin_user,
        )
        entries.append(entry)
    return entries


@pytest.fixture
def authenticated_client(superadmin_user):
    """Return client authenticated as superadmin."""
    client = Client()
    client.force_login(superadmin_user)
    return client


# ============================================================================
# Task 1: Menu tests
# ============================================================================


class TestAuditLogMenu:
    """Test audit_log menu item visibility (Task 1, AC#1, #6)."""

    def test_menu_item_exists_in_config(self):
        """Verify audit_log menu item exists in MENU_ITEMS."""
        from doi_portal.core.menu import MENU_ITEMS

        assert "audit_log" in MENU_ITEMS
        item = MENU_ITEMS["audit_log"]
        assert item["label"] == "Revizioni log"
        assert item["icon"] == "bi-clock-history"
        assert item["url_name"] == "core:audit-log-list"
        assert item["roles"] == ["Superadmin"]

    def test_menu_item_position_after_users_before_system_settings(self):
        """Verify audit_log is positioned between users and system_settings."""
        from doi_portal.core.menu import MENU_ITEMS

        keys = list(MENU_ITEMS.keys())
        users_idx = keys.index("users")
        audit_idx = keys.index("audit_log")
        settings_idx = keys.index("system_settings")
        assert users_idx < audit_idx < settings_idx

    @pytest.mark.django_db
    def test_menu_visible_for_superadmin(self, superadmin_user):
        """Superadmin should see audit_log in menu."""
        from doi_portal.core.menu import get_menu_for_user

        menu = get_menu_for_user(superadmin_user)
        keys = [item["key"] for item in menu]
        assert "audit_log" in keys

    @pytest.mark.django_db
    def test_menu_not_visible_for_admin(self, admin_user):
        """Administrator should NOT see audit_log in menu."""
        from doi_portal.core.menu import get_menu_for_user

        menu = get_menu_for_user(admin_user)
        keys = [item["key"] for item in menu]
        assert "audit_log" not in keys

    @pytest.mark.django_db
    def test_menu_not_visible_for_urednik(self, urednik_user):
        """Urednik should NOT see audit_log in menu."""
        from doi_portal.core.menu import get_menu_for_user

        menu = get_menu_for_user(urednik_user)
        keys = [item["key"] for item in menu]
        assert "audit_log" not in keys


# ============================================================================
# Task 8: Permission tests (AC#6)
# ============================================================================


@pytest.mark.django_db
class TestAuditLogPermissions:
    """Test access control for audit log views (Task 8, AC#6)."""

    def test_superadmin_can_access_list(self, authenticated_client):
        """AC6: Superadmin can access audit-log-list (200)."""
        url = reverse("core:audit-log-list")
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_administrator_gets_403(self, admin_user):
        """AC6: Administrator gets 403."""
        client = Client()
        client.force_login(admin_user)
        url = reverse("core:audit-log-list")
        response = client.get(url)
        assert response.status_code == 403

    def test_urednik_gets_403(self, urednik_user):
        """AC6: Urednik gets 403."""
        client = Client()
        client.force_login(urednik_user)
        url = reverse("core:audit-log-list")
        response = client.get(url)
        assert response.status_code == 403

    def test_bibliotekar_gets_403(self, bibliotekar_user):
        """AC6: Bibliotekar gets 403."""
        client = Client()
        client.force_login(bibliotekar_user)
        url = reverse("core:audit-log-list")
        response = client.get(url)
        assert response.status_code == 403

    def test_unauthenticated_redirected_to_login(self):
        """AC6: Unauthenticated user redirected to login."""
        client = Client()
        url = reverse("core:audit-log-list")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url or "login" in response.url

    def test_superadmin_can_access_detail(self, authenticated_client, sample_log_entries):
        """AC6: Superadmin can access audit-log-detail (200)."""
        entry = sample_log_entries[0]
        url = reverse("core:audit-log-detail", kwargs={"pk": entry.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_non_superadmin_gets_403_on_detail(self, admin_user, sample_log_entries):
        """AC6: Non-Superadmin gets 403 on detail view."""
        client = Client()
        client.force_login(admin_user)
        entry = sample_log_entries[0]
        url = reverse("core:audit-log-detail", kwargs={"pk": entry.pk})
        response = client.get(url)
        assert response.status_code == 403


# ============================================================================
# Task 9: List view and filtering tests (AC#2, #3, #5)
# ============================================================================


@pytest.mark.django_db
class TestAuditLogListView:
    """Test list view, filtering, and search (Task 9, AC#2, #3, #5)."""

    def test_list_shows_entries_reverse_chronological(self, authenticated_client, sample_log_entries):
        """AC2: Entries in reverse chronological order."""
        url = reverse("core:audit-log-list")
        response = authenticated_client.get(url)
        assert response.status_code == 200
        entries = response.context["object_list"]
        # Check reverse chronological - first entry should have latest timestamp
        timestamps = [e.timestamp for e in entries]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_pagination_50_per_page(self, authenticated_client, superadmin_user, user_content_type):
        """AC2: Pagination with 50 per page."""
        # Create 55 entries
        for i in range(55):
            LogEntry.objects.create(
                content_type=user_content_type,
                object_pk=str(i + 100),
                object_id=i + 100,
                object_repr=f"Paginated Object {i}",
                action=LogEntry.Action.CREATE,
                changes="{}",
                actor=superadmin_user,
            )
        url = reverse("core:audit-log-list")
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert len(response.context["object_list"]) == 50
        assert response.context["is_paginated"] is True

    def test_filter_by_date_range(self, authenticated_client, sample_log_entries):
        """AC3: Filter by date range."""
        from django.utils import timezone

        today = timezone.now().date()
        url = reverse("core:audit-log-list")
        response = authenticated_client.get(url, {
            "date_from": today.isoformat(),
            "date_to": today.isoformat(),
        })
        assert response.status_code == 200
        # All sample entries created today should be included
        # (may include auto-generated auditlog entries for user creation)
        result_pks = [e.pk for e in response.context["object_list"]]
        for entry in sample_log_entries:
            assert entry.pk in result_pks

    def test_filter_by_actor(self, authenticated_client, superadmin_user, sample_log_entries):
        """AC3: Filter by actor."""
        url = reverse("core:audit-log-list")
        response = authenticated_client.get(url, {"actor": superadmin_user.pk})
        assert response.status_code == 200
        for entry in response.context["object_list"]:
            assert entry.actor_id == superadmin_user.pk

    def test_filter_by_action(self, authenticated_client, sample_log_entries):
        """AC3: Filter by action (CREATE/UPDATE/DELETE)."""
        url = reverse("core:audit-log-list")
        response = authenticated_client.get(url, {"action": str(LogEntry.Action.CREATE)})
        assert response.status_code == 200
        for entry in response.context["object_list"]:
            assert entry.action == LogEntry.Action.CREATE

    def test_filter_by_content_type(self, authenticated_client, sample_log_entries, user_content_type):
        """AC3: Filter by model (content_type)."""
        url = reverse("core:audit-log-list")
        response = authenticated_client.get(url, {"model": user_content_type.pk})
        assert response.status_code == 200
        for entry in response.context["object_list"]:
            assert entry.content_type_id == user_content_type.pk

    def test_filter_by_object_id(self, authenticated_client, sample_log_entries):
        """AC3: Filter by object_id."""
        url = reverse("core:audit-log-list")
        response = authenticated_client.get(url, {"object_id": "1"})
        assert response.status_code == 200
        for entry in response.context["object_list"]:
            assert entry.object_pk == "1"

    def test_search_by_object_repr(self, authenticated_client, sample_log_entries):
        """AC5: Search by object representation."""
        url = reverse("core:audit-log-list")
        response = authenticated_client.get(url, {"q": "Test Object 3"})
        assert response.status_code == 200
        entries = response.context["object_list"]
        assert len(entries) >= 1
        assert any("Test Object 3" in e.object_repr for e in entries)

    def test_search_by_actor_email(self, authenticated_client, sample_log_entries):
        """AC5: Search by actor email."""
        url = reverse("core:audit-log-list")
        response = authenticated_client.get(url, {"q": "superadmin@test.com"})
        assert response.status_code == 200
        entries = response.context["object_list"]
        assert len(entries) >= 1

    def test_htmx_request_returns_partial(self, authenticated_client, sample_log_entries):
        """AC5: HTMX request returns partial template."""
        url = reverse("core:audit-log-list")
        response = authenticated_client.get(url, HTTP_HX_REQUEST="true")
        assert response.status_code == 200
        # Partial should NOT contain full HTML layout
        content = response.content.decode()
        assert "<!DOCTYPE html>" not in content
        assert "<table" in content or "audit-log-table" in content

    def test_invalid_action_parameter_returns_200(self, authenticated_client, sample_log_entries):
        """Security: Invalid action value should not cause 500 error."""
        url = reverse("core:audit-log-list")
        response = authenticated_client.get(url, {"action": "invalid"})
        assert response.status_code == 200

    def test_htmx_partial_does_not_load_dropdown_data(self, authenticated_client, sample_log_entries):
        """Performance: HTMX partial should not include dropdown data."""
        url = reverse("core:audit-log-list")
        response = authenticated_client.get(url, HTTP_HX_REQUEST="true")
        assert response.status_code == 200
        # users and content_types should not be in context for HTMX requests
        assert "users" not in response.context
        assert "content_types" not in response.context


# ============================================================================
# Task 10: Detail view tests (AC#4)
# ============================================================================


@pytest.mark.django_db
class TestAuditLogDetailView:
    """Test detail view with changes display (Task 10, AC#4)."""

    def test_detail_shows_metadata(self, authenticated_client, sample_log_entries):
        """AC4: Detail view shows LogEntry metadata."""
        entry = sample_log_entries[0]
        url = reverse("core:audit-log-detail", kwargs={"pk": entry.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert entry.object_repr in content

    def test_update_entry_shows_old_vs_new(self, authenticated_client, superadmin_user, user_content_type):
        """AC4: UPDATE entry shows old vs new values."""
        entry = LogEntry.objects.create(
            content_type=user_content_type,
            object_pk="1",
            object_id=1,
            object_repr="Updated Object",
            action=LogEntry.Action.UPDATE,
            changes=json.dumps({"name": ["Old Name", "New Name"]}),
            actor=superadmin_user,
        )
        url = reverse("core:audit-log-detail", kwargs={"pk": entry.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        context = response.context
        assert "changes_data" in context
        changes = context["changes_data"]
        assert "name" in changes
        assert changes["name"]["old"] == "Old Name"
        assert changes["name"]["new"] == "New Name"

    def test_create_entry_shows_set_values(self, authenticated_client, superadmin_user, user_content_type):
        """AC4: CREATE entry shows set values."""
        entry = LogEntry.objects.create(
            content_type=user_content_type,
            object_pk="1",
            object_id=1,
            object_repr="Created Object",
            action=LogEntry.Action.CREATE,
            changes=json.dumps({"name": ["", "New Name"], "email": ["", "test@test.com"]}),
            actor=superadmin_user,
        )
        url = reverse("core:audit-log-detail", kwargs={"pk": entry.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        context = response.context
        assert "changes_data" in context

    def test_delete_entry_shows_object_repr(self, authenticated_client, superadmin_user, user_content_type):
        """AC4: DELETE entry shows saved object_repr."""
        entry = LogEntry.objects.create(
            content_type=user_content_type,
            object_pk="1",
            object_id=1,
            object_repr="Deleted Object",
            action=LogEntry.Action.DELETE,
            changes="{}",
            actor=superadmin_user,
        )
        url = reverse("core:audit-log-detail", kwargs={"pk": entry.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Deleted Object" in content
