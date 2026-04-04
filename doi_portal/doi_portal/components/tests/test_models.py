"""
Model tests for components app.

Tests ComponentGroup, Component, ComponentContributor models.
"""

import pytest
from django.db import IntegrityError

from doi_portal.components.models import Component, ComponentContributor, ComponentGroup

from .factories import ComponentContributorFactory, ComponentFactory, ComponentGroupFactory


@pytest.mark.django_db
class TestComponentGroup:
    """Tests for ComponentGroup model."""

    def test_create_component_group(self):
        """ComponentGroup can be created with required fields."""
        cg = ComponentGroupFactory()
        assert cg.pk is not None
        assert cg.publisher is not None
        assert cg.parent_doi.startswith("10.")
        assert cg.created_at is not None
        assert cg.updated_at is not None

    def test_str_with_title(self):
        """__str__ returns title when set."""
        cg = ComponentGroupFactory(title="Audio komponente")
        assert str(cg) == "Audio komponente"

    def test_str_without_title(self):
        """__str__ returns parent_doi when title is empty."""
        cg = ComponentGroupFactory(title="")
        assert str(cg) == cg.parent_doi

    def test_component_count(self):
        """component_count returns number of non-deleted components."""
        cg = ComponentGroupFactory()
        ComponentFactory(component_group=cg)
        ComponentFactory(component_group=cg)
        assert cg.component_count == 2

    def test_component_count_excludes_deleted(self):
        """component_count excludes soft-deleted components."""
        cg = ComponentGroupFactory()
        ComponentFactory(component_group=cg)
        deleted = ComponentFactory(component_group=cg)
        deleted.is_deleted = True
        deleted.save()
        assert cg.component_count == 1

    def test_is_crossref_deposited(self):
        """is_crossref_deposited returns True when crossref_deposited_at is set."""
        cg = ComponentGroupFactory()
        assert cg.is_crossref_deposited is False

    def test_label_with_title(self):
        """label returns title when set."""
        cg = ComponentGroupFactory(title="Test")
        assert cg.label == "Test"

    def test_label_without_title(self):
        """label returns formatted parent_doi when title is empty."""
        cg = ComponentGroupFactory(title="", parent_doi="10.12345/test")
        assert cg.label == "Komponente za 10.12345/test"

    def test_unique_constraint_parent_doi_per_publisher(self):
        """Cannot create two ComponentGroups with same parent_doi for same publisher."""
        cg = ComponentGroupFactory(parent_doi="10.12345/unique")
        with pytest.raises(IntegrityError):
            ComponentGroupFactory(
                publisher=cg.publisher,
                parent_doi="10.12345/unique",
            )

    def test_unique_constraint_allows_different_publishers(self):
        """Two ComponentGroups with same parent_doi but different publishers are OK."""
        ComponentGroupFactory(parent_doi="10.12345/shared")
        cg2 = ComponentGroupFactory(parent_doi="10.12345/shared")
        assert cg2.pk is not None

    def test_soft_delete(self):
        """Soft-deleted ComponentGroup is excluded from default queryset."""
        cg = ComponentGroupFactory()
        pk = cg.pk
        cg.is_deleted = True
        cg.save()
        assert ComponentGroup.objects.filter(pk=pk).count() == 0
        assert ComponentGroup.all_objects.filter(pk=pk).count() == 1


@pytest.mark.django_db
class TestComponent:
    """Tests for Component model."""

    def test_create_component(self):
        """Component can be created with required fields."""
        c = ComponentFactory()
        assert c.pk is not None
        assert c.component_group is not None
        assert c.doi_suffix

    def test_str_with_title(self):
        """__str__ returns title when set."""
        c = ComponentFactory(title="Audio track")
        assert str(c) == "Audio track"

    def test_str_without_title(self):
        """__str__ returns doi_suffix when title is empty."""
        c = ComponentFactory(title="")
        assert str(c) == c.doi_suffix

    def test_full_doi(self):
        """full_doi returns publisher prefix / doi_suffix."""
        c = ComponentFactory(doi_suffix="component.audio.001")
        expected = f"{c.component_group.publisher.doi_prefix}/component.audio.001"
        assert c.full_doi == expected

    def test_unique_constraint_doi_suffix_per_group(self):
        """Cannot create two Components with same doi_suffix in same group."""
        c = ComponentFactory(doi_suffix="comp.unique")
        with pytest.raises(IntegrityError):
            ComponentFactory(
                component_group=c.component_group,
                doi_suffix="comp.unique",
            )

    def test_unique_constraint_allows_different_groups(self):
        """Two Components with same doi_suffix but different groups are OK."""
        ComponentFactory(doi_suffix="comp.shared")
        c2 = ComponentFactory(doi_suffix="comp.shared")
        assert c2.pk is not None

    def test_soft_delete(self):
        """Soft-deleted Component is excluded from default queryset."""
        c = ComponentFactory()
        pk = c.pk
        c.is_deleted = True
        c.save()
        assert Component.objects.filter(pk=pk).count() == 0
        assert Component.all_objects.filter(pk=pk).count() == 1

    def test_default_parent_relation(self):
        """Default parent_relation is isPartOf."""
        c = ComponentFactory()
        assert c.parent_relation == "isPartOf"


@pytest.mark.django_db
class TestComponentContributor:
    """Tests for ComponentContributor model."""

    def test_create_contributor(self):
        """ComponentContributor can be created."""
        ct = ComponentContributorFactory()
        assert ct.pk is not None
        assert ct.surname

    def test_str_with_given_name(self):
        """__str__ returns 'given_name surname'."""
        ct = ComponentContributorFactory(given_name="Petar", surname="Petrović")
        assert str(ct) == "Petar Petrović"

    def test_str_without_given_name(self):
        """__str__ returns just surname."""
        ct = ComponentContributorFactory(given_name="", surname="Petrović")
        assert str(ct) == "Petrović"

    def test_ordering(self):
        """Contributors are ordered by order field."""
        c = ComponentFactory()
        ct2 = ComponentContributorFactory(component=c, order=2)
        ct1 = ComponentContributorFactory(component=c, order=1)
        contributors = list(c.contributors.all())
        assert contributors[0].pk == ct1.pk
        assert contributors[1].pk == ct2.pk

    def test_soft_delete(self):
        """Soft-deleted contributor is excluded from default queryset."""
        ct = ComponentContributorFactory()
        pk = ct.pk
        ct.is_deleted = True
        ct.save()
        assert ComponentContributor.objects.filter(pk=pk).count() == 0
        assert ComponentContributor.all_objects.filter(pk=pk).count() == 1

    def test_orcid_validation(self):
        """ORCID field validates format."""
        from django.core.exceptions import ValidationError
        ct = ComponentContributorFactory.build(orcid="invalid")
        with pytest.raises(ValidationError):
            ct.full_clean()

    def test_valid_orcid(self):
        """Valid ORCID passes validation."""
        ct = ComponentContributorFactory.build(orcid="0000-0002-1825-0097")
        ct.full_clean()  # Should not raise
