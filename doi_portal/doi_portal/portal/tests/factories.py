"""
Factory classes for Portal tests.

Story 2.2: Public Publisher Page
Story 2.5: Public Publication List with Filters
"""

import factory
from factory.django import DjangoModelFactory

from doi_portal.publications.models import AccessType
from doi_portal.publications.models import Publication
from doi_portal.publications.models import PublicationType
from doi_portal.publishers.models import Publisher


class PublisherFactory(DjangoModelFactory):
    """Factory for creating Publisher instances in tests."""

    name = factory.Sequence(lambda n: f"Izdavač {n}")
    doi_prefix = factory.Sequence(lambda n: f"10.{1000 + n}")
    description = factory.Faker("paragraph", nb_sentences=3)
    contact_email = factory.Faker("email")
    contact_phone = factory.LazyAttribute(lambda _: "+381 11 123 4567")
    website = factory.Faker("url")

    class Meta:
        model = Publisher
        django_get_or_create = ("doi_prefix",)


class PublicationFactory(DjangoModelFactory):
    """Factory for creating Publication instances in portal tests."""

    title = factory.Sequence(lambda n: f"Publikacija {n}")
    publisher = factory.SubFactory(PublisherFactory)
    publication_type = PublicationType.JOURNAL
    description = factory.Faker("paragraph")
    language = "sr"
    subject_area = ""
    access_type = AccessType.OPEN

    class Meta:
        model = Publication
