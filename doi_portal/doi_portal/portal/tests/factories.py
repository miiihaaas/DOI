"""
Factory classes for Portal tests.

Story 2.2: Public Publisher Page
"""

import factory
from factory.django import DjangoModelFactory

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
