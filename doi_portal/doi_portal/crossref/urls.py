"""
Crossref URL configuration.

Story 5.1: Crossref Service Infrastructure.
Story 5.2: Pre-Generation Validation & Warnings.
Story 5.3: XML Generation for All Publication Types.
Story 5.5: XML Preview with Syntax Highlighting.
Story 5.6: XML Download - Export History Tracking.
Story 5.7: Crossref Deposit Workflow Page.
Component support: sa_component workflow routes.
"""

from django.urls import path

from doi_portal.crossref.views import ComponentGroupDepositView
from doi_portal.crossref.views import ComponentGroupValidationView
from doi_portal.crossref.views import CrossrefDepositView
from doi_portal.crossref.views import GenerateComponentXMLView
from doi_portal.crossref.views import GenerateXMLView
from doi_portal.crossref.views import IssueValidationView
from doi_portal.crossref.views import component_download_warning
from doi_portal.crossref.views import component_export_history
from doi_portal.crossref.views import component_export_redownload
from doi_portal.crossref.views import component_mark_deposited
from doi_portal.crossref.views import component_xml_download
from doi_portal.crossref.views import component_xml_download_force
from doi_portal.crossref.views import component_xml_preview
from doi_portal.crossref.views import download_warning
from doi_portal.crossref.views import export_history
from doi_portal.crossref.views import export_redownload
from doi_portal.crossref.views import mark_deposited
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
    # Story 5.7: Crossref Deposit Workflow Page
    path(
        "issues/<int:pk>/deposit/",
        CrossrefDepositView.as_view(),
        name="issue-deposit",
    ),
    path(
        "issues/<int:pk>/mark-deposited/",
        mark_deposited,
        name="mark-deposited",
    ),
    # Component workflow routes
    path(
        "component-groups/<int:pk>/validate/",
        ComponentGroupValidationView.as_view(),
        name="component-group-validate",
    ),
    path(
        "component-groups/<int:pk>/generate/",
        GenerateComponentXMLView.as_view(),
        name="component-group-generate",
    ),
    path(
        "component-groups/<int:pk>/preview/",
        component_xml_preview,
        name="component-xml-preview",
    ),
    path(
        "component-groups/<int:pk>/download/",
        component_xml_download,
        name="component-xml-download",
    ),
    path(
        "component-groups/<int:pk>/download-warning/",
        component_download_warning,
        name="component-download-warning",
    ),
    path(
        "component-groups/<int:pk>/download-force/",
        component_xml_download_force,
        name="component-xml-download-force",
    ),
    path(
        "component-groups/<int:pk>/export-history/",
        component_export_history,
        name="component-export-history",
    ),
    path(
        "component-groups/<int:pk>/deposit/",
        ComponentGroupDepositView.as_view(),
        name="component-group-deposit",
    ),
    path(
        "component-groups/<int:pk>/mark-deposited/",
        component_mark_deposited,
        name="component-mark-deposited",
    ),
    path(
        "component-exports/<int:pk>/redownload/",
        component_export_redownload,
        name="component-export-redownload",
    ),
]
