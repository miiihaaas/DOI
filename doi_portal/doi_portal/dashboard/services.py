"""
Dashboard service functions for DOI Portal.

Story 3.8: Dashboard Statistics & Pending Items.
Provides role-based statistics and pending item queries for the dashboard.
All business logic for dashboard data retrieval is centralized here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Count, Q

from doi_portal.articles.models import Article, ArticleStatus
from doi_portal.publications.models import Publication

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from doi_portal.users.models import User

__all__ = [
    "get_admin_statistics",
    "get_bibliotekar_statistics",
    "get_dashboard_statistics",
    "get_my_draft_articles",
    "get_pending_review_articles",
    "get_ready_to_publish_articles",
    "get_urednik_statistics",
]


def get_dashboard_statistics(user: User, role_flags: dict) -> dict:
    """
    Dispatch to role-specific statistics function.

    Args:
        user: Current user
        role_flags: Dict with is_admin, is_urednik, is_bibliotekar keys

    Returns:
        Dict with statistics keys appropriate for user's role
    """
    if role_flags["is_admin"]:
        return get_admin_statistics()
    if role_flags["is_urednik"]:
        return get_urednik_statistics(user)
    if role_flags["is_bibliotekar"]:
        return get_bibliotekar_statistics(user)
    return {}


def get_admin_statistics() -> dict:
    """
    Statistics for Administrator/Superadmin - full system view.

    Uses aggregate() with Count + filter for a single SQL query (NFR3).

    Returns:
        Dict with total_publications, total_articles, pending_review_count,
        ready_to_publish_count, published_count, draft_count.
    """
    article_counts = Article.objects.aggregate(
        total=Count("id"),
        pending_review=Count("id", filter=Q(status=ArticleStatus.REVIEW)),
        ready_to_publish=Count("id", filter=Q(status=ArticleStatus.READY)),
        published=Count("id", filter=Q(status=ArticleStatus.PUBLISHED)),
        draft=Count("id", filter=Q(status=ArticleStatus.DRAFT)),
    )
    return {
        "total_publications": Publication.objects.count(),
        "total_articles": article_counts["total"],
        "pending_review_count": article_counts["pending_review"],
        "ready_to_publish_count": article_counts["ready_to_publish"],
        "published_count": article_counts["published"],
        "draft_count": article_counts["draft"],
    }


def get_urednik_statistics(user: User) -> dict:
    """
    Statistics for Urednik - scoped to assigned publisher.

    Args:
        user: Urednik user with publisher assignment

    Returns:
        Dict with total_articles, pending_review_count, ready_to_publish_count
        scoped to user's publisher.
    """
    publisher = user.publisher
    if not publisher:
        return {
            "total_articles": 0,
            "pending_review_count": 0,
            "ready_to_publish_count": 0,
        }

    publisher_filter = Q(issue__publication__publisher=publisher)
    article_counts = Article.objects.filter(publisher_filter).aggregate(
        total=Count("id"),
        pending_review=Count("id", filter=Q(status=ArticleStatus.REVIEW)),
        ready_to_publish=Count("id", filter=Q(status=ArticleStatus.READY)),
    )
    return {
        "total_articles": article_counts["total"],
        "pending_review_count": article_counts["pending_review"],
        "ready_to_publish_count": article_counts["ready_to_publish"],
    }


def get_bibliotekar_statistics(user: User) -> dict:
    """
    Statistics for Bibliotekar - only their own articles.

    Args:
        user: Bibliotekar user

    Returns:
        Dict with my_total_count, my_drafts_count, my_submitted_count.
    """
    my_articles = Article.objects.filter(created_by=user)
    article_counts = my_articles.aggregate(
        total=Count("id"),
        drafts=Count("id", filter=Q(status=ArticleStatus.DRAFT)),
        submitted=Count("id", filter=Q(status=ArticleStatus.REVIEW)),
    )
    return {
        "my_total_count": article_counts["total"],
        "my_drafts_count": article_counts["drafts"],
        "my_submitted_count": article_counts["submitted"],
    }


def get_pending_review_articles(
    user: User, role_flags: dict, limit: int = 10
) -> QuerySet:
    """
    Get articles pending editorial review.

    For Admin: all REVIEW articles.
    For Urednik: only REVIEW articles from assigned publisher.

    Args:
        user: Current user
        role_flags: Dict with is_admin key
        limit: Maximum number of articles to return (default 10)

    Returns:
        QuerySet of Article objects in REVIEW status.
    """
    qs = Article.objects.filter(
        status=ArticleStatus.REVIEW,
    ).select_related(
        "issue__publication",
        "submitted_by",
        "created_by",
    )

    if not role_flags["is_admin"] and hasattr(user, "publisher") and user.publisher:
        qs = qs.filter(issue__publication__publisher=user.publisher)

    return qs.order_by("-submitted_at")[:limit]


def get_ready_to_publish_articles(
    user: User, role_flags: dict, limit: int = 10
) -> QuerySet:
    """
    Get articles ready for publication (READY status).

    For Admin: all READY articles.
    For Urednik: only READY articles from assigned publisher.

    Args:
        user: Current user
        role_flags: Dict with is_admin key
        limit: Maximum number of articles to return (default 10)

    Returns:
        QuerySet of Article objects in READY status.
    """
    qs = Article.objects.filter(
        status=ArticleStatus.READY,
    ).select_related(
        "issue__publication",
        "reviewed_by",
    )

    if not role_flags["is_admin"] and hasattr(user, "publisher") and user.publisher:
        qs = qs.filter(issue__publication__publisher=user.publisher)

    return qs.order_by("-reviewed_at")[:limit]


def get_my_draft_articles(user: User, limit: int = 10) -> QuerySet:
    """
    Get user's own draft articles for Bibliotekar dashboard.

    Args:
        user: Current user
        limit: Maximum number of articles to return (default 10)

    Returns:
        QuerySet of user's DRAFT Article objects.
    """
    return (
        Article.objects.filter(
            created_by=user,
            status=ArticleStatus.DRAFT,
        )
        .select_related("issue__publication")
        .order_by("-updated_at")[:limit]
    )
