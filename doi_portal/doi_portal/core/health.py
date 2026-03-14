"""
Health check service module for DOI Portal system health dashboard.

Story 6.6: Provides system health checks and content statistics
for the Superadmin health dashboard.
"""

from datetime import timedelta

from django.core.cache import cache
from django.db import connection
from django.utils import timezone

from auditlog.models import LogEntry


def get_system_health() -> dict:
    """Collect all health check data and content statistics."""
    return {
        "statistics": _get_content_statistics(),
        "integrations": {
            "database": _safe_check(_check_database),
            "redis": _safe_check(_check_redis),
            "celery": _safe_check(_check_celery),
            "storage": _safe_check(_check_storage),
        },
        "checked_at": timezone.now(),
    }


def _safe_check(check_func) -> dict:
    """Wrapper that catches all exceptions from health checks."""
    try:
        return check_func()
    except Exception as e:
        # Sanitize: only return exception class name and short message,
        # avoid leaking stack traces, file paths, or credentials
        error_type = type(e).__name__
        error_msg = str(e)
        # Truncate long messages to prevent information leakage
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        return {"status": "error", "message": f"{error_type}: {error_msg}"}


def _check_database() -> dict:
    """Check database connectivity using Django's connection.ensure_connection()."""
    connection.ensure_connection()
    return {"status": "ok", "message": "PostgreSQL konekcija aktivna"}


def _check_redis() -> dict:
    """Check Redis connectivity via Django cache backend."""
    cache.set("health_check", "1", 10)
    value = cache.get("health_check")
    if value == "1":
        return {"status": "ok", "message": "Redis konekcija aktivna"}
    return {"status": "error", "message": "Redis cache read/write neuspešan"}


def _check_celery() -> dict:
    """Check Celery worker availability via inspect ping."""
    from config.celery_app import app as celery_app

    inspector = celery_app.control.inspect(timeout=3.0)
    ping_result = inspector.ping()
    if ping_result:
        worker_count = len(ping_result)
        return {"status": "ok", "message": f"{worker_count} worker(a) aktivno"}
    return {"status": "error", "message": "Nema aktivnih Celery worker-a"}


def _check_storage() -> dict:
    """Check storage backend accessibility via default_storage.exists()."""
    from django.core.files.storage import default_storage

    default_storage.exists("health_check_test")
    return {"status": "ok", "message": "Skladište dostupno"}


def _get_content_statistics() -> dict:
    """Collect content statistics using Django ORM aggregates."""
    from django.db.models import Count, Q

    from doi_portal.articles.models import Article, ArticleStatus
    from doi_portal.issues.models import Issue
    from doi_portal.publications.models import Publication
    from doi_portal.publishers.models import Publisher
    from doi_portal.users.models import User

    # User counts - single query with conditional aggregation
    user_counts = User.objects.aggregate(
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )
    active_users = user_counts["active"]
    inactive_users = user_counts["inactive"]

    # Content counts
    publisher_count = Publisher.objects.count()
    publication_count = Publication.objects.count()
    issue_count = Issue.objects.count()

    # Article counts by status
    article_counts = Article.objects.aggregate(
        total=Count("id"),
        draft=Count("id", filter=Q(status=ArticleStatus.DRAFT)),
        review=Count("id", filter=Q(status=ArticleStatus.REVIEW)),
        ready=Count("id", filter=Q(status=ArticleStatus.READY)),
        published=Count("id", filter=Q(status=ArticleStatus.PUBLISHED)),
        withdrawn=Count("id", filter=Q(status=ArticleStatus.WITHDRAWN)),
    )

    # Recent audit activity (last 24h)
    since = timezone.now() - timedelta(hours=24)
    recent_audit_count = LogEntry.objects.filter(timestamp__gte=since).count()

    return {
        "active_users": active_users,
        "inactive_users": inactive_users,
        "publisher_count": publisher_count,
        "publication_count": publication_count,
        "issue_count": issue_count,
        "article_counts": article_counts,
        "recent_audit_count": recent_audit_count,
    }
