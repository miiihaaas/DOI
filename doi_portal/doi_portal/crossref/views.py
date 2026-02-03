"""
Crossref views.

Story 5.1: Crossref Service Infrastructure.
Story 5.2: Pre-Generation Validation & Warnings.
Story 5.3: XML Generation for All Publication Types.
"""

from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views import View

from doi_portal.crossref.services import CrossrefService
from doi_portal.crossref.services import PreValidationService
from doi_portal.crossref.tasks import crossref_generate_xml_task
from doi_portal.issues.models import Issue

if TYPE_CHECKING:
    from django.http import HttpRequest

__all__ = ["GenerateXMLView", "IssueValidationView"]


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

        return render(
            request,
            "crossref/partials/_generation_result.html",
            {
                "success": success,
                "message": "XML uspešno generisan" if success else result_data,
                "timestamp": issue.xml_generated_at,
            },
        )
