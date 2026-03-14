"""
Tests for middleware configuration (Story 6.1).

Tests cover:
- AC#1: AuditlogMiddleware is active in MIDDLEWARE settings
"""

import pytest
from django.conf import settings


@pytest.mark.django_db
class TestAuditlogMiddleware:
    """Test that AuditlogMiddleware is correctly configured."""

    def test_auditlog_middleware_in_settings(self):
        """AC1: AuditlogMiddleware is in MIDDLEWARE list."""
        assert "auditlog.middleware.AuditlogMiddleware" in settings.MIDDLEWARE

    def test_auditlog_middleware_after_authentication(self):
        """AC1: AuditlogMiddleware is positioned after AuthenticationMiddleware."""
        middleware_list = settings.MIDDLEWARE
        auth_index = middleware_list.index(
            "django.contrib.auth.middleware.AuthenticationMiddleware"
        )
        auditlog_index = middleware_list.index(
            "auditlog.middleware.AuditlogMiddleware"
        )
        assert auditlog_index > auth_index, (
            "AuditlogMiddleware must be after AuthenticationMiddleware"
        )

    def test_auditlog_in_installed_apps(self):
        """AC1: auditlog is in INSTALLED_APPS."""
        assert "auditlog" in settings.INSTALLED_APPS

    def test_celery_beat_schedule_has_archive_task(self):
        """AC7: CELERY_BEAT_SCHEDULE contains the audit log archive task."""
        assert hasattr(settings, "CELERY_BEAT_SCHEDULE"), (
            "CELERY_BEAT_SCHEDULE must be defined in settings"
        )
        assert "audit-log-archive-monthly" in settings.CELERY_BEAT_SCHEDULE, (
            "audit-log-archive-monthly task must be in CELERY_BEAT_SCHEDULE"
        )
        task_config = settings.CELERY_BEAT_SCHEDULE["audit-log-archive-monthly"]
        assert task_config["task"] == "doi_portal.core.tasks.audit_log_archive_task"
        assert task_config["kwargs"]["days_threshold"] == 365
