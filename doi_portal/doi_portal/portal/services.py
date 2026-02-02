"""
Portal service functions for DOI Portal.

Story 4.1: Portal Home Page.
Story 4.2: Article Search Functionality.
Provides portal-wide statistics, recent publications, and article search.
All business logic for portal data retrieval is centralized here.
"""

from __future__ import annotations

from django.db.models import Count, Q, QuerySet

from doi_portal.articles.models import Article, ArticleStatus, Author
from doi_portal.publications.models import Publication
from doi_portal.publishers.models import Publisher

__all__ = [
    "get_portal_statistics",
    "get_recent_publications",
    "search_articles",
]


def get_portal_statistics() -> dict[str, int]:
    """
    Get portal-wide statistics for home page.

    Uses aggregate() for single SQL query (same pattern as dashboard/services.py).

    Returns:
        Dict with total_publications, total_articles, published_articles_count,
        total_publishers.
    """
    article_counts = Article.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(status=ArticleStatus.PUBLISHED)),
    )
    return {
        "total_publications": Publication.objects.count(),
        "total_articles": article_counts["total"],
        "published_articles_count": article_counts["published"],
        "total_publishers": Publisher.objects.count(),
    }


def search_articles(query: str) -> QuerySet[Article]:
    """
    Search published articles by title, author names, keywords, and abstract.

    FR39: Posetilac moze pretrazivati clanke po nazivu, autoru i kljucnim recima.
    NFR5: Rezultati < 2 sekunde.

    Only PUBLISHED articles are searched.
    SoftDeleteManager already excludes is_deleted=True records.

    Args:
        query: Search term (minimum 3 characters expected, caller validates).

    Returns:
        QuerySet of matching Article objects with related data pre-fetched.
    """
    if not query or len(query.strip()) < 3:
        return Article.objects.none()

    q = query.strip()[:200]  # Cap query length to prevent oversized SQL

    # Find author IDs matching the search query
    matching_author_article_ids = (
        Author.objects.filter(
            Q(given_name__icontains=q) | Q(surname__icontains=q)
        )
        .values_list("article_id", flat=True)
        .distinct()
    )

    return (
        Article.objects.filter(
            Q(status=ArticleStatus.PUBLISHED),
            Q(title__icontains=q)
            | Q(abstract__icontains=q)
            | Q(keywords__icontains=q)
            | Q(id__in=matching_author_article_ids),
        )
        .select_related("issue__publication__publisher")
        .prefetch_related("authors")
        .order_by("-published_at", "-created_at")
        .distinct()
    )


def get_recent_publications(limit: int = 6) -> QuerySet[Publication]:
    """
    Get most recent active publications for home page.

    SoftDeleteManager already excludes is_deleted=True records.

    Args:
        limit: Maximum number of publications to return (default 6).

    Returns:
        QuerySet of Publication objects ordered by created_at descending.
    """
    return (
        Publication.objects.select_related("publisher")
        .order_by("-created_at")[:limit]
    )
