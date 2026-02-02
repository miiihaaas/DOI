"""
Tests for article search functionality.

Story 4.2: Article Search Functionality.
Tests for search_articles service, ArticleSearchView, and highlight_search template filter.
"""

import pytest
from django.urls import reverse

from doi_portal.articles.models import Article, ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory, AuthorFactory
from doi_portal.portal.services import search_articles


# =============================================================================
# Service Tests: search_articles()
# =============================================================================


@pytest.mark.django_db
class TestSearchArticlesService:
    """Tests for search_articles service function."""

    def test_search_by_title(self):
        """9.1: Finds articles matching title."""
        article = ArticleFactory(
            title="Quantum Computing Research",
            status=ArticleStatus.PUBLISHED,
        )
        results = search_articles("Quantum")
        assert article in results

    def test_search_by_author_surname(self):
        """9.2: Finds articles by author surname."""
        article = ArticleFactory(status=ArticleStatus.PUBLISHED)
        AuthorFactory(article=article, surname="Petrović")
        results = search_articles("Petrović")
        assert article in results

    def test_search_by_keywords(self):
        """9.3: Finds articles by keywords JSON field."""
        article = ArticleFactory(
            keywords=["machine learning", "AI"],
            status=ArticleStatus.PUBLISHED,
        )
        results = search_articles("machine learning")
        assert article in results

    def test_search_by_abstract(self):
        """9.4: Finds articles matching abstract text."""
        article = ArticleFactory(
            abstract="This paper explores deep learning techniques.",
            status=ArticleStatus.PUBLISHED,
        )
        results = search_articles("deep learning")
        assert article in results

    def test_excludes_non_published(self):
        """9.5: Only PUBLISHED articles are returned."""
        ArticleFactory(title="Draft Article", status=ArticleStatus.DRAFT)
        ArticleFactory(title="Review Article", status=ArticleStatus.REVIEW)
        ArticleFactory(title="Ready Article", status=ArticleStatus.READY)
        ArticleFactory(title="Withdrawn Article", status=ArticleStatus.WITHDRAWN)
        pub = ArticleFactory(title="Published Article", status=ArticleStatus.PUBLISHED)
        results = search_articles("Article")
        assert list(results) == [pub]

    def test_excludes_soft_deleted(self):
        """9.6: Soft-deleted articles excluded."""
        article = ArticleFactory(
            title="Deleted Research",
            status=ArticleStatus.PUBLISHED,
        )
        article.soft_delete()
        results = search_articles("Deleted")
        assert article not in results

    def test_empty_query_returns_none(self):
        """9.7: Empty query returns empty queryset."""
        ArticleFactory(status=ArticleStatus.PUBLISHED)
        results = search_articles("")
        assert results.count() == 0

    def test_short_query_returns_none(self):
        """9.7 (extra): Query < 3 chars returns empty queryset."""
        ArticleFactory(title="AB test", status=ArticleStatus.PUBLISHED)
        results = search_articles("AB")
        assert results.count() == 0

    def test_search_query_count(self, django_assert_num_queries):
        """9.8: Verify optimized query count with select_related/prefetch_related."""
        article = ArticleFactory(
            title="Query Count Test Article",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(article=article, surname="QueryAuthor")

        # Execute search and force queryset evaluation including related fields
        # 1 query for articles (with select_related join + inline author subquery)
        # 1 query for prefetch authors
        # Total: 2 queries (author subquery is inlined by Django ORM)
        with django_assert_num_queries(2):
            results = list(search_articles("Query Count"))
            # Access related fields to trigger lazy loading if not pre-fetched
            for r in results:
                _ = r.issue.publication.publisher
                _ = list(r.authors.all())

    def test_search_by_author_given_name(self):
        """Finds articles by author given_name."""
        article = ArticleFactory(status=ArticleStatus.PUBLISHED)
        AuthorFactory(article=article, given_name="Nikola", surname="Jovanović")
        results = search_articles("Nikola")
        assert article in results


# =============================================================================
# View Tests: ArticleSearchView
# =============================================================================


@pytest.mark.django_db
class TestArticleSearchView:
    """Tests for ArticleSearchView."""

    def test_search_page_returns_200(self, client):
        """9.9: GET /search/ returns 200."""
        response = client.get(reverse("article-search"))
        assert response.status_code == 200

    def test_search_uses_correct_template(self, client):
        """9.10: Uses portal/search_results.html template."""
        response = client.get(reverse("article-search"))
        template_names = [t.name for t in response.templates]
        assert "portal/search_results.html" in template_names

    def test_search_with_query(self, client):
        """9.11: Search with valid query returns results in context."""
        ArticleFactory(title="Quantum Test Article", status=ArticleStatus.PUBLISHED)
        response = client.get(reverse("article-search"), {"q": "Quantum"})
        assert "articles" in response.context
        assert response.context["query"] == "Quantum"

    def test_context_has_query_and_result_count(self, client):
        """9.12: context contains query and result_count."""
        ArticleFactory(title="Context Test Article", status=ArticleStatus.PUBLISHED)
        response = client.get(reverse("article-search"), {"q": "Context Test"})
        assert response.context["query"] == "Context Test"
        assert response.context["result_count"] == 1

    def test_empty_query_shows_form(self, client):
        """9.13: Empty query shows search form without results."""
        response = client.get(reverse("article-search"))
        content = response.content.decode()
        assert "Pretražite članke" in content

    def test_short_query_message(self, client):
        """9.14: Query < 3 chars shows minimum length message."""
        response = client.get(reverse("article-search"), {"q": "AB"})
        assert response.context["query"] == "AB"
        content = response.content.decode()
        assert "najmanje" in content or response.context["min_query_length"] == 3

    def test_pagination(self, client):
        """9.15: Pagination works with many results."""
        for i in range(25):
            ArticleFactory(
                title=f"Test Article {i}",
                status=ArticleStatus.PUBLISHED,
            )
        response = client.get(reverse("article-search"), {"q": "Test Article"})
        assert response.context["is_paginated"] is True

    def test_no_results_message(self, client):
        """9.16: No results shows empty state message."""
        response = client.get(
            reverse("article-search"),
            {"q": "nonexistent12345"},
        )
        content = response.content.decode()
        assert "Nema pronađenih članaka" in content

    def test_breadcrumbs(self, client):
        """9.17: Breadcrumbs include Početna and Pretraga."""
        response = client.get(reverse("article-search"))
        breadcrumbs = response.context["breadcrumbs"]
        assert breadcrumbs[0]["label"] == "Početna"
        assert breadcrumbs[1]["label"] == "Pretraga"

    def test_no_auth_required(self, client):
        """9.18: Public page - no login required."""
        response = client.get(reverse("article-search"))
        assert response.status_code == 200

    def test_htmx_returns_partial(self, client):
        """9.19: HTMX request returns partial template."""
        response = client.get(
            reverse("article-search"),
            {"q": "test"},
            HTTP_HX_REQUEST="true",
        )
        template_names = [t.name for t in response.templates]
        assert "portal/partials/_search_results.html" in template_names

    def test_no_results_result_count_zero(self, client):
        """result_count is 0 when no results found."""
        response = client.get(
            reverse("article-search"),
            {"q": "nonexistent12345"},
        )
        assert response.context["result_count"] == 0

    def test_long_query_truncated(self, client):
        """Very long queries are truncated to prevent DoS."""
        long_query = "a" * 500
        response = client.get(reverse("article-search"), {"q": long_query})
        assert response.status_code == 200
        # Query should be capped at 200 chars
        assert len(response.context["query"]) == 200


# =============================================================================
# Template Filter Tests: highlight_search
# =============================================================================


@pytest.mark.django_db
class TestHighlightSearchFilter:
    """Tests for highlight_search template filter."""

    def test_highlight_wraps_in_mark(self):
        """9.20: highlight_search wraps match in <mark> tag."""
        from doi_portal.portal.templatetags.portal_tags import highlight_search

        result = highlight_search("Quantum Computing Research", "Quantum")
        assert "<mark>Quantum</mark>" in result

    def test_highlight_case_insensitive(self):
        """9.21: highlight is case-insensitive."""
        from doi_portal.portal.templatetags.portal_tags import highlight_search

        result = highlight_search("Quantum Computing", "quantum")
        assert "<mark>Quantum</mark>" in result

    def test_highlight_escapes_html(self):
        """9.22: highlight escapes HTML input (XSS prevention)."""
        from doi_portal.portal.templatetags.portal_tags import highlight_search

        result = highlight_search("<script>alert('xss')</script>", "script")
        assert "<script>" not in result
        assert "&lt;" in result
        assert "<mark>" in result

    def test_highlight_empty_query(self):
        """highlight_search with empty query returns original text."""
        from doi_portal.portal.templatetags.portal_tags import highlight_search

        result = highlight_search("Some text", "")
        assert result == "Some text"

    def test_highlight_empty_text(self):
        """highlight_search with empty text returns empty."""
        from doi_portal.portal.templatetags.portal_tags import highlight_search

        result = highlight_search("", "query")
        assert result == ""

    def test_highlight_none_text(self):
        """highlight_search with None text returns empty string."""
        from doi_portal.portal.templatetags.portal_tags import highlight_search

        result = highlight_search(None, "query")
        assert result == ""

    def test_highlight_none_query(self):
        """highlight_search with None query returns original text."""
        from doi_portal.portal.templatetags.portal_tags import highlight_search

        result = highlight_search("Some text", None)
        assert result == "Some text"
