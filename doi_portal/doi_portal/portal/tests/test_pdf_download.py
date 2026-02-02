"""
Tests for PDF Download functionality.

Story 4.6: PDF Download.
FR42: Posetilac može preuzeti PDF članka.
NFR4: PDF download - Direktan link, bez procesiranja.

Tests cover:
- Download view redirect behavior (AC #1, #2, #3)
- 404 responses for missing/withdrawn/draft articles (AC #4, #5, #7)
- Landing page context with pdf_download_url (AC #1, #8)
- Floating action bar <a> tag vs <button disabled> (AC #1, #4, #5, #8)
- get_pdf_download_filename() service function (AC #1)
- Public access without authentication (AC #3)
- download attribute with descriptive filename (AC #1)
"""

import pytest
from django.urls import reverse

from doi_portal.articles.models import ArticleStatus, PdfStatus
from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.issues.models import IssueStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.portal.services import get_pdf_download_filename
from doi_portal.publications.tests.factories import (
    PublicationFactory,
    PublisherFactory,
)


def _create_article(status=ArticleStatus.PUBLISHED, has_pdf=False, doi_suffix="pdf-test-001", title=None):
    """Helper to create an article with full hierarchy for PDF download tests."""
    publisher = PublisherFactory(doi_prefix="10.9999")
    pub = PublicationFactory(publisher=publisher)
    issue = IssueFactory(publication=pub, status=IssueStatus.PUBLISHED)
    kwargs = {
        "issue": issue,
        "doi_suffix": doi_suffix,
        "status": status,
    }
    if title is not None:
        kwargs["title"] = title
    article = ArticleFactory(**kwargs)
    if has_pdf:
        article.pdf_file = "articles/pdfs/test.pdf"
        article.save()
    return article


# =============================================================================
# Download View Tests (AC #1, #2, #3, #7)
# =============================================================================


@pytest.mark.django_db
class TestArticlePdfDownloadView:
    """Tests for article_pdf_download view."""

    def test_download_redirects_to_pdf_url(self, client):
        """6.1: Download view returns redirect to PDF URL for PUBLISHED article with PDF."""
        article = _create_article(status=ArticleStatus.PUBLISHED, has_pdf=True)
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert "articles/pdfs/test.pdf" in response.url

    def test_download_404_without_pdf(self, client):
        """6.2: Download view returns 404 for article without PDF."""
        article = _create_article(status=ArticleStatus.PUBLISHED, has_pdf=False, doi_suffix="pdf-nopdf-001")
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_download_404_for_withdrawn(self, client):
        """6.3: Download view returns 404 for WITHDRAWN article even with PDF."""
        article = _create_article(status=ArticleStatus.WITHDRAWN, has_pdf=True, doi_suffix="pdf-withdrawn-001")
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_download_404_for_draft(self, client):
        """6.4: Download view returns 404 for DRAFT article."""
        article = _create_article(status=ArticleStatus.DRAFT, has_pdf=True, doi_suffix="pdf-draft-001")
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_download_404_for_nonexistent(self, client):
        """6.5: Download view returns 404 for nonexistent article."""
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": 99999})
        response = client.get(url)
        assert response.status_code == 404

    def test_download_no_auth_required(self, client):
        """6.11: Download URL works without authentication (public)."""
        article = _create_article(status=ArticleStatus.PUBLISHED, has_pdf=True, doi_suffix="pdf-noauth-001")
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.get(url)
        # Should redirect to PDF, not redirect to login
        assert response.status_code == 302
        assert "login" not in response.url
        assert "account" not in response.url

    def test_download_rejects_post_method(self, client):
        """Security: Download view rejects POST requests (only GET allowed)."""
        article = _create_article(status=ArticleStatus.PUBLISHED, has_pdf=True, doi_suffix="pdf-post-001")
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.post(url)
        assert response.status_code == 405

    def test_download_404_for_infected_pdf(self, client):
        """Security: Download view returns 404 for article with INFECTED pdf_status."""
        article = _create_article(status=ArticleStatus.PUBLISHED, has_pdf=True, doi_suffix="pdf-infected-001")
        article.pdf_status = PdfStatus.INFECTED
        article.save()
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_download_404_for_scanning_pdf(self, client):
        """Security: Download view returns 404 for article with SCANNING pdf_status."""
        article = _create_article(status=ArticleStatus.PUBLISHED, has_pdf=True, doi_suffix="pdf-scanning-001")
        article.pdf_status = PdfStatus.SCANNING
        article.save()
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_download_404_for_uploading_pdf(self, client):
        """Security: Download view returns 404 for article with UPLOADING pdf_status."""
        article = _create_article(status=ArticleStatus.PUBLISHED, has_pdf=True, doi_suffix="pdf-uploading-001")
        article.pdf_status = PdfStatus.UPLOADING
        article.save()
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404


# =============================================================================
# Landing Page Context Tests (AC #1, #8)
# =============================================================================


@pytest.mark.django_db
class TestLandingPagePdfContext:
    """Tests for pdf_download_url in ArticleLandingView context."""

    def test_context_has_pdf_download_url_with_pdf(self, client):
        """6.6: Landing page context contains pdf_download_url for article with PDF."""
        article = _create_article(
            status=ArticleStatus.PUBLISHED, has_pdf=True, doi_suffix="pdf-ctx-001"
        )
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        assert response.context["pdf_download_url"] is not None
        expected_url = reverse(
            "portal-articles:article-pdf-download", kwargs={"pk": article.pk}
        )
        assert response.context["pdf_download_url"] == expected_url

    def test_context_pdf_download_url_none_without_pdf(self, client):
        """6.7: Landing page context contains pdf_download_url = None for article without PDF."""
        article = _create_article(
            status=ArticleStatus.PUBLISHED, has_pdf=False, doi_suffix="pdf-ctx-002"
        )
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        assert response.context["pdf_download_url"] is None

    def test_context_has_pdf_download_filename(self, client):
        """6.12 (partial): Landing page context contains pdf_download_filename when has_pdf."""
        article = _create_article(
            status=ArticleStatus.PUBLISHED, has_pdf=True, doi_suffix="pdf-fname-001",
            title="Test Article Title"
        )
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        assert response.context["pdf_download_filename"] is not None
        assert response.context["pdf_download_filename"].endswith(".pdf")

    def test_context_pdf_download_filename_none_without_pdf(self, client):
        """pdf_download_filename is None when article has no PDF."""
        article = _create_article(
            status=ArticleStatus.PUBLISHED, has_pdf=False, doi_suffix="pdf-fname-002"
        )
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        assert response.context["pdf_download_filename"] is None


# =============================================================================
# Floating Action Bar Template Tests (AC #1, #4, #5, #8)
# =============================================================================


@pytest.mark.django_db
class TestFloatingActionBarPdf:
    """Tests for PDF button in floating action bar template."""

    def test_pdf_link_tag_with_pdf(self, client):
        """6.8: Floating action bar uses <a> tag with href for article with PDF."""
        article = _create_article(
            status=ArticleStatus.PUBLISHED, has_pdf=True, doi_suffix="pdf-fab-001"
        )
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        content = response.content.decode()
        expected_url = reverse(
            "portal-articles:article-pdf-download", kwargs={"pk": article.pk}
        )
        # Should have an <a> tag with the download URL
        assert f'href="{expected_url}"' in content
        assert "Preuzmi PDF" in content

    def test_pdf_button_disabled_without_pdf(self, client):
        """6.9: Floating action bar uses <button disabled> for article without PDF."""
        article = _create_article(
            status=ArticleStatus.PUBLISHED, has_pdf=False, doi_suffix="pdf-fab-002"
        )
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        content = response.content.decode()
        assert "disabled" in content
        assert "PDF nije dostupan" in content

    def test_pdf_link_has_download_attribute(self, client):
        """6.12: Floating action bar <a> tag contains download attribute with descriptive filename."""
        article = _create_article(
            status=ArticleStatus.PUBLISHED, has_pdf=True, doi_suffix="pdf-dl-001",
            title="My Test Article"
        )
        response = client.get(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )
        content = response.content.decode()
        expected_filename = get_pdf_download_filename(article)
        assert f'download="{expected_filename}"' in content


# =============================================================================
# Service Function Tests (AC #1)
# =============================================================================


@pytest.mark.django_db
class TestGetPdfDownloadFilename:
    """Tests for get_pdf_download_filename() service function."""

    def test_generates_correct_format(self):
        """6.10: get_pdf_download_filename() generates correct {doi_suffix}_{title_slug}.pdf format."""
        article = _create_article(
            status=ArticleStatus.PUBLISHED,
            doi_suffix="test-001",
            title="Some Article Title",
            has_pdf=True,
        )
        filename = get_pdf_download_filename(article)
        assert filename == "test-001_some-article-title.pdf"

    def test_handles_slash_in_doi_suffix(self):
        """doi_suffix with slashes should have slashes replaced with dashes."""
        article = _create_article(
            status=ArticleStatus.PUBLISHED,
            doi_suffix="prefix/test-002",
            title="Another Title",
            has_pdf=True,
        )
        filename = get_pdf_download_filename(article)
        assert filename == "prefix-test-002_another-title.pdf"

    def test_truncates_long_title_slug(self):
        """Title slug is truncated to max 100 characters."""
        long_title = "A" * 200 + " Word"
        article = _create_article(
            status=ArticleStatus.PUBLISHED,
            doi_suffix="long-001",
            title=long_title,
            has_pdf=True,
        )
        filename = get_pdf_download_filename(article)
        # slugify("A"*200 + " Word") -> "aaa...aaa-word", truncated to 100
        # doi_slug + "_" + truncated_slug + ".pdf"
        assert filename.startswith("long-001_")
        assert filename.endswith(".pdf")
        # The slug part (between first _ and .pdf) should be at most 100 chars
        slug_part = filename[len("long-001_"):-len(".pdf")]
        assert len(slug_part) <= 100

    def test_ends_with_pdf_extension(self):
        """Filename always ends with .pdf."""
        article = _create_article(
            status=ArticleStatus.PUBLISHED,
            doi_suffix="ext-001",
            title="Simple",
            has_pdf=True,
        )
        filename = get_pdf_download_filename(article)
        assert filename.endswith(".pdf")

    def test_handles_empty_slug_from_special_chars(self):
        """Edge case: title with only non-ASCII chars produces fallback filename without underscore."""
        article = _create_article(
            status=ArticleStatus.PUBLISHED,
            doi_suffix="special-001",
            title="\u0410\u0411\u0412",  # Cyrillic chars that slugify strips
            has_pdf=True,
        )
        filename = get_pdf_download_filename(article)
        # Should fallback to doi_slug.pdf without trailing underscore
        assert filename == "special-001.pdf"
