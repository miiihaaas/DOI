"""
Permission utilities for DOI Portal RBAC.

AC#3: django-guardian object-level permissions
AC#4: Group-based permission utilities
Story 2.8: Centralized permission helpers for row-level permissions
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest

if TYPE_CHECKING:
    from doi_portal.publishers.models import Publisher
    from doi_portal.users.models import User

logger = logging.getLogger(__name__)

__all__ = [
    "PublisherPermissionMixin",
    "get_user_publishers",
    "has_publisher_access",
    "role_required",
    "sync_guardian_permissions",
]


# ============================================================================
# Story 2.8: Centralized permission helpers (Task 1)
# ============================================================================


def get_user_publishers(user: User) -> QuerySet:
    """
    Return publishers accessible to a user.

    Superuser/Admin/Superadmin: all publishers.
    Urednik/Bibliotekar: only assigned publisher.
    Future: support M2M for multiple publishers.

    Args:
        user: The user to check publisher access for.

    Returns:
        QuerySet of Publisher objects accessible to the user.
    """
    from doi_portal.publishers.models import Publisher

    if user.is_superuser:
        return Publisher.objects.all()
    if user.groups.filter(name__in=["Superadmin", "Administrator"]).exists():
        return Publisher.objects.all()
    if user.publisher:
        return Publisher.objects.filter(pk=user.publisher_id)
    return Publisher.objects.none()


def has_publisher_access(user: User, publisher: Publisher) -> bool:
    """
    Check if user has access to a specific publisher.

    Args:
        user: The user to check access for.
        publisher: The publisher to check access to.

    Returns:
        True if user has access, False otherwise.
    """
    if user.is_superuser:
        return True
    if user.groups.filter(name__in=["Superadmin", "Administrator"]).exists():
        return True
    return user.publisher_id == publisher.pk if user.publisher else False


def sync_guardian_permissions(
    user: User,
    old_publisher: Publisher | None,
    new_publisher: Publisher | None,
) -> None:
    """
    Synchronize django-guardian object permissions when publisher changes.

    Removes permissions from old publisher and assigns to new publisher.
    Idempotent - safe to call multiple times with same arguments.

    Args:
        user: The user whose permissions should be synced.
        old_publisher: The publisher being removed (or None).
        new_publisher: The publisher being assigned (or None).
    """
    from doi_portal.users.services import assign_publisher_permissions
    from doi_portal.users.services import remove_publisher_permissions

    if old_publisher == new_publisher:
        return

    if old_publisher:
        remove_publisher_permissions(user, old_publisher)
        logger.info(
            "Removed guardian permissions for user %s from publisher %s",
            user.email,
            old_publisher.pk,
        )

    if new_publisher:
        assign_publisher_permissions(user, new_publisher)
        logger.info(
            "Assigned guardian permissions for user %s to publisher %s",
            user.email,
            new_publisher.pk,
        )


class PublisherPermissionMixin(UserPassesTestMixin):
    """
    Mixin for views that require publisher-level permissions.

    Superadmin and Administrator roles have full access.
    Urednik and Bibliotekar roles require publisher assignment.
    """

    def test_func(self) -> bool:
        """Test if user has permission to access the view."""
        user = self.request.user

        if not user.is_authenticated:
            return False

        # Superadmin and Administrator have full access (uses centralized check)
        if user.is_superuser:
            return True
        if user.groups.filter(name__in=["Superadmin", "Administrator"]).exists():
            return True

        # Urednik and Bibliotekar need publisher assignment
        return user.publisher is not None

    def get_queryset(self) -> QuerySet[Any]:
        """
        Filter queryset by publisher for Urednik/Bibliotekar.

        Superadmin/Administrator see all records.
        Urednik/Bibliotekar see only their publisher's content.
        Uses get_user_publishers() for centralized publisher resolution.

        Returns:
            QuerySet: Filtered queryset based on user's role and publisher.
        """
        qs = super().get_queryset()
        user = self.request.user

        # Superuser and admin roles see all records (no filtering needed)
        if user.is_superuser:
            return qs
        if user.groups.filter(name__in=["Superadmin", "Administrator"]).exists():
            return qs

        # Use centralized helper to get accessible publishers
        user_publishers = get_user_publishers(user)

        # Filter by publisher if model has direct publisher FK
        if hasattr(self.model, "publisher"):
            return qs.filter(publisher__in=user_publishers)

        # Filter via publication__publisher for models without direct publisher FK
        # (e.g., Issue model which relates to publisher through publication)
        if hasattr(self.model, "publication"):
            return qs.filter(publication__publisher__in=user_publishers)

        return qs


def role_required(*group_names: str) -> Callable:
    """
    Decorator for function-based views requiring specific role(s).

    Args:
        group_names: One or more group names that have access.

    Returns:
        Decorated view function.

    Raises:
        PermissionDenied: If user is not authenticated or not in any of the groups.

    Example:
        @role_required("Superadmin", "Administrator")
        def admin_only_view(request):
            ...
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied

            # Superuser always has access (consistent with all other permission checks)
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if not request.user.groups.filter(name__in=group_names).exists():
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
