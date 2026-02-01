"""
Tests for Portal Home Page.

Story 4.1: Portal Home Page.
Tests cover: PortalHomeView, get_portal_statistics(), get_recent_publications().
AC: #1-#8 coverage via view and service tests.
"""

import pytest
from django.urls import reverse

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.portal.services import get_portal_statistics, get_recent_publications
from doi_portal.portal.tests.factories import PublicationFactory, PublisherFactory


# =============================================================================
# Service Tests: get_portal_statistics() (AC: #5)
# =============================================================================


@pytest.mark.django_db
class TestPortalStatistics:
    """Tests for get_portal_statistics service function."""

    def test_returns_correct_counts(self):
        """8.6: Stats include total publications, articles, publishers."""
        # Create publishers and publications explicitly
        pub1 = PublisherFactory(name="Stats Pub 1", doi_prefix="10.9901")
        pub2 = PublisherFactory(name="Stats Pub 2", doi_prefix="10.9902")
        PublicationFactory(publisher=pub1, title="Stats Publication A")
        PublicationFactory(publisher=pub1, title="Stats Publication B")
        PublicationFactory(publisher=pub2, title="Stats Publication C")
        # ArticleFactory cascades through Issue -> Publication -> Publisher,
        # creating additional publishers/publications beyond the explicit ones above
        ArticleFactory(status=ArticleStatus.PUBLISHED)
        ArticleFactory(status=ArticleStatus.DRAFT)

        stats = get_portal_statistics()

        assert "total_publications" in stats
        assert "total_articles" in stats
        assert "total_publishers" in stats
        assert "published_articles_count" in stats
        # 2 explicit + 2 from ArticleFactory cascade = 4 publishers
        assert stats["total_publishers"] == 4
        # 3 explicit + 2 from ArticleFactory cascade = 5 publications
        assert stats["total_publications"] == 5
        assert stats["total_articles"] == 2
        assert stats["published_articles_count"] == 1

    def test_empty_database_returns_zeros(self):
        """8.7: Stats return zeros when database is empty."""
        stats = get_portal_statistics()

        assert stats["total_publications"] == 0
        assert stats["total_publishers"] == 0
        assert stats["total_articles"] == 0
        assert stats["published_articles_count"] == 0


# =============================================================================
# Service Tests: get_recent_publications() (AC: #6, #7)
# =============================================================================


@pytest.mark.django_db
class TestRecentPublications:
    """Tests for get_recent_publications service function."""

    def test_returns_max_6(self):
        """8.8: Returns max 6 publications."""
        publisher = PublisherFactory()
        for _ in range(10):
            PublicationFactory(publisher=publisher)

        result = get_recent_publications()
        assert len(result) <= 6

    def test_ordered_by_created_at_desc(self):
        """8.9: Results are sorted by created_at descending (newest first)."""
        publisher = PublisherFactory()
        pub1 = PublicationFactory(publisher=publisher, title="First")
        pub2 = PublicationFactory(publisher=publisher, title="Second")
        pub3 = PublicationFactory(publisher=publisher, title="Third")

        result = list(get_recent_publications())
        # Last created should be first in results
        assert result[0].pk == pub3.pk
        assert result[1].pk == pub2.pk
        assert result[2].pk == pub1.pk

    def test_excludes_soft_deleted(self):
        """8.10: Soft-deleted publications are excluded."""
        pub_active = PublicationFactory(title="Active Pub")
        pub_deleted = PublicationFactory(title="Deleted Pub")
        pub_deleted.soft_delete()

        result = get_recent_publications()
        titles = [p.title for p in result]
        assert "Active Pub" in titles
        assert "Deleted Pub" not in titles

    def test_custom_limit(self):
        """get_recent_publications respects custom limit parameter."""
        publisher = PublisherFactory()
        for _ in range(5):
            PublicationFactory(publisher=publisher)

        result = get_recent_publications(limit=3)
        assert len(result) <= 3


# =============================================================================
# View Tests: PortalHomeView (AC: #1, #2, #3, #4, #5, #7, #8)
# =============================================================================


@pytest.mark.django_db
class TestPortalHomeView:
    """Tests for PortalHomeView."""

    def test_home_returns_200(self, client):
        """8.1: Home page returns 200 on GET /."""
        response = client.get(reverse("home"))
        assert response.status_code == 200

    def test_home_uses_portal_template(self, client):
        """8.2: Home page uses portal/home.html template."""
        response = client.get(reverse("home"))
        template_names = [t.name for t in response.templates]
        assert "portal/home.html" in template_names

    def test_home_context_has_stats(self, client):
        """8.3: Context includes stats dict with expected keys."""
        response = client.get(reverse("home"))
        assert "stats" in response.context
        stats = response.context["stats"]
        assert "total_publications" in stats
        assert "total_articles" in stats
        assert "published_articles_count" in stats
        assert "total_publishers" in stats

    def test_home_context_has_recent_publications(self, client):
        """8.4: Context includes recent_publications."""
        response = client.get(reverse("home"))
        assert "recent_publications" in response.context

    def test_home_no_auth_required(self, client):
        """8.5: Public page - no login required (200, not 302)."""
        response = client.get(reverse("home"))
        assert response.status_code == 200

    def test_home_stats_displayed_in_html(self, client):
        """8.11: Statistics are displayed in HTML (publication count visible)."""
        PublisherFactory.create_batch(2)
        PublicationFactory.create_batch(3)

        response = client.get(reverse("home"))
        content = response.content.decode()
        # Stat cards should show labels
        assert "Publikacije" in content
        assert "Objavljeni članci" in content
        assert "Izdavači" in content

    def test_home_shows_publications_as_cards(self, client):
        """8.12: Recent publications are displayed as cards."""
        pub = PublicationFactory(title="Test Časopis")
        response = client.get(reverse("home"))
        content = response.content.decode()
        assert "Test Časopis" in content

    def test_home_empty_publications_message(self, client):
        """8.13: Shows empty message when no publications exist."""
        response = client.get(reverse("home"))
        content = response.content.decode()
        assert "Nema dostupnih publikacija" in content

    def test_home_search_form(self, client):
        """8.14: Hero search form has action="/search/" and input name="q"."""
        response = client.get(reverse("home"))
        content = response.content.decode()
        assert 'name="q"' in content
        assert '/search/' in content

    def test_home_no_breadcrumbs(self, client):
        """8.15: Breadcrumbs are not displayed on home page (root page)."""
        response = client.get(reverse("home"))
        # Context should not have breadcrumbs
        assert "breadcrumbs" not in response.context or not response.context.get("breadcrumbs")

    def test_publication_links_to_detail(self, client):
        """8.16: Publication card links to publication detail page."""
        pub = PublicationFactory(title="Link Test Pub")
        response = client.get(reverse("home"))
        content = response.content.decode()
        detail_url = reverse(
            "portal-publications:publication-detail",
            kwargs={"slug": pub.slug},
        )
        assert detail_url in content

    def test_home_title_tag(self, client):
        """8.17: Page has appropriate <title> tag for SEO."""
        response = client.get(reverse("home"))
        content = response.content.decode()
        assert "DOI Portal" in content
        assert "Početna strana" in content

    def test_home_meta_description(self, client):
        """SEO: Page has appropriate meta description tag."""
        response = client.get(reverse("home"))
        content = response.content.decode()
        assert "Pregledajte naučne publikacije i članke" in content
