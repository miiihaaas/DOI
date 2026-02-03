"""
Crossref views.

Story 5.1: Crossref Service Infrastructure.
Story 5.2: Pre-Generation Validation & Warnings.
Story 5.3: XML Generation for All Publication Types.
Story 5.5: XML Preview with Syntax Highlighting.
"""

from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.text import slugify
from django.views import View

from doi_portal.core.permissions import has_publisher_access
from doi_portal.crossref.services import CrossrefService
from doi_portal.crossref.services import PreValidationService
from doi_portal.crossref.tasks import crossref_generate_xml_task
from doi_portal.issues.models import Issue

if TYPE_CHECKING:
    from django.http import HttpRequest

__all__ = [
    "GenerateXMLView",
    "IssueValidationView",
    "xml_preview",
    "xml_download",
]


class IssueValidationView(LoginRequiredMixin, View):
    """
    View for validating an issue before XML generation.

    Returns an HTML partial for HTMX consumption (per project-context.md).
    Auto-triggered on page load to show validation status.
    Requires authentication (AC1: Administrator navigates to Crossref section).
    """

    def get(self, request: "HttpRequest", pk: int) -> HttpResponse:
        """
        Run pre-validation and return HTML partial.

        Args:
            request: HTTP request
            pk: Issue primary key

        Returns:
            HTML partial with validation results
        """
        issue = get_object_or_404(Issue, pk=pk)

        # Run validation
        service = PreValidationService()
        result = service.validate_issue(issue)

        return render(
            request,
            "crossref/partials/_validation_panel.html",
            {
                "issue": issue,
                "is_valid": result.is_valid,
                "errors": result.errors,
                "warnings": result.warnings,
                "error_count": len(result.errors),
                "warning_count": len(result.warnings),
            },
        )


class GenerateXMLView(LoginRequiredMixin, View):
    """
    View for generating Crossref XML for an issue.

    Story 5.3: XML Generation for All Publication Types.
    Handles both sync (small issues) and async (large issues) generation.
    Returns an HTML partial for HTMX consumption.
    """

    # Threshold for async generation
    ASYNC_ARTICLE_THRESHOLD = 20

    def post(self, request: "HttpRequest", pk: int) -> HttpResponse:
        """
        Generate Crossref XML for an issue.

        Args:
            request: HTTP request
            pk: Issue primary key

        Returns:
            HTML partial with generation results
        """
        issue = get_object_or_404(Issue, pk=pk)

        # Run pre-validation first (AC7)
        validator = PreValidationService()
        result = validator.validate_issue(issue)

        if not result.is_valid:
            return render(
                request,
                "crossref/partials/_generation_result.html",
                {
                    "success": False,
                    "message": "Generisanje blokirano zbog grešaka u validaciji",
                    "errors": result.errors,
                },
            )

        # Check article count for async decision (AC5)
        article_count = issue.articles.filter(is_deleted=False).count()

        if article_count > self.ASYNC_ARTICLE_THRESHOLD:
            # Async generation for large issues
            task = crossref_generate_xml_task.delay(issue.pk)
            return render(
                request,
                "crossref/partials/_generation_result.html",
                {
                    "generating": True,
                    "task_id": task.id,
                    "message": "Generisanje u toku...",
                },
            )

        # Sync generation for small issues
        service = CrossrefService()
        success, result_data = service.generate_and_store_xml(issue)

        # Refresh issue from DB to get updated XSD validation fields
        issue.refresh_from_db()

        return render(
            request,
            "crossref/partials/_generation_result.html",
            {
                "issue": issue,
                "success": success,
                "message": "XML uspešno generisan" if success else result_data,
                "timestamp": issue.xml_generated_at,
                "xsd_valid": issue.xsd_valid,
                "xsd_errors": issue.xsd_errors,
                "xsd_validated_at": issue.xsd_validated_at,
            },
        )


@login_required
def xml_preview(request: "HttpRequest", pk: int) -> HttpResponse:
    """
    Return XML preview modal for an issue.

    Story 5.5: XML Preview with Syntax Highlighting.

    Args:
        request: HTTP request
        pk: Issue primary key

    Returns:
        HTML partial with modal containing XML preview

    Raises:
        PermissionDenied: If user does not have access to the issue's publisher.
    """
    issue = get_object_or_404(Issue, pk=pk)

    # Check publisher-level permission (RBAC model requires row-level access)
    if not has_publisher_access(request.user, issue.publication.publisher):
        raise PermissionDenied

    if not issue.crossref_xml:
        return HttpResponse(
            '<div class="alert alert-warning">XML nije generisan.</div>',
            status=200,
        )

    # Extract error line numbers for highlighting
    error_lines = []
    if issue.xsd_errors:
        for error in issue.xsd_errors:
            if error.get("line"):
                error_lines.append(str(error["line"]))

    # Performance warning for large XML (>100KB as per Task 3)
    xml_size_kb = len(issue.crossref_xml.encode("utf-8")) / 1024
    is_large_xml = xml_size_kb > 100

    context = {
        "issue": issue,
        "xml_content": issue.crossref_xml,
        "xsd_valid": issue.xsd_valid,
        "xsd_errors": issue.xsd_errors,
        "error_lines": ",".join(error_lines),
        "is_large_xml": is_large_xml,
        "xml_size_kb": round(xml_size_kb, 1),
    }

    return TemplateResponse(
        request,
        "crossref/partials/_xml_preview_modal.html",
        context,
    )


@login_required
def xml_download(request: "HttpRequest", pk: int) -> HttpResponse:
    """
    Download Crossref XML for an issue.

    Story 5.5: XML Preview with Syntax Highlighting.

    Args:
        request: HTTP request
        pk: Issue primary key

    Returns:
        XML file download response

    Raises:
        PermissionDenied: If user does not have access to the issue's publisher.
    """
    issue = get_object_or_404(Issue, pk=pk)

    # Check publisher-level permission (RBAC model requires row-level access)
    if not has_publisher_access(request.user, issue.publication.publisher):
        raise PermissionDenied

    if not issue.crossref_xml:
        raise Http404("XML nije generisan.")

    # Generate filename: {publication-slug}_{volume}_{issue}_{timestamp}.xml
    publication_slug = slugify(issue.publication.title)[:30]
    volume = issue.volume or "v0"
    issue_num = issue.issue_number or "i0"
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{publication_slug}_{volume}_{issue_num}_{timestamp}.xml"

    response = HttpResponse(
        issue.crossref_xml,
        content_type="application/xml",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
