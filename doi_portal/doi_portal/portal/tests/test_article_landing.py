"""
Tests for Article Landing Page.

Story 4.4: Article Landing Page (Defining Experience).
FR41: Posetilac moze videti landing stranicu clanka sa svim metapodacima.
Tests cover service function, view, context data, template rendering.
"""

import pytest
from django.urls import reverse
from django.utils import timezone

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import (
    AffiliationFactory,
    ArticleFactory,
    AuthorFactory,
)
from doi_portal.issues.models import IssueStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.portal.services import get_article_for_landing
from doi_portal.publications.tests.factories import (
    PublicationFactory,
    PublisherFactory,
)


def _create_published_article(**kwargs):
    """Helper to create a PUBLISHED article with full hierarchy."""
    publisher = PublisherFactory(doi_prefix="10.9999")
    pub = PublicationFactory(publisher=publisher)
    issue = IssueFactory(publication=pub, status=IssueStatus.PUBLISHED)
    defaults = {
        "issue": issue,
        "title": "Test Članak za Landing Page",
        "subtitle": "Podnaslov testa",
        "abstract": "Ovo je apstrakt test članka za landing page.",
        "keywords": ["nauka", "istraživanje", "DOI"],
        "doi_suffix": "test-001",
        "status": ArticleStatus.PUBLISHED,
        "first_page": "1",
        "last_page": "15",
        "language": "sr",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "free_to_read": True,
        "published_at": timezone.now(),
    }
    defaults.update(kwargs)
    article = ArticleFactory(**defaults)
    author = AuthorFactory(
        article=article,
        given_name="Petar",
        surname="Petrović",
        orcid="0000-0001-2345-6789",
        is_corresponding=True,
    )
    AffiliationFactory(
        author=author,
        institution_name="Univerzitet u Beogradu",
        department="Filozofski fakultet",
    )
    return article


# =============================================================================
# Service Tests: get_article_for_landing()
# =============================================================================


@pytest.mark.django_db
class TestGetArticleForLandingService:
    """Tests for get_article_for_landing() service function."""

    def test_returns_published_article(self):
        """8.1: get_article_for_landing() returns PUBLISHED article."""
        article = _create_published_article()
        result = get_article_for_landing(article.pk)
        assert result is not None
        assert result.pk == article.pk
        assert result.status == ArticleStatus.PUBLISHED

    def test_returns_withdrawn_article(self):
        """8.2: get_article_for_landing() returns WITHDRAWN article."""
        article = _create_published_article(status=ArticleStatus.WITHDRAWN)
        result = get_article_for_landing(article.pk)
        assert result is not None
        assert result.pk == article.pk
        assert result.status == ArticleStatus.WITHDRAWN

    def test_returns_none_for_draft(self):
        """8.3: get_article_for_landing() returns None for DRAFT article."""
        article = _create_published_article(status=ArticleStatus.DRAFT)
        result = get_article_for_landing(article.pk)
        assert result is None

    def test_returns_none_for_review(self):
        """8.4: get_article_for_landing() returns None for REVIEW article."""
        article = _create_published_article(status=ArticleStatus.REVIEW)
        result = get_article_for_landing(article.pk)
        assert result is None

    def test_returns_none_for_ready(self):
        """8.5: get_article_for_landing() returns None for READY article."""
        article = _create_published_article(status=ArticleStatus.READY)
        result = get_article_for_landing(article.pk)
        assert result is None

    def test_returns_none_for_nonexistent_pk(self):
        """8.6: get_article_for_landing() returns None for nonexistent PK."""
        result = get_article_for_landing(99999)
        assert result is None

    def test_returns_none_for_soft_deleted(self):
        """8.7: get_article_for_landing() returns None for soft-deleted article."""
        article = _create_published_article()
        article.is_deleted = True
        article.save()
        result = get_article_for_landing(article.pk)
        assert result is None


# =============================================================================
# View Tests: ArticleLandingView
# =============================================================================


@pytest.mark.django_db
class TestArticleLandingView:
    """Tests for ArticleLandingView."""

    def test_published_article_returns_200(self, client):
        """8.8: GET /articles/{pk}/ for PUBLISHED article returns 200."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_withdrawn_article_returns_200(self, client):
        """8.9: GET /articles/{pk}/ for WITHDRAWN article returns 200."""
        article = _create_published_article(status=ArticleStatus.WITHDRAWN)
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_draft_article_returns_404(self, client):
        """8.10: GET /articles/{pk}/ for DRAFT article returns 404."""
        publisher = PublisherFactory()
        pub = PublicationFactory(publisher=publisher)
        issue = IssueFactory(publication=pub, status=IssueStatus.PUBLISHED)
        article = ArticleFactory(issue=issue, status=ArticleStatus.DRAFT)
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_nonexistent_pk_returns_404(self, client):
        """8.11: GET /articles/{pk}/ for nonexistent PK returns 404."""
        url = reverse("portal-articles:article-detail", kwargs={"pk": 99999})
        response = client.get(url)
        assert response.status_code == 404

    def test_context_has_breadcrumbs_with_5_items(self, client):
        """8.12: Context contains breadcrumbs with 5 items."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 5
        assert breadcrumbs[0]["label"] == "Početna"
        assert breadcrumbs[1]["label"] == "Publikacije"

    def test_context_is_withdrawn_true_for_withdrawn(self, client):
        """8.13: Context contains is_withdrawn = True for WITHDRAWN article."""
        article = _create_published_article(status=ArticleStatus.WITHDRAWN)
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.context["is_withdrawn"] is True

    def test_context_is_withdrawn_false_for_published(self, client):
        """8.14: Context contains is_withdrawn = False for PUBLISHED article."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.context["is_withdrawn"] is False

    def test_context_has_full_doi(self, client):
        """8.15: Context contains full_doi with correct format."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.context["full_doi"] == "10.9999/test-001"

    def test_context_has_doi_url(self, client):
        """8.16: Context contains doi_url with https://doi.org/ prefix."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.context["doi_url"] == "https://doi.org/10.9999/test-001"

    def test_template_contains_article_title(self, client):
        """8.17: Template contains article title in response content."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        assert article.title in response.content.decode()

    def test_withdrawn_article_shows_withdrawn_banner(self, client):
        """8.18: WITHDRAWN article displays withdrawn banner."""
        article = _create_published_article(
            status=ArticleStatus.WITHDRAWN,
            withdrawal_reason="Duplikat rada",
            withdrawn_at=timezone.now(),
        )
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Povučen članak" in content
        assert "Duplikat rada" in content

    def test_published_article_no_withdrawn_banner(self, client):
        """8.19: PUBLISHED article does NOT display withdrawn banner."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Povučen članak" not in content

    def test_authors_with_affiliations_displayed(self, client):
        """8.20: Authors with affiliations are displayed."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Petar" in content
        assert "Petrović" in content
        assert "Univerzitet u Beogradu" in content
        assert "0000-0001-2345-6789" in content

    def test_keywords_displayed_as_tags(self, client):
        """8.21: Keywords are displayed as badge tags."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "nauka" in content
        assert "istraživanje" in content
        assert "DOI" in content

    def test_breadcrumbs_correct_hierarchy(self, client):
        """8.22: Breadcrumbs contain correct hierarchy."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        breadcrumbs = response.context["breadcrumbs"]
        # Verify hierarchy: Home > Publications > Publication > Issue > Article
        assert breadcrumbs[0]["label"] == "Početna"
        assert breadcrumbs[0]["url"] is not None
        assert breadcrumbs[1]["label"] == "Publikacije"
        assert breadcrumbs[1]["url"] is not None
        assert breadcrumbs[2]["label"] == article.issue.publication.title
        assert breadcrumbs[2]["url"] is not None
        issue = article.issue
        expected_issue_label = f"Vol. {issue.volume}, No. {issue.issue_number} ({issue.year})"
        assert breadcrumbs[3]["label"] == expected_issue_label
        assert breadcrumbs[3]["url"] is not None
        assert breadcrumbs[4]["label"] == article.title[:80]
        assert breadcrumbs[4]["url"] is None

    def test_semantic_html_article_tag(self, client):
        """AC #9: Template uses semantic <article> tag."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "<article" in content
        assert "<aside" in content
        assert "<section" in content

    def test_orcid_link_has_rel_external(self, client):
        """AC #9: ORCID links have rel='external' and aria-label."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert 'rel="external"' in content
        assert "aria-label" in content

    def test_doi_link_displayed(self, client):
        """AC #3: DOI link is displayed in metadata section."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "10.9999/test-001" in content
        assert "https://doi.org/10.9999/test-001" in content

    def test_abstract_displayed(self, client):
        """AC #3: Abstract is displayed."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Apstrakt" in content
        assert article.abstract in content

    def test_sidebar_publication_info(self, client):
        """AC #4: Sidebar shows publication info."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert article.issue.publication.title in content
        assert "Publikacija" in content

    def test_sidebar_publisher_info(self, client):
        """AC #4: Sidebar shows publisher info."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert article.issue.publication.publisher.name in content
        assert "Izdavač" in content

    def test_review_article_returns_404(self, client):
        """AC #7: REVIEW status article returns 404."""
        publisher = PublisherFactory()
        pub = PublicationFactory(publisher=publisher)
        issue = IssueFactory(publication=pub, status=IssueStatus.PUBLISHED)
        article = ArticleFactory(issue=issue, status=ArticleStatus.REVIEW)
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_ready_article_returns_404(self, client):
        """AC #7: READY status article returns 404."""
        publisher = PublisherFactory()
        pub = PublicationFactory(publisher=publisher)
        issue = IssueFactory(publication=pub, status=IssueStatus.PUBLISHED)
        article = ArticleFactory(issue=issue, status=ArticleStatus.READY)
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_status_badge_displayed(self, client):
        """AC #6: Status badge is displayed."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        # ArticleStatus.PUBLISHED display is "Objavljeno"
        assert "Objavljeno" in content

    def test_pages_displayed(self, client):
        """AC #3: Pages (first_page-last_page) are displayed in metadata."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Stranice" in content
        # first_page is "1", last_page is "15" - check ndash separator pattern
        assert "1" in content
        assert "15" in content
        assert "ndash" in content  # &ndash; rendered between pages

    def test_soft_deleted_article_returns_404(self, client):
        """AC #7: Soft-deleted article returns 404 at view level."""
        article = _create_published_article()
        article.is_deleted = True
        article.save()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_license_url_displayed(self, client):
        """AC #3: License URL is displayed in metadata section."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Licenca" in content
        assert "creativecommons.org" in content

    def test_free_to_read_badge_displayed(self, client):
        """AC #3: Free to read badge is displayed when free_to_read=True."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Slobodan pristup" in content

    def test_subtitle_displayed(self, client):
        """AC #3: Subtitle is prominently displayed when present."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Podnaslov testa" in content
        assert "article-subtitle" in content

    def test_corresponding_author_badge(self, client):
        """AC #3: Corresponding author badge (Korespondent) is displayed."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Korespondent" in content

    def test_doi_link_has_aria_label(self, client):
        """AC #9: DOI link has aria-label for accessibility."""
        article = _create_published_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert 'aria-label="DOI: 10.9999/test-001"' in content
