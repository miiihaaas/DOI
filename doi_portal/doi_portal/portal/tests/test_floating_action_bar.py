"""
Tests for Floating Action Bar.

Story 4.5: Floating Action Bar (Custom UI Component #4).
FR42: Posetilac moze preuzeti PDF clanka (placeholder dugme).
FR41: Upotpunjujemo Article Landing Page sa floating akcijama.
Tests cover view context (has_pdf, share_url), HTML rendering, ARIA accessibility.
"""

import pytest
from django.urls import reverse

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.issues.models import IssueStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import (
    PublicationFactory,
    PublisherFactory,
)


def _create_article(status=ArticleStatus.PUBLISHED, has_pdf=False, doi_suffix="fab-test-001"):
    """Helper to create an article with full hierarchy for floating action bar tests."""
    publisher = PublisherFactory(doi_prefix="10.9999")
    pub = PublicationFactory(publisher=publisher)
    issue = IssueFactory(publication=pub, status=IssueStatus.PUBLISHED)
    article = ArticleFactory(
        issue=issue,
        doi_suffix=doi_suffix,
        status=status,
    )
    if has_pdf:
        article.pdf_file = "articles/pdfs/test.pdf"
        article.save()
    return article


# =============================================================================
# Context Tests: has_pdf and share_url
# =============================================================================


@pytest.mark.django_db
class TestFloatingActionBarContext:
    """Tests for floating action bar context variables (AC #3, #9)."""

    def test_has_pdf_true_for_published_with_pdf(self, client):
        """7.1: context has_pdf = True for article with PDF."""
        article = _create_article(status=ArticleStatus.PUBLISHED, has_pdf=True)
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        assert response.context["has_pdf"] is True

    def test_has_pdf_false_for_published_without_pdf(self, client):
        """7.2: context has_pdf = False for article without PDF."""
        article = _create_article(status=ArticleStatus.PUBLISHED, has_pdf=False)
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        assert response.context["has_pdf"] is False

    def test_has_pdf_false_for_withdrawn_with_pdf(self, client):
        """7.3: context has_pdf = False for WITHDRAWN article even with PDF."""
        article = _create_article(
            status=ArticleStatus.WITHDRAWN, has_pdf=True, doi_suffix="fab-withdrawn-ctx"
        )
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        assert response.context["has_pdf"] is False

    def test_share_url_in_context(self, client):
        """7.x: context contains share_url as absolute URL."""
        article = _create_article()
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        assert "share_url" in response.context
        share_url = response.context["share_url"]
        # share_url should contain the article URL path
        expected_path = reverse(
            "portal-articles:article-detail", kwargs={"pk": article.pk}
        )
        assert expected_path in share_url
        # share_url must be an absolute URL (starts with http)
        assert share_url.startswith("http"), f"share_url should be absolute, got: {share_url}"


# =============================================================================
# Rendering Tests: HTML content
# =============================================================================


@pytest.mark.django_db
class TestFloatingActionBarRendering:
    """Tests for floating action bar HTML rendering (AC #1, #2, #3, #5, #6, #8, #9)."""

    def test_floating_bar_present_in_response(self, client):
        """7.4: response contains floating-action-bar class."""
        article = _create_article()
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        assert "floating-action-bar" in response.content.decode()

    def test_pdf_button_disabled_without_pdf(self, client):
        """7.5: PDF button has disabled attribute for article without PDF."""
        article = _create_article(has_pdf=False, doi_suffix="fab-nopdf-001")
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        content = response.content.decode()
        assert "disabled" in content
        assert "PDF nije dostupan" in content

    def test_pdf_button_enabled_with_pdf(self, client):
        """7.6: PDF button NOT disabled for article with PDF (non-withdrawn)."""
        article = _create_article(has_pdf=True, doi_suffix="fab-haspdf-001")
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        content = response.content.decode()
        assert "Preuzmi PDF" in content
        # Verify the PDF button is NOT disabled - extract the PDF button HTML
        assert "PDF nije dostupan" not in content

    def test_copy_doi_button_present(self, client):
        """7.7: Copy DOI button present; DOI passed via floatingActionBar() x-data."""
        article = _create_article(doi_suffix="fab-doi-001")
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        content = response.content.decode()
        assert "floatingActionBar(" in content
        assert "10.9999/fab-doi-001" in content

    def test_share_button_present(self, client):
        """7.8: Share button present with bi-share icon."""
        article = _create_article(doi_suffix="fab-share-001")
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        assert "bi-share" in response.content.decode()

    def test_cite_button_present(self, client):
        """7.9: Cite button present with bi-quote icon."""
        article = _create_article(doi_suffix="fab-cite-001")
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        assert "bi-quote" in response.content.decode()

    def test_floating_bar_has_aria_label(self, client):
        """7.10: Floating bar nav element has aria-label."""
        article = _create_article(doi_suffix="fab-aria-001")
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        content = response.content.decode()
        assert 'aria-label="Akcije za' in content

    def test_withdrawn_article_has_disabled_pdf(self, client):
        """7.11: WITHDRAWN article has disabled PDF button."""
        article = _create_article(
            status=ArticleStatus.WITHDRAWN,
            has_pdf=True,
            doi_suffix="fab-withdrawn-001",
        )
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        content = response.content.decode()
        assert "disabled" in content
        assert "PDF nije dostupan" in content
