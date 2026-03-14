"""
Core Celery tasks.

Story 6.1: Audit log archive task for retention compliance.
"""

import json
import logging
from datetime import timedelta
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def audit_log_archive_task(self, days_threshold=365):
    """
    Archive audit log entries older than threshold days.

    Exports old LogEntry records to JSON files in the audit-archives directory.
    Uses local file storage (MEDIA_ROOT/audit-archives/) as fallback when
    S3 is not configured.

    IMPORTANT: Does NOT delete original entries - only exports them.

    Args:
        days_threshold: Number of days after which entries are archived (default: 365).

    Returns:
        str: Summary message with count of archived entries.
    """
    from auditlog.models import LogEntry

    cutoff_date = timezone.now() - timedelta(days=days_threshold)
    old_entries = LogEntry.objects.filter(timestamp__lt=cutoff_date)

    count = old_entries.count()
    if count == 0:
        msg = "No audit log entries older than {} days to archive.".format(days_threshold)
        logger.info(msg)
        return msg

    # Serialize entries to JSON (using iterator with chunk_size for memory efficiency)
    entries_data = []
    for entry in old_entries.iterator(chunk_size=2000):
        entries_data.append({
            "pk": entry.pk,
            "content_type_id": entry.content_type_id,
            "object_id": entry.object_id,
            "object_repr": entry.object_repr,
            "action": entry.action,
            "changes": entry.changes,
            "actor_id": entry.actor_id,
            "remote_addr": entry.remote_addr,
            "timestamp": entry.timestamp.isoformat(),
            "additional_data": entry.additional_data,
        })

    # Write to local file storage (MEDIA_ROOT/audit-archives/)
    try:
        archive_dir = Path(settings.MEDIA_ROOT) / "audit-archives"
        archive_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = timezone.now().strftime("%Y%m%d_%H%M%S")
        archive_filename = f"audit_log_archive_{timestamp_str}.json"
        archive_path = archive_dir / archive_filename

        archive_path.write_text(
            json.dumps(entries_data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.exception("Failed to write audit log archive file: %s", exc)
        raise self.retry(exc=exc)

    msg = f"Archived {count} audit log entries to {archive_filename}"
    logger.info(msg)
    return msg
