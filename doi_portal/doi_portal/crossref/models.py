"""
Crossref models.

Story 5.6: XML Download - Export History Tracking.
"""

from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import gettext_lazy as _

__all__ = [
    "CrossrefExport",
]


class CrossrefExport(models.Model):
    """
    Tracks XML export history for an issue.

    Story 5.6: XML Download - Export History Tracking.
    Each download creates a record preserving the XML state at export time.
    """

    issue = models.ForeignKey(
        "issues.Issue",
        on_delete=models.CASCADE,
        related_name="crossref_exports",
        verbose_name=_("Izdanje"),
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

    def __str__(self):
        return f"{self.filename} ({self.exported_at:%Y-%m-%d %H:%M})"


# Register with auditlog for tracking changes (Story 5.6 requirement)
auditlog.register(CrossrefExport)
