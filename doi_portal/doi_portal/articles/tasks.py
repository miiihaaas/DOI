"""
Celery tasks for articles app.

Story 3.3: PDF virus scanning via ClamAV daemon.
"""

import pyclamd
import structlog
from celery import shared_task
from celery.exceptions import Retry
from django.conf import settings
from django.core.files.storage import default_storage

logger = structlog.get_logger(__name__)


CLAMAV_SOCKET_TIMEOUT = 10  # seconds


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=300,
    time_limit=600,
)
def virus_scan_pdf_task(self, instance_id, model_label="articles.Article", old_pdf_path=None):
    """
    Scan uploaded PDF for viruses using ClamAV.

    Flow:
    1. Connect to ClamAV daemon
    2. Scan file stream
    3. Clean -> keep file, update status to "clean"
    4. Infected -> delete file, update status to "infected"
    5. Error -> retry up to 3 times, then "scan_failed"

    Args:
        instance_id: Primary key of the model instance to scan.
        model_label: App label and model name (e.g. "articles.Article").
        old_pdf_path: Path to old PDF for cleanup after successful scan.
    """
    from django.apps import apps
    from doi_portal.articles.models import PdfStatus

    Model = apps.get_model(model_label)

    try:
        instance = Model.all_objects.get(pk=instance_id)
    except Model.DoesNotExist:
        logger.error("instance_not_found", model_label=model_label, instance_id=instance_id)
        return

    try:
        _run_virus_scan(self, instance, old_pdf_path)
    except Retry:
        # Celery retry — let it propagate so the task is re-queued.
        raise
    except Exception:
        # Catch-all: if anything unexpected happens (SoftTimeLimitExceeded,
        # worker shutdown, etc.), ensure status doesn't stay stuck on SCANNING.
        logger.exception("virus_scan_unexpected_error", model_label=model_label, instance_id=instance_id)
        instance.refresh_from_db(fields=["pdf_status"])
        if instance.pdf_status == PdfStatus.SCANNING:
            instance.pdf_status = PdfStatus.SCAN_FAILED
            instance.save(update_fields=["pdf_status"])


def _run_virus_scan(task, instance, old_pdf_path):
    """Inner scan logic, separated so the caller can catch-all exceptions."""
    from doi_portal.articles.models import PdfStatus

    # Connect to ClamAV
    try:
        cd = pyclamd.ClamdNetworkSocket(
            host=getattr(settings, "CLAMAV_HOST", "localhost"),
            port=getattr(settings, "CLAMAV_PORT", 3310),
            timeout=CLAMAV_SOCKET_TIMEOUT,
        )
        cd.ping()
    except Exception as exc:
        logger.warning(
            "clamav_connection_failed",
            instance_id=instance.pk,
            error=str(exc),
            retry=task.request.retries,
        )
        try:
            raise task.retry(exc=exc)
        except task.MaxRetriesExceededError:
            instance.pdf_status = PdfStatus.SCAN_FAILED
            instance.save(update_fields=["pdf_status"])
            logger.error("clamav_max_retries_exceeded", instance_id=instance.pk)
            return

    # Scan the file
    try:
        scan_result = cd.scan_stream(instance.pdf_file.read())
        instance.pdf_file.seek(0)  # Reset file pointer
    except Exception as exc:
        logger.error("clamav_scan_error", instance_id=instance.pk, error=str(exc))
        try:
            raise task.retry(exc=exc)
        except task.MaxRetriesExceededError:
            instance.pdf_status = PdfStatus.SCAN_FAILED
            instance.save(update_fields=["pdf_status"])
            return

    if scan_result is None:
        # File is clean
        instance.pdf_status = PdfStatus.CLEAN
        instance.save(update_fields=["pdf_status"])
        logger.info("pdf_scan_clean", instance_id=instance.pk)

        # Delete old PDF if this was a replacement
        if old_pdf_path:
            _delete_old_pdf(old_pdf_path)
    else:
        # File is infected
        virus_name = str(scan_result)
        file_path = instance.pdf_file.name
        instance.pdf_file.delete(save=False)
        instance.pdf_file = ""
        instance.pdf_original_filename = ""
        instance.pdf_status = PdfStatus.INFECTED
        instance.save(
            update_fields=["pdf_file", "pdf_original_filename", "pdf_status"],
        )
        logger.error(
            "pdf_scan_infected",
            instance_id=instance.pk,
            virus=virus_name,
            file_path=file_path,
        )


def _delete_old_pdf(file_path):
    """Delete old PDF file from storage."""
    try:
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            logger.info("old_pdf_deleted", file_path=file_path)
    except Exception as exc:
        logger.warning("old_pdf_delete_failed", file_path=file_path, error=str(exc))
