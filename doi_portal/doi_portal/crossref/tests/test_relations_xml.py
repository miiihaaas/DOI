"""
Tests for Crossref Relations XML generation and pre-validation.

Tests ArticleRelation XML rendering and PreValidationService relations checks.
"""

import pytest

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import (
    ArticleFactory,
    ArticleRelationFactory,
    AuthorFactory,
)
from doi_portal.core.models import SiteSettings
from doi_portal.crossref.services import CrossrefService, PreValidationService
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import JournalFactory, PublisherFactory


@pytest.fixture
def setup_site_settings(db):
    """Ensure SiteSettings exists with depositor data."""
    settings = SiteSettings.get_settings()
    settings.depositor_name = "Test Depositor"
    settings.depositor_email = "test@example.com"
    settings.save()
    return settings


@pytest.fixture
def setup_journal_article(db, setup_site_settings):
    """Create a complete journal article setup for XML generation."""
    from django.contrib.sites.models import Site

    site = Site.objects.get_current()
    site.domain = "test.doi.rs"
    site.save()

    publisher = PublisherFactory(doi_prefix="10.5555")
    journal = JournalFactory(publisher=publisher, issn_print="1234-5678")
    issue = IssueFactory(publication=journal, year=2026, volume="1")
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
        sequence="first",
        order=1,
    )
    return article


# =============================================================================
# XML Generation tests
# =============================================================================


@pytest.mark.django_db
class TestRelationsXmlGeneration:
    """Tests for rel:program XML element generation."""

    def test_no_relations_no_rel_program(self, setup_journal_article):
        """Given article with no relations, XML has no rel:program element."""
        article = setup_journal_article
        service = CrossrefService()
        xml = service.generate_xml(article.issue)
        assert "<rel:program" not in xml

    def test_intra_work_relation(self, setup_journal_article):
        """Given intra_work relation, XML has rel:intra_work_relation element."""
        article = setup_journal_article
        ArticleRelationFactory(
            article=article,
            relationship_type="isPreprintOf",
            identifier_type="doi",
            target_identifier="10.1234/preprint",
        )
        service = CrossrefService()
        xml = service.generate_xml(article.issue)
        assert '<rel:program name="relations">' in xml
        assert '<rel:intra_work_relation relationship-type="isPreprintOf" identifier-type="doi">10.1234/preprint</rel:intra_work_relation>' in xml

    def test_inter_work_relation(self, setup_journal_article):
        """Given inter_work relation, XML has rel:inter_work_relation element."""
        article = setup_journal_article
        ArticleRelationFactory(
            article=article,
            relationship_type="isSupplementTo",
            identifier_type="uri",
            target_identifier="https://example.com/supplement",
        )
        service = CrossrefService()
        xml = service.generate_xml(article.issue)
        assert '<rel:program name="relations">' in xml
        assert '<rel:inter_work_relation relationship-type="isSupplementTo" identifier-type="uri">https://example.com/supplement</rel:inter_work_relation>' in xml

    def test_relation_with_description(self, setup_journal_article):
        """Given relation with description, XML has rel:description element."""
        article = setup_journal_article
        ArticleRelationFactory(
            article=article,
            relationship_type="isPreprintOf",
            identifier_type="doi",
            target_identifier="10.1234/preprint",
            description="This is the preprint version",
        )
        service = CrossrefService()
        xml = service.generate_xml(article.issue)
        assert "<rel:description>This is the preprint version</rel:description>" in xml

    def test_relation_without_description(self, setup_journal_article):
        """Given relation without description, XML has no rel:description element."""
        article = setup_journal_article
        ArticleRelationFactory(
            article=article,
            relationship_type="isPreprintOf",
            identifier_type="doi",
            target_identifier="10.1234/preprint",
            description="",
        )
        service = CrossrefService()
        xml = service.generate_xml(article.issue)
        assert "<rel:description>" not in xml

    def test_mixed_relations(self, setup_journal_article):
        """Given both intra and inter relations, both appear in XML."""
        article = setup_journal_article
        ArticleRelationFactory(
            article=article,
            relationship_type="isPreprintOf",
            identifier_type="doi",
            target_identifier="10.1234/preprint",
            order=0,
        )
        ArticleRelationFactory(
            article=article,
            relationship_type="isSupplementTo",
            identifier_type="uri",
            target_identifier="https://example.com/supplement",
            order=1,
        )
        service = CrossrefService()
        xml = service.generate_xml(article.issue)
        assert "<rel:intra_work_relation" in xml
        assert "<rel:inter_work_relation" in xml

    def test_xmlns_rel_present(self, setup_journal_article):
        """XML has xmlns:rel namespace declaration."""
        article = setup_journal_article
        service = CrossrefService()
        xml = service.generate_xml(article.issue)
        assert 'xmlns:rel="http://www.crossref.org/relations.xsd"' in xml

    def test_rel_program_position_before_doi_data(self, setup_journal_article):
        """rel:program appears before doi_data in XML output."""
        article = setup_journal_article
        ArticleRelationFactory(
            article=article,
            relationship_type="isPreprintOf",
            identifier_type="doi",
            target_identifier="10.1234/preprint",
        )
        service = CrossrefService()
        xml = service.generate_xml(article.issue)
        rel_pos = xml.index("<rel:program")
        doi_data_pos = xml.index("<doi_data>", rel_pos)
        assert rel_pos < doi_data_pos


# =============================================================================
# PreValidation tests
# =============================================================================


@pytest.mark.django_db
class TestPreValidationServiceRelations:
    """Tests for PreValidationService relations validation."""

    def test_doi_format_warning(self, setup_journal_article):
        """WARNING when identifier_type='doi' but target doesn't start with '10.'."""
        article = setup_journal_article
        ArticleRelationFactory(
            article=article,
            relationship_type="isPreprintOf",
            identifier_type="doi",
            target_identifier="invalid-doi",
        )
        service = PreValidationService()
        result = service.validate_issue(article.issue)
        warnings = [w for w in result.warnings if "10." in w.message]
        assert len(warnings) >= 1

    def test_intra_work_non_doi_warning(self, setup_journal_article):
        """WARNING when intra_work relation uses non-DOI identifier."""
        article = setup_journal_article
        ArticleRelationFactory(
            article=article,
            relationship_type="isPreprintOf",
            identifier_type="uri",
            target_identifier="https://example.com/preprint",
        )
        service = PreValidationService()
        result = service.validate_issue(article.issue)
        warnings = [w for w in result.warnings if "non-DOI" in w.message]
        assert len(warnings) >= 1

    def test_empty_identifier_error(self, setup_journal_article):
        """ERROR when target_identifier is empty."""
        article = setup_journal_article
        # Create relation with empty target_identifier directly via ORM
        from doi_portal.articles.models import ArticleRelation, RelationScope

        ArticleRelation.objects.create(
            article=article,
            relationship_type="isPreprintOf",
            relation_scope=RelationScope.INTRA_WORK,
            identifier_type="doi",
            target_identifier="",
            order=0,
        )
        service = PreValidationService()
        result = service.validate_issue(article.issue)
        errors = [e for e in result.errors if "identifikator" in e.message.lower()]
        assert len(errors) >= 1

    def test_valid_relation_no_extra_errors(self, setup_journal_article):
        """Valid relation should not produce relation-specific errors/warnings."""
        article = setup_journal_article
        ArticleRelationFactory(
            article=article,
            relationship_type="isSupplementTo",
            identifier_type="doi",
            target_identifier="10.1234/test",
        )
        service = PreValidationService()
        result = service.validate_issue(article.issue)
        # Should have no errors related to relations
        relation_errors = [
            e for e in result.errors
            if "relacij" in e.message.lower() or "identifikator" in e.message.lower()
        ]
        assert len(relation_errors) == 0
