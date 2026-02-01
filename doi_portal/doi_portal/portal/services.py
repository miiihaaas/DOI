"""
Portal service functions for DOI Portal.

Story 4.1: Portal Home Page.
Provides portal-wide statistics and recent publications for the home page.
All business logic for portal data retrieval is centralized here.
"""

from __future__ import annotations

from django.db.models import Count, Q, QuerySet

from doi_portal.articles.models import Article, ArticleStatus
from doi_portal.publications.models import Publication
from doi_portal.publishers.models import Publisher

__all__ = [
    "get_portal_statistics",
    "get_recent_publications",
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
