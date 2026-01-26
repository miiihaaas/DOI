"""
Publisher access mixins.

Story 2.1 - Task 3.5: Permission mixins for Publisher views.
"""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class AdministratorRequiredMixin(UserPassesTestMixin):
    """
    Mixin that requires user to be Administrator or Superadmin.

    Used for Publisher management which requires Administrator role.
    """

    def test_func(self):
        """Check if user has Administrator or Superadmin access."""
        user = self.request.user
        if not user.is_authenticated:
            return False

        # Superuser always has access
        if user.is_superuser:
            return True

        # Check for Administrator or Superadmin group
        allowed_groups = ["Administrator", "Superadmin"]
        return user.groups.filter(name__in=allowed_groups).exists()

    def handle_no_permission(self):
        """Raise 403 for authenticated users without permission."""
        if self.request.user.is_authenticated:
            raise PermissionDenied("Nemate dozvolu za pristup ovoj stranici.")
        return super().handle_no_permission()
