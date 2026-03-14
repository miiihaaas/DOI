"""
Tests for User model auditlog registration (Story 6.1).

Tests cover:
- AC#2: User model registered with auditlog
- AC#3: CREATE log entries for User
- AC#4: UPDATE log entries for User
- AC#5: DELETE log entries for User
- AC#6: System actions without user context
"""

import pytest
from auditlog.models import LogEntry
from auditlog.registry import auditlog
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from doi_portal.users.tests.factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestUserAuditlogRegistration:
    """AC2: Test User model is registered with auditlog."""

    def test_user_registered_with_auditlog(self):
        """AC2: User model is registered in auditlog registry."""
        assert auditlog.contains(User), "User model must be registered with auditlog"


@pytest.mark.django_db
class TestUserCreateAuditLog:
    """AC3: Test CREATE log entries for User model."""

    def test_user_create_generates_log_entry(self):
        """AC3: Creating a User generates a LogEntry with action=CREATE."""
        user = UserFactory()
        content_type = ContentType.objects.get_for_model(User)
        log_entries = LogEntry.objects.filter(
            content_type=content_type,
            object_id=str(user.pk),
            action=LogEntry.Action.CREATE,
        )
        assert log_entries.exists(), "CREATE LogEntry must exist for new User"

    def test_user_create_log_has_required_fields(self):
        """AC3: LogEntry contains timestamp, content_type, object_id, changes."""
        user = UserFactory()
        content_type = ContentType.objects.get_for_model(User)
        log_entry = LogEntry.objects.filter(
            content_type=content_type,
            object_id=str(user.pk),
            action=LogEntry.Action.CREATE,
        ).first()
        assert log_entry is not None
        assert log_entry.timestamp is not None
        assert log_entry.content_type == content_type
        assert str(log_entry.object_id) == str(user.pk)
        assert log_entry.changes is not None


@pytest.mark.django_db
class TestUserUpdateAuditLog:
    """AC4: Test UPDATE log entries for User model."""

    def test_user_update_generates_log_entry(self):
        """AC4: Updating a User generates a LogEntry with action=UPDATE."""
        user = UserFactory(name="Original Name")
        user.name = "Updated Name"
        user.save()

        content_type = ContentType.objects.get_for_model(User)
        log_entries = LogEntry.objects.filter(
            content_type=content_type,
            object_id=str(user.pk),
            action=LogEntry.Action.UPDATE,
        )
        assert log_entries.exists(), "UPDATE LogEntry must exist after User update"

    def test_user_update_log_contains_old_and_new_values(self):
        """AC4: Changes JSON contains old and new values for modified fields."""
        user = UserFactory(name="Original Name")
        user.name = "Updated Name"
        user.save()

        content_type = ContentType.objects.get_for_model(User)
        log_entry = LogEntry.objects.filter(
            content_type=content_type,
            object_id=str(user.pk),
            action=LogEntry.Action.UPDATE,
        ).first()
        assert log_entry is not None
        changes = log_entry.changes_dict
        assert "name" in changes, "Changes must include the 'name' field"
        assert changes["name"][0] == "Original Name"
        assert changes["name"][1] == "Updated Name"


@pytest.mark.django_db
class TestUserDeleteAuditLog:
    """AC5: Test DELETE log entries for User model."""

    def test_user_delete_generates_log_entry(self):
        """AC5: Deleting a User generates a LogEntry with action=DELETE."""
        user = UserFactory()
        user_pk = str(user.pk)
        content_type = ContentType.objects.get_for_model(User)
        user.delete()

        log_entries = LogEntry.objects.filter(
            content_type=content_type,
            object_id=user_pk,
            action=LogEntry.Action.DELETE,
        )
        assert log_entries.exists(), "DELETE LogEntry must exist after User delete"

    def test_user_delete_log_preserves_object_repr(self):
        """AC5: Object representation is preserved in log after deletion."""
        user = UserFactory()
        user_pk = str(user.pk)
        user_repr = str(user)
        content_type = ContentType.objects.get_for_model(User)
        user.delete()

        log_entry = LogEntry.objects.filter(
            content_type=content_type,
            object_id=user_pk,
            action=LogEntry.Action.DELETE,
        ).first()
        assert log_entry is not None
        assert log_entry.object_repr != "", "Object repr must be preserved after delete"


@pytest.mark.django_db
class TestSystemActionsWithoutUser:
    """AC6: Test system actions (Celery tasks, management commands) without user context."""

    def test_create_without_request_context_actor_is_none(self):
        """AC6: When no request context, actor is None."""
        user = UserFactory()
        content_type = ContentType.objects.get_for_model(User)
        log_entry = LogEntry.objects.filter(
            content_type=content_type,
            object_id=str(user.pk),
            action=LogEntry.Action.CREATE,
        ).first()
        assert log_entry is not None
        assert log_entry.actor is None, (
            "Actor must be None when no request context (simulating Celery task)"
        )

    def test_update_without_request_context_still_creates_log(self):
        """AC6: LogEntry is still created even without user context."""
        user = UserFactory(name="Before")
        user.name = "After"
        user.save()

        content_type = ContentType.objects.get_for_model(User)
        log_entries = LogEntry.objects.filter(
            content_type=content_type,
            object_id=str(user.pk),
        )
        assert log_entries.count() >= 2, (
            "LogEntries must be created even without request context"
        )
