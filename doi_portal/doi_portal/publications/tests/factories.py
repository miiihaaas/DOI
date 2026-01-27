"""
Test factories for publications app.

Story 2.3: Publication model factories for testing.
"""

import factory
from factory.django import DjangoModelFactory

from doi_portal.publications.models import AccessType, Publication, PublicationType
from doi_portal.publishers.models import Publisher


class PublisherFactory(DjangoModelFactory):
    """Factory for Publisher model."""

    class Meta:
        model = Publisher

    name = factory.Sequence(lambda n: f"Izdavač {n}")
    doi_prefix = factory.Sequence(lambda n: f"10.{1000 + n}")
    description = factory.Faker("paragraph")
    contact_email = factory.Faker("email")
    website = factory.Faker("url")


class PublicationFactory(DjangoModelFactory):
    """Factory for Publication model."""

    class Meta:
        model = Publication

    title = factory.Sequence(lambda n: f"Publikacija {n}")
    publisher = factory.SubFactory(PublisherFactory)
    publication_type = PublicationType.JOURNAL
    description = factory.Faker("paragraph")
    language = "sr"
    access_type = AccessType.OPEN


class JournalFactory(PublicationFactory):
    """Factory for Journal publications."""

    publication_type = PublicationType.JOURNAL
    issn_print = factory.Sequence(lambda n: f"{1000 + n:04d}-{5000 + n:04d}"[:9])
    issn_online = factory.Sequence(lambda n: f"{2000 + n:04d}-{6000 + n:04d}"[:9])
    abbreviation = factory.Sequence(lambda n: f"J. Sci. {n}")
    frequency = "Kvartalno"


class ConferenceFactory(PublicationFactory):
    """Factory for Conference publications."""

    publication_type = PublicationType.CONFERENCE
    conference_name = factory.Sequence(lambda n: f"Naučna konferencija {n}")
    conference_acronym = factory.Sequence(lambda n: f"NK{n}")
    conference_location = "Beograd, Srbija"
    conference_date = factory.Faker("date_object")


class BookFactory(PublicationFactory):
    """Factory for Book/Monograph publications."""

    publication_type = PublicationType.BOOK
    isbn_print = factory.Sequence(lambda n: f"978-86-7549-{100 + n:03d}-{n % 10}")
    edition = "1. izdanje"
    series_title = factory.Sequence(lambda n: f"Naučna edicija {n}")
