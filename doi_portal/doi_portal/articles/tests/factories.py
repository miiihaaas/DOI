"""
Test factories for articles app.

Story 3.1: Article model factories for testing.
Story 3.2: Author and Affiliation model factories for testing.
"""

import factory
from factory.django import DjangoModelFactory

from doi_portal.articles.models import (
    Affiliation,
    Article,
    ArticleContentType,
    ArticleStatus,
    Author,
    AuthorSequence,
    ContributorRole,
)
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.users.tests.factories import UserFactory

__all__ = [
    "AffiliationFactory",
    "ArticleFactory",
    "AuthorFactory",
]


class ArticleFactory(DjangoModelFactory):
    """Factory for Article model."""

    class Meta:
        model = Article

    title = factory.Faker("sentence", nb_words=6)
    abstract = factory.Faker("paragraph")
    doi_suffix = factory.Sequence(lambda n: f"article.2026.{n:03d}")
    status = ArticleStatus.DRAFT
    issue = factory.SubFactory(IssueFactory)
    created_by = factory.SubFactory(UserFactory)
    language = "sr"
    publication_type = ArticleContentType.FULL_TEXT


class AuthorFactory(DjangoModelFactory):
    """Factory for Author model."""

    class Meta:
        model = Author

    given_name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    article = factory.SubFactory(ArticleFactory)
    contributor_role = ContributorRole.AUTHOR
    sequence = AuthorSequence.ADDITIONAL
    order = factory.Sequence(lambda n: n + 1)


class AffiliationFactory(DjangoModelFactory):
    """Factory for Affiliation model."""

    class Meta:
        model = Affiliation

    institution_name = factory.Faker("company")
    author = factory.SubFactory(AuthorFactory)
    order = factory.Sequence(lambda n: n + 1)
