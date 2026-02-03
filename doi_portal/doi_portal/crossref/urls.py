"""
Crossref URL configuration.

Story 5.1: Crossref Service Infrastructure.
Story 5.2: Pre-Generation Validation & Warnings.
Story 5.3: XML Generation for All Publication Types.
"""

from django.urls import path

from doi_portal.crossref.views import GenerateXMLView
from doi_portal.crossref.views import IssueValidationView

app_name = "crossref"

urlpatterns = [
    # Story 5.2: Pre-generation validation
    path(
        "issues/<int:pk>/validate/",
        IssueValidationView.as_view(),
        name="issue-validate",
    ),
    # Story 5.3: XML generation
    path(
        "issues/<int:pk>/generate/",
        GenerateXMLView.as_view(),
        name="issue-generate",
    ),
]
