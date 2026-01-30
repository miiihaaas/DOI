"""
Test factories for issues app.

Story 2.6: Issue model factories for testing.
"""

import factory
from factory.django import DjangoModelFactory

from doi_portal.issues.models import Issue, IssueStatus
from doi_portal.publications.tests.factories import (
    ConferenceFactory,
    PublicationFactory,
    PublisherFactory,
)

__all__ = [
    "IssueFactory",
    "PublicationFactory",
    "PublisherFactory",
    "ConferenceFactory",
]


class IssueFactory(DjangoModelFactory):
    """Factory for Issue model."""

    class Meta:
        model = Issue

    publication = factory.SubFactory(PublicationFactory)
    volume = factory.Sequence(lambda n: str(n + 1))
    issue_number = factory.Sequence(lambda n: str(n + 1))
    year = 2026
    status = IssueStatus.DRAFT
