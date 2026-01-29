"""
Publisher access mixins.

Story 2.1 - Task 3.5: Permission mixins for Publisher views.
Story 2.4 - Task 3: PublisherScopedMixin for row-level permissions.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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


class PublisherScopedMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that scopes access based on publisher assignment.

    Story 2.4 - Task 3: Row-level permissions for publications.

    - Superadmin/Administrator: full access to all publications
    - Urednik/Bibliotekar: only publications from their assigned publisher
    - Unauthenticated: redirect to login
    """

    def _get_user_role_flags(self):
        """
        Cache and return user role flags to avoid redundant DB queries.

        Returns dict with: is_admin, is_urednik, is_bibliotekar, has_publisher.
        Called once per request, result is cached on the view instance.
        """
        if hasattr(self, "_role_flags"):
            return self._role_flags

        user = self.request.user
        flags = {
            "is_admin": False,
            "is_urednik": False,
            "is_bibliotekar": False,
            "has_publisher": hasattr(user, "publisher") and user.publisher is not None,
        }

        if user.is_superuser:
            flags["is_admin"] = True
        else:
            # Single DB query to get all group names
            user_groups = set(user.groups.values_list("name", flat=True))
            if "Administrator" in user_groups or "Superadmin" in user_groups:
                flags["is_admin"] = True
            if "Urednik" in user_groups:
                flags["is_urednik"] = True
            if "Bibliotekar" in user_groups:
                flags["is_bibliotekar"] = True

        self._role_flags = flags
        return flags

    def test_func(self):
        """Check if user has appropriate role and publisher assignment."""
        user = self.request.user
        if not user.is_authenticated:
            return False

        flags = self._get_user_role_flags()

        # Superuser/Administrator/Superadmin - full access
        if flags["is_admin"]:
            return True

        # Urednik/Bibliotekar - must have publisher assignment
        if flags["is_urednik"] or flags["is_bibliotekar"]:
            return flags["has_publisher"]

        return False

    def get_scoped_queryset(self, queryset):
        """Filter queryset based on user's publisher assignment."""
        flags = self._get_user_role_flags()

        if flags["is_admin"]:
            return queryset

        # Urednik/Bibliotekar - filter by publisher
        if flags["has_publisher"]:
            return queryset.filter(publisher=self.request.user.publisher)

        return queryset.none()

    def handle_no_permission(self):
        """Raise 403 for authenticated users without permission."""
        if self.request.user.is_authenticated:
            raise PermissionDenied("Nemate dozvolu za pristup ovoj stranici.")
        return super().handle_no_permission()


class PublisherScopedEditMixin(PublisherScopedMixin):
    """
    Mixin for edit views that restricts Bibliotekar to read-only.

    Story 2.4 - Task 3.5: Urednik can edit their publisher's publications,
    Bibliotekar cannot edit (read-only access).
    """

    def test_func(self):
        """Check if user has edit permission."""
        user = self.request.user
        if not user.is_authenticated:
            return False

        flags = self._get_user_role_flags()

        # Superuser/Administrator/Superadmin - full access
        if flags["is_admin"]:
            return True

        # Urednik can edit their publisher's publications
        if flags["is_urednik"]:
            return flags["has_publisher"]

        # Bibliotekar cannot edit
        return False
