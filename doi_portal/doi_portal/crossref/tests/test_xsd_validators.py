"""
Tests for XSD validation.

Story 5.4: XSD Validation.
Tests for XSDValidationResult, XSDValidationError, and validate_xml function.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from lxml import etree

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.models import AuthorSequence
from doi_portal.articles.models import ContributorRole
from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.articles.tests.factories import AuthorFactory
from doi_portal.core.models import SiteSettings
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import JournalFactory
from doi_portal.publications.tests.factories import PublisherFactory


# =============================================================================
# Task 3: Tests for XSDValidationResult and XSDValidationError dataclasses
# =============================================================================


class TestXSDValidationError:
    """Tests for XSDValidationError dataclass."""

    def test_create_basic_error(self):
        """Test creating a basic XSD validation error."""
        from doi_portal.crossref.validators import XSDValidationError

        error = XSDValidationError(
            message="Element 'title' is required",
        )
        assert error.message == "Element 'title' is required"
        assert error.line is None
        assert error.column is None
        assert error.element is None

    def test_create_error_with_line_info(self):
        """Test creating error with line and column info."""
        from doi_portal.crossref.validators import XSDValidationError

        error = XSDValidationError(
            message="Invalid element",
            line=15,
            column=42,
            element="journal_metadata",
        )
        assert error.line == 15
        assert error.column == 42
        assert error.element == "journal_metadata"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        from doi_portal.crossref.validators import XSDValidationError

        error = XSDValidationError(
            message="Test error",
            line=10,
            column=5,
            element="test_element",
        )
        result = error.to_dict()

        assert result == {
            "message": "Test error",
            "line": 10,
            "column": 5,
            "element": "test_element",
        }

    def test_to_dict_with_none_values(self):
        """Test to_dict with None values."""
        from doi_portal.crossref.validators import XSDValidationError

        error = XSDValidationError(message="Error only")
        result = error.to_dict()

        assert result == {
            "message": "Error only",
            "line": None,
            "column": None,
            "element": None,
        }


class TestXSDValidationResult:
    """Tests for XSDValidationResult dataclass."""

    def test_valid_result(self):
        """Test creating a valid result."""
        from doi_portal.crossref.validators import XSDValidationResult

        result = XSDValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.validated_at is None

    def test_invalid_result_with_errors(self):
        """Test creating invalid result with errors."""
        from doi_portal.crossref.validators import XSDValidationError
        from doi_portal.crossref.validators import XSDValidationResult

        errors = [
            XSDValidationError(message="Error 1", line=10),
            XSDValidationError(message="Error 2", line=20),
        ]
        result = XSDValidationResult(is_valid=False, errors=errors)

        assert result.is_valid is False
        assert len(result.errors) == 2

    def test_to_dict(self):
        """Test conversion to dictionary."""
        from django.utils import timezone

        from doi_portal.crossref.validators import XSDValidationError
        from doi_portal.crossref.validators import XSDValidationResult

        now = timezone.now()
        result = XSDValidationResult(
            is_valid=False,
            errors=[XSDValidationError(message="Test", line=5)],
            validated_at=now,
        )
        data = result.to_dict()

        assert data["is_valid"] is False
        assert len(data["errors"]) == 1
        assert data["errors"][0]["message"] == "Test"
        assert data["validated_at"] == now.isoformat()

    def test_to_dict_without_timestamp(self):
        """Test to_dict when validated_at is None."""
        from doi_portal.crossref.validators import XSDValidationResult

        result = XSDValidationResult(is_valid=True)
        data = result.to_dict()

        assert data["validated_at"] is None


# =============================================================================
# Task 2: Tests for XSD validation service
# =============================================================================


class TestSchemaLoading:
    """Tests for XSD schema loading."""

    def test_schema_files_exist(self):
        """Test that required schema files are present."""
        schema_dir = Path(__file__).parent.parent / "schemas"
        assert (schema_dir / "crossref5.4.0.xsd").exists()
        assert (schema_dir / "common5.4.0.xsd").exists()

    def test_get_schema_returns_xmlschema(self):
        """Test that _get_schema returns a compiled XMLSchema."""
        from doi_portal.crossref.validators import _get_schema

        schema = _get_schema()
        assert isinstance(schema, etree.XMLSchema)

    def test_schema_cached_between_calls(self):
        """Test that schema is cached and reused."""
        from doi_portal.crossref import validators

        # Clear cache first
        validators._SCHEMA_CACHE = None

        schema1 = validators._get_schema()
        schema2 = validators._get_schema()

        # Should be the exact same object (cached)
        assert schema1 is schema2

    def test_schema_not_found_raises_runtime_error(self):
        """Test that missing schema raises RuntimeError."""
        from doi_portal.crossref import validators

        # Clear cache
        validators._SCHEMA_CACHE = None

        # Mock the schema path to a non-existent file
        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(RuntimeError, match="schema not found"):
                validators._get_schema()

        # Restore cache state for other tests
        validators._SCHEMA_CACHE = None


class TestXSDValidation:
    """Tests for validate_xml function."""

    def test_valid_minimal_journal_xml(self):
        """Test validation of valid minimal journal XML."""
        from doi_portal.crossref.validators import validate_xml

        # Minimal valid Crossref journal XML
        valid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<doi_batch version="5.4.0" xmlns="http://www.crossref.org/schema/5.4.0">
    <head>
        <doi_batch_id>test_batch_001</doi_batch_id>
        <timestamp>20260203120000</timestamp>
        <depositor>
            <depositor_name>Test Depositor</depositor_name>
            <email_address>test@example.com</email_address>
        </depositor>
        <registrant>Test Publisher</registrant>
    </head>
    <body>
        <journal>
            <journal_metadata language="en">
                <full_title>Test Journal</full_title>
                <issn media_type="print">1234-5678</issn>
            </journal_metadata>
            <journal_issue>
                <publication_date media_type="print">
                    <year>2026</year>
                </publication_date>
                <journal_volume>
                    <volume>10</volume>
                </journal_volume>
                <issue>1</issue>
            </journal_issue>
            <journal_article publication_type="full_text">
                <titles>
                    <title>Test Article Title</title>
                </titles>
                <contributors>
                    <person_name sequence="first" contributor_role="author">
                        <given_name>John</given_name>
                        <surname>Doe</surname>
                    </person_name>
                </contributors>
                <publication_date media_type="print">
                    <year>2026</year>
                </publication_date>
                <doi_data>
                    <doi>10.12345/test.2026.001</doi>
                    <resource>https://example.com/article</resource>
                </doi_data>
            </journal_article>
        </journal>
    </body>
</doi_batch>"""

        result = validate_xml(valid_xml)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.validated_at is not None

    def test_malformed_xml_returns_syntax_error(self):
        """Test that malformed XML returns syntax error."""
        from doi_portal.crossref.validators import validate_xml

        malformed_xml = """<?xml version="1.0"?>
<doi_batch>
    <head>
        <unclosed_tag>
    </head>
</doi_batch>"""

        result = validate_xml(malformed_xml)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "sintaksna" in result.errors[0].message.lower() or "syntax" in result.errors[0].message.lower()

    def test_missing_required_element_fails(self):
        """Test XML missing required elements fails validation."""
        from doi_portal.crossref.validators import validate_xml

        # Missing head element
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<doi_batch version="5.4.0" xmlns="http://www.crossref.org/schema/5.4.0">
    <body>
        <journal>
            <journal_metadata language="en">
                <full_title>Test</full_title>
            </journal_metadata>
        </journal>
    </body>
</doi_batch>"""

        result = validate_xml(invalid_xml)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_error_includes_line_number(self):
        """Test that validation errors include line numbers."""
        from doi_portal.crossref.validators import validate_xml

        # XML with error on specific line
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<doi_batch version="5.4.0" xmlns="http://www.crossref.org/schema/5.4.0">
    <invalid_element>Test</invalid_element>
</doi_batch>"""

        result = validate_xml(invalid_xml)
        assert result.is_valid is False
        assert len(result.errors) > 0
        # Check that at least one error has a line number
        has_line_number = any(e.line is not None for e in result.errors)
        assert has_line_number

    def test_empty_xml_string(self):
        """Test validation of empty XML string."""
        from doi_portal.crossref.validators import validate_xml

        result = validate_xml("")
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "prazan" in result.errors[0].message.lower()

    def test_whitespace_only_xml_string(self):
        """Test validation of whitespace-only XML string."""
        from doi_portal.crossref.validators import validate_xml

        result = validate_xml("   \n\t  ")
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "prazan" in result.errors[0].message.lower()

    def test_validation_sets_timestamp(self):
        """Test that validation sets the validated_at timestamp."""
        from django.utils import timezone

        from doi_portal.crossref.validators import validate_xml

        before = timezone.now()
        result = validate_xml("<invalid/>")
        after = timezone.now()

        assert result.validated_at is not None
        assert before <= result.validated_at <= after


# =============================================================================
# Task 4: Tests for integration with generation workflow
# =============================================================================


@pytest.fixture
def site_settings(db):
    """Create SiteSettings with depositor data."""
    return SiteSettings.objects.create(
        depositor_name="Test Depositor",
        depositor_email="depositor@test.com",
    )


@pytest.fixture
def publisher(db):
    """Create test publisher."""
    return PublisherFactory(
        name="Test Publisher",
        doi_prefix="10.12345",
    )


@pytest.fixture
def journal(publisher):
    """Create journal publication."""
    return JournalFactory(
        title="Test Journal",
        publisher=publisher,
        issn_print="1234-5678",
    )


@pytest.fixture
def issue_with_article(journal, site_settings):
    """Create issue with a valid article."""
    issue = IssueFactory(
        publication=journal,
        volume="10",
        issue_number="1",
        year=2026,
        publication_date=date(2026, 1, 15),
    )
    article = ArticleFactory(
        issue=issue,
        title="Test Article",
        doi_suffix="test.2026.001",
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
    return issue


@pytest.mark.django_db
class TestXSDIntegration:
    """Tests for XSD validation integration with generation workflow."""

    def test_generation_runs_xsd_validation(self, issue_with_article):
        """Test that XML generation automatically runs XSD validation."""
        from doi_portal.crossref.services import CrossrefService

        service = CrossrefService()
        success, result = service.generate_and_store_xml(issue_with_article)

        # Refresh from database
        issue_with_article.refresh_from_db()

        # XSD validation should have been run
        assert issue_with_article.xsd_validated_at is not None

    def test_valid_xml_sets_xsd_valid_true(self, issue_with_article):
        """Test that valid XML sets Issue.xsd_valid to True."""
        from doi_portal.crossref.services import CrossrefService

        service = CrossrefService()
        success, result = service.generate_and_store_xml(issue_with_article)

        issue_with_article.refresh_from_db()
        assert success is True
        assert issue_with_article.xsd_valid is True

    def test_xsd_errors_stored_in_json_field(self, issue_with_article):
        """Test that XSD errors are stored in Issue.xsd_errors JSONField."""
        from doi_portal.crossref.services import CrossrefService

        # Generate valid XML first
        service = CrossrefService()
        service.generate_and_store_xml(issue_with_article)

        issue_with_article.refresh_from_db()
        # For valid XML, errors should be empty list
        assert issue_with_article.xsd_errors == []

    def test_xsd_validated_at_timestamp_set(self, issue_with_article):
        """Test that XSD validation timestamp is recorded."""
        from django.utils import timezone

        from doi_portal.crossref.services import CrossrefService

        before = timezone.now()
        service = CrossrefService()
        service.generate_and_store_xml(issue_with_article)
        after = timezone.now()

        issue_with_article.refresh_from_db()
        assert issue_with_article.xsd_validated_at is not None
        assert before <= issue_with_article.xsd_validated_at <= after

    def test_invalid_xml_sets_xsd_valid_false(self, issue_with_article):
        """Test that invalid XML sets Issue.xsd_valid to False."""
        from unittest.mock import patch

        from django.utils import timezone

        from doi_portal.crossref.services import CrossrefService
        from doi_portal.crossref.validators import XSDValidationError
        from doi_portal.crossref.validators import XSDValidationResult

        # Mock validate_xml to return invalid result
        mock_result = XSDValidationResult(
            is_valid=False,
            errors=[XSDValidationError(message="Test error", line=10)],
            validated_at=timezone.now(),
        )

        with patch("doi_portal.crossref.validators.validate_xml", return_value=mock_result):
            service = CrossrefService()
            service.generate_and_store_xml(issue_with_article)

        issue_with_article.refresh_from_db()
        assert issue_with_article.xsd_valid is False
        assert len(issue_with_article.xsd_errors) > 0


# =============================================================================
# Task 5 & 6: Tests for UI templates
# =============================================================================


@pytest.fixture
def admin_user(db):
    """Create admin user."""
    from doi_portal.users.tests.factories import UserFactory

    return UserFactory(is_superuser=True, is_staff=True)


@pytest.mark.django_db
class TestXSDValidationResultTemplate:
    """Tests for XSD validation result UI template."""

    def test_valid_state_shows_green_checkmark(self, client, admin_user, issue_with_article):
        """Test valid state shows green checkmark and success message."""
        from django.template import Context
        from django.template import Template
        from django.utils import timezone

        template = Template(
            '{% include "crossref/partials/_xsd_validation_result.html" %}'
        )
        context = Context({
            "xsd_valid": True,
            "xsd_validated_at": timezone.now(),  # Must be datetime, not date
            "xsd_errors": [],
        })
        rendered = template.render(context)

        # Verify valid state display (AC2)
        assert "alert-success" in rendered
        assert "XML je validan" in rendered
        assert "bi-check-circle-fill" in rendered

    def test_invalid_state_shows_error_list(self):
        """Test invalid state shows error list with line numbers."""
        from django.template import Context
        from django.template import Template

        template = Template(
            '{% include "crossref/partials/_xsd_validation_result.html" %}'
        )
        context = Context({
            "xsd_valid": False,
            "xsd_validated_at": None,
            "xsd_errors": [
                {"message": "Test error message", "line": 15, "column": 5},
                {"message": "Another error", "line": None},
            ],
        })
        rendered = template.render(context)

        # Verify error display
        assert "Nevažeći XML" in rendered
        assert "ne može se poslati na Crossref" in rendered
        assert "Linija 15:" in rendered
        assert "Test error message" in rendered
        assert "Another error" in rendered

    def test_validating_state_shows_spinner(self):
        """Test validating state shows spinner with Serbian text."""
        from django.template import Context
        from django.template import Template

        template = Template(
            '{% include "crossref/partials/_xsd_validation_result.html" %}'
        )
        context = Context({
            "xsd_validating": True,
            "xsd_valid": None,
            "xsd_errors": [],
        })
        rendered = template.render(context)

        # Verify spinner and Serbian text (AC5)
        assert "spinner-border" in rendered
        assert "Validacija prema Crossref shemi..." in rendered
