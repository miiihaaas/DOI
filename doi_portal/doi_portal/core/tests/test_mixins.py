"""
Tests for SoftDeleteMixin and SoftDeleteManager in core/mixins.py.

Story 6.3: Soft Delete Implementation - Tasks 12, 13.
Tests mixin through real models (Publisher, Article, Author) as per anti-patterns.
"""

import pytest
from django.utils import timezone

from doi_portal.articles.models import Article, Author
from doi_portal.articles.tests.factories import ArticleFactory, AuthorFactory
from doi_portal.core.mixins import SoftDeleteManager, SoftDeleteMixin
from doi_portal.publications.tests.factories import PublisherFactory
from doi_portal.publishers.models import Publisher
from doi_portal.users.tests.factories import UserFactory


# ============================================================================
# Task 12: SoftDeleteMixin tests (AC: #1, #2)
# ============================================================================


@pytest.mark.django_db
class TestSoftDeleteMixinSoftDelete:
    """Test 12.1: soft_delete() sets is_deleted, deleted_at, deleted_by."""

    def test_soft_delete_sets_fields(self):
        user = UserFactory()
        publisher = PublisherFactory()

        publisher.soft_delete(user=user)
        publisher.refresh_from_db()

        assert publisher.is_deleted is True
        assert publisher.deleted_at is not None
        assert publisher.deleted_by == user

    def test_soft_delete_without_user(self):
        publisher = PublisherFactory()

        publisher.soft_delete()
        publisher.refresh_from_db()

        assert publisher.is_deleted is True
        assert publisher.deleted_at is not None
        assert publisher.deleted_by is None


@pytest.mark.django_db
class TestSoftDeleteMixinRestore:
    """Test 12.2: restore() resets is_deleted, deleted_at, deleted_by."""

    def test_restore_resets_fields(self):
        user = UserFactory()
        publisher = PublisherFactory()
        publisher.soft_delete(user=user)

        publisher.restore()
        publisher.refresh_from_db()

        assert publisher.is_deleted is False
        assert publisher.deleted_at is None
        assert publisher.deleted_by is None


@pytest.mark.django_db
class TestSoftDeleteManagerDefault:
    """Test 12.3: Default queryset excludes soft-deleted records."""

    def test_default_queryset_excludes_deleted(self):
        p1 = PublisherFactory()
        p2 = PublisherFactory()
        p2.soft_delete()

        qs = Publisher.objects.all()
        assert p1 in qs
        assert p2 not in qs


@pytest.mark.django_db
class TestSoftDeleteManagerAllWithDeleted:
    """Test 12.4: all_with_deleted() includes all records."""

    def test_all_with_deleted_includes_all(self):
        p1 = PublisherFactory()
        p2 = PublisherFactory()
        p2.soft_delete()

        qs = Publisher.objects.all_with_deleted()
        assert p1 in qs
        assert p2 in qs


@pytest.mark.django_db
class TestSoftDeleteManagerDeletedOnly:
    """Test 12.5: deleted_only() returns only deleted records."""

    def test_deleted_only_returns_deleted(self):
        p1 = PublisherFactory()
        p2 = PublisherFactory()
        p2.soft_delete()

        qs = Publisher.objects.deleted_only()
        assert p1 not in qs
        assert p2 in qs


# ============================================================================
# Task 13: Author soft delete tests (AC: #3)
# ============================================================================


@pytest.mark.django_db
class TestAuthorSoftDelete:
    """Test 13.1: Author soft_delete() works."""

    def test_author_soft_delete(self):
        user = UserFactory()
        author = AuthorFactory()

        author.soft_delete(user=user)
        author.refresh_from_db()

        assert author.is_deleted is True
        assert author.deleted_at is not None
        assert author.deleted_by == user


@pytest.mark.django_db
class TestAuthorRestore:
    """Test 13.2: Author restore() works."""

    def test_author_restore(self):
        user = UserFactory()
        author = AuthorFactory()
        author.soft_delete(user=user)

        author.restore()
        author.refresh_from_db()

        assert author.is_deleted is False
        assert author.deleted_at is None
        assert author.deleted_by is None


@pytest.mark.django_db
class TestAuthorDefaultQueryset:
    """Test 13.3: Deleted authors excluded from default queryset."""

    def test_deleted_authors_excluded(self):
        article = ArticleFactory()
        a1 = AuthorFactory(article=article)
        a2 = AuthorFactory(article=article)
        a2.soft_delete()

        # Default manager should exclude deleted
        assert a1 in Author.objects.all()
        assert a2 not in Author.objects.all()

        # all_objects should include all
        assert a1 in Author.all_objects.all()
        assert a2 in Author.all_objects.all()

    def test_article_authors_relation_excludes_deleted(self):
        """Related manager (article.authors.all()) should use default manager."""
        article = ArticleFactory()
        a1 = AuthorFactory(article=article)
        a2 = AuthorFactory(article=article)
        a2.soft_delete()

        # article.authors uses the default manager (SoftDeleteManager)
        authors = article.authors.all()
        assert a1 in authors
        assert a2 not in authors
