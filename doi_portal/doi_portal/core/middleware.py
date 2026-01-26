"""
Custom middleware for DOI Portal.

LastActivityMiddleware - Updates User.last_activity on each authenticated request.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils import timezone

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest
    from django.http import HttpResponse

    from doi_portal.users.models import User


class LastActivityMiddleware:
    """
    Update last_activity on each authenticated request.

    This middleware tracks user activity for session management (AC#5).

    Optimization:
    - Only updates if more than 60 seconds since last update (throttling)
    - Skips static file requests
    - Uses update_fields for efficient database write
    """

    # Throttle interval in seconds - avoid excessive DB writes
    THROTTLE_SECONDS = 60

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Skip static files
            if not self._is_static_request(request):
                self._update_last_activity(request.user)

        return response

    def _is_static_request(self, request: HttpRequest) -> bool:
        """Check if request is for static files."""
        return request.path.startswith(("/static/", "/media/", "/__debug__/"))

    def _update_last_activity(self, user: User) -> None:
        """
        Update last_activity if more than THROTTLE_SECONDS have passed.

        Uses queryset update for efficiency (avoids triggering signals).
        """
        now = timezone.now()

        # Only update if last_activity is None or older than throttle interval
        should_update = user.last_activity is None or (
            (now - user.last_activity).total_seconds() > self.THROTTLE_SECONDS
        )

        if should_update:
            # Use queryset update for efficiency - doesn't trigger model signals
            user.__class__.objects.filter(pk=user.pk).update(last_activity=now)
