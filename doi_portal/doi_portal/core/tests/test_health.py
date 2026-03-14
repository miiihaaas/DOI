"""
Tests for system health check service and SystemHealthView (Story 6.6).

Task 6: Tests for health check service (AC: #2, #3, #4)
Task 7: Tests for view (AC: #1, #6)
Task 8: Tests for menu (AC: #6)
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.core.health import (
    _check_celery,
    _check_database,
    _check_redis,
    _check_storage,
    _get_content_statistics,
    _safe_check,
    get_system_health,
)
from doi_portal.issues.tests.factories import IssueFactory, PublisherFactory
from doi_portal.publications.tests.factories import PublicationFactory
from doi_portal.users.models import User


# ============================================================================
# Task 6: Health Check Service Tests
# ============================================================================


@pytest.mark.django_db
class TestCheckDatabase:
    """Tests for _check_database() (Task 6.2)."""

    def test_returns_ok_when_db_available(self):
        """_check_database() should return OK when database is accessible."""
        result = _check_database()
        assert result["status"] == "ok"
        assert "PostgreSQL" in result["message"]

    def test_returns_error_when_db_unavailable(self):
        """_check_database() should return error via _safe_check when DB is down."""
        with patch("doi_portal.core.health.connection") as mock_conn:
            mock_conn.ensure_connection.side_effect = Exception("connection refused")
            result = _safe_check(_check_database)
            assert result["status"] == "error"
            assert "connection refused" in result["message"]


@pytest.mark.django_db
class TestCheckRedis:
    """Tests for _check_redis() (Task 6.3)."""

    def test_returns_ok_when_cache_works(self):
        """_check_redis() should return OK when cache set/get works."""
        with patch("doi_portal.core.health.cache") as mock_cache:
            mock_cache.get.return_value = "1"
            result = _check_redis()
            assert result["status"] == "ok"
            assert "Redis" in result["message"]
            mock_cache.set.assert_called_once_with("health_check", "1", 10)
            mock_cache.get.assert_called_once_with("health_check")

    def test_returns_error_when_cache_fails(self):
        """_check_redis() should return error when cache read fails."""
        with patch("doi_portal.core.health.cache") as mock_cache:
            mock_cache.get.return_value = None
            result = _check_redis()
            assert result["status"] == "error"
            assert "neuspešan" in result["message"]


class TestCheckCelery:
    """Tests for _check_celery() (Task 6.4, 6.5)."""

    def test_returns_error_when_no_workers(self):
        """_check_celery() should return error when no workers respond (Task 6.4)."""
        with patch("config.celery_app.app") as mock_app:
            mock_inspector = MagicMock()
            mock_inspector.ping.return_value = None
            mock_app.control.inspect.return_value = mock_inspector
            result = _check_celery()
            assert result["status"] == "error"
            assert "Nema aktivnih" in result["message"]

    def test_returns_ok_when_workers_respond(self):
        """_check_celery() should return OK when workers respond (Task 6.5)."""
        with patch(
            "config.celery_app.app"
        ) as mock_app:
            mock_inspector = MagicMock()
            mock_inspector.ping.return_value = {
                "celery@worker1": {"ok": "pong"},
                "celery@worker2": {"ok": "pong"},
            }
            mock_app.control.inspect.return_value = mock_inspector
            result = _check_celery()
            assert result["status"] == "ok"
            assert "2 worker(a)" in result["message"]


class TestCheckStorage:
    """Tests for _check_storage() (Task 6.6, 6.7)."""

    def test_returns_ok_when_storage_works(self):
        """_check_storage() should return OK when storage.exists() works (Task 6.6)."""
        with patch(
            "django.core.files.storage.default_storage"
        ) as mock_storage:
            mock_storage.exists.return_value = False
            result = _check_storage()
            assert result["status"] == "ok"
            assert "Skladište" in result["message"]

    def test_returns_error_when_storage_unavailable(self):
        """_check_storage() should return error via _safe_check when storage raises exception (Task 6.7)."""
        with patch(
            "django.core.files.storage.default_storage"
        ) as mock_storage:
            mock_storage.exists.side_effect = Exception("Connection refused")
            result = _safe_check(_check_storage)
            assert result["status"] == "error"
            assert "Connection refused" in result["message"]
            assert "Exception:" in result["message"]


@pytest.mark.django_db
class TestGetContentStatistics:
    """Tests for _get_content_statistics() (Task 6.8)."""

    def test_returns_correct_counts(self):
        """_get_content_statistics() should return correct content counts."""
        # Create test data
        User.objects.create_user(email="active1@test.com", password="test123")
        User.objects.create_user(
            email="inactive1@test.com", password="test123", is_active=False
        )

        PublisherFactory()
        PublisherFactory()
        PublicationFactory()
        IssueFactory()

        # Create articles with different statuses
        ArticleFactory(status=ArticleStatus.DRAFT)
        ArticleFactory(status=ArticleStatus.DRAFT)
        ArticleFactory(status=ArticleStatus.REVIEW)
        ArticleFactory(status=ArticleStatus.PUBLISHED)

        result = _get_content_statistics()

        # Users (factory-created users from sub-factories also count)
        assert result["active_users"] >= 1
        assert result["inactive_users"] >= 1

        # Content
        assert result["publisher_count"] >= 2
        assert result["publication_count"] >= 1
        assert result["issue_count"] >= 1

        # Articles by status
        assert result["article_counts"]["draft"] >= 2
        assert result["article_counts"]["review"] >= 1
        assert result["article_counts"]["published"] >= 1
        assert result["article_counts"]["total"] >= 4

        # Recent audit count (non-negative)
        assert result["recent_audit_count"] >= 0

    def test_recent_audit_count_filters_by_24h_window(self):
        """recent_audit_count should only include LogEntry records from the last 24h."""
        from auditlog.models import LogEntry
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(User)

        # Create a LogEntry within the 24h window (recent)
        recent_entry = LogEntry.objects.create(
            content_type=ct,
            object_repr="Recent item",
            action=LogEntry.Action.CREATE,
        )

        # Create a LogEntry outside the 24h window (old)
        old_entry = LogEntry.objects.create(
            content_type=ct,
            object_repr="Old item",
            action=LogEntry.Action.CREATE,
        )
        # Manually backdate the old entry
        LogEntry.objects.filter(pk=old_entry.pk).update(
            timestamp=timezone.now() - timedelta(hours=25)
        )

        result = _get_content_statistics()
        # Should count the recent one but not the old one
        assert result["recent_audit_count"] >= 1
        # Verify the old entry is excluded by checking total is less than all entries
        total_entries = LogEntry.objects.count()
        assert result["recent_audit_count"] < total_entries or total_entries == 1


@pytest.mark.django_db
class TestGetSystemHealth:
    """Tests for get_system_health() (Task 6.9)."""

    @patch("doi_portal.core.health._check_celery")
    @patch("doi_portal.core.health._check_storage")
    def test_returns_complete_dict(self, mock_storage, mock_celery):
        """get_system_health() should return dict with all required keys."""
        mock_celery.return_value = {"status": "ok", "message": "1 worker(a) aktivno"}
        mock_storage.return_value = {"status": "ok", "message": "Skladište dostupno"}

        result = get_system_health()

        assert "statistics" in result
        assert "integrations" in result
        assert "checked_at" in result

        # Verify integration keys
        integrations = result["integrations"]
        assert "database" in integrations
        assert "redis" in integrations
        assert "celery" in integrations
        assert "storage" in integrations

        # Verify each integration has status and message
        for key in ["database", "redis", "celery", "storage"]:
            assert "status" in integrations[key]
            assert "message" in integrations[key]

        # Verify statistics keys
        stats = result["statistics"]
        assert "active_users" in stats
        assert "inactive_users" in stats
        assert "publisher_count" in stats
        assert "publication_count" in stats
        assert "issue_count" in stats
        assert "article_counts" in stats
        assert "recent_audit_count" in stats


class TestSafeCheck:
    """Tests for _safe_check() wrapper."""

    def test_catches_exceptions(self):
        """_safe_check() should catch exceptions and return error dict."""

        def failing_check():
            raise ConnectionError("Cannot connect")

        result = _safe_check(failing_check)
        assert result["status"] == "error"
        assert "Cannot connect" in result["message"]
        assert "ConnectionError" in result["message"]

    def test_truncates_long_error_messages(self):
        """_safe_check() should truncate excessively long error messages."""

        def long_error_check():
            raise Exception("x" * 300)

        result = _safe_check(long_error_check)
        assert result["status"] == "error"
        assert len(result["message"]) < 300
        assert result["message"].endswith("...")

    def test_passes_through_success(self):
        """_safe_check() should pass through successful results."""

        def ok_check():
            return {"status": "ok", "message": "All good"}

        result = _safe_check(ok_check)
        assert result["status"] == "ok"


# ============================================================================
# Task 7: View Tests
# ============================================================================


@pytest.mark.django_db
class TestSystemHealthView:
    """Tests for SystemHealthView (AC: #1, #6)."""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        """Set up test fixtures."""
        self.superadmin = User.objects.create_user(
            email="superadmin@test.com",
            password="testpass123",
            is_superuser=True,
        )
        self.regular_user = User.objects.create_user(
            email="regular@test.com",
            password="testpass123",
        )
        self.client = client

    @patch("doi_portal.core.health._check_celery")
    @patch("doi_portal.core.health._check_storage")
    def test_superadmin_can_access_health_dashboard(self, mock_storage, mock_celery):
        """AC#1: Superadmin can access health dashboard (200) (Task 7.2)."""
        mock_celery.return_value = {"status": "ok", "message": "1 worker(a) aktivno"}
        mock_storage.return_value = {"status": "ok", "message": "Skladište dostupno"}
        self.client.force_login(self.superadmin)
        response = self.client.get(reverse("core:system-health"))
        assert response.status_code == 200

    @patch("doi_portal.core.health._check_celery")
    @patch("doi_portal.core.health._check_storage")
    def test_superadmin_via_group_can_access(self, mock_storage, mock_celery):
        """AC#1: Superadmin via group membership can access health dashboard (200)."""
        mock_celery.return_value = {"status": "ok", "message": "1 worker(a) aktivno"}
        mock_storage.return_value = {"status": "ok", "message": "Skladište dostupno"}
        group_user = User.objects.create_user(
            email="groupadmin@test.com",
            password="testpass123",
        )
        group, _ = Group.objects.get_or_create(name="Superadmin")
        group_user.groups.add(group)
        self.client.force_login(group_user)
        response = self.client.get(reverse("core:system-health"))
        assert response.status_code == 200

    def test_non_superadmin_gets_403(self):
        """AC#1: Non-superadmin users get 403 (Task 7.3)."""
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse("core:system-health"))
        assert response.status_code == 403

    def test_anonymous_user_redirected_to_login(self):
        """Anonymous users should be redirected to login (Task 7.4)."""
        response = self.client.get(reverse("core:system-health"))
        assert response.status_code == 302

    @patch("doi_portal.core.health._check_celery")
    @patch("doi_portal.core.health._check_storage")
    def test_page_uses_correct_template(self, mock_storage, mock_celery):
        """Page should use core/system_health.html template (Task 7.5)."""
        mock_celery.return_value = {"status": "ok", "message": "1 worker(a) aktivno"}
        mock_storage.return_value = {"status": "ok", "message": "Skladište dostupno"}
        self.client.force_login(self.superadmin)
        response = self.client.get(reverse("core:system-health"))
        assert "core/system_health.html" in [t.name for t in response.templates]

    @patch("doi_portal.core.health._check_celery")
    @patch("doi_portal.core.health._check_storage")
    def test_context_contains_health_data(self, mock_storage, mock_celery):
        """Context should contain health_data key (Task 7.6)."""
        mock_celery.return_value = {"status": "ok", "message": "1 worker(a) aktivno"}
        mock_storage.return_value = {"status": "ok", "message": "Skladište dostupno"}
        self.client.force_login(self.superadmin)
        response = self.client.get(reverse("core:system-health"))
        assert "health_data" in response.context


# ============================================================================
# Task 8: Menu Tests
# ============================================================================


@pytest.mark.django_db
class TestSystemHealthMenu:
    """Tests for sidebar menu visibility (AC: #6)."""

    def test_system_health_menu_visible_for_superadmin(self):
        """AC#6: 'Zdravlje sistema' should be visible for Superadmin (Task 8.1)."""
        from doi_portal.core.menu import get_menu_for_user

        superadmin = User.objects.create_user(
            email="super@test.com",
            password="testpass123",
            is_superuser=True,
        )
        menu = get_menu_for_user(superadmin)
        menu_keys = [item["key"] for item in menu]
        assert "system_health" in menu_keys

        # Verify it appears after sentry_test
        sentry_idx = menu_keys.index("sentry_test")
        health_idx = menu_keys.index("system_health")
        assert health_idx > sentry_idx

    def test_system_health_menu_not_visible_for_non_superadmin(self):
        """AC#6: Non-Superadmin should NOT see 'Zdravlje sistema' (Task 8.2)."""
        from doi_portal.core.menu import get_menu_for_user

        user = User.objects.create_user(
            email="urednik@test.com",
            password="testpass123",
        )
        group, _ = Group.objects.get_or_create(name="Urednik")
        user.groups.add(group)
        menu = get_menu_for_user(user)
        menu_keys = [item["key"] for item in menu]
        assert "system_health" not in menu_keys
