"""
Permission mixins for user management views (Story 1.6).

This module provides:
- SuperadminRequiredMixin: Restricts access to Superadmin group or is_superuser
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

# Permission denied message (ruff EM101 fix)
MSG_SUPERADMIN_REQUIRED = "Samo Superadmin ima pristup ovoj stranici."


class SuperadminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires user to be in Superadmin group or be a Django superuser.

    This mixin combines LoginRequiredMixin and UserPassesTestMixin to:
    1. Redirect anonymous users to login
    2. Return 403 Forbidden for authenticated non-Superadmin users

    AC#6: Non-Superadmin users receive 403 Forbidden.
    """

    def test_func(self) -> bool:
        """
        Test if user has Superadmin privileges.

        Returns:
            True if user is in Superadmin group or is Django superuser.
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        return user.groups.filter(name="Superadmin").exists() or user.is_superuser

    def handle_no_permission(self):
        """
        Handle permission denied case.

        Raises PermissionDenied (403) for authenticated users without
        Superadmin privileges. For unauthenticated users, redirects to login.
        """
        if self.request.user.is_authenticated:
            raise PermissionDenied(MSG_SUPERADMIN_REQUIRED)
        # For unauthenticated users, LoginRequiredMixin handles redirect to login
        return super().handle_no_permission()
