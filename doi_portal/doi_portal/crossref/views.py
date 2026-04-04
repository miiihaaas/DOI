"""
Crossref views.

Story 5.1: Crossref Service Infrastructure.
Story 5.2: Pre-Generation Validation & Warnings.
Story 5.3: XML Generation for All Publication Types.
Story 5.5: XML Preview with Syntax Highlighting.
Story 5.6: XML Download - Export History Tracking.
Story 5.7: Crossref Deposit Workflow Page.
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
from django.urls import reverse
from django.utils import timezone
from slugify import slugify
from django.views import View

from doi_portal.core.permissions import has_publisher_access
from doi_portal.crossref.models import CrossrefExport
from doi_portal.crossref.services import CrossrefService
from doi_portal.crossref.services import PreValidationService
from doi_portal.crossref.tasks import crossref_generate_component_xml_task
from doi_portal.crossref.tasks import crossref_generate_xml_task
from doi_portal.issues.models import Issue

if TYPE_CHECKING:
    from django.http import HttpRequest

from doi_portal.crossref.models import ExportType

__all__ = [
    "CrossrefDepositView",
    "GenerateXMLView",
    "IssueValidationView",
    "mark_deposited",
    "xml_preview",
    "xml_download",
    "download_warning",
    "xml_download_force",
    "export_redownload",
    "export_history",
    # Component workflow
    "ComponentGroupValidationView",
    "GenerateComponentXMLView",
    "ComponentGroupDepositView",
    "component_xml_preview",
    "component_xml_download",
    "component_download_warning",
    "component_xml_download_force",
    "component_export_redownload",
    "component_export_history",
    "component_mark_deposited",
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

        Raises:
            PermissionDenied: If user does not have access to the issue's publisher.
        """
        issue = get_object_or_404(Issue, pk=pk)

        # Check publisher-level permission (RBAC model requires row-level access)
        if not has_publisher_access(request.user, issue.publication.publisher):
            raise PermissionDenied

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

        Raises:
            PermissionDenied: If user does not have access to the issue's publisher.
        """
        issue = get_object_or_404(Issue, pk=pk)

        # Check publisher-level permission (RBAC model requires row-level access)
        if not has_publisher_access(request.user, issue.publication.publisher):
            raise PermissionDenied

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


def _generate_filename(issue: Issue) -> str:
    """
    Generate standardized filename for XML export.

    Story 5.6: XML Download - Filename Generation.

    Args:
        issue: The Issue to generate filename for

    Returns:
        Filename in format: {publication-slug}_{volume}_{issue}_{timestamp}.xml
    """
    publication_slug = slugify(issue.publication.title)[:30] or "publication"
    volume = issue.volume or "v0"
    issue_num = issue.issue_number or "i0"
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    return f"{publication_slug}_{volume}_{issue_num}_{timestamp}.xml"


def _create_xml_download_response(
    request: "HttpRequest",
    issue: Issue,
) -> HttpResponse:
    """
    Create XML download response with export tracking.

    Story 5.6: XML Download - Shared helper for xml_download and xml_download_force.
    Eliminates code duplication between the two download views.

    Args:
        request: HTTP request (for user tracking)
        issue: The Issue to download XML from

    Returns:
        HttpResponse with XML attachment

    Raises:
        Http404: If XML is not generated for the issue.
    """
    if not issue.crossref_xml:
        raise Http404("XML nije generisan.")

    # Generate filename
    filename = _generate_filename(issue)

    # Create export record (Story 5.6: Export History Tracking)
    CrossrefExport.objects.create(
        issue=issue,
        xml_content=issue.crossref_xml,
        exported_by=request.user,
        filename=filename,
        xsd_valid_at_export=issue.xsd_valid,
    )

    # Return XML with proper headers (AC2: UTF-8 encoding)
    response = HttpResponse(
        issue.crossref_xml,
        content_type="application/xml; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def xml_download(request: "HttpRequest", pk: int) -> HttpResponse:
    """
    Download Crossref XML for an issue with export tracking.

    Story 5.6: XML Download - Export History Tracking.
    Creates a CrossrefExport record for each download.

    Args:
        request: HTTP request
        pk: Issue primary key

    Returns:
        XML file download response

    Raises:
        PermissionDenied: If user does not have access to the issue's publisher.
        Http404: If XML is not generated for the issue.
    """
    issue = get_object_or_404(Issue, pk=pk)

    # Check publisher-level permission (RBAC model requires row-level access)
    if not has_publisher_access(request.user, issue.publication.publisher):
        raise PermissionDenied

    return _create_xml_download_response(request, issue)


@login_required
def download_warning(request: "HttpRequest", pk: int) -> HttpResponse:
    """
    Return warning modal for invalid XML download.

    Story 5.6: Warning for Invalid XML (AC4).
    Shows modal with error count and options to proceed or cancel.

    Args:
        request: HTTP request
        pk: Issue primary key

    Returns:
        HTML partial with warning modal

    Raises:
        PermissionDenied: If user does not have access to the issue's publisher.
    """
    issue = get_object_or_404(Issue, pk=pk)

    if not has_publisher_access(request.user, issue.publication.publisher):
        raise PermissionDenied

    error_count = len(issue.xsd_errors) if issue.xsd_errors else 0

    return TemplateResponse(
        request,
        "crossref/partials/_download_warning_modal.html",
        {"issue": issue, "error_count": error_count},
    )


@login_required
def xml_download_force(request: "HttpRequest", pk: int) -> HttpResponse:
    """
    Download XML regardless of validation status.

    Story 5.6: XML Download with Export Tracking.
    Creates export history record even for invalid XML.
    Uses same logic as xml_download, bypassing the xsd_valid check in template.

    Args:
        request: HTTP request
        pk: Issue primary key

    Returns:
        XML file download response

    Raises:
        PermissionDenied: If user does not have access to the issue's publisher.
        Http404: If XML is not generated for the issue.
    """
    issue = get_object_or_404(Issue, pk=pk)

    if not has_publisher_access(request.user, issue.publication.publisher):
        raise PermissionDenied

    return _create_xml_download_response(request, issue)


@login_required
def export_redownload(request: "HttpRequest", pk: int) -> HttpResponse:
    """
    Re-download a previous export.

    Story 5.6: Export History Re-download (AC5).
    Serves stored XML content from CrossrefExport record.

    Args:
        request: HTTP request
        pk: CrossrefExport primary key

    Returns:
        XML file download response

    Raises:
        PermissionDenied: If user does not have access to the export's issue publisher.
    """
    export = get_object_or_404(CrossrefExport, pk=pk)

    # Permission check — handle both issue and component_group exports
    if export.issue:
        publisher = export.issue.publication.publisher
    elif export.component_group:
        publisher = export.component_group.publisher
    else:
        raise Http404
    if not has_publisher_access(request.user, publisher):
        raise PermissionDenied

    response = HttpResponse(
        export.xml_content,
        content_type="application/xml; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{export.filename}"'
    return response


@login_required
def export_history(request: "HttpRequest", pk: int) -> HttpResponse:
    """
    Return export history partial for an issue.

    Story 5.6: Export History Display (AC5).
    Lists previous exports with timestamps, users, and validation status.

    Args:
        request: HTTP request
        pk: Issue primary key

    Returns:
        HTML partial with export history table

    Raises:
        PermissionDenied: If user does not have access to the issue's publisher.
    """
    issue = get_object_or_404(Issue, pk=pk)

    if not has_publisher_access(request.user, issue.publication.publisher):
        raise PermissionDenied

    exports = issue.crossref_exports.select_related("exported_by")[:10]

    return TemplateResponse(
        request,
        "crossref/partials/_export_history.html",
        {"issue": issue, "exports": exports},
    )


class CrossrefDepositView(LoginRequiredMixin, View):
    """
    Dedicated Crossref Deposit workflow page.

    Story 5.7: Crossref Deposit Workflow Page.
    Orchestrates existing HTMX partials into a step-by-step workflow.
    """

    def get(self, request: "HttpRequest", pk: int) -> HttpResponse:
        """
        Render the deposit workflow page with computed step statuses.

        Args:
            request: HTTP request
            pk: Issue primary key

        Returns:
            Rendered deposit workflow page

        Raises:
            PermissionDenied: If user does not have access to the issue's publisher.
        """
        issue = get_object_or_404(Issue, pk=pk)

        if not has_publisher_access(request.user, issue.publication.publisher):
            raise PermissionDenied

        # Compute step statuses
        has_xml = bool(issue.crossref_xml)
        validator = PreValidationService()
        validation_result = validator.validate_issue(issue)

        steps = [
            {
                "number": 1,
                "title": "Pre-validacija",
                "completed": validation_result.is_valid,
                "active": not validation_result.is_valid,
                "icon": "clipboard-check",
            },
            {
                "number": 2,
                "title": "Generisanje XML",
                "completed": has_xml,
                "active": validation_result.is_valid and not has_xml,
                "icon": "file-code",
            },
            {
                "number": 3,
                "title": "XSD Validacija",
                "completed": has_xml and issue.xsd_valid is True,
                "active": has_xml and issue.xsd_valid is not True,
                "icon": "shield-check",
            },
            {
                "number": 4,
                "title": "Pregled XML",
                "completed": False,  # Always available, never "completed"
                "active": has_xml,
                "icon": "eye",
            },
            {
                "number": 5,
                "title": "Preuzimanje XML",
                "completed": issue.crossref_exports.exists(),
                "active": has_xml,
                "icon": "download",
            },
        ]

        # Check if all critical steps are complete for "ready for Crossref"
        all_ready = (
            has_xml
            and issue.xsd_valid is True
            and issue.crossref_exports.exists()
        )

        # Breadcrumbs
        breadcrumbs = [
            {
                "label": "Izdanja",
                "url": reverse("issues:list"),
            },
            {
                "label": str(issue),
                "url": reverse("issues:detail", args=[issue.pk]),
            },
            {
                "label": "Crossref Deposit",
                "url": "",
            },
        ]

        return TemplateResponse(
            request,
            "crossref/issue_crossref_deposit.html",
            {
                "issue": issue,
                "steps": steps,
                "has_xml": has_xml,
                "validation_result": validation_result,
                "is_deposited": issue.is_crossref_deposited,
                "all_ready": all_ready,
                "breadcrumbs": breadcrumbs,
            },
        )


@login_required
def mark_deposited(request: "HttpRequest", pk: int) -> HttpResponse:
    """
    Mark an issue as deposited to Crossref.

    Story 5.7: Mark as Deposited (AC5).

    Args:
        request: HTTP request
        pk: Issue primary key

    Returns:
        HTML partial with deposited status

    Raises:
        PermissionDenied: If user does not have access to the issue's publisher.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    issue = get_object_or_404(Issue, pk=pk)

    if not has_publisher_access(request.user, issue.publication.publisher):
        raise PermissionDenied

    issue.crossref_deposited_at = timezone.now()
    issue.crossref_deposited_by = request.user
    issue.save(update_fields=["crossref_deposited_at", "crossref_deposited_by"])

    return render(
        request,
        "crossref/partials/_deposit_status.html",
        {
            "issue": issue,
            "is_deposited": True,
        },
    )


# =============================================================================
# Component Workflow Views
# =============================================================================


def _get_component_group(pk):
    """Get ComponentGroup with publisher select_related."""
    from doi_portal.components.models import ComponentGroup
    return get_object_or_404(
        ComponentGroup.objects.select_related("publisher"),
        pk=pk,
    )


def _generate_component_filename(component_group) -> str:
    """Generate standardized filename for component XML export."""
    parent_doi_slug = slugify(component_group.parent_doi)[:30] or "component"
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    return f"component_{parent_doi_slug}_{timestamp}.xml"


def _create_component_xml_download_response(request, component_group):
    """Create XML download response with export tracking for component groups."""
    if not component_group.crossref_xml:
        raise Http404("XML nije generisan.")

    filename = _generate_component_filename(component_group)

    CrossrefExport.objects.create(
        component_group=component_group,
        export_type=ExportType.COMPONENT_GROUP,
        xml_content=component_group.crossref_xml,
        exported_by=request.user,
        filename=filename,
        xsd_valid_at_export=component_group.xsd_valid,
    )

    response = HttpResponse(
        component_group.crossref_xml,
        content_type="application/xml; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


class ComponentGroupValidationView(LoginRequiredMixin, View):
    """Validate a ComponentGroup before XML generation."""

    def get(self, request: "HttpRequest", pk: int) -> HttpResponse:
        cg = _get_component_group(pk)
        if not has_publisher_access(request.user, cg.publisher):
            raise PermissionDenied

        service = PreValidationService()
        result = service.validate_component_group(cg)

        return render(
            request,
            "crossref/partials/_component_validation_panel.html",
            {
                "component_group": cg,
                "is_valid": result.is_valid,
                "errors": result.errors,
                "warnings": result.warnings,
                "error_count": len(result.errors),
                "warning_count": len(result.warnings),
            },
        )


class GenerateComponentXMLView(LoginRequiredMixin, View):
    """Generate Crossref XML for a ComponentGroup."""

    ASYNC_COMPONENT_THRESHOLD = 20

    def post(self, request: "HttpRequest", pk: int) -> HttpResponse:
        cg = _get_component_group(pk)
        if not has_publisher_access(request.user, cg.publisher):
            raise PermissionDenied

        # Pre-validation
        validator = PreValidationService()
        result = validator.validate_component_group(cg)

        if not result.is_valid:
            return render(
                request,
                "crossref/partials/_component_generation_result.html",
                {
                    "success": False,
                    "message": "Generisanje blokirano zbog grešaka u validaciji",
                    "errors": result.errors,
                },
            )

        component_count = cg.components.filter(is_deleted=False).count()

        if component_count > self.ASYNC_COMPONENT_THRESHOLD:
            task = crossref_generate_component_xml_task.delay(cg.pk)
            return render(
                request,
                "crossref/partials/_component_generation_result.html",
                {
                    "generating": True,
                    "task_id": task.id,
                    "message": "Generisanje u toku...",
                },
            )

        # Sync generation
        service = CrossrefService()
        success, result_data = service.generate_and_store_component_xml(cg)
        cg.refresh_from_db()

        return render(
            request,
            "crossref/partials/_component_generation_result.html",
            {
                "component_group": cg,
                "success": success,
                "message": "XML uspešno generisan" if success else result_data,
                "timestamp": cg.xml_generated_at,
                "xsd_valid": cg.xsd_valid,
                "xsd_errors": cg.xsd_errors,
                "xsd_validated_at": cg.xsd_validated_at,
            },
        )


@login_required
def component_xml_preview(request: "HttpRequest", pk: int) -> HttpResponse:
    """Return XML preview modal for a ComponentGroup."""
    cg = _get_component_group(pk)
    if not has_publisher_access(request.user, cg.publisher):
        raise PermissionDenied

    if not cg.crossref_xml:
        return HttpResponse(
            '<div class="alert alert-warning">XML nije generisan.</div>',
            status=200,
        )

    error_lines = []
    if cg.xsd_errors:
        for error in cg.xsd_errors:
            if error.get("line"):
                error_lines.append(str(error["line"]))

    xml_size_kb = len(cg.crossref_xml.encode("utf-8")) / 1024
    is_large_xml = xml_size_kb > 100

    return TemplateResponse(
        request,
        "crossref/partials/_xml_preview_modal.html",
        {
            "component_group": cg,
            "xml_content": cg.crossref_xml,
            "xsd_valid": cg.xsd_valid,
            "xsd_errors": cg.xsd_errors,
            "error_lines": ",".join(error_lines),
            "is_large_xml": is_large_xml,
            "xml_size_kb": round(xml_size_kb, 1),
        },
    )


@login_required
def component_xml_download(request: "HttpRequest", pk: int) -> HttpResponse:
    """Download Crossref XML for a ComponentGroup."""
    cg = _get_component_group(pk)
    if not has_publisher_access(request.user, cg.publisher):
        raise PermissionDenied
    return _create_component_xml_download_response(request, cg)


@login_required
def component_download_warning(request: "HttpRequest", pk: int) -> HttpResponse:
    """Return warning modal for invalid component XML download."""
    cg = _get_component_group(pk)
    if not has_publisher_access(request.user, cg.publisher):
        raise PermissionDenied

    error_count = len(cg.xsd_errors) if cg.xsd_errors else 0
    return TemplateResponse(
        request,
        "crossref/partials/_download_warning_modal.html",
        {"component_group": cg, "error_count": error_count},
    )


@login_required
def component_xml_download_force(request: "HttpRequest", pk: int) -> HttpResponse:
    """Download component XML regardless of validation status."""
    cg = _get_component_group(pk)
    if not has_publisher_access(request.user, cg.publisher):
        raise PermissionDenied
    return _create_component_xml_download_response(request, cg)


@login_required
def component_export_redownload(request: "HttpRequest", pk: int) -> HttpResponse:
    """Re-download a previous component export."""
    export = get_object_or_404(CrossrefExport, pk=pk)

    if export.component_group:
        publisher = export.component_group.publisher
    elif export.issue:
        publisher = export.issue.publication.publisher
    else:
        raise Http404

    if not has_publisher_access(request.user, publisher):
        raise PermissionDenied

    response = HttpResponse(
        export.xml_content,
        content_type="application/xml; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{export.filename}"'
    return response


@login_required
def component_export_history(request: "HttpRequest", pk: int) -> HttpResponse:
    """Return export history partial for a ComponentGroup."""
    cg = _get_component_group(pk)
    if not has_publisher_access(request.user, cg.publisher):
        raise PermissionDenied

    exports = CrossrefExport.objects.filter(
        component_group=cg
    ).select_related("exported_by")[:10]

    return TemplateResponse(
        request,
        "crossref/partials/_component_export_history.html",
        {"component_group": cg, "exports": exports},
    )


class ComponentGroupDepositView(LoginRequiredMixin, View):
    """Crossref Deposit workflow page for ComponentGroup."""

    def get(self, request: "HttpRequest", pk: int) -> HttpResponse:
        cg = _get_component_group(pk)
        if not has_publisher_access(request.user, cg.publisher):
            raise PermissionDenied

        has_xml = bool(cg.crossref_xml)
        validator = PreValidationService()
        validation_result = validator.validate_component_group(cg)

        steps = [
            {
                "number": 1,
                "title": "Pre-validacija",
                "completed": validation_result.is_valid,
                "active": not validation_result.is_valid,
                "icon": "clipboard-check",
            },
            {
                "number": 2,
                "title": "Generisanje XML",
                "completed": has_xml,
                "active": validation_result.is_valid and not has_xml,
                "icon": "file-code",
            },
            {
                "number": 3,
                "title": "XSD Validacija",
                "completed": has_xml and cg.xsd_valid is True,
                "active": has_xml and cg.xsd_valid is not True,
                "icon": "shield-check",
            },
            {
                "number": 4,
                "title": "Pregled XML",
                "completed": False,
                "active": has_xml,
                "icon": "eye",
            },
            {
                "number": 5,
                "title": "Preuzimanje XML",
                "completed": cg.crossref_exports.exists(),
                "active": has_xml,
                "icon": "download",
            },
        ]

        all_ready = (
            has_xml
            and cg.xsd_valid is True
            and cg.crossref_exports.exists()
        )

        breadcrumbs = [
            {"label": "Komponente", "url": reverse("components:group-list")},
            {"label": str(cg), "url": reverse("components:group-detail", args=[cg.pk])},
            {"label": "Crossref Deposit", "url": ""},
        ]

        return TemplateResponse(
            request,
            "crossref/component_crossref_deposit.html",
            {
                "component_group": cg,
                "steps": steps,
                "has_xml": has_xml,
                "validation_result": validation_result,
                "is_deposited": cg.is_crossref_deposited,
                "all_ready": all_ready,
                "breadcrumbs": breadcrumbs,
            },
        )


@login_required
def component_mark_deposited(request: "HttpRequest", pk: int) -> HttpResponse:
    """Mark a ComponentGroup as deposited to Crossref."""
    if request.method != "POST":
        return HttpResponse(status=405)

    cg = _get_component_group(pk)
    if not has_publisher_access(request.user, cg.publisher):
        raise PermissionDenied

    cg.crossref_deposited_at = timezone.now()
    cg.crossref_deposited_by = request.user
    cg.save(update_fields=["crossref_deposited_at", "crossref_deposited_by"])

    return render(
        request,
        "crossref/partials/_component_deposit_status.html",
        {
            "component_group": cg,
            "is_deposited": True,
        },
    )
