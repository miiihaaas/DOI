"""
Article business logic services for DOI Portal.

Story 3.1: Placeholder for future business logic (status transitions in Story 3.5).
Story 3.5: Submit Article for Review - DRAFT -> REVIEW status transition.
Story 3.6: Editorial Review Process - approve_article, return_article_for_revision.
"""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from .models import Article, ArticleStatus, PdfStatus


class InvalidStatusTransition(Exception):
    """Raised when article status transition is invalid."""

    pass


def validate_article_for_submit(article: Article) -> list[str]:
    """
    Validate that an article meets all requirements for submission.

    Checks: status is DRAFT, title non-empty, abstract non-empty,
    at least one author, PDF status is CLEAN.

    Args:
        article: Article instance to validate

    Returns:
        List of error messages (empty if article is ready)
    """
    errors = []
    if article.status != ArticleStatus.DRAFT:
        errors.append("Članak nije u statusu Nacrt.")
    if not article.title or not article.title.strip():
        errors.append("Naslov je obavezan.")
    if not article.abstract or not article.abstract.strip():
        errors.append("Apstrakt je obavezan.")
    if article.authors.count() == 0:
        errors.append("Potreban je bar jedan autor.")
    if article.pdf_status != PdfStatus.CLEAN:
        errors.append("PDF fajl mora biti otpremljen i uspešno skeniran.")

    return errors


def submit_article_for_review(article: Article, user) -> Article:
    """
    Submit article for editorial review.

    Validates required fields and transitions DRAFT -> REVIEW.

    Args:
        article: Article instance to submit
        user: User performing the submission

    Returns:
        Updated Article instance

    Raises:
        InvalidStatusTransition: If article is not in DRAFT status or
            required fields are missing
    """
    # Validate status first (separate error for non-DRAFT)
    if article.status != ArticleStatus.DRAFT:
        raise InvalidStatusTransition(
            "Samo članci u statusu Nacrt mogu biti poslati na pregled."
        )

    # Validate required fields using shared validation
    errors = validate_article_for_submit(article)
    if errors:
        raise InvalidStatusTransition(
            "Članak nije spreman za pregled: " + "; ".join(errors)
        )

    # Perform transition within atomic block to prevent race conditions
    with transaction.atomic():
        article.status = ArticleStatus.REVIEW
        article.submitted_by = user
        article.submitted_at = timezone.now()
        article.save(update_fields=["status", "submitted_by", "submitted_at", "updated_at"])

    return article


def approve_article(article: Article, user) -> Article:
    """
    Approve article for publication (REVIEW -> READY).

    Args:
        article: Article instance to approve
        user: User performing the approval (Urednik/Admin)

    Returns:
        Updated Article instance

    Raises:
        InvalidStatusTransition: If article is not in REVIEW status
    """
    if article.status != ArticleStatus.REVIEW:
        raise InvalidStatusTransition(
            "Samo članci na pregledu mogu biti odobreni."
        )

    with transaction.atomic():
        # Lock the row to prevent concurrent status transitions
        article = Article.objects.select_for_update().get(pk=article.pk)
        # Re-validate after lock acquisition (another request may have changed status)
        if article.status != ArticleStatus.REVIEW:
            raise InvalidStatusTransition(
                "Samo članci na pregledu mogu biti odobreni."
            )
        article.status = ArticleStatus.READY
        article.reviewed_by = user
        article.reviewed_at = timezone.now()
        # Clear previous revision/return tracking from prior return cycle
        article.revision_comment = ""
        article.returned_by = None
        article.returned_at = None
        article.save(update_fields=[
            "status", "reviewed_by", "reviewed_at",
            "revision_comment", "returned_by", "returned_at",
            "updated_at",
        ])

    return article


def return_article_for_revision(article: Article, user, comment: str) -> Article:
    """
    Return article for revision (REVIEW -> DRAFT).

    Args:
        article: Article instance to return
        user: User performing the return (Urednik/Admin)
        comment: Revision comment explaining what needs to change

    Returns:
        Updated Article instance

    Raises:
        InvalidStatusTransition: If article is not in REVIEW status
            or comment is empty
    """
    if article.status != ArticleStatus.REVIEW:
        raise InvalidStatusTransition(
            "Samo članci na pregledu mogu biti vraćeni na doradu."
        )

    if not comment or not comment.strip():
        raise InvalidStatusTransition(
            "Komentar je obavezan pri vraćanju članka na doradu."
        )

    with transaction.atomic():
        # Lock the row to prevent concurrent status transitions
        article = Article.objects.select_for_update().get(pk=article.pk)
        # Re-validate after lock acquisition (another request may have changed status)
        if article.status != ArticleStatus.REVIEW:
            raise InvalidStatusTransition(
                "Samo članci na pregledu mogu biti vraćeni na doradu."
            )
        article.status = ArticleStatus.DRAFT
        article.revision_comment = comment.strip()
        article.returned_by = user
        article.returned_at = timezone.now()
        # Reset submit tracking for new cycle
        article.submitted_by = None
        article.submitted_at = None
        # Clear previous review tracking from prior approve attempt
        article.reviewed_by = None
        article.reviewed_at = None
        article.save(update_fields=[
            "status", "revision_comment", "returned_by",
            "returned_at", "submitted_by", "submitted_at",
            "reviewed_by", "reviewed_at", "updated_at",
        ])

    return article
