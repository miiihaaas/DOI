"""
Tests for RBAC (Role-Based Access Control) functionality.

Tests User model extensions and Group configuration.
"""

import pytest
from django.conf import settings
from django.contrib.auth.models import Group

from doi_portal.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestRBACGroups:
    """Test RBAC group configuration."""

    def test_superadmin_group_exists(self):
        """AC#2: Superadmin group is created."""
        assert Group.objects.filter(name="Superadmin").exists()

    def test_administrator_group_exists(self):
        """AC#2: Administrator group is created."""
        assert Group.objects.filter(name="Administrator").exists()

    def test_urednik_group_exists(self):
        """AC#2: Urednik group is created."""
        assert Group.objects.filter(name="Urednik").exists()

    def test_bibliotekar_group_exists(self):
        """AC#2: Bibliotekar group is created."""
        assert Group.objects.filter(name="Bibliotekar").exists()

    def test_all_four_groups_exist(self):
        """AC#2: All 4 RBAC groups are created."""
        group_names = ["Superadmin", "Administrator", "Urednik", "Bibliotekar"]
        for name in group_names:
            assert Group.objects.filter(name=name).exists(), f"Group {name} not found"

    def test_user_can_be_assigned_to_group(self):
        """Test user can be assigned to RBAC group."""
        user = UserFactory()
        group = Group.objects.get(name="Bibliotekar")
        user.groups.add(group)
        assert user.groups.filter(name="Bibliotekar").exists()


@pytest.mark.django_db
class TestUserModel:
    """Test User model extensions for RBAC."""

    def test_user_has_publisher_field(self):
        """AC#1: User model has publisher FK field."""
        user = UserFactory()
        assert hasattr(user, "publisher")

    def test_user_publisher_is_nullable(self):
        """AC#1: Publisher FK is nullable until Publisher model exists."""
        user = UserFactory()
        assert user.publisher is None

    def test_user_has_last_activity_field(self):
        """AC#1: User model has last_activity DateTimeField."""
        user = UserFactory()
        assert hasattr(user, "last_activity")

    def test_user_last_activity_is_nullable(self):
        """AC#1: last_activity is nullable."""
        user = UserFactory()
        assert user.last_activity is None

    def test_user_has_is_active_field(self):
        """AC#5: User model includes is_active field for activation/deactivation."""
        user = UserFactory()
        assert hasattr(user, "is_active")

    def test_user_is_active_by_default(self):
        """AC#5: New users are active by default."""
        user = UserFactory()
        assert user.is_active is True


@pytest.mark.django_db
class TestDjangoGuardian:
    """Test django-guardian integration."""

    def test_guardian_backend_is_configured(self):
        """AC#3: django-guardian backend is in AUTHENTICATION_BACKENDS."""
        backend = "guardian.backends.ObjectPermissionBackend"
        assert backend in settings.AUTHENTICATION_BACKENDS

    def test_guardian_raise_403_is_enabled(self):
        """AC#3: GUARDIAN_RAISE_403 is True."""
        assert settings.GUARDIAN_RAISE_403 is True
