"""
Signal handlers for user-related events (Story 1.5).

This module contains signal handlers for:
- Session invalidation on password change (AC#4, NFR9)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from allauth.account.signals import password_changed
from allauth.account.signals import password_reset
from allauth.account.signals import password_set
from django.contrib.sessions.models import Session
from django.utils import timezone

if TYPE_CHECKING:
    from django.http import HttpRequest

    from doi_portal.users.models import User


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
