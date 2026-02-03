"""
Crossref views.

Story 5.1: Crossref Service Infrastructure.
Story 5.2: Pre-Generation Validation & Warnings.
"""

from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views import View

from doi_portal.crossref.services import PreValidationService
from doi_portal.issues.models import Issue

if TYPE_CHECKING:
    from django.http import HttpRequest

__all__ = ["IssueValidationView"]


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
