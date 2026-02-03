"""
Tests for pre-generation validation.

Story 5.2: Pre-Generation Validation & Warnings.
Tests for ValidationResult, ValidationIssue, and PreValidationService.
"""

from datetime import date

import pytest

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.models import AuthorSequence
from doi_portal.articles.models import ContributorRole
from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.articles.tests.factories import AuthorFactory
from doi_portal.core.models import SiteSettings
from doi_portal.crossref.validation import ValidationIssue
from doi_portal.crossref.validation import ValidationResult
from doi_portal.crossref.validation import ValidationSeverity
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.models import PublicationType
from doi_portal.publications.tests.factories import BookFactory
from doi_portal.publications.tests.factories import ConferenceFactory
from doi_portal.publications.tests.factories import JournalFactory
from doi_portal.publications.tests.factories import PublisherFactory
from doi_portal.users.tests.factories import UserFactory


# =============================================================================
# Task 1: Tests for ValidationResult and ValidationIssue data classes
# =============================================================================


class TestValidationSeverity:
    """Tests for ValidationSeverity enum."""

    def test_severity_values(self):
        """Test severity enum has expected values."""
        assert ValidationSeverity.ERROR.value == "error"
        assert ValidationSeverity.WARNING.value == "warning"


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""

    def test_create_error_issue(self):
        """Test creating an error issue."""
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Nedostaje ISSN",
            field_name="issn_print",
        )
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.message == "Nedostaje ISSN"
        assert issue.field_name == "issn_print"
        assert issue.article_id is None
        assert issue.fix_url is None

    def test_create_warning_issue(self):
        """Test creating a warning issue."""
        issue = ValidationIssue(
            severity=ValidationSeverity.WARNING,
            message="Autor nema ime",
            field_name="given_name",
            article_id=123,
        )
        assert issue.severity == ValidationSeverity.WARNING
        assert issue.article_id == 123

    def test_issue_with_fix_url(self):
        """Test issue with fix URL."""
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Test",
            field_name="test",
            fix_url="/admin/articles/1/change/",
        )
        assert issue.fix_url == "/admin/articles/1/change/"


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_empty_result_is_valid(self):
        """Test empty result is valid."""
        result = ValidationResult()
        assert result.is_valid is True
        assert result.has_errors() is False
        assert result.has_warnings() is False

    def test_result_with_error_is_invalid(self):
        """Test result with error is invalid."""
        result = ValidationResult()
        result.add_error("Test error", "field")
        assert result.is_valid is False
        assert result.has_errors() is True

    def test_result_with_warning_only_is_valid(self):
        """Test result with only warnings is still valid."""
        result = ValidationResult()
        result.add_warning("Test warning", "field")
        assert result.is_valid is True
        assert result.has_warnings() is True
        assert result.has_errors() is False

    def test_add_error(self):
        """Test add_error method."""
        result = ValidationResult()
        result.add_error(
            message="Nedostaje naslov članka",
            field_name="title",
            article_id=42,
            fix_url="/articles/42/edit/",
        )
        assert len(result.errors) == 1
        error = result.errors[0]
        assert error.severity == ValidationSeverity.ERROR
        assert error.message == "Nedostaje naslov članka"
        assert error.field_name == "title"
        assert error.article_id == 42
        assert error.fix_url == "/articles/42/edit/"

    def test_add_warning(self):
        """Test add_warning method."""
        result = ValidationResult()
        result.add_warning(
            message="Autor nema ime",
            field_name="given_name",
        )
        assert len(result.warnings) == 1
        warning = result.warnings[0]
        assert warning.severity == ValidationSeverity.WARNING

    def test_errors_property_filters_correctly(self):
        """Test errors property returns only errors."""
        result = ValidationResult()
        result.add_error("Error 1", "field1")
        result.add_warning("Warning 1", "field2")
        result.add_error("Error 2", "field3")

        assert len(result.errors) == 2
        assert all(e.severity == ValidationSeverity.ERROR for e in result.errors)

    def test_warnings_property_filters_correctly(self):
        """Test warnings property returns only warnings."""
        result = ValidationResult()
        result.add_error("Error 1", "field1")
        result.add_warning("Warning 1", "field2")
        result.add_warning("Warning 2", "field3")

        assert len(result.warnings) == 2
        assert all(w.severity == ValidationSeverity.WARNING for w in result.warnings)

    def test_all_issues_returns_copy(self):
        """Test all_issues returns a copy of the list."""
        result = ValidationResult()
        result.add_error("Error", "field")
        issues = result.all_issues()
        issues.clear()  # Modify the returned list
        assert len(result.issues) == 1  # Original should be unchanged

    def test_merge_combines_issues(self):
        """Test merge combines issues from another result."""
        result1 = ValidationResult()
        result1.add_error("Error 1", "field1")

        result2 = ValidationResult()
        result2.add_warning("Warning 1", "field2")
        result2.add_error("Error 2", "field3")

        result1.merge(result2)

        assert len(result1.issues) == 3
        assert len(result1.errors) == 2
        assert len(result1.warnings) == 1


# =============================================================================
# Task 2 & 6: Tests for PreValidationService
# =============================================================================


@pytest.fixture
def site_settings_configured(db):
    """Create SiteSettings with depositor data configured."""
    return SiteSettings.objects.create(
        depositor_name="Test Depositor",
        depositor_email="depositor@test.com",
    )


@pytest.fixture
def site_settings_empty(db):
    """Create SiteSettings without depositor data."""
    return SiteSettings.objects.create(
        depositor_name="",
        depositor_email="",
    )


@pytest.fixture
def publisher(db):
    """Create test publisher."""
    return PublisherFactory(
        name="Test Publisher",
        doi_prefix="10.12345",
    )


@pytest.fixture
def journal_with_issn(publisher):
    """Create journal publication with ISSN."""
    return JournalFactory(
        title="Test Journal",
        publisher=publisher,
        issn_print="1234-5678",
        issn_online="",
    )


@pytest.fixture
def journal_without_issn(publisher):
    """Create journal publication without ISSN."""
    return JournalFactory(
        title="Test Journal No ISSN",
        publisher=publisher,
        issn_print="",
        issn_online="",
    )


@pytest.fixture
def conference_with_fields(publisher):
    """Create conference publication with required fields."""
    return ConferenceFactory(
        title="Test Conference",
        publisher=publisher,
        conference_name="International Test Conference",
        conference_date=date(2026, 5, 15),
        conference_location="Belgrade, Serbia",
    )


@pytest.fixture
def conference_without_fields(publisher):
    """Create conference publication without required fields."""
    return ConferenceFactory(
        title="Test Conference Missing",
        publisher=publisher,
        conference_name="",
        conference_date=None,
        conference_location="",
    )


@pytest.fixture
def book_with_isbn(publisher):
    """Create book publication with ISBN."""
    return BookFactory(
        title="Test Book",
        publisher=publisher,
        isbn_print="978-86-7549-100-1",
    )


@pytest.fixture
def book_without_isbn(publisher):
    """Create book publication without ISBN."""
    return BookFactory(
        title="Test Book No ISBN",
        publisher=publisher,
        isbn_print="",
        isbn_online="",
    )


@pytest.fixture
def journal_issue(journal_with_issn):
    """Create journal issue with publication date."""
    return IssueFactory(
        publication=journal_with_issn,
        volume="10",
        issue_number="2",
        year=2026,
        publication_date=date(2026, 3, 15),
    )


@pytest.fixture
def journal_issue_without_date(journal_with_issn):
    """Create journal issue without publication date."""
    return IssueFactory(
        publication=journal_with_issn,
        volume="10",
        issue_number="2",
        year=2026,
        publication_date=None,
    )


@pytest.fixture
def valid_article(journal_issue, site_settings_configured):
    """Create a fully valid article with all required fields."""
    article = ArticleFactory(
        issue=journal_issue,
        title="Valid Article Title",
        doi_suffix="test.2026.001",
        status=ArticleStatus.PUBLISHED,
    )
    # Create first author with all required fields
    AuthorFactory(
        article=article,
        given_name="John",
        surname="Doe",
        sequence=AuthorSequence.FIRST,
        contributor_role=ContributorRole.AUTHOR,
        order=1,
    )
    return article


@pytest.fixture
def article_without_title(journal_issue, site_settings_configured):
    """Create article without title."""
    article = ArticleFactory(
        issue=journal_issue,
        title="",
        doi_suffix="test.2026.002",
        status=ArticleStatus.PUBLISHED,
    )
    AuthorFactory(
        article=article,
        surname="Doe",
        sequence=AuthorSequence.FIRST,
        contributor_role=ContributorRole.AUTHOR,
    )
    return article


@pytest.fixture
def article_without_doi_suffix(journal_issue, site_settings_configured):
    """Create article without DOI suffix."""
    article = ArticleFactory(
        issue=journal_issue,
        title="Article Without DOI",
        doi_suffix="",
        status=ArticleStatus.PUBLISHED,
    )
    AuthorFactory(
        article=article,
        surname="Doe",
        sequence=AuthorSequence.FIRST,
        contributor_role=ContributorRole.AUTHOR,
    )
    return article


@pytest.fixture
def article_without_authors(journal_issue, site_settings_configured):
    """Create article without any authors."""
    return ArticleFactory(
        issue=journal_issue,
        title="Article Without Authors",
        doi_suffix="test.2026.003",
        status=ArticleStatus.PUBLISHED,
    )


@pytest.fixture
def article_with_invalid_author(journal_issue, site_settings_configured):
    """Create article with author missing required fields."""
    article = ArticleFactory(
        issue=journal_issue,
        title="Article With Invalid Author",
        doi_suffix="test.2026.004",
        status=ArticleStatus.PUBLISHED,
    )
    # Author without surname
    AuthorFactory(
        article=article,
        given_name="John",
        surname="",
        sequence=AuthorSequence.FIRST,
        contributor_role=ContributorRole.AUTHOR,
    )
    return article


@pytest.fixture
def article_first_author_not_first(journal_issue, site_settings_configured):
    """Create article where first author doesn't have sequence='first'."""
    article = ArticleFactory(
        issue=journal_issue,
        title="Article Bad Sequence",
        doi_suffix="test.2026.005",
        status=ArticleStatus.PUBLISHED,
    )
    # First author in order but with 'additional' sequence
    AuthorFactory(
        article=article,
        surname="Doe",
        sequence=AuthorSequence.ADDITIONAL,  # Wrong!
        contributor_role=ContributorRole.AUTHOR,
        order=1,
    )
    return article


@pytest.mark.django_db
class TestPreValidationServiceDepositor:
    """Tests for depositor settings validation (AC5)."""

    def test_validates_depositor_settings_missing(self, journal_issue, site_settings_empty):
        """Test error when depositor settings not configured."""
        from doi_portal.crossref.services import PreValidationService

        service = PreValidationService()
        result = service.validate_issue(journal_issue)

        assert result.has_errors()
        error_messages = [e.message for e in result.errors]
        assert any("depositor" in msg.lower() or "deponent" in msg.lower() for msg in error_messages)

    def test_validates_depositor_settings_present(self, journal_issue, site_settings_configured):
        """Test passes when depositor settings configured."""
        from doi_portal.crossref.services import PreValidationService

        # Create a valid article to avoid other validation errors
        article = ArticleFactory(
            issue=journal_issue,
            title="Test",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        service = PreValidationService()
        result = service.validate_issue(journal_issue)

        depositor_errors = [
            e for e in result.errors
            if "depositor" in e.field_name.lower() or "deponent" in e.field_name.lower()
        ]
        assert len(depositor_errors) == 0


@pytest.mark.django_db
class TestPreValidationServiceJournal:
    """Tests for journal-specific validation (AC2)."""

    def test_validates_journal_issn_missing(self, journal_without_issn, site_settings_configured):
        """Test error when journal has no ISSN."""
        from doi_portal.crossref.services import PreValidationService

        issue = IssueFactory(
            publication=journal_without_issn,
            year=2026,
            publication_date=date(2026, 1, 1),
        )
        # Add a valid article
        article = ArticleFactory(
            issue=issue,
            title="Test",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        service = PreValidationService()
        result = service.validate_issue(issue)

        assert result.has_errors()
        issn_errors = [e for e in result.errors if "issn" in e.field_name.lower()]
        assert len(issn_errors) > 0

    def test_validates_journal_issn_present_print(self, journal_with_issn, site_settings_configured):
        """Test passes when journal has print ISSN."""
        from doi_portal.crossref.services import PreValidationService

        issue = IssueFactory(
            publication=journal_with_issn,
            year=2026,
            publication_date=date(2026, 1, 1),
        )
        article = ArticleFactory(
            issue=issue,
            title="Test",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        service = PreValidationService()
        result = service.validate_issue(issue)

        issn_errors = [e for e in result.errors if "issn" in e.field_name.lower()]
        assert len(issn_errors) == 0

    def test_validates_journal_issn_present_online(self, publisher, site_settings_configured):
        """Test passes when journal has online ISSN only."""
        from doi_portal.crossref.services import PreValidationService

        journal = JournalFactory(
            title="Online Journal",
            publisher=publisher,
            issn_print="",
            issn_online="2345-6789",
        )
        issue = IssueFactory(
            publication=journal,
            year=2026,
            publication_date=date(2026, 1, 1),
        )
        article = ArticleFactory(
            issue=issue,
            title="Test",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        service = PreValidationService()
        result = service.validate_issue(issue)

        issn_errors = [e for e in result.errors if "issn" in e.field_name.lower()]
        assert len(issn_errors) == 0


@pytest.mark.django_db
class TestPreValidationServiceConference:
    """Tests for conference-specific validation (AC3)."""

    def test_validates_conference_name_missing(self, conference_without_fields, site_settings_configured):
        """Test error when conference name is missing."""
        from doi_portal.crossref.services import PreValidationService

        issue = IssueFactory(
            publication=conference_without_fields,
            year=2026,
            publication_date=date(2026, 1, 1),
        )
        article = ArticleFactory(
            issue=issue,
            title="Test",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        service = PreValidationService()
        result = service.validate_issue(issue)

        assert result.has_errors()
        conf_errors = [e for e in result.errors if "conference" in e.field_name.lower()]
        assert len(conf_errors) > 0

    def test_validates_conference_fields_present(self, conference_with_fields, site_settings_configured):
        """Test passes when conference fields are present."""
        from doi_portal.crossref.services import PreValidationService

        issue = IssueFactory(
            publication=conference_with_fields,
            year=2026,
            publication_date=date(2026, 1, 1),
            proceedings_title="Test Proceedings",
        )
        article = ArticleFactory(
            issue=issue,
            title="Test",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        service = PreValidationService()
        result = service.validate_issue(issue)

        conf_errors = [e for e in result.errors if "conference" in e.field_name.lower()]
        assert len(conf_errors) == 0

    def test_validates_conference_date_warning(self, conference_without_fields, site_settings_configured):
        """Test warning when conference date is missing."""
        from doi_portal.crossref.services import PreValidationService

        # Set conference_name but not date
        conference_without_fields.conference_name = "Test Conference"
        conference_without_fields.save()

        issue = IssueFactory(
            publication=conference_without_fields,
            year=2026,
            publication_date=date(2026, 1, 1),
            proceedings_title="Test Proceedings",
        )
        article = ArticleFactory(
            issue=issue,
            title="Test",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        service = PreValidationService()
        result = service.validate_issue(issue)

        # Should have warning for missing date
        date_warnings = [w for w in result.warnings if "date" in w.field_name.lower() or "datum" in w.message.lower()]
        assert len(date_warnings) > 0


@pytest.mark.django_db
class TestPreValidationServiceBook:
    """Tests for book-specific validation (AC4)."""

    def test_validates_book_isbn_missing(self, book_without_isbn, site_settings_configured):
        """Test error when book has no ISBN."""
        from doi_portal.crossref.services import PreValidationService

        issue = IssueFactory(
            publication=book_without_isbn,
            year=2026,
            publication_date=date(2026, 1, 1),
        )
        article = ArticleFactory(
            issue=issue,
            title="Test",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        service = PreValidationService()
        result = service.validate_issue(issue)

        assert result.has_errors()
        isbn_errors = [e for e in result.errors if "isbn" in e.field_name.lower()]
        assert len(isbn_errors) > 0

    def test_validates_book_isbn_present(self, book_with_isbn, site_settings_configured):
        """Test passes when book has ISBN."""
        from doi_portal.crossref.services import PreValidationService

        issue = IssueFactory(
            publication=book_with_isbn,
            year=2026,
            publication_date=date(2026, 1, 1),
        )
        article = ArticleFactory(
            issue=issue,
            title="Test",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        service = PreValidationService()
        result = service.validate_issue(issue)

        isbn_errors = [e for e in result.errors if "isbn" in e.field_name.lower()]
        assert len(isbn_errors) == 0


@pytest.mark.django_db
class TestPreValidationServiceArticle:
    """Tests for article-level validation (AC2)."""

    def test_validates_article_title_required(self, article_without_title):
        """Test error when article missing title."""
        from doi_portal.crossref.services import PreValidationService

        service = PreValidationService()
        result = service.validate_issue(article_without_title.issue)

        assert result.has_errors()
        title_errors = [e for e in result.errors if "title" in e.field_name.lower() or "naslov" in e.message.lower()]
        assert len(title_errors) > 0

    def test_validates_article_doi_suffix_required(self, article_without_doi_suffix):
        """Test error when article missing DOI suffix."""
        from doi_portal.crossref.services import PreValidationService

        service = PreValidationService()
        result = service.validate_issue(article_without_doi_suffix.issue)

        assert result.has_errors()
        doi_errors = [e for e in result.errors if "doi" in e.field_name.lower()]
        assert len(doi_errors) > 0

    def test_validates_article_has_authors(self, article_without_authors):
        """Test error when article has no authors."""
        from doi_portal.crossref.services import PreValidationService

        service = PreValidationService()
        result = service.validate_issue(article_without_authors.issue)

        assert result.has_errors()
        author_errors = [e for e in result.errors if "author" in e.field_name.lower() or "autor" in e.message.lower()]
        assert len(author_errors) > 0


@pytest.mark.django_db
class TestPreValidationServiceAuthor:
    """Tests for author-level validation (AC2)."""

    def test_validates_author_surname_required(self, article_with_invalid_author):
        """Test error when author missing surname."""
        from doi_portal.crossref.services import PreValidationService

        service = PreValidationService()
        result = service.validate_issue(article_with_invalid_author.issue)

        assert result.has_errors()
        surname_errors = [e for e in result.errors if "surname" in e.field_name.lower() or "prezime" in e.message.lower()]
        assert len(surname_errors) > 0

    def test_validates_author_sequence_first(self, article_first_author_not_first):
        """Test error when first author doesn't have sequence='first'."""
        from doi_portal.crossref.services import PreValidationService

        service = PreValidationService()
        result = service.validate_issue(article_first_author_not_first.issue)

        assert result.has_errors()
        sequence_errors = [e for e in result.errors if "sequence" in e.field_name.lower()]
        assert len(sequence_errors) > 0

    def test_validates_author_given_name_warning(self, journal_issue, site_settings_configured):
        """Test warning when author missing given_name (recommended but not required)."""
        from doi_portal.crossref.services import PreValidationService

        article = ArticleFactory(
            issue=journal_issue,
            title="Test Article",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        # Author with surname but no given_name
        AuthorFactory(
            article=article,
            given_name="",
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        service = PreValidationService()
        result = service.validate_issue(journal_issue)

        # Should be a warning, not an error
        name_warnings = [w for w in result.warnings if "given_name" in w.field_name.lower() or "ime" in w.message.lower()]
        assert len(name_warnings) > 0

    def test_validates_author_contributor_role(self, journal_issue, site_settings_configured):
        """Test author contributor_role is validated."""
        from doi_portal.crossref.services import PreValidationService

        article = ArticleFactory(
            issue=journal_issue,
            title="Test Article",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        author = AuthorFactory(
            article=article,
            surname="Doe",
            sequence=AuthorSequence.FIRST,
        )
        # Clear contributor_role (should be set by default, but let's test)
        author.contributor_role = ""
        author.save()

        service = PreValidationService()
        result = service.validate_issue(journal_issue)

        role_errors = [e for e in result.errors if "contributor_role" in e.field_name.lower() or "uloga" in e.message.lower()]
        assert len(role_errors) > 0


@pytest.mark.django_db
class TestPreValidationServiceCommon:
    """Tests for common field validation."""

    def test_validates_publication_date_required(self, journal_issue_without_date, site_settings_configured):
        """Test error when publication_date is missing."""
        from doi_portal.crossref.services import PreValidationService

        article = ArticleFactory(
            issue=journal_issue_without_date,
            title="Test",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        service = PreValidationService()
        result = service.validate_issue(journal_issue_without_date)

        assert result.has_errors()
        date_errors = [e for e in result.errors if "publication_date" in e.field_name.lower() or "datum" in e.message.lower()]
        assert len(date_errors) > 0


@pytest.mark.django_db
class TestPreValidationServiceCategorization:
    """Tests for validation result categorization (AC6)."""

    def test_categorizes_errors_and_warnings(self, journal_issue, site_settings_configured):
        """Test issues properly categorized by severity."""
        from doi_portal.crossref.services import PreValidationService

        article = ArticleFactory(
            issue=journal_issue,
            title="Test Article",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        # Author without given_name (warning) but with other required fields
        AuthorFactory(
            article=article,
            given_name="",  # Missing - should be warning
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        service = PreValidationService()
        result = service.validate_issue(journal_issue)

        # Should have at least one warning for missing given_name
        assert len(result.warnings) >= 1
        # All errors and warnings should be properly categorized
        for issue in result.errors:
            assert issue.severity == ValidationSeverity.ERROR
        for issue in result.warnings:
            assert issue.severity == ValidationSeverity.WARNING

    def test_is_valid_with_no_errors(self, valid_article):
        """Test is_valid returns True when no errors."""
        from doi_portal.crossref.services import PreValidationService

        service = PreValidationService()
        result = service.validate_issue(valid_article.issue)

        assert result.is_valid is True

    def test_is_valid_false_with_errors(self, article_without_title):
        """Test is_valid returns False when errors present."""
        from doi_portal.crossref.services import PreValidationService

        service = PreValidationService()
        result = service.validate_issue(article_without_title.issue)

        assert result.is_valid is False


@pytest.mark.django_db
class TestPreValidationServiceIntegration:
    """Integration tests for complete validation scenarios."""

    def test_fully_valid_journal_issue(self, journal_issue, site_settings_configured):
        """Test a fully valid journal issue passes all validations."""
        from doi_portal.crossref.services import PreValidationService

        # Create complete valid article
        article = ArticleFactory(
            issue=journal_issue,
            title="Complete Valid Article",
            doi_suffix="valid.2026.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            given_name="John",
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
            order=1,
        )

        service = PreValidationService()
        result = service.validate_issue(journal_issue)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_only_published_articles_validated(self, journal_issue, site_settings_configured):
        """Test only PUBLISHED articles are validated."""
        from doi_portal.crossref.services import PreValidationService

        # Create draft article with missing data - should NOT cause errors
        ArticleFactory(
            issue=journal_issue,
            title="",  # Missing title
            doi_suffix="",  # Missing DOI
            status=ArticleStatus.DRAFT,  # Not published
        )

        # Create valid published article
        article = ArticleFactory(
            issue=journal_issue,
            title="Valid Published",
            doi_suffix="pub.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            given_name="John",
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        service = PreValidationService()
        result = service.validate_issue(journal_issue)

        # Should pass because only the valid published article is checked
        assert result.is_valid is True


# =============================================================================
# Task 3 & 6: Tests for IssueValidationView
# =============================================================================


@pytest.fixture
def admin_user(db):
    """Create an admin user for view tests."""
    return UserFactory(is_superuser=True, is_staff=True)


@pytest.mark.django_db
class TestIssueValidationView:
    """Tests for the IssueValidationView (AC1, AC6, AC7)."""

    def test_view_returns_html(self, client, admin_user, journal_issue, site_settings_configured):
        """Test view returns HTML partial."""
        client.force_login(admin_user)

        # Create valid article
        article = ArticleFactory(
            issue=journal_issue,
            title="Test Article",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            given_name="John",
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        response = client.get(f"/dashboard/crossref/issues/{journal_issue.pk}/validate/")

        assert response.status_code == 200
        assert "text/html" in response["Content-Type"]

    def test_view_returns_404_for_invalid_issue(self, client, admin_user, site_settings_configured):
        """Test view returns 404 for non-existent issue."""
        client.force_login(admin_user)
        response = client.get("/dashboard/crossref/issues/99999/validate/")
        assert response.status_code == 404

    def test_view_context_contains_validation_data(self, client, admin_user, journal_issue, site_settings_configured):
        """Test view context contains validation result data."""
        client.force_login(admin_user)

        # Create article with missing title to trigger error
        ArticleFactory(
            issue=journal_issue,
            title="",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )

        response = client.get(f"/dashboard/crossref/issues/{journal_issue.pk}/validate/")

        assert response.status_code == 200
        assert "is_valid" in response.context
        assert "errors" in response.context
        assert "warnings" in response.context
        assert "error_count" in response.context

    def test_view_shows_errors_for_invalid_issue(self, client, admin_user, journal_issue, site_settings_configured):
        """Test view shows errors when validation fails."""
        client.force_login(admin_user)

        # Create article without authors
        ArticleFactory(
            issue=journal_issue,
            title="Test Article",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )

        response = client.get(f"/dashboard/crossref/issues/{journal_issue.pk}/validate/")

        assert response.status_code == 200
        assert response.context["is_valid"] is False
        assert response.context["error_count"] > 0

    def test_view_shows_valid_for_complete_issue(self, client, admin_user, journal_issue, site_settings_configured):
        """Test view shows valid state for complete issue (AC7)."""
        client.force_login(admin_user)

        # Create complete valid article
        article = ArticleFactory(
            issue=journal_issue,
            title="Complete Article",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            given_name="John",
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        response = client.get(f"/dashboard/crossref/issues/{journal_issue.pk}/validate/")

        assert response.status_code == 200
        assert response.context["is_valid"] is True
        assert response.context["error_count"] == 0

    def test_view_uses_correct_template(self, client, admin_user, journal_issue, site_settings_configured):
        """Test view uses the validation panel template."""
        client.force_login(admin_user)

        article = ArticleFactory(
            issue=journal_issue,
            title="Test",
            doi_suffix="test.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        response = client.get(f"/dashboard/crossref/issues/{journal_issue.pk}/validate/")

        assert response.status_code == 200
        assert "crossref/partials/_validation_panel.html" in [t.name for t in response.templates]

    def test_view_requires_authentication(self, client, journal_issue, site_settings_configured):
        """Test view requires login (AC1: Administrator access)."""
        # Unauthenticated request should redirect to login
        response = client.get(f"/dashboard/crossref/issues/{journal_issue.pk}/validate/")

        # Should redirect to login page (302)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url or "/login/" in response.url

    def test_view_works_with_htmx_header(self, client, admin_user, journal_issue, site_settings_configured):
        """Test view works correctly with HTMX request header."""
        client.force_login(admin_user)

        article = ArticleFactory(
            issue=journal_issue,
            title="HTMX Test Article",
            doi_suffix="htmx.001",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            given_name="Jane",
            surname="Doe",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
        )

        # Simulate HTMX request
        response = client.get(
            f"/dashboard/crossref/issues/{journal_issue.pk}/validate/",
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        assert "text/html" in response["Content-Type"]
        # Should still return the partial template
        assert "crossref/partials/_validation_panel.html" in [t.name for t in response.templates]
