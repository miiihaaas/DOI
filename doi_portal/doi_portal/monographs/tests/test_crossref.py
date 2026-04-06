"""
Tests for monograph Crossref XML generation and pre-validation.

Task 9.3: Crossref XML generation tests and pre-validation tests
for monographs.
"""

import pytest
from lxml import etree

from doi_portal.articles.models import AuthorSequence, ContributorRole
from doi_portal.core.models import SiteSettings
from doi_portal.crossref.services import CrossrefService, PreValidationService
from doi_portal.monographs.models import MonographStatus
from doi_portal.monographs.tests.factories import (
    ChapterContributorFactory,
    ChapterFundingFactory,
    MonographAffiliationFactory,
    MonographChapterFactory,
    MonographContributorFactory,
    MonographFactory,
)
from doi_portal.publications.tests.factories import PublisherFactory


# =============================================================================
# Shared fixtures
# =============================================================================

NS = {
    "cr": "http://www.crossref.org/schema/5.4.0",
    "jats": "http://www.ncbi.nlm.nih.gov/JATS1",
    "ai": "http://www.crossref.org/AccessIndicators.xsd",
    "fr": "http://www.crossref.org/fundref.xsd",
    "rel": "http://www.crossref.org/relations.xsd",
}


@pytest.fixture
def site_settings_configured(db):
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
def service():
    """CrossrefService instance."""
    return CrossrefService()


@pytest.fixture
def pre_validation_service():
    """PreValidationService instance."""
    return PreValidationService()


def _parse_xml(xml_str):
    """Parse XML string and return lxml root element."""
    return etree.fromstring(xml_str.encode("utf-8"))


def _generate_xml(service, monograph):
    """Generate XML for a monograph and return parsed root."""
    xml_str = service.generate_monograph_xml(monograph)
    return _parse_xml(xml_str), xml_str


# =============================================================================
# XML generation tests
# =============================================================================


@pytest.mark.django_db
class TestMonographXmlGeneration:
    """Tests for Crossref XML generation of monographs."""

    def test_xml_generation_monograph_no_chapters(
        self, site_settings_configured, publisher, service,
    ):
        """Monograph without chapters generates valid XML."""
        monograph = MonographFactory(
            title="Monograph Without Chapters",
            doi_suffix="mono.001",
            year=2026,
            publisher=publisher,
            status=MonographStatus.PUBLISHED,
            isbn_print="978-86-7549-100-1",
        )
        MonographContributorFactory(
            monograph=monograph,
            given_name="Marko",
            surname="Petrovic",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
            order=1,
        )

        root, xml_str = _generate_xml(service, monograph)

        # Basic structure checks
        assert root.tag == "{http://www.crossref.org/schema/5.4.0}doi_batch"
        books = root.findall(".//cr:book", NS)
        assert len(books) == 1
        assert books[0].get("book_type") == "monograph"

        # No content_items (no chapters)
        content_items = root.findall(".//cr:content_item", NS)
        assert len(content_items) == 0

        # DOI present
        dois = root.findall(".//cr:book_metadata/cr:doi_data/cr:doi", NS)
        assert len(dois) == 1
        assert dois[0].text == "10.12345/mono.001"

        # Title present
        titles = root.findall(".//cr:book_metadata/cr:titles/cr:title", NS)
        assert len(titles) == 1
        assert "Monograph Without Chapters" in titles[0].text

    def test_xml_generation_monograph_with_chapters(
        self, site_settings_configured, publisher, service,
    ):
        """Monograph with PUBLISHED chapters generates valid XML with content_items."""
        monograph = MonographFactory(
            title="Monograph With Chapters",
            doi_suffix="mono.002",
            year=2026,
            publisher=publisher,
            status=MonographStatus.PUBLISHED,
            isbn_print="978-86-7549-200-8",
        )
        MonographContributorFactory(
            monograph=monograph,
            given_name="Ana",
            surname="Jovanovic",
            sequence=AuthorSequence.FIRST,
            order=1,
        )
        ch1 = MonographChapterFactory(
            monograph=monograph,
            title="Chapter One",
            doi_suffix="ch.001",
            order=1,
            status=MonographStatus.PUBLISHED,
        )
        ChapterContributorFactory(
            chapter=ch1,
            given_name="Ivan",
            surname="Nikolic",
            sequence=AuthorSequence.FIRST,
            order=1,
        )
        ch2 = MonographChapterFactory(
            monograph=monograph,
            title="Chapter Two",
            doi_suffix="ch.002",
            order=2,
            status=MonographStatus.PUBLISHED,
        )
        ChapterContributorFactory(
            chapter=ch2,
            given_name="Jelena",
            surname="Stankovic",
            sequence=AuthorSequence.FIRST,
            order=1,
        )

        root, xml_str = _generate_xml(service, monograph)

        content_items = root.findall(".//cr:content_item", NS)
        assert len(content_items) == 2
        assert content_items[0].get("component_type") == "chapter"

        # Chapter DOIs
        ch_dois = [
            ci.find("cr:doi_data/cr:doi", NS).text
            for ci in content_items
        ]
        assert "10.12345/ch.001" in ch_dois
        assert "10.12345/ch.002" in ch_dois

    def test_xml_draft_chapters_excluded(
        self, site_settings_configured, publisher, service,
    ):
        """DRAFT chapters are NOT in generated XML."""
        monograph = MonographFactory(
            title="Mixed Chapters",
            doi_suffix="mono.003",
            year=2026,
            publisher=publisher,
            isbn_print="978-86-7549-300-5",
        )
        MonographContributorFactory(monograph=monograph, order=1)

        # Published chapter
        pub_ch = MonographChapterFactory(
            monograph=monograph,
            title="Published Chapter",
            doi_suffix="ch.pub.001",
            status=MonographStatus.PUBLISHED,
        )
        ChapterContributorFactory(chapter=pub_ch, order=1)

        # Draft chapter — should be excluded
        MonographChapterFactory(
            monograph=monograph,
            title="Draft Chapter",
            doi_suffix="ch.draft.001",
            status=MonographStatus.DRAFT,
        )

        root, xml_str = _generate_xml(service, monograph)

        content_items = root.findall(".//cr:content_item", NS)
        assert len(content_items) == 1

        ch_doi = content_items[0].find("cr:doi_data/cr:doi", NS).text
        assert ch_doi == "10.12345/ch.pub.001"
        assert "Draft Chapter" not in xml_str

    def test_xml_noisbn_fallback(
        self, site_settings_configured, publisher, service,
    ):
        """Monograph without ISBN generates <noisbn reason='monograph'/>."""
        monograph = MonographFactory(
            title="No ISBN Book",
            doi_suffix="mono.noisbn",
            year=2026,
            publisher=publisher,
            isbn_print="",
            isbn_online="",
        )
        MonographContributorFactory(monograph=monograph, order=1)

        root, xml_str = _generate_xml(service, monograph)

        noisbn = root.findall(".//cr:book_metadata/cr:noisbn", NS)
        assert len(noisbn) == 1
        assert noisbn[0].get("reason") == "monograph"

        # No isbn elements
        isbns = root.findall(".//cr:book_metadata/cr:isbn", NS)
        assert len(isbns) == 0

    def test_xml_isbn_both_types(
        self, site_settings_configured, publisher, service,
    ):
        """Both ISBN types rendered with correct media_type."""
        monograph = MonographFactory(
            title="Dual ISBN Book",
            doi_suffix="mono.dualisbns",
            year=2026,
            publisher=publisher,
            isbn_print="978-86-7549-400-2",
            isbn_online="978-86-7549-401-9",
        )
        MonographContributorFactory(monograph=monograph, order=1)

        root, xml_str = _generate_xml(service, monograph)

        isbns = root.findall(".//cr:book_metadata/cr:isbn", NS)
        assert len(isbns) == 2

        isbn_map = {isbn.get("media_type"): isbn.text for isbn in isbns}
        assert isbn_map["print"] == "978-86-7549-400-2"
        assert isbn_map["electronic"] == "978-86-7549-401-9"

        # No noisbn
        noisbn = root.findall(".//cr:book_metadata/cr:noisbn", NS)
        assert len(noisbn) == 0

    def test_xml_contributors_with_orcid(
        self, site_settings_configured, publisher, service,
    ):
        """ORCID and affiliations are rendered in XML."""
        monograph = MonographFactory(
            title="ORCID Test Book",
            doi_suffix="mono.orcid",
            year=2026,
            publisher=publisher,
            isbn_print="978-86-7549-500-9",
        )
        contrib = MonographContributorFactory(
            monograph=monograph,
            given_name="Nikola",
            surname="Tesla",
            orcid="0000-0002-1825-0097",
            orcid_authenticated=True,
            sequence=AuthorSequence.FIRST,
            order=1,
        )
        MonographAffiliationFactory(
            contributor=contrib,
            institution_name="University of Belgrade",
        )

        root, xml_str = _generate_xml(service, monograph)

        # ORCID element
        orcids = root.findall(".//cr:book_metadata/cr:contributors/cr:person_name/cr:ORCID", NS)
        assert len(orcids) == 1
        assert "0000-0002-1825-0097" in orcids[0].text
        assert orcids[0].get("authenticated") == "true"

        # Affiliation
        institutions = root.findall(
            ".//cr:book_metadata/cr:contributors/cr:person_name"
            "/cr:affiliations/cr:institution/cr:institution_name",
            NS,
        )
        assert len(institutions) == 1
        assert institutions[0].text == "University of Belgrade"

    def test_xml_chapter_funding_rendered(
        self, site_settings_configured, publisher, service,
    ):
        """fr:program in content_item for chapter funding."""
        monograph = MonographFactory(
            title="Funded Chapter Book",
            doi_suffix="mono.funding",
            year=2026,
            publisher=publisher,
            isbn_print="978-86-7549-600-6",
        )
        MonographContributorFactory(monograph=monograph, order=1)

        chapter = MonographChapterFactory(
            monograph=monograph,
            title="Funded Chapter",
            doi_suffix="ch.funded.001",
            status=MonographStatus.PUBLISHED,
        )
        ChapterContributorFactory(chapter=chapter, order=1)
        ChapterFundingFactory(
            chapter=chapter,
            funder_name="Serbian Science Fund",
            funder_doi="https://doi.org/10.13039/501100004564",
            award_number="GRANT-123",
        )

        root, xml_str = _generate_xml(service, monograph)

        # fr:program inside content_item
        content_items = root.findall(".//cr:content_item", NS)
        assert len(content_items) == 1

        fr_programs = content_items[0].findall("fr:program", NS)
        assert len(fr_programs) == 1

        funder_names = fr_programs[0].findall(
            ".//fr:assertion[@name='funder_name']", NS,
        )
        assert len(funder_names) == 1
        assert funder_names[0].text == "Serbian Science Fund"

        award_numbers = fr_programs[0].findall(
            ".//fr:assertion[@name='award_number']", NS,
        )
        assert len(award_numbers) == 1
        assert award_numbers[0].text == "GRANT-123"

    def test_xml_element_ordering(
        self, site_settings_configured, publisher, service,
    ):
        """Verify key elements are in correct XSD order in book_metadata."""
        monograph = MonographFactory(
            title="Order Test Book",
            doi_suffix="mono.order",
            year=2026,
            publisher=publisher,
            isbn_print="978-86-7549-700-3",
            edition_number="2",
            abstract="Test abstract",
            license_url="https://creativecommons.org/licenses/by/4.0/",
        )
        MonographContributorFactory(
            monograph=monograph,
            given_name="Test",
            surname="Author",
            sequence=AuthorSequence.FIRST,
            order=1,
        )

        root, xml_str = _generate_xml(service, monograph)

        book_metadata = root.find(".//cr:book_metadata", NS)
        children = [etree.QName(child).localname for child in book_metadata]

        # XSD order: contributors, titles, abstract, edition_number,
        # publication_date, isbn/noisbn, publisher, fr:program, ai:program,
        # rel:program, doi_data
        expected_order = [
            "contributors",
            "titles",
            "abstract",
            "edition_number",
            "publication_date",
            "isbn",
            "publisher",
            "program",  # ai:program (AccessIndicators)
            "doi_data",
        ]

        # Filter children to only expected elements (skip namespaced variants)
        # and check relative ordering
        filtered = [c for c in children if c in expected_order]
        # Each element in filtered should appear in expected_order order
        expected_indices = [expected_order.index(c) for c in filtered]
        assert expected_indices == sorted(expected_indices), (
            f"Elements not in XSD order: {filtered}"
        )


# =============================================================================
# Pre-validation tests
# =============================================================================


@pytest.mark.django_db
class TestMonographPreValidation:
    """Tests for PreValidationService.validate_monograph."""

    def test_pre_validation_missing_title(
        self, site_settings_configured, publisher, pre_validation_service,
    ):
        """Missing title produces an error."""
        monograph = MonographFactory(
            title="",
            doi_suffix="mono.val.001",
            year=2026,
            publisher=publisher,
        )

        result = pre_validation_service.validate_monograph(monograph)

        assert result.has_errors() is True
        error_messages = [e.message for e in result.errors]
        assert any("naslov" in msg.lower() for msg in error_messages)

    def test_pre_validation_missing_isbn_warning(
        self, site_settings_configured, publisher, pre_validation_service,
    ):
        """Missing ISBN produces a warning (not error)."""
        monograph = MonographFactory(
            title="Valid Title",
            doi_suffix="mono.val.002",
            year=2026,
            publisher=publisher,
            isbn_print="",
            isbn_online="",
        )

        result = pre_validation_service.validate_monograph(monograph)

        # Should have ISBN warning
        warning_messages = [w.message for w in result.warnings]
        assert any("isbn" in msg.lower() or "noisbn" in msg.lower() for msg in warning_messages)

        # ISBN issue should NOT be an error
        error_fields = [e.field_name for e in result.errors]
        assert "isbn" not in error_fields

    def test_pre_validation_chapter_missing_contributor(
        self, site_settings_configured, publisher, pre_validation_service,
    ):
        """Chapter without contributors produces an error."""
        monograph = MonographFactory(
            title="Valid Monograph",
            doi_suffix="mono.val.003",
            year=2026,
            publisher=publisher,
            isbn_print="978-86-7549-800-0",
        )
        # Add a PUBLISHED chapter with NO contributors
        MonographChapterFactory(
            monograph=monograph,
            title="Contributorless Chapter",
            doi_suffix="ch.val.001",
            status=MonographStatus.PUBLISHED,
        )

        result = pre_validation_service.validate_monograph(monograph)

        assert result.has_errors() is True
        error_messages = [e.message for e in result.errors]
        assert any("kontributor" in msg.lower() for msg in error_messages)

    def test_generate_and_store(
        self, site_settings_configured, publisher, service,
    ):
        """generate_and_store_monograph_xml generates and stores XML on model fields."""
        monograph = MonographFactory(
            title="Store Test Book",
            doi_suffix="mono.store.001",
            year=2026,
            publisher=publisher,
            isbn_print="978-86-7549-900-7",
        )
        MonographContributorFactory(
            monograph=monograph,
            given_name="Store",
            surname="Author",
            sequence=AuthorSequence.FIRST,
            order=1,
        )

        success, xml = service.generate_and_store_monograph_xml(monograph)

        assert success is True
        assert len(xml) > 0

        monograph.refresh_from_db()
        assert monograph.crossref_xml == xml
        assert monograph.xml_generated_at is not None
        assert monograph.xml_generation_status == "completed"
        assert monograph.xsd_validated_at is not None
