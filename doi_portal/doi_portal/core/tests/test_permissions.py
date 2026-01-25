"""
Tests for permission utilities.

AC#3: django-guardian object-level permissions
AC#4: Group permissions
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from doi_portal.core.permissions import PublisherPermissionMixin
from doi_portal.core.permissions import role_required
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
    publisher = Publisher.objects.create(name="Test Publisher")
    user = UserFactory()
    user.publisher = publisher
    user.save()
    group = Group.objects.get(name="Urednik")
    user.groups.add(group)
    return user


@pytest.fixture
def bibliotekar_user(db):
    """Create a bibliotekar user with publisher."""
    publisher = Publisher.objects.create(name="Test Publisher 2")
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
        self, request_factory, administrator_user,
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
        self, request_factory, urednik_no_publisher,
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
