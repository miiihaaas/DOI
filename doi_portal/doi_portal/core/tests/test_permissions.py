"""
Tests for permission utilities.

AC#3: django-guardian object-level permissions
AC#4: Group permissions
Story 2.8: Centralized permission helpers
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from doi_portal.core.permissions import PublisherPermissionMixin
from doi_portal.core.permissions import get_user_publishers
from doi_portal.core.permissions import has_publisher_access
from doi_portal.core.permissions import role_required
from doi_portal.core.permissions import sync_guardian_permissions
from doi_portal.publishers.models import Publisher
from doi_portal.users.tests.factories import UserFactory

User = get_user_model()


@pytest.fixture
def request_factory():
    """Provide request factory for tests."""
    return RequestFactory()


@pytest.fixture
def superadmin_user(db):
    """Create a superadmin user."""
    user = UserFactory()
    group = Group.objects.get(name="Superadmin")
    user.groups.add(group)
    return user


@pytest.fixture
def administrator_user(db):
    """Create an administrator user."""
    user = UserFactory()
    group = Group.objects.get(name="Administrator")
    user.groups.add(group)
    return user


@pytest.fixture
def urednik_user(db):
    """Create an urednik user with publisher."""
    publisher = Publisher.objects.create(
        name="Test Publisher", doi_prefix="10.9901"
    )
    user = UserFactory()
    user.publisher = publisher
    user.save()
    group = Group.objects.get(name="Urednik")
    user.groups.add(group)
    return user


@pytest.fixture
def bibliotekar_user(db):
    """Create a bibliotekar user with publisher."""
    publisher = Publisher.objects.create(
        name="Test Publisher 2", doi_prefix="10.9902"
    )
    user = UserFactory()
    user.publisher = publisher
    user.save()
    group = Group.objects.get(name="Bibliotekar")
    user.groups.add(group)
    return user


@pytest.fixture
def urednik_no_publisher(db):
    """Create an urednik user without publisher."""
    user = UserFactory()
    group = Group.objects.get(name="Urednik")
    user.groups.add(group)
    return user


@pytest.mark.django_db
class TestRoleRequiredDecorator:
    """Test role_required decorator."""

    def test_role_required_allows_matching_role(self, request_factory, superadmin_user):
        """AC#4: role_required allows users with matching role."""

        @role_required("Superadmin")
        def protected_view(request):
            return "success"

        request = request_factory.get("/test/")
        request.user = superadmin_user
        result = protected_view(request)
        assert result == "success"

    def test_role_required_denies_wrong_role(self, request_factory, bibliotekar_user):
        """AC#4: role_required denies users without matching role."""

        @role_required("Superadmin")
        def protected_view(request):
            return "success"

        request = request_factory.get("/test/")
        request.user = bibliotekar_user
        with pytest.raises(PermissionDenied):
            protected_view(request)

    def test_role_required_allows_multiple_roles(
        self,
        request_factory,
        administrator_user,
    ):
        """AC#4: role_required allows any of multiple roles."""

        @role_required("Superadmin", "Administrator")
        def protected_view(request):
            return "success"

        request = request_factory.get("/test/")
        request.user = administrator_user
        result = protected_view(request)
        assert result == "success"

    def test_role_required_denies_unauthenticated(self, request_factory):
        """AC#4: role_required denies unauthenticated users."""

        @role_required("Superadmin")
        def protected_view(request):
            return "success"

        request = request_factory.get("/test/")
        request.user = AnonymousUser()
        with pytest.raises(PermissionDenied):
            protected_view(request)

    def test_role_required_allows_superuser(self, request_factory, db):
        """AC#4: Superuser bypasses role_required check."""

        @role_required("Superadmin")
        def protected_view(request):
            return "success"

        superuser = UserFactory(is_superuser=True)
        request = request_factory.get("/test/")
        request.user = superuser
        result = protected_view(request)
        assert result == "success"


@pytest.mark.django_db
class TestPublisherPermissionMixin:
    """Test PublisherPermissionMixin."""

    def test_mixin_allows_superadmin(self, request_factory, superadmin_user):
        """AC#4: Superadmin has full access."""

        class TestMixin(PublisherPermissionMixin):
            pass

        mixin = TestMixin()
        request = request_factory.get("/test/")
        request.user = superadmin_user
        mixin.request = request

        assert mixin.test_func() is True

    def test_mixin_allows_administrator(self, request_factory, administrator_user):
        """AC#4: Administrator has full access."""

        class TestMixin(PublisherPermissionMixin):
            pass

        mixin = TestMixin()
        request = request_factory.get("/test/")
        request.user = administrator_user
        mixin.request = request

        assert mixin.test_func() is True

    def test_mixin_allows_urednik_with_publisher(self, request_factory, urednik_user):
        """AC#4: Urednik with publisher assignment has access."""

        class TestMixin(PublisherPermissionMixin):
            pass

        mixin = TestMixin()
        request = request_factory.get("/test/")
        request.user = urednik_user
        mixin.request = request

        assert mixin.test_func() is True

    def test_mixin_denies_urednik_without_publisher(
        self,
        request_factory,
        urednik_no_publisher,
    ):
        """AC#4: Urednik without publisher assignment is denied."""

        class TestMixin(PublisherPermissionMixin):
            pass

        mixin = TestMixin()
        request = request_factory.get("/test/")
        request.user = urednik_no_publisher
        mixin.request = request

        assert mixin.test_func() is False

    def test_mixin_denies_unauthenticated(self, request_factory):
        """AC#4: Unauthenticated users are denied."""

        class TestMixin(PublisherPermissionMixin):
            pass

        mixin = TestMixin()
        request = request_factory.get("/test/")
        request.user = AnonymousUser()
        mixin.request = request

        assert mixin.test_func() is False


# ============================================================================
# Story 2.8: Tests for centralized permission helpers (Task 1)
# ============================================================================


@pytest.fixture
def publisher_a(db):
    """Create Publisher A for testing."""
    return Publisher.objects.create(
        name="Publisher A", doi_prefix="10.1111"
    )


@pytest.fixture
def publisher_b(db):
    """Create Publisher B for testing."""
    return Publisher.objects.create(
        name="Publisher B", doi_prefix="10.2222"
    )


@pytest.mark.django_db
class TestGetUserPublishers:
    """Test get_user_publishers() helper (Story 2.8 - Task 1.1)."""

    def test_superuser_gets_all_publishers(self, publisher_a, publisher_b):
        """AC#4: Superuser sees all publishers."""
        user = UserFactory(is_superuser=True)
        result = get_user_publishers(user)
        assert publisher_a in result
        assert publisher_b in result

    def test_administrator_gets_all_publishers(self, publisher_a, publisher_b):
        """AC#4: Administrator sees all publishers."""
        user = UserFactory()
        Group.objects.get(name="Administrator").user_set.add(user)
        result = get_user_publishers(user)
        assert publisher_a in result
        assert publisher_b in result

    def test_superadmin_gets_all_publishers(self, publisher_a, publisher_b):
        """AC#4: Superadmin sees all publishers."""
        user = UserFactory()
        Group.objects.get(name="Superadmin").user_set.add(user)
        result = get_user_publishers(user)
        assert publisher_a in result
        assert publisher_b in result

    def test_urednik_gets_only_assigned_publisher(self, publisher_a, publisher_b):
        """AC#2: Urednik sees only assigned publisher."""
        user = UserFactory()
        user.publisher = publisher_a
        user.save()
        Group.objects.get(name="Urednik").user_set.add(user)
        result = get_user_publishers(user)
        assert publisher_a in result
        assert publisher_b not in result

    def test_bibliotekar_gets_only_assigned_publisher(self, publisher_a, publisher_b):
        """AC#2: Bibliotekar sees only assigned publisher."""
        user = UserFactory()
        user.publisher = publisher_b
        user.save()
        Group.objects.get(name="Bibliotekar").user_set.add(user)
        result = get_user_publishers(user)
        assert publisher_b in result
        assert publisher_a not in result

    def test_user_without_publisher_gets_none(self):
        """AC#8: User without publisher gets empty queryset."""
        user = UserFactory()
        Group.objects.get(name="Urednik").user_set.add(user)
        result = get_user_publishers(user)
        assert result.count() == 0


@pytest.mark.django_db
class TestHasPublisherAccess:
    """Test has_publisher_access() helper (Story 2.8 - Task 1.2)."""

    def test_superuser_has_access_to_any_publisher(self, publisher_a, publisher_b):
        """AC#4: Superuser has access to any publisher."""
        user = UserFactory(is_superuser=True)
        assert has_publisher_access(user, publisher_a) is True
        assert has_publisher_access(user, publisher_b) is True

    def test_administrator_has_access_to_any_publisher(self, publisher_a, publisher_b):
        """AC#4: Administrator has access to any publisher."""
        user = UserFactory()
        Group.objects.get(name="Administrator").user_set.add(user)
        assert has_publisher_access(user, publisher_a) is True
        assert has_publisher_access(user, publisher_b) is True

    def test_urednik_has_access_to_assigned_publisher(self, publisher_a, publisher_b):
        """AC#2: Urednik has access only to assigned publisher."""
        user = UserFactory()
        user.publisher = publisher_a
        user.save()
        Group.objects.get(name="Urednik").user_set.add(user)
        assert has_publisher_access(user, publisher_a) is True
        assert has_publisher_access(user, publisher_b) is False

    def test_user_without_publisher_has_no_access(self, publisher_a):
        """AC#8: User without publisher has no access."""
        user = UserFactory()
        Group.objects.get(name="Urednik").user_set.add(user)
        assert has_publisher_access(user, publisher_a) is False


@pytest.mark.django_db
class TestSyncGuardianPermissions:
    """Test sync_guardian_permissions() service (Story 2.8 - Task 1.3)."""

    def test_sync_assigns_new_permissions(self, publisher_a):
        """AC#1: Assigning publisher grants guardian permissions."""
        from guardian.shortcuts import get_perms

        user = UserFactory()
        sync_guardian_permissions(user, old_publisher=None, new_publisher=publisher_a)
        perms = get_perms(user, publisher_a)
        assert "view_publisher" in perms
        assert "change_publisher" in perms

    def test_sync_removes_old_permissions(self, publisher_a, publisher_b):
        """AC#5: Changing publisher removes old permissions and assigns new."""
        from guardian.shortcuts import get_perms

        user = UserFactory()
        # First assign publisher_a
        sync_guardian_permissions(user, old_publisher=None, new_publisher=publisher_a)
        # Then change to publisher_b
        sync_guardian_permissions(
            user, old_publisher=publisher_a, new_publisher=publisher_b
        )
        perms_a = get_perms(user, publisher_a)
        perms_b = get_perms(user, publisher_b)
        assert "view_publisher" not in perms_a
        assert "change_publisher" not in perms_a
        assert "view_publisher" in perms_b
        assert "change_publisher" in perms_b

    def test_sync_removes_all_when_publisher_cleared(self, publisher_a):
        """AC#5: Clearing publisher removes all permissions."""
        from guardian.shortcuts import get_perms

        user = UserFactory()
        sync_guardian_permissions(user, old_publisher=None, new_publisher=publisher_a)
        sync_guardian_permissions(user, old_publisher=publisher_a, new_publisher=None)
        perms = get_perms(user, publisher_a)
        assert "view_publisher" not in perms
        assert "change_publisher" not in perms

    def test_sync_noop_when_same_publisher(self, publisher_a):
        """sync_guardian_permissions is noop when publisher unchanged."""
        from guardian.shortcuts import get_perms

        user = UserFactory()
        sync_guardian_permissions(user, old_publisher=None, new_publisher=publisher_a)
        # Calling again with same should not raise
        sync_guardian_permissions(
            user, old_publisher=publisher_a, new_publisher=publisher_a
        )
        perms = get_perms(user, publisher_a)
        assert "view_publisher" in perms
        assert "change_publisher" in perms

    def test_sync_noop_when_both_none(self):
        """sync_guardian_permissions is noop when both are None."""
        user = UserFactory()
        # Should not raise any error
        sync_guardian_permissions(user, old_publisher=None, new_publisher=None)


# ============================================================================
# Story 2.8: Tests for signal-based permission sync (Task 2)
# ============================================================================


@pytest.mark.django_db
class TestPublisherPermissionSignals:
    """Test signal-based publisher permission sync (Story 2.8 - Task 2)."""

    def test_signal_assigns_permissions_on_publisher_set(self, publisher_a):
        """AC#1: Setting publisher on user auto-assigns guardian permissions."""
        from guardian.shortcuts import get_perms

        user = UserFactory()
        user.publisher = publisher_a
        user.save()
        perms = get_perms(user, publisher_a)
        assert "view_publisher" in perms
        assert "change_publisher" in perms

    def test_signal_syncs_permissions_on_publisher_change(
        self, publisher_a, publisher_b
    ):
        """AC#5: Changing publisher removes old and assigns new permissions."""
        from guardian.shortcuts import get_perms

        user = UserFactory()
        user.publisher = publisher_a
        user.save()

        # Change publisher
        user.publisher = publisher_b
        user.save()

        perms_a = get_perms(user, publisher_a)
        perms_b = get_perms(user, publisher_b)
        assert "view_publisher" not in perms_a
        assert "change_publisher" not in perms_a
        assert "view_publisher" in perms_b
        assert "change_publisher" in perms_b

    def test_signal_removes_permissions_on_publisher_cleared(self, publisher_a):
        """AC#5: Clearing publisher removes all permissions."""
        from guardian.shortcuts import get_perms

        user = UserFactory()
        user.publisher = publisher_a
        user.save()

        # Clear publisher
        user.publisher = None
        user.save()

        perms = get_perms(user, publisher_a)
        assert "view_publisher" not in perms
        assert "change_publisher" not in perms

    def test_signal_noop_on_non_publisher_field_change(self, publisher_a):
        """Signal should not re-sync when non-publisher field changes."""
        from guardian.shortcuts import get_perms

        user = UserFactory()
        user.publisher = publisher_a
        user.save()

        # Change name only - permissions should remain
        user.name = "New Name"
        user.save()

        perms = get_perms(user, publisher_a)
        assert "view_publisher" in perms
        assert "change_publisher" in perms

    def test_signal_on_new_user_creation_with_publisher(self, publisher_a):
        """AC#1: New user with publisher gets permissions on creation."""
        from guardian.shortcuts import get_perms

        user = UserFactory()
        # UserFactory creates user then we set publisher in a separate save
        user.publisher = publisher_a
        user.save()

        perms = get_perms(user, publisher_a)
        assert "view_publisher" in perms
        assert "change_publisher" in perms
