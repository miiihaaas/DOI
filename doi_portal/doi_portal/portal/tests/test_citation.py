"""
Tests for Citation Modal.

Story 4.7: Citation Modal (Custom UI Component #8).
Tests cover citation service functions (APA, MLA, Chicago, BibTeX, RIS),
HTMX view endpoint, download endpoint, template rendering, and accessibility.
"""

import pytest
from django.urls import reverse

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory, AuthorFactory
from doi_portal.issues.models import IssueStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import (
    PublicationFactory,
    PublisherFactory,
)
from doi_portal.portal.services import (
    format_citation_apa,
    format_citation_bibtex,
    format_citation_chicago,
    format_citation_mla,
    format_citation_ris,
    generate_citation,
)


def _create_article(status=ArticleStatus.PUBLISHED, num_authors=2):
    """Helper to create article with full hierarchy for citation tests."""
    publisher = PublisherFactory(doi_prefix="10.9999")
    pub = PublicationFactory(publisher=publisher, title="Test Journal")
    issue = IssueFactory(
        publication=pub,
        status=IssueStatus.PUBLISHED,
        volume="12",
        issue_number="3",
        year=2025,
    )
    article = ArticleFactory(
        issue=issue,
        doi_suffix="test-001",
        status=status,
        title="Test Article Title",
        first_page="45",
        last_page="67",
    )
    for i in range(num_authors):
        AuthorFactory(
            article=article,
            given_name=f"Name{i}",
            surname=f"Surname{i}",
            order=i,
        )
    return article


# =============================================================================
# 11.1: Citation endpoint returns HTML fragment for PUBLISHED article (APA default)
# =============================================================================


@pytest.mark.django_db
class TestArticleCitationView:
    """Tests for article citation HTMX endpoint."""

    def test_citation_returns_html_fragment(self, client):
        """11.1: Citation endpoint returns HTML fragment for PUBLISHED article with APA format (default)."""
        article = _create_article()
        url = reverse("portal-articles:article-citation", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "text/html" in response["Content-Type"]

    def test_citation_default_apa(self, client):
        """11.1b: Citation endpoint returns APA format by default."""
        article = _create_article()
        url = reverse("portal-articles:article-citation", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Test Article Title" in content

    # =========================================================================
    # 11.2: Citation endpoint returns HTML fragment for each format
    # =========================================================================

    @pytest.mark.parametrize(
        "fmt",
        ["apa", "mla", "chicago", "bibtex", "ris"],
    )
    def test_citation_each_format(self, client, fmt):
        """11.2: Citation endpoint returns HTML fragment for each format."""
        article = _create_article()
        url = reverse("portal-articles:article-citation", kwargs={"pk": article.pk})
        response = client.get(url, {"format": fmt})
        assert response.status_code == 200
        content = response.content.decode()
        assert "Test Article Title" in content

    # =========================================================================
    # 11.3: Citation endpoint returns 404 for DRAFT article
    # =========================================================================

    def test_citation_404_for_draft(self, client):
        """11.3: Citation endpoint returns 404 for DRAFT article."""
        article = _create_article(status=ArticleStatus.DRAFT)
        url = reverse("portal-articles:article-citation", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    # =========================================================================
    # 11.4: Citation endpoint returns 404 for non-existent article
    # =========================================================================

    def test_citation_404_for_nonexistent(self, client):
        """11.4: Citation endpoint returns 404 for non-existent article."""
        url = reverse("portal-articles:article-citation", kwargs={"pk": 99999})
        response = client.get(url)
        assert response.status_code == 404

    # =========================================================================
    # 11.5: Citation endpoint works for WITHDRAWN article
    # =========================================================================

    def test_citation_works_for_withdrawn(self, client):
        """11.5: Citation endpoint works for WITHDRAWN article."""
        article = _create_article(status=ArticleStatus.WITHDRAWN)
        url = reverse("portal-articles:article-citation", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 200

    # =========================================================================
    # 11.14: Citation endpoint does not require authentication (public)
    # =========================================================================

    def test_citation_endpoint_public(self, client):
        """11.14: Citation endpoint does not require authentication."""
        article = _create_article()
        url = reverse("portal-articles:article-citation", kwargs={"pk": article.pk})
        response = client.get(url)
        # No redirect to login - direct 200
        assert response.status_code == 200


# =============================================================================
# Citation Formatting Service Tests
# =============================================================================


@pytest.mark.django_db
class TestCitationFormatting:
    """Tests for citation format service functions."""

    # =========================================================================
    # 11.6: format_citation_apa generates correct APA format with all fields
    # =========================================================================

    def test_format_citation_apa_full(self):
        """11.6: format_citation_apa() generates correct APA format with all fields."""
        article = _create_article()
        result = format_citation_apa(article)
        # APA: Surname, Initials., Surname2, Initials2. (Year). Title. Journal, Vol(Issue), Pages. DOI
        assert "Surname0, N." in result
        assert "Surname1, N." in result
        assert "(2025)" in result
        assert "Test Article Title" in result
        assert "Test Journal" in result
        # Volume is italicized with markdown (*12*) followed by (3)
        assert "12" in result
        assert "(3)" in result
        assert "45-67" in result or "45\u201367" in result
        assert "https://doi.org/10.9999/test-001" in result

    # =========================================================================
    # 11.7: format_citation_apa gracefully handles missing pages
    # =========================================================================

    def test_format_citation_apa_missing_pages(self):
        """11.7: format_citation_apa() gracefully handles missing pages."""
        article = _create_article()
        article.first_page = ""
        article.last_page = ""
        article.save()
        result = format_citation_apa(article)
        # Should still be valid APA format, just no pages
        assert "Test Article Title" in result
        assert "(2025)" in result
        assert "https://doi.org/10.9999/test-001" in result

    # =========================================================================
    # 11.15: format_citation_mla generates correct MLA format
    # =========================================================================

    def test_format_citation_mla_full(self):
        """11.15: format_citation_mla() generates correct MLA format."""
        article = _create_article()
        result = format_citation_mla(article)
        # MLA: Surname, GivenName, et al. "Title." Journal, vol. V, no. N, Year, pp. Pages. DOI: doi.
        assert "Surname0, Name0" in result
        assert "Test Article Title" in result
        assert "Test Journal" in result
        assert "vol. 12" in result
        assert "no. 3" in result
        assert "2025" in result
        assert "pp. 45-67" in result or "pp. 45\u201367" in result

    # =========================================================================
    # 11.16: format_citation_chicago generates correct Chicago format
    # =========================================================================

    def test_format_citation_chicago_full(self):
        """11.16: format_citation_chicago() generates correct Chicago format."""
        article = _create_article()
        result = format_citation_chicago(article)
        # Chicago: Surname, GivenName, and GivenName2 Surname2. Year. "Title." Journal V (N): Pages. DOI.
        assert "Surname0, Name0" in result
        assert "2025" in result
        assert "Test Article Title" in result
        assert "Test Journal" in result
        assert "https://doi.org/10.9999/test-001" in result

    # =========================================================================
    # 11.8: format_citation_bibtex generates valid BibTeX entry
    # =========================================================================

    def test_format_citation_bibtex_valid(self):
        """11.8: format_citation_bibtex() generates valid BibTeX entry."""
        article = _create_article()
        result = format_citation_bibtex(article)
        assert "@article{" in result
        assert "author = {" in result
        assert "title = {Test Article Title}" in result
        assert "journal = {Test Journal}" in result
        assert "year = {2025}" in result
        assert "volume = {12}" in result
        assert "number = {3}" in result
        assert "pages = {45--67}" in result
        assert "doi = {10.9999/test-001}" in result

    # =========================================================================
    # 11.9: format_citation_ris generates valid RIS entry
    # =========================================================================

    def test_format_citation_ris_valid(self):
        """11.9: format_citation_ris() generates valid RIS entry."""
        article = _create_article()
        result = format_citation_ris(article)
        assert "TY  - JOUR" in result
        assert "AU  - Surname0, Name0" in result
        assert "AU  - Surname1, Name1" in result
        assert "TI  - Test Article Title" in result
        assert "JO  - Test Journal" in result
        assert "VL  - 12" in result
        assert "IS  - 3" in result
        assert "SP  - 45" in result
        assert "EP  - 67" in result
        assert "PY  - 2025" in result
        assert "DO  - 10.9999/test-001" in result
        assert "ER  -" in result

    # =========================================================================
    # 11.x: generate_citation dispatches to correct format
    # =========================================================================

    def test_generate_citation_dispatches(self):
        """generate_citation() delegates to format-specific function."""
        article = _create_article()
        apa = generate_citation(article, "apa")
        assert "(2025)" in apa
        bibtex = generate_citation(article, "bibtex")
        assert "@article{" in bibtex
        ris = generate_citation(article, "ris")
        assert "TY  - JOUR" in ris

    def test_generate_citation_default_apa(self):
        """generate_citation() defaults to APA when no format given."""
        article = _create_article()
        result = generate_citation(article, "unknown_format")
        # Should fall back to APA
        assert "(2025)" in result


# =============================================================================
# Citation Download Tests
# =============================================================================


@pytest.mark.django_db
class TestArticleCitationDownload:
    """Tests for citation download endpoint."""

    # =========================================================================
    # 11.10: Citation download returns file with correct Content-Disposition
    # =========================================================================

    def test_download_bibtex_content_disposition(self, client):
        """11.10: Citation download returns BibTeX file with correct Content-Disposition."""
        article = _create_article()
        url = reverse(
            "portal-articles:article-citation-download", kwargs={"pk": article.pk}
        )
        response = client.get(url, {"format": "bibtex"})
        assert response.status_code == 200
        assert "attachment" in response["Content-Disposition"]
        assert ".bib" in response["Content-Disposition"]
        assert "application/x-bibtex" in response["Content-Type"]

    def test_download_ris_content_disposition(self, client):
        """11.10b: Citation download returns RIS file with correct Content-Disposition."""
        article = _create_article()
        url = reverse(
            "portal-articles:article-citation-download", kwargs={"pk": article.pk}
        )
        response = client.get(url, {"format": "ris"})
        assert response.status_code == 200
        assert "attachment" in response["Content-Disposition"]
        assert ".ris" in response["Content-Disposition"]
        assert "application/x-research-info-systems" in response["Content-Type"]

    # =========================================================================
    # 11.11: Citation download returns 400 for unknown format
    # =========================================================================

    def test_download_400_for_unknown_format(self, client):
        """11.11: Citation download returns 400 for unknown format."""
        article = _create_article()
        url = reverse(
            "portal-articles:article-citation-download", kwargs={"pk": article.pk}
        )
        response = client.get(url, {"format": "apa"})
        assert response.status_code == 400

    def test_download_400_for_missing_format(self, client):
        """11.11b: Citation download returns 400 when no format specified."""
        article = _create_article()
        url = reverse(
            "portal-articles:article-citation-download", kwargs={"pk": article.pk}
        )
        response = client.get(url)
        assert response.status_code == 400

    def test_download_404_for_draft_article(self, client):
        """Citation download returns 404 for DRAFT article."""
        article = _create_article(status=ArticleStatus.DRAFT)
        url = reverse(
            "portal-articles:article-citation-download", kwargs={"pk": article.pk}
        )
        response = client.get(url, {"format": "bibtex"})
        assert response.status_code == 404

    def test_download_404_for_nonexistent_article(self, client):
        """Citation download returns 404 for non-existent article."""
        url = reverse(
            "portal-articles:article-citation-download", kwargs={"pk": 99999}
        )
        response = client.get(url, {"format": "bibtex"})
        assert response.status_code == 404

    def test_download_bibtex_utf8_charset(self, client):
        """Citation download includes charset=utf-8 for proper Serbian character encoding."""
        article = _create_article()
        url = reverse(
            "portal-articles:article-citation-download", kwargs={"pk": article.pk}
        )
        response = client.get(url, {"format": "bibtex"})
        assert "charset=utf-8" in response["Content-Type"]

    def test_download_works_for_withdrawn(self, client):
        """Citation download works for WITHDRAWN article (standard academic practice)."""
        article = _create_article(status=ArticleStatus.WITHDRAWN)
        url = reverse(
            "portal-articles:article-citation-download", kwargs={"pk": article.pk}
        )
        response = client.get(url, {"format": "ris"})
        assert response.status_code == 200


# =============================================================================
# Template Tests
# =============================================================================


@pytest.mark.django_db
class TestCitationTemplates:
    """Tests for citation modal and floating action bar template rendering."""

    # =========================================================================
    # 11.12: Citation modal template contains Bootstrap 5 modal structure
    # =========================================================================

    def test_citation_modal_in_article_detail(self, client):
        """11.12: Citation modal template contains Bootstrap 5 modal structure."""
        article = _create_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert 'id="citationModal"' in content
        assert "modal-dialog" in content
        assert "modal-content" in content
        assert 'role="dialog"' in content
        assert 'aria-labelledby="citationModalLabel"' in content

    # =========================================================================
    # 11.13: Floating action bar Cite button contains data-bs-toggle="modal"
    # =========================================================================

    def test_cite_button_data_bs_toggle(self, client):
        """11.13: Floating action bar Cite button contains data-bs-toggle='modal'."""
        article = _create_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert 'data-bs-toggle="modal"' in content
        assert 'data-bs-target="#citationModal"' in content

    def test_cite_button_no_handleciteclick(self, client):
        """Floating action bar Cite button no longer has handleCiteClick handler."""
        article = _create_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "handleCiteClick" not in content

    def test_citation_modal_has_tabs(self, client):
        """Citation modal has format tabs: APA, MLA, Chicago, BibTeX, RIS."""
        article = _create_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "APA" in content
        assert "MLA" in content
        assert "BibTeX" in content
        assert "RIS" in content

    def test_citation_content_bibtex_code_format(self, client):
        """BibTeX citation is displayed in code format (pre/code block)."""
        article = _create_article()
        url = reverse("portal-articles:article-citation", kwargs={"pk": article.pk})
        response = client.get(url, {"format": "bibtex"})
        content = response.content.decode()
        assert "<pre" in content
        assert "<code" in content

    def test_citation_content_ris_code_format(self, client):
        """RIS citation is displayed in code format (pre/code block)."""
        article = _create_article()
        url = reverse("portal-articles:article-citation", kwargs={"pk": article.pk})
        response = client.get(url, {"format": "ris"})
        content = response.content.decode()
        assert "<pre" in content
        assert "<code" in content

    def test_citation_content_apa_plain_text(self, client):
        """APA citation is displayed as plain text (no pre/code block)."""
        article = _create_article()
        url = reverse("portal-articles:article-citation", kwargs={"pk": article.pk})
        response = client.get(url, {"format": "apa"})
        content = response.content.decode()
        assert "citation-text" in content

    def test_citation_tabs_have_aria_selected(self, client):
        """Citation modal tabs use Alpine.js :aria-selected binding for accessibility."""
        article = _create_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert ":aria-selected" in content

    def test_citation_tabs_use_alpine_class_binding(self, client):
        """Citation modal tabs use Alpine.js :class binding for active state."""
        article = _create_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert ":class=" in content
        assert "currentFormat" in content

    def test_article_detail_has_citation_url_context(self, client):
        """ArticleLandingView includes citation_url in context."""
        article = _create_article()
        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)
        assert "citation_url" in response.context
        assert "citation_download_url" in response.context
