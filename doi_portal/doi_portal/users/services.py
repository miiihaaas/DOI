"""
User management service functions (Story 1.6).

This module provides business logic for:
- Session invalidation for deactivated users (AC#5)
- Guardian permission assignment for publishers (AC#3)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.sessions.models import Session
from django.utils import timezone

if TYPE_CHECKING:
    from doi_portal.publishers.models import Publisher
    from doi_portal.users.models import User

logger = logging.getLogger(__name__)

# Check if guardian is available at module load time
try:
    from guardian.shortcuts import assign_perm
    from guardian.shortcuts import remove_perm

    GUARDIAN_AVAILABLE = True
except ImportError:
    GUARDIAN_AVAILABLE = False
    assign_perm = None  # type: ignore[assignment, misc]
    remove_perm = None  # type: ignore[assignment, misc]


def invalidate_user_sessions(user: User) -> int:
    """
    Clear all active sessions for a specific user.

    Used when deactivating a user to terminate their existing sessions (AC#5).

    Args:
        user: The user whose sessions should be invalidated.

    Returns:
        Number of sessions deleted.
    """
    user_id_str = str(user.pk)
    sessions_to_delete = []

    # Get all non-expired sessions and filter by user
    for session in Session.objects.filter(expire_date__gte=timezone.now()).iterator():
        try:
            session_data = session.get_decoded()
            if str(session_data.get("_auth_user_id")) == user_id_str:
                sessions_to_delete.append(session.session_key)
        except Exception:  # noqa: BLE001
            # Log and skip malformed sessions (ruff S112 fix)
            logger.warning(
                "Failed to decode session %s while invalidating user sessions",
                session.session_key,
            )
            continue

    # Bulk delete all user sessions
    if sessions_to_delete:
        Session.objects.filter(session_key__in=sessions_to_delete).delete()

    return len(sessions_to_delete)


def assign_publisher_permissions(user: User, publisher: Publisher | None) -> bool:
    """
    Assign row-level permissions to user for publisher.

    Uses django-guardian for object-level permissions (AC#3).

    Args:
        user: The user to assign permissions to.
        publisher: The publisher to grant permissions for (or None to skip).

    Returns:
        True if permissions were assigned, False if skipped or guardian unavailable.
    """
    if publisher is None:
        return False

    if not GUARDIAN_AVAILABLE:
        logger.debug("Guardian not available, skipping permission assignment")
        return False

    assign_perm("publishers.view_publisher", user, publisher)
    assign_perm("publishers.change_publisher", user, publisher)
    logger.info(
        "Assigned publisher permissions to user %s for publisher %s",
        user.email,
        publisher.pk,
    )
    return True


def remove_publisher_permissions(user: User, publisher: Publisher | None) -> bool:
    """
    Remove row-level permissions from user for publisher.

    Uses django-guardian for object-level permissions (AC#4).

    Args:
        user: The user to remove permissions from.
        publisher: The publisher to revoke permissions for (or None to skip).

    Returns:
        True if permissions were removed, False if skipped or guardian unavailable.
    """
    if publisher is None:
        return False

    if not GUARDIAN_AVAILABLE:
        logger.debug("Guardian not available, skipping permission removal")
        return False

    remove_perm("publishers.view_publisher", user, publisher)
    remove_perm("publishers.change_publisher", user, publisher)
    logger.info(
        "Removed publisher permissions from user %s for publisher %s",
        user.email,
        publisher.pk,
    )
    return True
