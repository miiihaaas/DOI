"""
Crossref Celery tasks.

Story 5.1: Crossref Service Infrastructure.
Story 5.3: XML Generation for All Publication Types.
Celery tasks for background XML generation.
"""

from __future__ import annotations

from celery import shared_task

__all__ = ["crossref_generate_xml_task"]


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def crossref_generate_xml_task(self, issue_id: int) -> dict:
    """
    Generate Crossref XML asynchronously.

    Story 5.3: XML Generation for All Publication Types (AC5).
    Handles XML generation for large issues (>20 articles) asynchronously.
    Uses exponential backoff with max 3 retries.

    Args:
        issue_id: ID of Issue to generate XML for

    Returns:
        Dict with status and message
    """
    # Import inside task to avoid circular imports
    from celery.exceptions import MaxRetriesExceededError

    from doi_portal.crossref.services import CrossrefService
    from doi_portal.issues.models import Issue

    try:
        issue = Issue.objects.get(pk=issue_id)

        # Set generating status
        issue.xml_generation_status = "generating"
        issue.save(update_fields=["xml_generation_status"])

        # Generate XML
        service = CrossrefService()
        success, result = service.generate_and_store_xml(issue)

        return {
            "success": success,
            "message": "XML uspešno generisan" if success else result,
        }
    except Issue.DoesNotExist:
        return {
            "success": False,
            "message": f"Izdanje {issue_id} nije pronađeno",
        }
    except MaxRetriesExceededError:
        # All retries exhausted - set status to failed
        try:
            issue = Issue.objects.get(pk=issue_id)
            issue.xml_generation_status = "failed"
            issue.save(update_fields=["xml_generation_status"])
        except Issue.DoesNotExist:
            pass
        return {
            "success": False,
            "message": "Generisanje neuspešno nakon više pokušaja",
        }
    except Exception as e:
        # Retry on transient errors
        try:
            raise self.retry(exc=e)
        except MaxRetriesExceededError:
            # Set failed status when retries exhausted
            try:
                issue = Issue.objects.get(pk=issue_id)
                issue.xml_generation_status = "failed"
                issue.save(update_fields=["xml_generation_status"])
            except Issue.DoesNotExist:
                pass
            return {
                "success": False,
                "message": f"Generisanje neuspešno: {e!s}",
            }
