"""
Crossref URL configuration.

Story 5.1: Crossref Service Infrastructure.
Story 5.2: Pre-Generation Validation & Warnings.
Story 5.3: XML Generation for All Publication Types.
Story 5.5: XML Preview with Syntax Highlighting.
Story 5.6: XML Download - Export History Tracking.
"""

from django.urls import path

from doi_portal.crossref.views import GenerateXMLView
from doi_portal.crossref.views import IssueValidationView
from doi_portal.crossref.views import download_warning
from doi_portal.crossref.views import export_history
from doi_portal.crossref.views import export_redownload
from doi_portal.crossref.views import xml_download
from doi_portal.crossref.views import xml_download_force
from doi_portal.crossref.views import xml_preview

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
    # Story 5.5: XML preview and download
    path(
        "issues/<int:pk>/preview/",
        xml_preview,
        name="xml-preview",
    ),
    path(
        "issues/<int:pk>/download/",
        xml_download,
        name="xml-download",
    ),
    # Story 5.6: XML Download enhancements
    path(
        "issues/<int:pk>/download-warning/",
        download_warning,
        name="download-warning",
    ),
    path(
        "issues/<int:pk>/download-force/",
        xml_download_force,
        name="xml-download-force",
    ),
    path(
        "exports/<int:pk>/redownload/",
        export_redownload,
        name="export-redownload",
    ),
    path(
        "issues/<int:pk>/export-history/",
        export_history,
        name="export-history",
    ),
]
