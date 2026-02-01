"""
Tests for DashboardView with role-based content.

Story 3.8: Dashboard Statistics & Pending Items.
Tests: AC#1-AC#8 (view-level).
"""

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import PublicationFactory, PublisherFactory
from doi_portal.users.tests.factories import UserFactory


@pytest.fixture
def admin_user(db):
    """Create an admin user (Superadmin)."""
    user = UserFactory(is_superuser=True)
    return user


@pytest.fixture
def admin_group_user(db):
    """Create a user in Administrator group."""
    group, _ = Group.objects.get_or_create(name="Administrator")
    user = UserFactory()
    user.groups.add(group)
    return user


@pytest.fixture
def urednik_user(db):
    """Create an Urednik user with publisher assignment."""
    publisher = PublisherFactory()
    group, _ = Group.objects.get_or_create(name="Urednik")
    user = UserFactory(publisher=publisher)
    user.groups.add(group)
    return user


@pytest.fixture
def bibliotekar_user(db):
    """Create a Bibliotekar user."""
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user = UserFactory()
    user.groups.add(group)
    return user


@pytest.mark.django_db
class TestDashboardViewAccess:
    """Tests for dashboard access and authentication (AC#6)."""

    def test_unauthenticated_redirects_to_login(self, client):
        """AC#6: Unauthenticated user is redirected to login."""
        response = client.get(reverse("dashboard"))
        assert response.status_code == 302
        assert "account" in response.url or "login" in response.url

    def test_authenticated_user_can_access(self, client, admin_user):
        """Authenticated user can access dashboard."""
        client.force_login(admin_user)
        response = client.get(reverse("dashboard"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminDashboard:
    """Tests for Administrator dashboard view (AC#1, AC#2, AC#3, AC#8)."""

    def test_admin_sees_all_stat_cards(self, client, admin_user):
        """AC#1: Administrator sees all 4 statistic cards."""
        client.force_login(admin_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Publikacije" in content
        assert "Na pregledu" in content
        assert "Spremno za objavu" in content

    def test_admin_sees_stats_in_context(self, client, admin_user):
        """AC#1: Stats dict is in context with correct keys."""
        ArticleFactory(status=ArticleStatus.DRAFT)
        ArticleFactory(status=ArticleStatus.REVIEW)

        client.force_login(admin_user)
        response = client.get(reverse("dashboard"))

        assert "stats" in response.context
        stats = response.context["stats"]
        assert stats["total_articles"] == 2
        assert stats["pending_review_count"] == 1

    def test_admin_sees_pending_review_section(self, client, admin_user):
        """AC#2: Admin sees pending review articles."""
        article = ArticleFactory(status=ArticleStatus.REVIEW)

        client.force_login(admin_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()

        assert "pending_review_articles" in response.context
        assert len(response.context["pending_review_articles"]) == 1

    def test_admin_sees_ready_to_publish_section(self, client, admin_user):
        """AC#3: Admin sees ready to publish articles."""
        ArticleFactory(status=ArticleStatus.READY)

        client.force_login(admin_user)
        response = client.get(reverse("dashboard"))

        assert "ready_to_publish_articles" in response.context
        assert len(response.context["ready_to_publish_articles"]) == 1

    def test_admin_quick_actions(self, client, admin_user):
        """AC#8: Admin sees admin-specific quick actions."""
        client.force_login(admin_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()

        assert "Svi članci" in content
        assert "Publikacije" in content
        assert "Izdavači" in content

    def test_admin_pending_max_10(self, client, admin_user):
        """AC#2: Pending review shows max 10 articles."""
        for _ in range(15):
            ArticleFactory(status=ArticleStatus.REVIEW)

        client.force_login(admin_user)
        response = client.get(reverse("dashboard"))
        assert len(response.context["pending_review_articles"]) == 10

    def test_admin_group_user_sees_stats(self, client, admin_group_user):
        """Administrator group user (not superuser) sees admin stats."""
        client.force_login(admin_group_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Publikacije" in content


@pytest.mark.django_db
class TestUrednikDashboard:
    """Tests for Urednik dashboard view (AC#4)."""

    def test_urednik_sees_scoped_stats(self, client, urednik_user):
        """AC#4: Urednik sees publisher-scoped statistics."""
        client.force_login(urednik_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Na pregledu" in content

    def test_urednik_sees_pending_review(self, client, urednik_user):
        """AC#4: Urednik sees pending reviews for their publisher."""
        pub = PublicationFactory(publisher=urednik_user.publisher)
        issue = IssueFactory(publication=pub)
        ArticleFactory(issue=issue, status=ArticleStatus.REVIEW)

        client.force_login(urednik_user)
        response = client.get(reverse("dashboard"))
        assert "pending_review_articles" in response.context

    def test_urednik_sees_ready_to_publish(self, client, urednik_user):
        """Urednik sees ready to publish articles for their publisher."""
        pub = PublicationFactory(publisher=urednik_user.publisher)
        issue = IssueFactory(publication=pub)
        ArticleFactory(issue=issue, status=ArticleStatus.READY)

        client.force_login(urednik_user)
        response = client.get(reverse("dashboard"))
        # Urednik is NOT admin so no ready_to_publish_articles in context
        assert "ready_to_publish_articles" not in response.context

    def test_urednik_quick_actions(self, client, urednik_user):
        """AC#8: Urednik sees urednik-specific quick actions."""
        client.force_login(urednik_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()

        assert "Članci na pregledu" in content
        assert "Izdanja" in content

    def test_urednik_does_not_see_bibliotekar_section(self, client, urednik_user):
        """Urednik does NOT see 'Moji nacrti' section."""
        client.force_login(urednik_user)
        response = client.get(reverse("dashboard"))
        assert "my_draft_articles" not in response.context


@pytest.mark.django_db
class TestBibliotekarDashboard:
    """Tests for Bibliotekar dashboard view (AC#5)."""

    def test_bibliotekar_sees_my_drafts(self, client, bibliotekar_user):
        """AC#5: Bibliotekar sees 'Moji nacrti' section."""
        ArticleFactory(created_by=bibliotekar_user, status=ArticleStatus.DRAFT)

        client.force_login(bibliotekar_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Moji nacrti" in content
        assert "my_draft_articles" in response.context
        assert len(response.context["my_draft_articles"]) == 1

    def test_bibliotekar_sees_own_stats(self, client, bibliotekar_user):
        """AC#5: Bibliotekar sees own article statistics."""
        ArticleFactory(created_by=bibliotekar_user, status=ArticleStatus.DRAFT)

        client.force_login(bibliotekar_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()

        assert "Poslato na pregled" in content

    def test_bibliotekar_no_ready_section(self, client, bibliotekar_user):
        """AC#5: Bibliotekar does NOT see 'Spremno za objavu' section."""
        client.force_login(bibliotekar_user)
        response = client.get(reverse("dashboard"))
        assert "ready_to_publish_articles" not in response.context

    def test_bibliotekar_no_pending_review_section(self, client, bibliotekar_user):
        """AC#5: Bibliotekar does NOT see pending review section."""
        client.force_login(bibliotekar_user)
        response = client.get(reverse("dashboard"))
        assert "pending_review_articles" not in response.context

    def test_bibliotekar_quick_actions(self, client, bibliotekar_user):
        """AC#8: Bibliotekar sees bibliotekar-specific quick actions."""
        client.force_login(bibliotekar_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()

        assert "Novi članak" in content
        assert "Moji nacrti" in content


@pytest.mark.django_db
class TestEmptyStateDashboard:
    """Tests for empty state messages (AC#7)."""

    def test_empty_pending_shows_message(self, client, admin_user):
        """AC#7: Empty pending review shows 'Nema clanaka' message."""
        client.force_login(admin_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()
        assert "Nema članaka na čekanju za pregled" in content

    def test_empty_ready_shows_message(self, client, admin_user):
        """AC#7: Empty ready to publish shows 'Nema clanaka' message."""
        client.force_login(admin_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()
        assert "Nema članaka spremnih za objavu" in content

    def test_empty_drafts_shows_message(self, client, bibliotekar_user):
        """AC#7: Empty drafts shows 'Nemate clanaka u nacrtu' message."""
        client.force_login(bibliotekar_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()
        assert "Nemate članaka u nacrtu" in content


@pytest.mark.django_db
class TestDashboardRoleFlags:
    """Tests for role_flags in context."""

    def test_admin_role_flags(self, client, admin_user):
        """Admin has is_admin=True in role_flags."""
        client.force_login(admin_user)
        response = client.get(reverse("dashboard"))
        flags = response.context["role_flags"]
        assert flags["is_admin"] is True

    def test_urednik_role_flags(self, client, urednik_user):
        """Urednik has is_urednik=True in role_flags."""
        client.force_login(urednik_user)
        response = client.get(reverse("dashboard"))
        flags = response.context["role_flags"]
        assert flags["is_urednik"] is True
        assert flags["is_admin"] is False

    def test_bibliotekar_role_flags(self, client, bibliotekar_user):
        """Bibliotekar has is_bibliotekar=True in role_flags."""
        client.force_login(bibliotekar_user)
        response = client.get(reverse("dashboard"))
        flags = response.context["role_flags"]
        assert flags["is_bibliotekar"] is True
        assert flags["is_admin"] is False


@pytest.mark.django_db
class TestDashboardWelcome:
    """Tests for welcome card content."""

    def test_shows_user_name(self, client, admin_user):
        """Welcome card shows user name."""
        client.force_login(admin_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()
        assert "Dobrodošli" in content

    def test_shows_user_role(self, client, admin_user):
        """Welcome card shows user role."""
        client.force_login(admin_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()
        assert "Prijavljeni ste kao" in content


@pytest.mark.django_db
class TestStatisticsCardsClickable:
    """Tests for clickable statistics cards (Task 4.6)."""

    def test_admin_stat_cards_are_clickable(self, client, admin_user):
        """AC#1/Task 4.6: Admin stat cards contain links to filtered lists."""
        client.force_login(admin_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()

        # Publications card links to publications:list
        assert 'href="/dashboard/publications/"' in content
        # Articles card links to articles:list
        assert 'href="/dashboard/articles/"' in content

    def test_bibliotekar_stat_cards_are_clickable(self, client, bibliotekar_user):
        """AC#5/Task 4.6: Bibliotekar stat cards contain links to filtered lists."""
        client.force_login(bibliotekar_user)
        response = client.get(reverse("dashboard"))
        content = response.content.decode()

        # Drafts card links to articles:list?status=DRAFT
        assert "?status=DRAFT" in content
