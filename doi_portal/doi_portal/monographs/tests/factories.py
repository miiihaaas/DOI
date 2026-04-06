"""
Test factories for monographs app.

Factories for Monograph, MonographChapter, contributors, affiliations,
funding, and relation models.
"""

import factory
from factory.django import DjangoModelFactory

from doi_portal.articles.models import AuthorSequence, ContributorRole
from doi_portal.monographs.models import (
    ChapterAffiliation,
    ChapterContributor,
    ChapterFunding,
    ChapterRelation,
    Monograph,
    MonographAffiliation,
    MonographChapter,
    MonographContributor,
    MonographFunding,
    MonographRelation,
    MonographStatus,
)
from doi_portal.publications.tests.factories import PublisherFactory
from doi_portal.users.tests.factories import UserFactory

__all__ = [
    "ChapterAffiliationFactory",
    "ChapterContributorFactory",
    "ChapterFundingFactory",
    "ChapterRelationFactory",
    "MonographAffiliationFactory",
    "MonographChapterFactory",
    "MonographContributorFactory",
    "MonographFactory",
    "MonographFundingFactory",
    "MonographRelationFactory",
]


class MonographFactory(DjangoModelFactory):
    """Factory for Monograph model."""

    class Meta:
        model = Monograph

    title = factory.Faker("sentence", nb_words=6)
    doi_suffix = factory.Sequence(lambda n: f"mono.2026.{n:03d}")
    year = 2026
    publisher = factory.SubFactory(PublisherFactory)
    status = MonographStatus.DRAFT
    created_by = factory.SubFactory(UserFactory)


class MonographChapterFactory(DjangoModelFactory):
    """Factory for MonographChapter model."""

    class Meta:
        model = MonographChapter

    monograph = factory.SubFactory(MonographFactory)
    title = factory.Faker("sentence", nb_words=6)
    doi_suffix = factory.Sequence(lambda n: f"ch.2026.{n:03d}")
    order = factory.Sequence(lambda n: n + 1)


class MonographContributorFactory(DjangoModelFactory):
    """Factory for MonographContributor model."""

    class Meta:
        model = MonographContributor

    monograph = factory.SubFactory(MonographFactory)
    given_name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    contributor_role = ContributorRole.AUTHOR
    sequence = AuthorSequence.ADDITIONAL
    order = factory.Sequence(lambda n: n + 1)


class MonographAffiliationFactory(DjangoModelFactory):
    """Factory for MonographAffiliation model."""

    class Meta:
        model = MonographAffiliation

    contributor = factory.SubFactory(MonographContributorFactory)
    institution_name = factory.Faker("company")


class ChapterContributorFactory(DjangoModelFactory):
    """Factory for ChapterContributor model."""

    class Meta:
        model = ChapterContributor

    chapter = factory.SubFactory(MonographChapterFactory)
    given_name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    contributor_role = ContributorRole.AUTHOR
    sequence = AuthorSequence.ADDITIONAL
    order = factory.Sequence(lambda n: n + 1)


class ChapterAffiliationFactory(DjangoModelFactory):
    """Factory for ChapterAffiliation model."""

    class Meta:
        model = ChapterAffiliation

    contributor = factory.SubFactory(ChapterContributorFactory)
    institution_name = factory.Faker("company")


class MonographFundingFactory(DjangoModelFactory):
    """Factory for MonographFunding model."""

    class Meta:
        model = MonographFunding

    monograph = factory.SubFactory(MonographFactory)
    funder_name = factory.Faker("company")


class MonographRelationFactory(DjangoModelFactory):
    """Factory for MonographRelation model."""

    class Meta:
        model = MonographRelation

    monograph = factory.SubFactory(MonographFactory)
    relationship_type = "isSupplementTo"
    identifier_type = "doi"
    target_identifier = factory.Sequence(lambda n: f"10.5555/target.{n}")
    order = factory.Sequence(lambda n: n)


class ChapterFundingFactory(DjangoModelFactory):
    """Factory for ChapterFunding model."""

    class Meta:
        model = ChapterFunding

    chapter = factory.SubFactory(MonographChapterFactory)
    funder_name = factory.Faker("company")


class ChapterRelationFactory(DjangoModelFactory):
    """Factory for ChapterRelation model."""

    class Meta:
        model = ChapterRelation

    chapter = factory.SubFactory(MonographChapterFactory)
    relationship_type = "isSupplementTo"
    identifier_type = "doi"
    target_identifier = factory.Sequence(lambda n: f"10.5555/ch-target.{n}")
    order = factory.Sequence(lambda n: n)
