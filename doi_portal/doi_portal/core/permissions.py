"""
Permission utilities for DOI Portal RBAC.

AC#3: django-guardian object-level permissions
AC#4: Group-based permission utilities
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest

__all__ = ["PublisherPermissionMixin", "role_required"]


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

        # Superadmin and Administrator have full access
        if user.groups.filter(name__in=["Superadmin", "Administrator"]).exists():
            return True

        # Urednik and Bibliotekar need publisher assignment
        return user.publisher is not None

    def get_queryset(self) -> QuerySet[Any]:
        """
        Filter queryset by publisher for Urednik/Bibliotekar.

        Superadmin/Administrator see all records.
        Urednik/Bibliotekar see only their publisher's content.

        Returns:
            QuerySet: Filtered queryset based on user's role and publisher.
        """
        qs = super().get_queryset()
        user = self.request.user

        # Superadmin/Administrator see all
        if user.groups.filter(name__in=["Superadmin", "Administrator"]).exists():
            return qs

        # Others see only their publisher's content
        if hasattr(self.model, "publisher"):
            return qs.filter(publisher=user.publisher)

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

            if not request.user.groups.filter(name__in=group_names).exists():
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
