"""
Crossref models.

Story 5.6: XML Download - Export History Tracking.
Component support: export_type discriminator + component_group FK.
"""

from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import gettext_lazy as _

__all__ = [
    "CrossrefExport",
    "ExportType",
]


class ExportType(models.TextChoices):
    """Export type discriminator for CrossrefExport."""

    ISSUE = "ISSUE", _("Izdanje")
    COMPONENT_GROUP = "COMPONENT_GROUP", _("Grupa komponenti")


class CrossrefExport(models.Model):
    """
    Tracks XML export history for an issue or component group.

    Story 5.6: XML Download - Export History Tracking.
    Each download creates a record preserving the XML state at export time.
    Supports both Issue and ComponentGroup exports via export_type discriminator.
    """

    issue = models.ForeignKey(
        "issues.Issue",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="crossref_exports",
        verbose_name=_("Izdanje"),
    )
    component_group = models.ForeignKey(
        "components.ComponentGroup",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="crossref_exports",
        verbose_name=_("Grupa komponenti"),
    )
    export_type = models.CharField(
        _("Tip eksporta"),
        max_length=20,
        choices=ExportType.choices,
        default=ExportType.ISSUE,
    )
    xml_content = models.TextField(
        verbose_name=_("XML sadržaj"),
        help_text=_("Snapshot XML sadržaja u trenutku eksporta"),
    )
    exported_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Eksportovano"),
    )
    exported_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="crossref_exports",
        verbose_name=_("Eksportovao"),
    )
    filename = models.CharField(
        max_length=255,
        verbose_name=_("Ime fajla"),
    )
    xsd_valid_at_export = models.BooleanField(
        null=True,
        verbose_name=_("XSD validan pri eksportu"),
    )

    class Meta:
        verbose_name = _("Crossref eksport")
        verbose_name_plural = _("Crossref eksporti")
        ordering = ["-exported_at"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(issue__isnull=False, component_group__isnull=True, export_type="ISSUE")
                    | models.Q(issue__isnull=True, component_group__isnull=False, export_type="COMPONENT_GROUP")
                ),
                name="crossref_export_exactly_one_source",
            ),
        ]

    def __str__(self):
        return f"{self.filename} ({self.exported_at:%Y-%m-%d %H:%M})"


# Register with auditlog for tracking changes (Story 5.6 requirement)
auditlog.register(CrossrefExport)
