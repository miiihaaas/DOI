"""
Custom middleware for DOI Portal.

LastActivityMiddleware - Updates User.last_activity on each authenticated request.
"""

from collections.abc import Callable

from django.http import HttpRequest
from django.http import HttpResponse
from django.utils import timezone


class LastActivityMiddleware:
    """
    Update last_activity on each authenticated request.

    This middleware tracks user activity for session management (AC#2).
    The last_activity field is updated without triggering model save signals
    to minimize database overhead.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Update without triggering model save signals
            # This is more efficient than user.save()
            request.user.__class__.objects.filter(pk=request.user.pk).update(
                last_activity=timezone.now(),
            )

        return response
