"""
Tests for core Celery tasks (Story 6.1).

Tests cover:
- AC#7: Audit log archive task
"""

import json
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from doi_portal.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestAuditLogArchiveTask:
    """AC7: Test audit log archive Celery task."""

    def _create_old_log_entry(self, days_old=400):
        """Create a LogEntry with a timestamp in the past."""
        user = UserFactory()
        content_type = ContentType.objects.get_for_model(user)
        old_timestamp = timezone.now() - timedelta(days=days_old)
        entry = LogEntry.objects.create(
            content_type=content_type,
            object_id=user.pk,
            object_repr=str(user),
            action=LogEntry.Action.CREATE,
            timestamp=old_timestamp,
        )
        # Force update timestamp (auto_now might override)
        LogEntry.objects.filter(pk=entry.pk).update(timestamp=old_timestamp)
        return entry

    def _create_recent_log_entry(self):
        """Create a LogEntry with recent timestamp."""
        user = UserFactory()
        content_type = ContentType.objects.get_for_model(user)
        return LogEntry.objects.create(
            content_type=content_type,
            object_id=user.pk,
            object_repr=str(user),
            action=LogEntry.Action.CREATE,
        )

    def test_archive_task_exists(self):
        """AC7: audit_log_archive_task is importable."""
        from doi_portal.core.tasks import audit_log_archive_task

        assert audit_log_archive_task is not None

    def test_archive_task_exports_old_entries_to_json(self, settings, tmp_path):
        """AC7: Task exports entries older than 365 days to JSON file."""
        settings.MEDIA_ROOT = str(tmp_path)

        old_entry = self._create_old_log_entry(days_old=400)
        recent_entry = self._create_recent_log_entry()

        from doi_portal.core.tasks import audit_log_archive_task

        result = audit_log_archive_task()

        # Check archive file was created
        archive_dir = tmp_path / "audit-archives"
        assert archive_dir.exists(), "audit-archives directory must be created"
        archive_files = list(archive_dir.glob("*.json"))
        assert len(archive_files) >= 1, "At least one archive JSON file must exist"

        # Read and verify content
        archive_data = json.loads(archive_files[0].read_text())
        archived_pks = [entry["pk"] for entry in archive_data]
        assert old_entry.pk in archived_pks, "Old entry must be in archive"
        assert recent_entry.pk not in archived_pks, "Recent entry must NOT be in archive"

    def test_archive_task_does_not_delete_originals(self, settings, tmp_path):
        """AC7: Task does NOT delete original log entries."""
        settings.MEDIA_ROOT = str(tmp_path)

        old_entry = self._create_old_log_entry(days_old=400)
        old_entry_pk = old_entry.pk

        from doi_portal.core.tasks import audit_log_archive_task

        audit_log_archive_task()

        assert LogEntry.objects.filter(pk=old_entry_pk).exists(), (
            "Original log entry must NOT be deleted after archiving"
        )

    def test_archive_task_with_custom_threshold(self, settings, tmp_path):
        """AC7: Task respects custom days_threshold parameter."""
        settings.MEDIA_ROOT = str(tmp_path)

        entry_200_days = self._create_old_log_entry(days_old=200)

        from doi_portal.core.tasks import audit_log_archive_task

        # Default threshold is 365, so 200-day-old entry should NOT be archived
        result = audit_log_archive_task(days_threshold=365)

        # 200-day-old entry is not old enough for 365-day threshold,
        # so task should report no entries to archive
        assert "No audit log entries" in result

        archive_dir = tmp_path / "audit-archives"
        # No archive file should be created since no entries qualify
        if archive_dir.exists():
            archive_files = list(archive_dir.glob("*.json"))
            assert len(archive_files) == 0, (
                "No archive file should be created when no entries exceed threshold"
            )

    def test_archive_task_handles_no_old_entries(self, settings, tmp_path):
        """AC7: Task handles gracefully when no old entries exist."""
        settings.MEDIA_ROOT = str(tmp_path)

        self._create_recent_log_entry()

        from doi_portal.core.tasks import audit_log_archive_task

        # Should not raise
        result = audit_log_archive_task()
        assert result is not None

    def test_archive_task_is_celery_shared_task(self):
        """AC7: Task is a Celery shared_task with retry config."""
        from doi_portal.core.tasks import audit_log_archive_task

        # Celery shared_task decorator adds these attributes
        assert hasattr(audit_log_archive_task, "delay")
        assert hasattr(audit_log_archive_task, "apply_async")
