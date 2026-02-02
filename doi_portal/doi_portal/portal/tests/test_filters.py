"""
Tests for advanced article filtering.

Story 4.3: Advanced Filtering for Articles.
Tests for search_articles() filters and ArticleSearchView filter context.
"""

import pytest
from django.urls import reverse

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory, AuthorFactory
from doi_portal.issues.models import IssueStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.portal.services import search_articles
from doi_portal.publications.models import AccessType, PublicationType
from doi_portal.publications.tests.factories import PublicationFactory, PublisherFactory


# =============================================================================
# Helper
# =============================================================================


def _create_article(
    title,
    pub_type=PublicationType.JOURNAL,
    subject="",
    language="sr",
    access=AccessType.OPEN,
    year=2025,
):
    """Create a published article with specific publication attributes."""
    publisher = PublisherFactory()
    pub = PublicationFactory(
        publisher=publisher,
        publication_type=pub_type,
        subject_area=subject,
        language=language,
        access_type=access,
    )
    issue = IssueFactory(publication=pub, year=year, status=IssueStatus.PUBLISHED)
    return ArticleFactory(issue=issue, title=title, status=ArticleStatus.PUBLISHED)


# =============================================================================
# Service Tests: search_articles() with filters
# =============================================================================


@pytest.mark.django_db
class TestSearchArticlesFilters:
    """Tests for search_articles() with filter parameters (6.1-6.8)."""

    def test_filter_by_publication_type(self):
        """6.1: Filter returns only articles from matching publication type."""
        journal_art = _create_article("Test Journal Article", pub_type=PublicationType.JOURNAL)
        conf_art = _create_article("Test Conference Article", pub_type=PublicationType.CONFERENCE)

        results = search_articles("Test", filters={"types": [PublicationType.JOURNAL]})

        assert journal_art in results
        assert conf_art not in results

    def test_filter_by_subject_area(self):
        """6.2: Filter returns only articles from matching subject area."""
        math = _create_article("Test Math Article", subject="Matematika")
        phys = _create_article("Test Physics Article", subject="Fizika")

        results = search_articles("Test", filters={"subjects": ["Matematika"]})

        assert math in results
        assert phys not in results

    def test_filter_by_language(self):
        """6.3: Filter returns only articles matching language."""
        sr_art = _create_article("Test Serbian Article", language="sr")
        en_art = _create_article("Test English Article", language="en")

        results = search_articles("Test", filters={"languages": ["sr"]})

        assert sr_art in results
        assert en_art not in results

    def test_filter_by_access_type(self):
        """6.4: Filter returns only articles with matching access type."""
        open_art = _create_article("Test Open Article", access=AccessType.OPEN)
        restricted_art = _create_article("Test Restricted Article", access=AccessType.RESTRICTED)

        results = search_articles("Test", filters={"access_types": [AccessType.OPEN]})

        assert open_art in results
        assert restricted_art not in results

    def test_filter_by_year_range(self):
        """6.5: Filter returns articles within year range."""
        old = _create_article("Test Old Article", year=2020)
        new = _create_article("Test New Article", year=2025)

        results = search_articles("Test", filters={"year_from": 2024, "year_to": 2026})

        assert new in results
        assert old not in results

    def test_combined_search_and_filter(self):
        """6.6: Search query and filters combine with AND logic."""
        match = _create_article("Quantum Research Paper", pub_type=PublicationType.JOURNAL)
        no_match = _create_article("Quantum Conference Paper", pub_type=PublicationType.CONFERENCE)

        results = search_articles("Quantum", filters={"types": [PublicationType.JOURNAL]})

        assert match in results
        assert no_match not in results

    def test_empty_filter_does_not_affect_results(self):
        """6.7: Empty filters dict does not affect results."""
        _create_article("Test Article Unchanged")

        results_no_filter = list(search_articles("Test"))
        results_empty_filter = list(search_articles("Test", filters={}))

        assert results_no_filter == results_empty_filter

    def test_invalid_filter_values_ignored(self):
        """6.8: Invalid/empty filter values are ignored gracefully."""
        art = _create_article("Test Resilient Article")

        # None values, empty lists within filters dict should not raise
        results = search_articles("Test", filters={
            "types": [],
            "subjects": [],
            "languages": [],
            "access_types": [],
        })

        assert art in results

    def test_filter_year_from_only(self):
        """Year from filter without year to works."""
        old = _create_article("Test YearFrom Old", year=2018)
        new = _create_article("Test YearFrom New", year=2025)

        results = search_articles("Test YearFrom", filters={"year_from": 2024})

        assert new in results
        assert old not in results

    def test_filter_year_to_only(self):
        """Year to filter without year from works."""
        old = _create_article("Test YearTo Old", year=2018)
        new = _create_article("Test YearTo New", year=2025)

        results = search_articles("Test YearTo", filters={"year_to": 2020})

        assert old in results
        assert new not in results

    def test_multiple_types_filter(self):
        """Multi-select type filter: JOURNAL + CONFERENCE returns both."""
        journal_art = _create_article("Test Multi Journal", pub_type=PublicationType.JOURNAL)
        conf_art = _create_article("Test Multi Conference", pub_type=PublicationType.CONFERENCE)
        book_art = _create_article("Test Multi Book", pub_type=PublicationType.BOOK)

        results = search_articles(
            "Test Multi",
            filters={"types": [PublicationType.JOURNAL, PublicationType.CONFERENCE]},
        )

        assert journal_art in results
        assert conf_art in results
        assert book_art not in results

    def test_none_filters_parameter(self):
        """None filters parameter same as no filters."""
        art = _create_article("Test None Filters")

        results_default = list(search_articles("Test None Filters"))
        results_none = list(search_articles("Test None Filters", filters=None))

        assert results_default == results_none


# =============================================================================
# View Tests: ArticleSearchView with filters
# =============================================================================


@pytest.mark.django_db
class TestArticleSearchViewFilters:
    """Tests for ArticleSearchView filter context and behavior (6.9-6.18)."""

    def test_filter_returns_filtered_results(self, client):
        """6.9: GET /search/ with filter params returns filtered results."""
        journal_art = _create_article("TestView Journal", pub_type=PublicationType.JOURNAL)
        conf_art = _create_article("TestView Conference", pub_type=PublicationType.CONFERENCE)

        response = client.get(reverse("article-search"), {"q": "TestView", "type": "JOURNAL"})

        articles = list(response.context["articles"])
        assert journal_art in articles
        assert conf_art not in articles

    def test_context_has_publication_types(self, client):
        """6.10: Context includes publication_types choices."""
        response = client.get(reverse("article-search"), {"q": "test"})
        assert "publication_types" in response.context

    def test_context_has_access_types(self, client):
        """6.10: Context includes access_types choices."""
        response = client.get(reverse("article-search"), {"q": "test"})
        assert "access_types" in response.context

    def test_context_has_subject_areas(self, client):
        """6.10: Context includes subject_areas."""
        response = client.get(reverse("article-search"), {"q": "test"})
        assert "subject_areas" in response.context

    def test_context_has_languages(self, client):
        """6.10: Context includes languages."""
        response = client.get(reverse("article-search"), {"q": "test"})
        assert "languages" in response.context

    def test_context_has_current_types(self, client):
        """6.11: Context includes current_types filter state."""
        response = client.get(reverse("article-search"), {"q": "test", "type": "JOURNAL"})
        assert "current_types" in response.context
        assert "JOURNAL" in response.context["current_types"]

    def test_context_has_current_subjects(self, client):
        """6.11: Context includes current_subjects filter state."""
        response = client.get(reverse("article-search"), {"q": "test", "subject": "Matematika"})
        assert "current_subjects" in response.context
        assert "Matematika" in response.context["current_subjects"]

    def test_context_has_current_languages(self, client):
        """6.11: Context includes current_languages."""
        response = client.get(reverse("article-search"), {"q": "test", "language": "sr"})
        assert "current_languages" in response.context
        assert "sr" in response.context["current_languages"]

    def test_context_has_current_access(self, client):
        """6.11: Context includes current_access."""
        response = client.get(reverse("article-search"), {"q": "test", "access": "OPEN"})
        assert "current_access" in response.context
        assert "OPEN" in response.context["current_access"]

    def test_has_active_filters_true(self, client):
        """6.12: has_active_filters is True when filters are applied."""
        response = client.get(reverse("article-search"), {"q": "test", "type": "JOURNAL"})
        assert response.context["has_active_filters"] is True

    def test_has_active_filters_false(self, client):
        """6.13: has_active_filters is False when no filters applied."""
        response = client.get(reverse("article-search"), {"q": "test"})
        assert response.context["has_active_filters"] is False

    def test_url_params_parsed_correctly(self, client):
        """6.14: All filter URL params parsed correctly."""
        response = client.get(
            reverse("article-search"),
            {
                "q": "test",
                "type": "JOURNAL",
                "subject": "Matematika",
                "language": "sr",
                "access": "OPEN",
                "year_from": "2020",
                "year_to": "2025",
            },
        )
        assert response.context["current_types"] == ["JOURNAL"]
        assert response.context["current_subjects"] == ["Matematika"]
        assert response.context["current_languages"] == ["sr"]
        assert response.context["current_access"] == ["OPEN"]
        assert response.context["current_year_from"] == "2020"
        assert response.context["current_year_to"] == "2025"

    def test_query_preserved_with_filters(self, client):
        """6.15: q parameter is preserved when filters are applied."""
        response = client.get(reverse("article-search"), {"q": "myquery", "type": "JOURNAL"})
        assert response.context["query"] == "myquery"

    def test_htmx_returns_partial_with_filters(self, client):
        """6.16: HTMX request returns partial template with filters."""
        response = client.get(
            reverse("article-search"),
            {"q": "test", "type": "JOURNAL"},
            HTTP_HX_REQUEST="true",
        )
        template_names = [t.name for t in response.templates]
        assert "portal/partials/_search_results.html" in template_names

    def test_clear_filters_preserves_query(self, client):
        """6.17: Clear all filters link preserves q param."""
        _create_article("TestClear Article", pub_type=PublicationType.JOURNAL)
        response = client.get(
            reverse("article-search"),
            {"q": "TestClear", "type": "JOURNAL"},
        )
        content = response.content.decode()
        # The clear link should go to /search/?q=TestClear
        assert "q=TestClear" in content

    def test_year_range_in_context(self, client):
        """6.18: year_range in context contains min and max year."""
        _create_article("TestYear Article", year=2020)
        _create_article("TestYear Recent", year=2025)

        response = client.get(reverse("article-search"), {"q": "TestYear"})
        year_range = response.context["year_range"]
        assert year_range["min"] is not None
        assert year_range["max"] is not None
        assert year_range["min"] <= year_range["max"]

    def test_has_active_filters_true_with_year_from(self, client):
        """has_active_filters is True when year_from is set."""
        response = client.get(
            reverse("article-search"),
            {"q": "test", "year_from": "2020"},
        )
        assert response.context["has_active_filters"] is True

    def test_has_active_filters_true_with_year_to(self, client):
        """has_active_filters is True when year_to is set."""
        response = client.get(
            reverse("article-search"),
            {"q": "test", "year_to": "2025"},
        )
        assert response.context["has_active_filters"] is True

    def test_invalid_year_ignored(self, client):
        """Non-numeric year params are ignored."""
        response = client.get(
            reverse("article-search"),
            {"q": "test", "year_from": "abc", "year_to": "xyz"},
        )
        assert response.context["current_year_from"] == ""
        assert response.context["current_year_to"] == ""
        assert response.context["has_active_filters"] is False

    def test_invalid_subject_filter_ignored(self, client):
        """Subject values not in database are ignored by view filter parsing."""
        _create_article("TestSubjectValid Article", subject="Matematika")

        response = client.get(
            reverse("article-search"),
            {"q": "TestSubjectValid", "subject": "NONEXISTENT_SUBJECT"},
        )
        # Invalid subject should be ignored, so all articles returned
        articles = list(response.context["articles"])
        assert len(articles) == 1

    def test_invalid_language_filter_ignored(self, client):
        """Language values not in database are ignored by view filter parsing."""
        _create_article("TestLangValid Article", language="sr")

        response = client.get(
            reverse("article-search"),
            {"q": "TestLangValid", "language": "NONEXISTENT_LANG"},
        )
        # Invalid language should be ignored, so all articles returned
        articles = list(response.context["articles"])
        assert len(articles) == 1
