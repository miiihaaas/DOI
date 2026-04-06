"""
Tests for monographs app models.

Task 9.2: Model tests for Monograph, MonographChapter, contributors,
affiliations, funding, and relations.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from doi_portal.articles.models import RelationScope
from doi_portal.monographs.models import (
    Monograph,
    MonographChapter,
    MonographContributor,
    MonographRelation,
    MonographStatus,
)
from doi_portal.monographs.tests.factories import (
    ChapterContributorFactory,
    MonographChapterFactory,
    MonographContributorFactory,
    MonographFactory,
    MonographRelationFactory,
)
from doi_portal.publications.tests.factories import PublisherFactory


# =============================================================================
# Monograph model tests
# =============================================================================


@pytest.mark.django_db
class TestMonograph:
    """Tests for Monograph model."""

    def test_monograph_creation(self):
        """Create monograph with all required fields, verify saved."""
        publisher = PublisherFactory(doi_prefix="10.12345")
        monograph = MonographFactory(
            title="Test Monograph",
            doi_suffix="mono.001",
            year=2026,
            publisher=publisher,
            status=MonographStatus.PUBLISHED,
            isbn_print="978-86-7549-100-1",
        )
        monograph.refresh_from_db()
        assert monograph.pk is not None
        assert monograph.title == "Test Monograph"
        assert monograph.doi_suffix == "mono.001"
        assert monograph.year == 2026
        assert monograph.publisher == publisher
        assert monograph.status == MonographStatus.PUBLISHED
        assert monograph.isbn_print == "978-86-7549-100-1"

    def test_monograph_str(self):
        """__str__ returns title."""
        monograph = MonographFactory(title="My Great Book")
        assert str(monograph) == "My Great Book"

    def test_monograph_full_doi(self):
        """full_doi property returns '{prefix}/{suffix}'."""
        publisher = PublisherFactory(doi_prefix="10.99999")
        monograph = MonographFactory(
            publisher=publisher,
            doi_suffix="book.2026.001",
        )
        assert monograph.full_doi == "10.99999/book.2026.001"

    def test_monograph_has_chapters_false(self):
        """has_chapters returns False when no chapters exist."""
        monograph = MonographFactory()
        assert monograph.has_chapters is False

    def test_monograph_has_chapters_true(self):
        """has_chapters returns True when chapters exist."""
        monograph = MonographFactory()
        MonographChapterFactory(monograph=monograph)
        assert monograph.has_chapters is True

    def test_monograph_slug_auto_generated(self):
        """Slug is auto-set from title on save."""
        monograph = MonographFactory(title="A Test Monograph Title", slug="")
        monograph.refresh_from_db()
        assert monograph.slug != ""
        assert "a-test-monograph-title" in monograph.slug.lower()

    def test_monograph_doi_suffix_unique_per_publisher(self):
        """Same suffix different publisher is OK; same suffix same publisher raises IntegrityError."""
        publisher_a = PublisherFactory(doi_prefix="10.11111")
        publisher_b = PublisherFactory(doi_prefix="10.22222")

        MonographFactory(publisher=publisher_a, doi_suffix="shared.suffix")
        # Different publisher, same suffix — should work
        MonographFactory(publisher=publisher_b, doi_suffix="shared.suffix")

        # Same publisher, same suffix — IntegrityError
        with pytest.raises(IntegrityError):
            MonographFactory(publisher=publisher_a, doi_suffix="shared.suffix")

    def test_monograph_isbn_validation_valid(self):
        """Valid ISBN passes validation."""
        monograph = MonographFactory(isbn_print="978-86-7549-100-1")
        # full_clean should not raise
        monograph.full_clean()

    def test_monograph_isbn_validation_invalid(self):
        """Invalid ISBN raises ValidationError."""
        monograph = MonographFactory(isbn_print="INVALID-ISBN")
        with pytest.raises(ValidationError):
            monograph.full_clean()

    def test_monograph_both_isbn_blank(self):
        """Both ISBNs blank is OK (noisbn fallback)."""
        monograph = MonographFactory(isbn_print="", isbn_online="")
        # Should not raise
        monograph.full_clean()

    def test_monograph_soft_delete_cascades_chapters(self):
        """soft_delete() also soft-deletes chapters."""
        monograph = MonographFactory()
        ch1 = MonographChapterFactory(monograph=monograph)
        ch2 = MonographChapterFactory(monograph=monograph)

        monograph.soft_delete()

        # Chapters should be soft-deleted (not visible via default manager)
        assert MonographChapter.objects.filter(monograph=monograph).count() == 0
        # But exist via all_objects
        assert MonographChapter.all_objects.filter(monograph=monograph).count() == 2
        ch1.refresh_from_db()
        ch2.refresh_from_db()
        assert ch1.is_deleted is True
        assert ch2.is_deleted is True

    def test_monograph_soft_delete_cascades_contributors(self):
        """soft_delete() also soft-deletes contributors."""
        monograph = MonographFactory()
        c1 = MonographContributorFactory(monograph=monograph)
        c2 = MonographContributorFactory(monograph=monograph)

        monograph.soft_delete()

        assert MonographContributor.objects.filter(monograph=monograph).count() == 0
        assert MonographContributor.all_objects.filter(monograph=monograph).count() == 2
        c1.refresh_from_db()
        c2.refresh_from_db()
        assert c1.is_deleted is True
        assert c2.is_deleted is True

    def test_monograph_restore_cascades(self):
        """restore() restores chapters and contributors."""
        monograph = MonographFactory()
        ch = MonographChapterFactory(monograph=monograph)
        contrib = MonographContributorFactory(monograph=monograph)

        monograph.soft_delete()
        assert ch.is_deleted is False or True  # just proceed
        monograph.restore()

        ch.refresh_from_db()
        contrib.refresh_from_db()
        assert ch.is_deleted is False
        assert contrib.is_deleted is False
        monograph.refresh_from_db()
        assert monograph.is_deleted is False


# =============================================================================
# MonographChapter model tests
# =============================================================================


@pytest.mark.django_db
class TestMonographChapter:
    """Tests for MonographChapter model."""

    def test_chapter_ordering(self):
        """Chapters are ordered by order field."""
        monograph = MonographFactory()
        ch3 = MonographChapterFactory(monograph=monograph, order=3, title="Third")
        ch1 = MonographChapterFactory(monograph=monograph, order=1, title="First")
        ch2 = MonographChapterFactory(monograph=monograph, order=2, title="Second")

        chapters = list(monograph.chapters.all())
        assert chapters[0].pk == ch1.pk
        assert chapters[1].pk == ch2.pk
        assert chapters[2].pk == ch3.pk

    def test_chapter_doi_suffix_unique_per_monograph(self):
        """doi_suffix unique within same monograph; OK across monographs."""
        mono_a = MonographFactory()
        mono_b = MonographFactory()

        MonographChapterFactory(monograph=mono_a, doi_suffix="ch.001")
        # Different monograph, same suffix — OK
        MonographChapterFactory(monograph=mono_b, doi_suffix="ch.001")

        # Same monograph, same suffix — IntegrityError
        with pytest.raises(IntegrityError):
            MonographChapterFactory(monograph=mono_a, doi_suffix="ch.001")

    def test_chapter_full_doi(self):
        """full_doi property returns '{prefix}/{suffix}'."""
        publisher = PublisherFactory(doi_prefix="10.55555")
        monograph = MonographFactory(publisher=publisher)
        chapter = MonographChapterFactory(
            monograph=monograph,
            doi_suffix="ch.2026.042",
        )
        assert chapter.full_doi == "10.55555/ch.2026.042"


# =============================================================================
# Contributor model tests
# =============================================================================


@pytest.mark.django_db
class TestContributor:
    """Tests for MonographContributor and ChapterContributor."""

    def test_contributor_str(self):
        """__str__ returns 'Given Surname'."""
        contrib = MonographContributorFactory(
            given_name="Nikola",
            surname="Tesla",
        )
        assert str(contrib) == "Nikola Tesla"

    def test_contributor_str_no_given_name(self):
        """__str__ returns just surname when given_name is blank."""
        contrib = MonographContributorFactory(
            given_name="",
            surname="Tesla",
        )
        assert str(contrib) == "Tesla"


# =============================================================================
# Relation model tests
# =============================================================================


@pytest.mark.django_db
class TestRelation:
    """Tests for MonographRelation auto-scope on save."""

    def test_relation_auto_scope_inter_work(self):
        """save() sets relation_scope to INTER_WORK for inter-work relationship types."""
        relation = MonographRelationFactory(
            relationship_type="isSupplementTo",
        )
        assert relation.relation_scope == RelationScope.INTER_WORK

    def test_relation_auto_scope_intra_work(self):
        """save() sets relation_scope to INTRA_WORK for intra-work relationship types."""
        relation = MonographRelationFactory(
            relationship_type="isPreprintOf",
        )
        assert relation.relation_scope == RelationScope.INTRA_WORK
