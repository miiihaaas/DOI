"""
Tests for Crossref service layer.

Story 5.1: Crossref Service Infrastructure.
Tests for CrossrefService class and XML generation.
"""

import re
from datetime import date

import pytest

from doi_portal.articles.models import AuthorSequence
from doi_portal.articles.models import ContributorRole
from doi_portal.articles.tests.factories import AffiliationFactory
from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.articles.tests.factories import AuthorFactory
from doi_portal.core.models import SiteSettings
from doi_portal.crossref.services import CrossrefService
from doi_portal.crossref.services import format_date
from doi_portal.crossref.services import format_orcid_url
from doi_portal.crossref.services import xml_escape
from doi_portal.crossref.validators import validate_xml
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import BookFactory
from doi_portal.publications.tests.factories import ConferenceFactory
from doi_portal.publications.tests.factories import JournalFactory
from doi_portal.publications.tests.factories import PublisherFactory


@pytest.fixture
def site_settings(db):
    """Create SiteSettings with test depositor data."""
    return SiteSettings.objects.create(
        depositor_name="Test Depositor",
        depositor_email="test@example.com",
    )


@pytest.fixture
def publisher(db):
    """Create test publisher with DOI prefix."""
    return PublisherFactory(
        name="Test Publisher",
        doi_prefix="10.12345",
    )


@pytest.fixture
def journal_publication(publisher):
    """Create test journal publication."""
    return JournalFactory(
        title="Test Journal",
        publisher=publisher,
        issn_print="1234-5678",
        issn_online="2345-6789",
        language="sr",
    )


@pytest.fixture
def conference_publication(publisher):
    """Create test conference publication."""
    return ConferenceFactory(
        title="Test Conference Proceedings",
        publisher=publisher,
        conference_name="International Test Conference",
        conference_acronym="ITC",
        conference_location="Belgrade, Serbia",
        conference_date=date(2026, 5, 15),
        conference_date_end=date(2026, 5, 17),
        conference_number=5,
    )


@pytest.fixture
def book_publication(publisher):
    """Create test book publication."""
    return BookFactory(
        title="Test Monograph",
        publisher=publisher,
        isbn_print="978-86-7549-100-1",
        edition="1. izdanje",
    )


@pytest.fixture
def journal_issue(journal_publication):
    """Create test journal issue."""
    return IssueFactory(
        publication=journal_publication,
        volume="10",
        issue_number="2",
        year=2026,
        publication_date=date(2026, 3, 15),
    )


@pytest.fixture
def conference_issue(conference_publication):
    """Create test conference issue."""
    return IssueFactory(
        publication=conference_publication,
        volume="",
        issue_number="",
        year=2026,
        publication_date=date(2026, 5, 17),
        proceedings_title="Proceedings of ITC 2026",
        proceedings_publisher_name="Test Publisher",
        proceedings_publisher_place="Belgrade",
    )


@pytest.fixture
def book_issue(book_publication):
    """Create test book issue (represents the book itself)."""
    return IssueFactory(
        publication=book_publication,
        volume="",
        issue_number="",
        year=2026,
        publication_date=date(2026, 1, 1),
    )


@pytest.fixture
def article_with_authors(journal_issue, site_settings):
    """Create article with authors and affiliations."""
    article = ArticleFactory(
        issue=journal_issue,
        title="Test Article Title",
        subtitle="A Comprehensive Study",
        abstract="This is a test abstract.",
        doi_suffix="test.2026.001",
        first_page="1",
        last_page="15",
        language="sr",
    )
    # Create first author with ORCID and affiliation
    author1 = AuthorFactory(
        article=article,
        given_name="John",
        surname="Doe",
        orcid="0000-0001-2345-6789",
        orcid_authenticated=True,
        sequence=AuthorSequence.FIRST,
        contributor_role=ContributorRole.AUTHOR,
        order=1,
    )
    AffiliationFactory(
        author=author1,
        institution_name="Test University",
        institution_ror_id="https://ror.org/12345678",
        department="Department of Science",
        order=1,
    )
    # Create second author
    AuthorFactory(
        article=article,
        given_name="Jane",
        surname="Smith",
        sequence=AuthorSequence.ADDITIONAL,
        contributor_role=ContributorRole.AUTHOR,
        order=2,
    )
    return article


class TestXmlEscape:
    """Tests for xml_escape filter."""

    def test_escape_ampersand(self):
        """Test ampersand escaping."""
        assert xml_escape("Test & Value") == "Test &amp; Value"

    def test_escape_less_than(self):
        """Test less-than escaping."""
        assert xml_escape("a < b") == "a &lt; b"

    def test_escape_greater_than(self):
        """Test greater-than escaping."""
        assert xml_escape("a > b") == "a &gt; b"

    def test_escape_quotes(self):
        """Test quote escaping."""
        assert xml_escape('Test "quoted"') == "Test &quot;quoted&quot;"
        assert xml_escape("Test 'quoted'") == "Test &apos;quoted&apos;"

    def test_escape_none(self):
        """Test None value handling."""
        assert xml_escape(None) == ""

    def test_escape_multiple_characters(self):
        """Test escaping multiple special characters."""
        assert xml_escape("A & B < C > D") == "A &amp; B &lt; C &gt; D"


class TestFormatDate:
    """Tests for format_date filter."""

    def test_format_default(self):
        """Test default date format."""
        d = date(2026, 3, 15)
        assert format_date(d) == "20260315"

    def test_format_custom(self):
        """Test custom date format."""
        d = date(2026, 3, 15)
        assert format_date(d, "%Y-%m-%d") == "2026-03-15"

    def test_format_month(self):
        """Test month extraction."""
        d = date(2026, 3, 15)
        assert format_date(d, "%m") == "03"

    def test_format_none(self):
        """Test None value handling."""
        assert format_date(None) == ""


class TestFormatOrcidUrl:
    """Tests for format_orcid_url filter."""

    def test_format_orcid(self):
        """Test ORCID URL formatting."""
        expected = "https://orcid.org/0000-0001-2345-6789"
        assert format_orcid_url("0000-0001-2345-6789") == expected

    def test_format_orcid_with_url_prefix(self):
        """Test ORCID already with URL prefix."""
        orcid_url = "https://orcid.org/0000-0001-2345-6789"
        assert format_orcid_url(orcid_url) == orcid_url

    def test_format_orcid_empty(self):
        """Test empty ORCID handling."""
        assert format_orcid_url("") == ""
        assert format_orcid_url(None) == ""


class TestCrossrefServiceInitialization:
    """Tests for CrossrefService initialization."""

    def test_service_initialization(self):
        """Test CrossrefService can be initialized."""
        service = CrossrefService()
        assert service.env is not None

    def test_jinja2_environment_has_custom_filters(self):
        """Test Jinja2 environment has custom filters registered."""
        service = CrossrefService()
        assert "xml_escape" in service.env.filters
        assert "format_date" in service.env.filters
        assert "format_orcid_url" in service.env.filters

    def test_template_map_exists(self):
        """Test template map has all publication types."""
        service = CrossrefService()
        assert "JOURNAL" in service.TEMPLATE_MAP
        assert "CONFERENCE" in service.TEMPLATE_MAP
        assert "BOOK" in service.TEMPLATE_MAP


class TestGenerateDoiBatchId:
    """Tests for generate_doi_batch_id method."""

    def test_batch_id_format(self):
        """Test DOI batch ID format."""
        service = CrossrefService()
        batch_id = service.generate_doi_batch_id()
        # Format: UUID_TIMESTAMP (8 hex chars + underscore + 14 digit timestamp)
        pattern = r"^[a-f0-9]{8}_\d{14}$"
        assert re.match(pattern, batch_id) is not None

    def test_batch_id_uniqueness(self):
        """Test DOI batch IDs are unique."""
        service = CrossrefService()
        batch_ids = [service.generate_doi_batch_id() for _ in range(10)]
        assert len(set(batch_ids)) == 10


@pytest.mark.django_db
class TestGenerateHead:
    """Tests for generate_head method."""

    def test_generate_head_with_settings(self, journal_issue, site_settings):
        """Test head generation uses SiteSettings."""
        service = CrossrefService()
        head = service.generate_head(journal_issue)

        assert head["depositor_name"] == "Test Depositor"
        assert head["depositor_email"] == "test@example.com"
        assert head["registrant"] == journal_issue.publication.publisher.name
        assert "doi_batch_id" in head
        assert "timestamp" in head

    def test_generate_head_timestamp_format(self, journal_issue, site_settings):
        """Test timestamp is in YYYYMMDDHHmmss format."""
        service = CrossrefService()
        head = service.generate_head(journal_issue)

        # Timestamp should be 14 digits
        assert len(head["timestamp"]) == 14
        assert head["timestamp"].isdigit()

    def test_generate_head_default_depositor(self, journal_issue, db):
        """Test head generation with empty SiteSettings uses defaults."""
        # Create settings with empty depositor info
        SiteSettings.objects.create(depositor_name="", depositor_email="")
        service = CrossrefService()
        head = service.generate_head(journal_issue)

        assert head["depositor_name"] == "DOI Portal"
        assert head["depositor_email"] == "admin@example.com"


class TestGetRequiredFields:
    """Tests for get_required_fields method."""

    def test_journal_required_fields(self):
        """Test required fields for JOURNAL type."""
        service = CrossrefService()
        fields = service.get_required_fields("JOURNAL")

        assert "publication" in fields
        assert "issue" in fields
        assert "article" in fields
        assert "author" in fields
        assert "title" in fields["publication"]
        assert "doi_suffix" in fields["article"]
        assert "sequence" in fields["author"]
        assert "contributor_role" in fields["author"]

    def test_conference_required_fields(self):
        """Test required fields for CONFERENCE type."""
        service = CrossrefService()
        fields = service.get_required_fields("CONFERENCE")

        assert "conference_name" in fields["publication"]

    def test_unknown_type_defaults_to_journal(self):
        """Test unknown type returns JOURNAL fields."""
        service = CrossrefService()
        fields = service.get_required_fields("UNKNOWN")

        assert fields == service.REQUIRED_FIELDS["JOURNAL"]


class TestGetTemplateName:
    """Tests for _get_template_name method."""

    def test_journal_template(self):
        """Test JOURNAL uses journal_article template."""
        service = CrossrefService()
        template_name = service._get_template_name("JOURNAL")
        assert template_name == "journal_article.xml.j2"

    def test_conference_template(self):
        """Test CONFERENCE uses conference_paper template."""
        service = CrossrefService()
        template_name = service._get_template_name("CONFERENCE")
        assert template_name == "conference_paper.xml.j2"

    def test_book_template(self):
        """Test BOOK uses book_chapter template."""
        service = CrossrefService()
        template_name = service._get_template_name("BOOK")
        assert template_name == "book_chapter.xml.j2"

    def test_other_defaults_to_journal(self):
        """Test OTHER type uses journal template."""
        service = CrossrefService()
        template_name = service._get_template_name("OTHER")
        assert template_name == "journal_article.xml.j2"


@pytest.mark.django_db
class TestGenerateXmlJournal:
    """Tests for generate_xml with JOURNAL publication type."""

    def test_generate_xml_returns_string(self, article_with_authors, site_settings):
        """Test generate_xml returns a string."""
        service = CrossrefService()
        xml = service.generate_xml(article_with_authors.issue)
        assert isinstance(xml, str)

    def test_generate_xml_has_xml_declaration(
        self, article_with_authors, site_settings,
    ):
        """Test XML has proper declaration."""
        service = CrossrefService()
        xml = service.generate_xml(article_with_authors.issue)
        assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')

    def test_generate_xml_has_crossref_namespace(
        self, article_with_authors, site_settings,
    ):
        """Test XML has Crossref namespace."""
        service = CrossrefService()
        xml = service.generate_xml(article_with_authors.issue)
        assert 'xmlns="http://www.crossref.org/schema/5.4.0"' in xml

    def test_generate_xml_has_head_section(self, article_with_authors, site_settings):
        """Test XML contains head section with required elements."""
        service = CrossrefService()
        xml = service.generate_xml(article_with_authors.issue)

        assert "<head>" in xml
        assert "<doi_batch_id>" in xml
        assert "<timestamp>" in xml
        assert "<depositor>" in xml
        assert "<depositor_name>Test Depositor</depositor_name>" in xml
        assert "<email_address>test@example.com</email_address>" in xml
        assert "<registrant>" in xml

    def test_generate_xml_has_journal_structure(
        self, article_with_authors, site_settings,
    ):
        """Test XML has journal structure."""
        service = CrossrefService()
        xml = service.generate_xml(article_with_authors.issue)

        assert "<journal>" in xml
        assert "<journal_metadata" in xml
        assert "<journal_issue>" in xml
        assert "<journal_article" in xml

    def test_generate_xml_has_issn(self, article_with_authors, site_settings):
        """Test XML contains ISSN."""
        service = CrossrefService()
        xml = service.generate_xml(article_with_authors.issue)

        assert '<issn media_type="print">' in xml

    def test_generate_xml_has_article_title(self, article_with_authors, site_settings):
        """Test XML contains article title."""
        service = CrossrefService()
        xml = service.generate_xml(article_with_authors.issue)

        assert "<title>Test Article Title</title>" in xml
        assert "<subtitle>A Comprehensive Study</subtitle>" in xml

    def test_generate_xml_has_contributors(self, article_with_authors, site_settings):
        """Test XML contains contributors with required attributes."""
        service = CrossrefService()
        xml = service.generate_xml(article_with_authors.issue)

        assert "<contributors>" in xml
        assert 'sequence="first"' in xml
        assert 'contributor_role="author"' in xml
        assert "<given_name>John</given_name>" in xml
        assert "<surname>Doe</surname>" in xml

    def test_generate_xml_has_orcid(self, article_with_authors, site_settings):
        """Test XML contains ORCID with authenticated attribute."""
        service = CrossrefService()
        xml = service.generate_xml(article_with_authors.issue)

        expected_orcid = (
            '<ORCID authenticated="true">'
            "https://orcid.org/0000-0001-2345-6789</ORCID>"
        )
        assert expected_orcid in xml

    def test_generate_xml_has_affiliations(self, article_with_authors, site_settings):
        """Test XML contains affiliations with ROR ID."""
        service = CrossrefService()
        xml = service.generate_xml(article_with_authors.issue)

        assert "<affiliations>" in xml
        assert "<institution_name>Test University</institution_name>" in xml
        expected_ror = '<institution_id type="ror">https://ror.org/12345678</institution_id>'
        assert expected_ror in xml

    def test_generate_xml_has_doi_data(self, article_with_authors, site_settings):
        """Test XML contains DOI data."""
        service = CrossrefService()
        xml = service.generate_xml(article_with_authors.issue)

        assert "<doi_data>" in xml
        assert "<doi>10.12345/test.2026.001</doi>" in xml
        assert "<resource>https://doi.org/10.12345/test.2026.001</resource>" in xml

    def test_generate_xml_has_pages(self, article_with_authors, site_settings):
        """Test XML contains page information."""
        service = CrossrefService()
        xml = service.generate_xml(article_with_authors.issue)

        assert "<pages>" in xml
        assert "<first_page>1</first_page>" in xml
        assert "<last_page>15</last_page>" in xml


@pytest.mark.django_db
class TestGenerateXmlConference:
    """Tests for generate_xml with CONFERENCE publication type."""

    def test_generate_xml_conference_structure(self, conference_issue, site_settings):
        """Test XML has conference structure."""
        # Create an article for the conference
        ArticleFactory(
            issue=conference_issue,
            title="Conference Paper Title",
            doi_suffix="conf.2026.001",
        )
        service = CrossrefService()
        xml = service.generate_xml(conference_issue)

        assert "<conference>" in xml
        assert "<event_metadata>" in xml
        assert "<proceedings_metadata" in xml
        assert "<conference_paper" in xml

    def test_generate_xml_has_event_metadata(self, conference_issue, site_settings):
        """Test XML contains event metadata."""
        ArticleFactory(issue=conference_issue, title="Test", doi_suffix="test.001")
        service = CrossrefService()
        xml = service.generate_xml(conference_issue)

        assert "<conference_name>International Test Conference</conference_name>" in xml
        assert "<conference_acronym>ITC</conference_acronym>" in xml
        assert "<conference_number>5</conference_number>" in xml
        assert "<conference_location>Belgrade, Serbia</conference_location>" in xml

    def test_generate_xml_has_proceedings_metadata(
        self, conference_issue, site_settings,
    ):
        """Test XML contains proceedings metadata."""
        ArticleFactory(issue=conference_issue, title="Test", doi_suffix="test.001")
        service = CrossrefService()
        xml = service.generate_xml(conference_issue)

        assert "<proceedings_title>Proceedings of ITC 2026</proceedings_title>" in xml
        assert "<publisher_name>Test Publisher</publisher_name>" in xml
        assert "<publisher_place>Belgrade</publisher_place>" in xml


@pytest.mark.django_db
class TestGenerateXmlBook:
    """Tests for generate_xml with BOOK publication type."""

    def test_generate_xml_book_structure(self, book_issue, site_settings):
        """Test XML has book structure."""
        ArticleFactory(
            issue=book_issue,
            title="Book Chapter Title",
            doi_suffix="book.2026.001",
        )
        service = CrossrefService()
        xml = service.generate_xml(book_issue)

        assert '<book book_type="monograph">' in xml
        assert "<book_metadata" in xml
        assert "<content_item" in xml

    def test_generate_xml_has_isbn(self, book_issue, site_settings):
        """Test XML contains ISBN."""
        ArticleFactory(issue=book_issue, title="Test", doi_suffix="test.001")
        service = CrossrefService()
        xml = service.generate_xml(book_issue)

        assert '<isbn media_type="print">978-86-7549-100-1</isbn>' in xml

    def test_generate_xml_book_without_isbn(self, book_publication, site_settings):
        """Test XML has noisbn element when ISBN is missing."""
        book_publication.isbn_print = ""
        book_publication.isbn_online = ""
        book_publication.save()
        issue = IssueFactory(publication=book_publication, year=2026)
        ArticleFactory(issue=issue, title="Test", doi_suffix="test.001")

        service = CrossrefService()
        xml = service.generate_xml(issue)

        assert '<noisbn reason="monograph"/>' in xml


@pytest.mark.django_db
class TestValidateXml:
    """Tests for validate_xml stub."""

    def test_validate_xml_stub_returns_valid(self):
        """Test validate_xml stub returns (True, [])."""
        is_valid, errors = validate_xml("<test>xml</test>")
        assert is_valid is True
        assert errors == []

    def test_validate_xml_stub_with_any_input(self):
        """Test validate_xml accepts any input in stub mode."""
        is_valid, errors = validate_xml("invalid xml {}")
        assert is_valid is True
        assert errors == []


@pytest.mark.django_db
class TestXmlOutput:
    """Tests for XML output structure validation."""

    def test_xml_is_utf8_encoded(self, article_with_authors, site_settings):
        """Test XML contains proper UTF-8 declaration."""
        service = CrossrefService()
        xml = service.generate_xml(article_with_authors.issue)

        assert 'encoding="UTF-8"' in xml

    def test_xml_escapes_special_characters(self, journal_issue, site_settings):
        """Test special characters are properly escaped."""
        ArticleFactory(
            issue=journal_issue,
            title="Test & Experiment <Special>",
            doi_suffix="test.001",
        )
        service = CrossrefService()
        xml = service.generate_xml(journal_issue)

        assert "Test &amp; Experiment &lt;Special&gt;" in xml

    def test_xml_handles_empty_optional_fields(self, journal_issue, site_settings):
        """Test XML handles missing optional fields gracefully."""
        ArticleFactory(
            issue=journal_issue,
            title="Minimal Article",
            doi_suffix="test.001",
            subtitle="",
            abstract="",
            first_page="",
            last_page="",
        )
        service = CrossrefService()
        xml = service.generate_xml(journal_issue)

        # Should not contain empty optional elements
        assert "<subtitle></subtitle>" not in xml
        assert "<pages>" not in xml


@pytest.mark.django_db
class TestBuildContext:
    """Tests for _build_context method."""

    def test_build_context_contains_all_keys(self, article_with_authors, site_settings):
        """Test context contains all required keys."""
        service = CrossrefService()
        context = service._build_context(article_with_authors.issue)

        assert "head" in context
        assert "publisher" in context
        assert "publication" in context
        assert "issue" in context
        assert "articles" in context

    def test_build_context_articles_have_authors(
        self, article_with_authors, site_settings,
    ):
        """Test articles context includes authors."""
        service = CrossrefService()
        context = service._build_context(article_with_authors.issue)

        assert len(context["articles"]) == 1
        assert len(context["articles"][0]["authors"]) == 2

    def test_build_context_authors_have_affiliations(
        self, article_with_authors, site_settings,
    ):
        """Test author context includes affiliations."""
        service = CrossrefService()
        context = service._build_context(article_with_authors.issue)

        first_author = context["articles"][0]["authors"][0]
        assert len(first_author["affiliations"]) == 1
        assert first_author["affiliations"][0]["institution_name"] == "Test University"
