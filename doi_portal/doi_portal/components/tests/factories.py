"""
Test factories for components app.

Crossref sa_component support: ComponentGroup, Component, ComponentContributor factories.
"""

import factory
from factory.django import DjangoModelFactory

from doi_portal.components.models import Component, ComponentContributor, ComponentGroup
from doi_portal.publications.tests.factories import PublisherFactory


class ComponentGroupFactory(DjangoModelFactory):
    """Factory for ComponentGroup model."""

    class Meta:
        model = ComponentGroup

    publisher = factory.SubFactory(PublisherFactory)
    parent_doi = factory.Sequence(lambda n: f"10.12345/test.{n}")
    title = factory.Faker("sentence")


class ComponentFactory(DjangoModelFactory):
    """Factory for Component model."""

    class Meta:
        model = Component

    component_group = factory.SubFactory(ComponentGroupFactory)
    doi_suffix = factory.Sequence(lambda n: f"comp.{n}")
    title = factory.Faker("sentence")
    format_mime_type = "audio/mpeg"


class ComponentContributorFactory(DjangoModelFactory):
    """Factory for ComponentContributor model."""

    class Meta:
        model = ComponentContributor

    component = factory.SubFactory(ComponentFactory)
    given_name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    sequence = "first"
    contributor_role = "author"
