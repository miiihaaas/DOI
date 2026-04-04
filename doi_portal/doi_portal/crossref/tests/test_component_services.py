"""
Service tests for component XML generation.

Tests CrossrefService and PreValidationService for sa_component support.
"""

import pytest

from doi_portal.components.tests.factories import (
    ComponentContributorFactory,
    ComponentFactory,
    ComponentGroupFactory,
)
from doi_portal.crossref.services import CrossrefService, PreValidationService


@pytest.mark.django_db
class TestCrossrefServiceComponentXML:
    """Tests for CrossrefService component XML generation."""

    def test_generate_component_xml_basic(self):
        """generate_component_xml produces valid XML structure."""
        cg = ComponentGroupFactory(parent_doi="10.12345/test.parent")
        ComponentFactory(
            component_group=cg,
            doi_suffix="comp.001",
            title="Audio Track 1",
            format_mime_type="audio/mpeg",
        )
        service = CrossrefService()
        xml = service.generate_component_xml(cg)

        assert '<?xml version="1.0" encoding="UTF-8"?>' in xml
        assert '<sa_component parent_doi="10.12345/test.parent">' in xml
        assert "<component_list>" in xml
        assert '<component parent_relation="isPartOf">' in xml
        assert "<title>Audio Track 1</title>" in xml
        assert '<format mime_type="audio/mpeg"/>' in xml
        assert "<doi>10.12345/comp.001</doi>" in xml

    def test_generate_component_xml_with_contributors(self):
        """XML includes contributor data."""
        cg = ComponentGroupFactory(parent_doi="10.12345/test.contrib")
        comp = ComponentFactory(component_group=cg, doi_suffix="comp.002")
        ComponentContributorFactory(
            component=comp,
            given_name="Petar",
            surname="Petrović",
            sequence="first",
            contributor_role="author",
        )
        service = CrossrefService()
        xml = service.generate_component_xml(cg)

        assert "<contributors>" in xml
        assert '<person_name sequence="first" contributor_role="author">' in xml
        assert "<given_name>Petar</given_name>" in xml
        assert "<surname>Petrović</surname>" in xml

    def test_generate_component_xml_with_orcid(self):
        """XML includes ORCID URL for contributors."""
        cg = ComponentGroupFactory()
        comp = ComponentFactory(component_group=cg, doi_suffix="comp.orcid")
        ComponentContributorFactory(
            component=comp,
            surname="Test",
            orcid="0000-0002-1825-0097",
        )
        service = CrossrefService()
        xml = service.generate_component_xml(cg)

        assert "<ORCID>https://orcid.org/0000-0002-1825-0097</ORCID>" in xml

    def test_generate_component_xml_with_description(self):
        """XML includes description element."""
        cg = ComponentGroupFactory()
        ComponentFactory(
            component_group=cg,
            doi_suffix="comp.desc",
            description="Audio zapis predavanja",
        )
        service = CrossrefService()
        xml = service.generate_component_xml(cg)

        assert "<description>Audio zapis predavanja</description>" in xml

    def test_generate_component_xml_without_title(self):
        """XML omits titles element when title is empty."""
        cg = ComponentGroupFactory()
        ComponentFactory(
            component_group=cg,
            doi_suffix="comp.notitle",
            title="",
        )
        service = CrossrefService()
        xml = service.generate_component_xml(cg)

        assert "<titles>" not in xml

    def test_generate_component_xml_auto_resource_url(self):
        """Auto-generates resource_url when not provided."""
        cg = ComponentGroupFactory()
        comp = ComponentFactory(
            component_group=cg,
            doi_suffix="comp.auto",
            resource_url="",
        )
        service = CrossrefService()
        xml = service.generate_component_xml(cg)

        assert f"/components/{comp.pk}/" in xml

    def test_generate_component_xml_explicit_resource_url(self):
        """Uses explicit resource_url when provided."""
        cg = ComponentGroupFactory()
        ComponentFactory(
            component_group=cg,
            doi_suffix="comp.explicit",
            resource_url="https://example.com/audio.mp3",
        )
        service = CrossrefService()
        xml = service.generate_component_xml(cg)

        assert "<resource>https://example.com/audio.mp3</resource>" in xml

    def test_generate_component_xml_with_publication_date(self):
        """XML includes publication_date with year, month, day."""
        cg = ComponentGroupFactory()
        ComponentFactory(
            component_group=cg,
            doi_suffix="comp.date",
            publication_year=2026,
            publication_month=3,
            publication_day=15,
        )
        service = CrossrefService()
        xml = service.generate_component_xml(cg)

        assert "<publication_date>" in xml
        assert "<month>03</month>" in xml
        assert "<day>15</day>" in xml
        assert "<year>2026</year>" in xml

    def test_generate_component_xml_partial_date_year_only(self):
        """XML includes only year when month/day are absent."""
        cg = ComponentGroupFactory()
        ComponentFactory(
            component_group=cg,
            doi_suffix="comp.yearonly",
            publication_year=2026,
            publication_month=None,
            publication_day=None,
        )
        service = CrossrefService()
        xml = service.generate_component_xml(cg)

        assert "<publication_date>" in xml
        assert "<year>2026</year>" in xml
        assert "<month>" not in xml
        assert "<day>" not in xml

    def test_generate_component_xml_partial_date_year_month(self):
        """XML includes year and month when day is absent (AC22)."""
        cg = ComponentGroupFactory()
        ComponentFactory(
            component_group=cg,
            doi_suffix="comp.yearmonth",
            publication_year=2026,
            publication_month=3,
            publication_day=None,
        )
        service = CrossrefService()
        xml = service.generate_component_xml(cg)

        assert "<month>03</month>" in xml
        assert "<year>2026</year>" in xml
        assert "<day>" not in xml

    def test_generate_component_xml_ampersand_escape(self):
        """Autoescape handles & in description (AC23)."""
        cg = ComponentGroupFactory()
        ComponentFactory(
            component_group=cg,
            doi_suffix="comp.amp",
            description="Audio & Video zapis",
        )
        service = CrossrefService()
        xml = service.generate_component_xml(cg)

        # Single escape, not double
        assert "&amp;" in xml
        assert "&amp;amp;" not in xml

    def test_generate_and_store_component_xml(self):
        """generate_and_store_component_xml stores XML and XSD results."""
        cg = ComponentGroupFactory()
        ComponentFactory(component_group=cg, doi_suffix="comp.store")
        service = CrossrefService()
        success, result = service.generate_and_store_component_xml(cg)

        cg.refresh_from_db()
        assert cg.crossref_xml != ""
        assert cg.xml_generated_at is not None
        assert cg.xml_generation_status == "completed"
        assert cg.xsd_validated_at is not None

    def test_generate_component_xml_excludes_deleted(self):
        """Deleted components are excluded from XML."""
        cg = ComponentGroupFactory()
        ComponentFactory(component_group=cg, doi_suffix="comp.active")
        deleted = ComponentFactory(component_group=cg, doi_suffix="comp.deleted")
        deleted.is_deleted = True
        deleted.save()

        service = CrossrefService()
        xml = service.generate_component_xml(cg)

        assert "comp.active" in xml
        assert "comp.deleted" not in xml

    def test_generate_component_xml_multiple_components(self):
        """XML contains all active components in order."""
        cg = ComponentGroupFactory()
        ComponentFactory(component_group=cg, doi_suffix="comp.a", order=2, title="Second")
        ComponentFactory(component_group=cg, doi_suffix="comp.b", order=1, title="First")

        service = CrossrefService()
        xml = service.generate_component_xml(cg)

        # Both should be in XML
        assert "comp.a" in xml
        assert "comp.b" in xml
        # First should come before Second (ordered by order field)
        first_pos = xml.index("First")
        second_pos = xml.index("Second")
        assert first_pos < second_pos


@pytest.mark.django_db
class TestPreValidationServiceComponent:
    """Tests for PreValidationService component validation."""

    def test_validate_valid_component_group(self):
        """Valid component group passes validation."""
        cg = ComponentGroupFactory(parent_doi="10.12345/valid")
        comp = ComponentFactory(component_group=cg, doi_suffix="comp.valid", title="Test")
        ComponentContributorFactory(component=comp, surname="Test")

        service = PreValidationService()
        result = service.validate_component_group(cg)

        # May have warnings but should not have errors (except depositor if not set)
        errors_without_depositor = [
            e for e in result.errors
            if "depositor" not in e.message.lower()
        ]
        assert len(errors_without_depositor) == 0

    def test_validate_empty_parent_doi(self):
        """Empty parent_doi produces error."""
        cg = ComponentGroupFactory(parent_doi="")
        ComponentFactory(component_group=cg)

        service = PreValidationService()
        result = service.validate_component_group(cg)

        error_messages = [e.message for e in result.errors]
        assert any("Parent DOI je obavezan" in m for m in error_messages)

    def test_validate_no_components(self):
        """No components produces error."""
        cg = ComponentGroupFactory()
        # No components created

        service = PreValidationService()
        result = service.validate_component_group(cg)

        error_messages = [e.message for e in result.errors]
        assert any("bar jednu komponentu" in m for m in error_messages)

    def test_validate_component_without_doi_suffix(self):
        """Component without doi_suffix produces error."""
        cg = ComponentGroupFactory()
        ComponentFactory(component_group=cg, doi_suffix="")

        service = PreValidationService()
        result = service.validate_component_group(cg)

        error_messages = [e.message for e in result.errors]
        assert any("DOI sufiks je obavezan" in m for m in error_messages)

    def test_validate_component_doi_suffix_with_slash(self):
        """Component with / in doi_suffix produces error."""
        cg = ComponentGroupFactory()
        ComponentFactory(component_group=cg, doi_suffix="comp/bad")

        service = PreValidationService()
        result = service.validate_component_group(cg)

        error_messages = [e.message for e in result.errors]
        assert any("ne sme sadržati '/'" in m for m in error_messages)

    def test_validate_component_without_title_warning(self):
        """Component without title produces warning."""
        cg = ComponentGroupFactory()
        ComponentFactory(component_group=cg, title="")

        service = PreValidationService()
        result = service.validate_component_group(cg)

        warning_messages = [w.message for w in result.warnings]
        assert any("naslov komponente" in m for m in warning_messages)

    def test_validate_invalid_mime_type_warning(self):
        """Invalid MIME type produces warning."""
        cg = ComponentGroupFactory()
        ComponentFactory(component_group=cg, format_mime_type="invalid")

        service = PreValidationService()
        result = service.validate_component_group(cg)

        warning_messages = [w.message for w in result.warnings]
        assert any("MIME tip" in m for m in warning_messages)

    def test_validate_parent_doi_not_found_warning(self):
        """Parent DOI not in system produces warning."""
        cg = ComponentGroupFactory(parent_doi="10.99999/nonexistent")
        ComponentFactory(component_group=cg)

        service = PreValidationService()
        result = service.validate_component_group(cg)

        warning_messages = [w.message for w in result.warnings]
        assert any("nije pronađen u sistemu" in m for m in warning_messages)

    def test_validate_no_contributors_warning(self):
        """Component without contributors produces warning."""
        cg = ComponentGroupFactory()
        ComponentFactory(component_group=cg)
        # No contributors

        service = PreValidationService()
        result = service.validate_component_group(cg)

        warning_messages = [w.message for w in result.warnings]
        assert any("nema kontributore" in m for m in warning_messages)

    def test_validate_contributor_without_surname(self):
        """Contributor without surname produces error."""
        cg = ComponentGroupFactory()
        comp = ComponentFactory(component_group=cg)
        ComponentContributorFactory(component=comp, surname="")

        service = PreValidationService()
        result = service.validate_component_group(cg)

        error_messages = [e.message for e in result.errors]
        assert any("nema prezime" in m for m in error_messages)

    def test_validate_contributor_without_role(self):
        """Contributor without contributor_role produces error."""
        cg = ComponentGroupFactory()
        comp = ComponentFactory(component_group=cg)
        ComponentContributorFactory(component=comp, contributor_role="")

        service = PreValidationService()
        result = service.validate_component_group(cg)

        error_messages = [e.message for e in result.errors]
        assert any("nema definisanu ulogu" in m for m in error_messages)

    def test_validate_parent_doi_format(self):
        """parent_doi not starting with 10. produces error."""
        cg = ComponentGroupFactory(parent_doi="invalid/doi")
        ComponentFactory(component_group=cg)

        service = PreValidationService()
        result = service.validate_component_group(cg)

        error_messages = [e.message for e in result.errors]
        assert any("mora početi sa '10.'" in m for m in error_messages)
