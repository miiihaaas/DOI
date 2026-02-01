"""
Tests for dashboard service functions.

Story 3.8: Dashboard Statistics & Pending Items.
Tests: AC#1, AC#4, AC#5, AC#6 (statistics), AC#2, AC#3 (pending items).
"""

import pytest
from django.contrib.auth.models import Group

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.dashboard.services import (
    get_admin_statistics,
    get_bibliotekar_statistics,
    get_dashboard_statistics,
    get_my_draft_articles,
    get_pending_review_articles,
    get_ready_to_publish_articles,
    get_urednik_statistics,
)
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import PublicationFactory, PublisherFactory
from doi_portal.users.tests.factories import UserFactory


# ============================================================
# Task 1 Tests: Statistics Functions (AC#1, #4, #5, #6)
# ============================================================


@pytest.mark.django_db
class TestAdminStatistics:
    """Tests for get_admin_statistics (AC#1)."""

    def test_returns_all_counts(self):
        """Admin stats include total_publications, total_articles, pending, ready, published, draft."""
        ArticleFactory(status=ArticleStatus.DRAFT)
        ArticleFactory(status=ArticleStatus.REVIEW)
        ArticleFactory(status=ArticleStatus.READY)
        ArticleFactory(status=ArticleStatus.PUBLISHED)

        stats = get_admin_statistics()

        assert stats["total_articles"] == 4
        assert stats["pending_review_count"] == 1
        assert stats["ready_to_publish_count"] == 1
        assert stats["published_count"] == 1
        assert stats["draft_count"] == 1

    def test_includes_total_publications(self):
        """Admin stats include total publication count."""
        PublicationFactory()
        PublicationFactory()

        stats = get_admin_statistics()
        assert stats["total_publications"] == 2

    def test_empty_system(self):
        """Admin stats return zeros when no articles or publications exist."""
        stats = get_admin_statistics()
        assert stats["total_articles"] == 0
        assert stats["total_publications"] == 0
        assert stats["pending_review_count"] == 0
        assert stats["ready_to_publish_count"] == 0
        assert stats["published_count"] == 0
        assert stats["draft_count"] == 0

    def test_excludes_withdrawn(self):
        """Withdrawn articles are counted in total but not in other categories."""
        ArticleFactory(status=ArticleStatus.WITHDRAWN)
        ArticleFactory(status=ArticleStatus.DRAFT)

        stats = get_admin_statistics()
        assert stats["total_articles"] == 2
        assert stats["draft_count"] == 1


@pytest.mark.django_db
class TestUrednikStatistics:
    """Tests for get_urednik_statistics (AC#4)."""

    def test_scoped_to_publisher(self):
        """Urednik stats only count articles from their publisher."""
        publisher1 = PublisherFactory()
        publisher2 = PublisherFactory()

        pub1 = PublicationFactory(publisher=publisher1)
        pub2 = PublicationFactory(publisher=publisher2)

        issue1 = IssueFactory(publication=pub1)
        issue2 = IssueFactory(publication=pub2)

        urednik_user = UserFactory(publisher=publisher1)

        # Articles from urednik's publisher
        ArticleFactory(issue=issue1, status=ArticleStatus.REVIEW)
        ArticleFactory(issue=issue1, status=ArticleStatus.READY)

        # Articles from different publisher - should NOT be counted
        ArticleFactory(issue=issue2, status=ArticleStatus.REVIEW)
        ArticleFactory(issue=issue2, status=ArticleStatus.DRAFT)

        stats = get_urednik_statistics(urednik_user)
        assert stats["total_articles"] == 2
        assert stats["pending_review_count"] == 1
        assert stats["ready_to_publish_count"] == 1

    def test_no_publisher_returns_zeros(self):
        """Urednik without publisher assignment returns zeros."""
        user = UserFactory(publisher=None)
        stats = get_urednik_statistics(user)
        assert stats["total_articles"] == 0
        assert stats["pending_review_count"] == 0
        assert stats["ready_to_publish_count"] == 0


@pytest.mark.django_db
class TestBibliotekarStatistics:
    """Tests for get_bibliotekar_statistics (AC#5)."""

    def test_only_own_articles(self):
        """Bibliotekar stats only count their own articles."""
        user1 = UserFactory()
        user2 = UserFactory()

        ArticleFactory(created_by=user1, status=ArticleStatus.DRAFT)
        ArticleFactory(created_by=user1, status=ArticleStatus.REVIEW)

        # Article by other user - should NOT be counted
        ArticleFactory(created_by=user2, status=ArticleStatus.DRAFT)

        stats = get_bibliotekar_statistics(user1)
        assert stats["my_drafts_count"] == 1
        assert stats["my_submitted_count"] == 1
        assert stats["my_total_count"] == 2

    def test_no_articles(self):
        """Bibliotekar with no articles returns zeros."""
        user = UserFactory()
        stats = get_bibliotekar_statistics(user)
        assert stats["my_drafts_count"] == 0
        assert stats["my_submitted_count"] == 0
        assert stats["my_total_count"] == 0


@pytest.mark.django_db
class TestDashboardStatisticsDispatcher:
    """Tests for get_dashboard_statistics dispatcher."""

    def test_dispatches_to_admin(self):
        """Admin flag dispatches to get_admin_statistics."""
        flags = {"is_admin": True, "is_urednik": False, "is_bibliotekar": False}
        user = UserFactory()

        stats = get_dashboard_statistics(user, flags)
        assert "total_publications" in stats
        assert "total_articles" in stats

    def test_dispatches_to_urednik(self):
        """Urednik flag dispatches to get_urednik_statistics."""
        publisher = PublisherFactory()
        user = UserFactory(publisher=publisher)
        flags = {"is_admin": False, "is_urednik": True, "is_bibliotekar": False}

        stats = get_dashboard_statistics(user, flags)
        assert "total_articles" in stats
        assert "pending_review_count" in stats

    def test_dispatches_to_bibliotekar(self):
        """Bibliotekar flag dispatches to get_bibliotekar_statistics."""
        user = UserFactory()
        flags = {"is_admin": False, "is_urednik": False, "is_bibliotekar": True}

        stats = get_dashboard_statistics(user, flags)
        assert "my_total_count" in stats
        assert "my_drafts_count" in stats

    def test_unknown_role_returns_empty(self):
        """No matching role returns empty dict."""
        user = UserFactory()
        flags = {"is_admin": False, "is_urednik": False, "is_bibliotekar": False}

        stats = get_dashboard_statistics(user, flags)
        assert stats == {}


# ============================================================
# Task 2 Tests: Pending Items Functions (AC#2, #3, #4, #5)
# ============================================================


@pytest.mark.django_db
class TestPendingReviewArticles:
    """Tests for get_pending_review_articles (AC#2, AC#4)."""

    def test_returns_review_articles(self):
        """Returns only articles in REVIEW status."""
        ArticleFactory(status=ArticleStatus.REVIEW)
        ArticleFactory(status=ArticleStatus.DRAFT)
        ArticleFactory(status=ArticleStatus.PUBLISHED)

        flags = {"is_admin": True}
        articles = get_pending_review_articles(UserFactory(), flags)
        assert len(articles) == 1
        assert articles[0].status == ArticleStatus.REVIEW

    def test_limited_to_10(self):
        """Returns max 10 articles by default."""
        for _ in range(15):
            ArticleFactory(status=ArticleStatus.REVIEW)

        flags = {"is_admin": True}
        articles = get_pending_review_articles(UserFactory(), flags)
        assert len(articles) == 10

    def test_ordered_by_submitted_at_desc(self):
        """Articles are ordered by submitted_at descending (newest first)."""
        from django.utils import timezone
        import datetime

        a1 = ArticleFactory(
            status=ArticleStatus.REVIEW,
            submitted_at=timezone.now() - datetime.timedelta(days=2),
        )
        a2 = ArticleFactory(
            status=ArticleStatus.REVIEW,
            submitted_at=timezone.now() - datetime.timedelta(days=1),
        )
        a3 = ArticleFactory(
            status=ArticleStatus.REVIEW,
            submitted_at=timezone.now(),
        )

        flags = {"is_admin": True}
        articles = list(get_pending_review_articles(UserFactory(), flags))
        assert articles[0].pk == a3.pk
        assert articles[1].pk == a2.pk
        assert articles[2].pk == a1.pk

    def test_urednik_scoped_to_publisher(self):
        """Urednik only sees articles from their publisher."""
        publisher1 = PublisherFactory()
        publisher2 = PublisherFactory()

        pub1 = PublicationFactory(publisher=publisher1)
        pub2 = PublicationFactory(publisher=publisher2)

        issue1 = IssueFactory(publication=pub1)
        issue2 = IssueFactory(publication=pub2)

        urednik_user = UserFactory(publisher=publisher1)

        ArticleFactory(issue=issue1, status=ArticleStatus.REVIEW)
        ArticleFactory(issue=issue2, status=ArticleStatus.REVIEW)

        flags = {"is_admin": False}
        articles = get_pending_review_articles(urednik_user, flags)
        assert len(articles) == 1

    def test_empty_returns_empty(self):
        """No review articles returns empty queryset."""
        flags = {"is_admin": True}
        articles = get_pending_review_articles(UserFactory(), flags)
        assert len(articles) == 0


@pytest.mark.django_db
class TestReadyToPublishArticles:
    """Tests for get_ready_to_publish_articles (AC#3)."""

    def test_returns_ready_articles(self):
        """Returns only articles in READY status."""
        ArticleFactory(status=ArticleStatus.READY)
        ArticleFactory(status=ArticleStatus.REVIEW)
        ArticleFactory(status=ArticleStatus.DRAFT)

        flags = {"is_admin": True}
        articles = get_ready_to_publish_articles(UserFactory(), flags)
        assert len(articles) == 1
        assert articles[0].status == ArticleStatus.READY

    def test_limited_to_10(self):
        """Returns max 10 articles by default."""
        for _ in range(12):
            ArticleFactory(status=ArticleStatus.READY)

        flags = {"is_admin": True}
        articles = get_ready_to_publish_articles(UserFactory(), flags)
        assert len(articles) == 10

    def test_urednik_scoped_to_publisher(self):
        """Urednik only sees READY articles from their publisher."""
        publisher1 = PublisherFactory()
        publisher2 = PublisherFactory()

        pub1 = PublicationFactory(publisher=publisher1)
        pub2 = PublicationFactory(publisher=publisher2)

        issue1 = IssueFactory(publication=pub1)
        issue2 = IssueFactory(publication=pub2)

        urednik_user = UserFactory(publisher=publisher1)

        ArticleFactory(issue=issue1, status=ArticleStatus.READY)
        ArticleFactory(issue=issue2, status=ArticleStatus.READY)

        flags = {"is_admin": False}
        articles = get_ready_to_publish_articles(urednik_user, flags)
        assert len(articles) == 1

    def test_empty_returns_empty(self):
        """No ready articles returns empty queryset."""
        flags = {"is_admin": True}
        articles = get_ready_to_publish_articles(UserFactory(), flags)
        assert len(articles) == 0


@pytest.mark.django_db
class TestMyDraftArticles:
    """Tests for get_my_draft_articles (AC#5)."""

    def test_returns_only_own_drafts(self):
        """Returns only user's own DRAFT articles."""
        user1 = UserFactory()
        user2 = UserFactory()

        ArticleFactory(created_by=user1, status=ArticleStatus.DRAFT)
        ArticleFactory(created_by=user1, status=ArticleStatus.REVIEW)  # Not draft
        ArticleFactory(created_by=user2, status=ArticleStatus.DRAFT)  # Not own

        articles = get_my_draft_articles(user1)
        assert len(articles) == 1
        assert articles[0].created_by == user1
        assert articles[0].status == ArticleStatus.DRAFT

    def test_limited_to_10(self):
        """Returns max 10 drafts by default."""
        user = UserFactory()
        for _ in range(15):
            ArticleFactory(created_by=user, status=ArticleStatus.DRAFT)

        articles = get_my_draft_articles(user)
        assert len(articles) == 10

    def test_ordered_by_updated_at_desc(self):
        """Drafts are ordered by updated_at descending."""
        user = UserFactory()
        a1 = ArticleFactory(created_by=user, status=ArticleStatus.DRAFT)
        a2 = ArticleFactory(created_by=user, status=ArticleStatus.DRAFT)

        # Force update ordering by saving
        a1.title = "Updated first"
        a1.save()

        articles = list(get_my_draft_articles(user))
        # a1 was updated last, should be first
        assert articles[0].pk == a1.pk

    def test_empty_returns_empty(self):
        """User with no drafts returns empty queryset."""
        user = UserFactory()
        articles = get_my_draft_articles(user)
        assert len(articles) == 0
