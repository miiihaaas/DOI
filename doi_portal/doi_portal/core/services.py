"""
Core services for DOI Portal.

Story 6.4: GdprService - business logic for GDPR data request handling.
"""

import logging
from datetime import timedelta

from django.utils import timezone

from doi_portal.core.models import GdprRequest, GdprRequestStatus

logger = logging.getLogger(__name__)

__all__ = ["GdprService"]


class GdprService:
    """Service layer for GDPR data request operations."""

    @staticmethod
    def identify_affected_data(requester_email):
        """
        Identify data affected by a GDPR request.

        Args:
            requester_email: Email address to search for.

        Returns:
            Dict with: user (User or None), authors (QuerySet),
            audit_entries_count (int).
        """
        from auditlog.models import LogEntry

        from doi_portal.articles.models import Author
        from doi_portal.users.models import User

        # Find user by email
        try:
            user = User.objects.get(email=requester_email)
        except User.DoesNotExist:
            user = None

        # Find author records - use all_objects to include soft-deleted
        authors = Author.all_objects.filter(email=requester_email)

        # Count audit log entries for the user
        audit_entries_count = 0
        if user:
            audit_entries_count = LogEntry.objects.filter(actor=user).count()

        return {
            "user": user,
            "authors": authors,
            "audit_entries_count": audit_entries_count,
        }

    @staticmethod
    def process_deletion_request(gdpr_request, processed_by):
        """
        Process a GDPR deletion request: soft delete + schedule anonymization.

        Args:
            gdpr_request: GdprRequest instance.
            processed_by: User performing the action.
        """
        from doi_portal.articles.models import Author
        from doi_portal.users.models import User

        affected = GdprService.identify_affected_data(
            gdpr_request.requester_email
        )

        # Soft delete user (deactivate)
        user = affected["user"]
        if user:
            user.is_active = False
            user.save(update_fields=["is_active"])

        # Soft delete author records
        for author in affected["authors"]:
            if not author.is_deleted:
                author.soft_delete()

        # Update request status
        gdpr_request.status = GdprRequestStatus.PROCESSING
        gdpr_request.processed_at = timezone.now()
        gdpr_request.processed_by = processed_by
        gdpr_request.grace_period_end = timezone.now().date() + timedelta(days=30)
        gdpr_request.save()

        # Schedule permanent anonymization via Celery
        from doi_portal.core.tasks import gdpr_permanent_anonymize_task

        eta = timezone.now() + timedelta(days=30)
        gdpr_permanent_anonymize_task.apply_async(
            args=[gdpr_request.id],
            eta=eta,
        )

        logger.info(
            "GDPR deletion request %s processed by %s. Grace period ends %s.",
            gdpr_request.pk,
            processed_by.email,
            gdpr_request.grace_period_end,
        )

    @staticmethod
    def cancel_request(gdpr_request, reason, cancelled_by):
        """
        Cancel a GDPR request and restore soft-deleted data.

        Args:
            gdpr_request: GdprRequest instance.
            reason: Cancellation reason text.
            cancelled_by: User performing the cancellation.

        Raises:
            ValueError: If grace period has already expired.
        """
        from doi_portal.articles.models import Author
        from doi_portal.users.models import User

        # Prevent cancellation after grace period has expired
        if (
            gdpr_request.grace_period_end
            and gdpr_request.grace_period_end <= timezone.now().date()
        ):
            raise ValueError(
                "Nije moguće otkazati zahtev - grace period je istekao."
            )

        affected = GdprService.identify_affected_data(
            gdpr_request.requester_email
        )

        # Restore user
        user = affected["user"]
        if user and not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])

        # Restore soft-deleted authors
        for author in affected["authors"]:
            if author.is_deleted:
                author.restore()

        # Update request
        gdpr_request.status = GdprRequestStatus.CANCELLED
        gdpr_request.cancellation_reason = reason
        gdpr_request.save()

        logger.info(
            "GDPR request %s cancelled by %s. Reason: %s",
            gdpr_request.pk,
            cancelled_by.email,
            reason,
        )

    @staticmethod
    def complete_request(gdpr_request):
        """
        Complete a GDPR request: permanent anonymization.

        Args:
            gdpr_request: GdprRequest instance.
        """
        from auditlog.models import LogEntry

        from doi_portal.articles.models import Author
        from doi_portal.users.models import User

        affected = GdprService.identify_affected_data(
            gdpr_request.requester_email
        )

        # Anonymize user
        user = affected["user"]
        if user:
            user.email = f"deleted_{user.pk}@anonymized.local"
            user.name = ""
            user.is_active = False
            user.set_unusable_password()
            user.save()

            # Nullify audit log actor references
            LogEntry.objects.filter(actor=user).update(actor=None)

        # Anonymize author records
        for author in affected["authors"]:
            author.given_name = "[Anonimizirano]"
            author.surname = "[Anonimizirano]"
            author.email = ""
            author.orcid = ""
            author.orcid_authenticated = False
            author.save()

        # Update request status
        gdpr_request.status = GdprRequestStatus.COMPLETED
        gdpr_request.completed_at = timezone.now()
        gdpr_request.save()

        logger.info(
            "GDPR request %s completed. Data permanently anonymized.",
            gdpr_request.pk,
        )

    @staticmethod
    def generate_confirmation_report(gdpr_request):
        """
        Generate a plain text confirmation report for a GDPR request.

        Args:
            gdpr_request: GdprRequest instance.

        Returns:
            str: Plain text report content.
        """
        affected = GdprService.identify_affected_data(
            gdpr_request.requester_email
        )

        user_status = "Anonimizovan" if affected["user"] else "Nije pronađen"
        author_count = affected["authors"].count()
        audit_count = affected["audit_entries_count"]

        completed_date = ""
        if gdpr_request.completed_at:
            completed_date = gdpr_request.completed_at.strftime("%Y-%m-%d")

        report = f"""========================================
GDPR ZAHTEV - IZVEŠTAJ O OBRADI
========================================

Zahtev br.: GDPR-{gdpr_request.pk}
Email podnosioca: {gdpr_request.requester_email}
Tip zahteva: {gdpr_request.get_request_type_display()}
Datum prijema: {gdpr_request.received_date}
Datum obrade: {completed_date}
Status: {gdpr_request.get_status_display()}

OBRAĐENI PODACI:
- Korisnički nalog: {user_status}
- Autorski zapisi: {author_count} anonimizovano
- Revizioni log: {audit_count} zapisa - actor veza uklonjena

NAPOMENA: Svi personalni podaci su trajno anonimizovani
u skladu sa GDPR regulativom.
========================================
"""
        return report
