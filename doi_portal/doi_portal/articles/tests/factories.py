"""
Test factories for articles app.

Story 3.1: Article model factories for testing.
"""

import factory
from factory.django import DjangoModelFactory

from doi_portal.articles.models import Article, ArticleContentType, ArticleStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.users.tests.factories import UserFactory

__all__ = [
    "ArticleFactory",
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
