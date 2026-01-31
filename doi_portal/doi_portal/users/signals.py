"""
Signal handlers for user-related events.

Story 1.5: Session invalidation on password change (AC#4, NFR9)
Story 2.8: Publisher permission sync on user save (AC#1, AC#5)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any

from allauth.account.signals import password_changed
from allauth.account.signals import password_reset
from allauth.account.signals import password_set
from django.contrib.sessions.models import Session
from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

if TYPE_CHECKING:
    from django.http import HttpRequest

    from doi_portal.users.models import User

logger = logging.getLogger(__name__)


def invalidate_user_sessions(
    sender: type,
    request: HttpRequest | None,
    user: User,
    **kwargs: Any,
) -> None:
    """
    Invalidate all sessions for a user when their password is changed.

    This ensures that after a password reset, all existing sessions are logged out
    for security purposes (AC#4, NFR9).

    Uses bulk deletion with session key filtering for performance optimization
    instead of iterating through all sessions (avoids N+1 query problem).

    Args:
        sender: The sender of the signal (User model class)
        request: The HTTP request object (may be None)
        user: The user whose password was changed
        **kwargs: Additional keyword arguments
    """
    user_id_str = str(user.pk)

    # Get all non-expired sessions and filter by user
    # Note: Django stores session data encoded, so we must decode to check user_id
    # We collect session keys first, then bulk delete to minimize queries
    sessions_to_delete = []
    for session in Session.objects.filter(expire_date__gte=timezone.now()).iterator():
        try:
            session_data = session.get_decoded()
            if str(session_data.get("_auth_user_id")) == user_id_str:
                sessions_to_delete.append(session.session_key)
        except Exception:  # noqa: BLE001, S112
            # Skip malformed sessions - logging intentionally omitted for security
            continue

    # Bulk delete all user sessions in a single query
    if sessions_to_delete:
        Session.objects.filter(session_key__in=sessions_to_delete).delete()


# Connect signal handlers
# password_changed - fired when user changes password while logged in
password_changed.connect(invalidate_user_sessions)

# password_reset - fired when user resets password via email link
password_reset.connect(invalidate_user_sessions)

# password_set - fired when user sets password for the first time
password_set.connect(invalidate_user_sessions)


# ============================================================================
# Story 2.8: Publisher permission sync signals (Task 2)
# ============================================================================


@receiver(pre_save, sender="users.User")
def capture_old_publisher(
    sender: type,
    instance: User,
    **kwargs: Any,
) -> None:
    """
    Capture old publisher before save for permission sync.

    Uses _old_publisher pattern to detect publisher changes in post_save.
    Only queries DB for existing users (not new ones).

    Args:
        sender: The User model class.
        instance: The user being saved.
        **kwargs: Additional keyword arguments.
    """
    if instance.pk:
        try:
            from doi_portal.users.models import User as UserModel

            old_user = UserModel.objects.get(pk=instance.pk)
            instance._old_publisher = old_user.publisher  # type: ignore[attr-defined]
        except sender.DoesNotExist:
            instance._old_publisher = None  # type: ignore[attr-defined]
    else:
        instance._old_publisher = None  # type: ignore[attr-defined]


@receiver(post_save, sender="users.User")
def sync_publisher_permissions(
    sender: type,
    instance: User,
    created: bool,
    **kwargs: Any,
) -> None:
    """
    Auto-sync guardian permissions when publisher changes.

    Acts as a safety net for direct ORM changes (admin shell, bulk update).
    UserUpdateForm.save() already handles form-based changes - guardian's
    assign_perm is idempotent so double-assignment is harmless.

    Args:
        sender: The User model class.
        instance: The user that was saved.
        created: Whether this is a new user.
        **kwargs: Additional keyword arguments.
    """
    from doi_portal.core.permissions import sync_guardian_permissions

    old_publisher = getattr(instance, "_old_publisher", None)
    new_publisher = instance.publisher

    if old_publisher != new_publisher:
        sync_guardian_permissions(instance, old_publisher, new_publisher)
        logger.info(
            "Signal synced publisher permissions for user %s: %s -> %s",
            instance.email,
            old_publisher,
            new_publisher,
        )
