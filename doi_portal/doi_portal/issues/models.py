"""
Issue models for DOI Portal.

Story 2.6: Issue Model & Admin CRUD.
Story 6.3: Refactored to use SoftDeleteMixin from core.mixins.
Supports: Volume/Issue tracking within Publications for Crossref DOI registration.
"""

from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from doi_portal.core.mixins import SoftDeleteManager, SoftDeleteMixin
from doi_portal.publications.models import Publication

__all__ = [
    "Issue",
    "IssueStatus",
]


class IssueStatus(models.TextChoices):
    """Issue status choices."""

    DRAFT = "DRAFT", _("Nacrt")
    SCHEDULED = "SCHEDULED", _("Zakazano")
    PUBLISHED = "PUBLISHED", _("Objavljeno")
    ARCHIVE = "ARCHIVE", _("Arhivirano")


class Issue(SoftDeleteMixin, models.Model):
    """
    Issue model for DOI Portal.

    Represents a single issue (volume/number) within a publication.
    Part of the hierarchy: Publisher > Publication > Issue > Article.
    """

    # === CORE FIELDS ===
    publication = models.ForeignKey(
        Publication,
        on_delete=models.PROTECT,
        related_name="issues",
        verbose_name=_("Publikacija"),
    )
    volume = models.CharField(
        _("Volumen"),
        max_length=20,
        blank=True,
        help_text=_("Volumen izdanja (npr. '1', 'Special')"),
    )
    issue_number = models.CharField(
        _("Broj izdanja"),
        max_length=20,
        blank=True,
        help_text=_("Broj izdanja (npr. '1', 'Supplement')"),
    )
    year = models.PositiveIntegerField(
        _("Godina"),
        help_text=_("Godina izdanja"),
    )
    title = models.CharField(
        _("Naslov"),
        max_length=500,
        blank=True,
        help_text=_("Opcioni naslov izdanja"),
    )
    cover_image = models.ImageField(
        _("Naslovna slika"),
        upload_to="issues/covers/",
        blank=True,
        null=True,
        help_text=_("Naslovna slika izdanja"),
    )
    publication_month = models.PositiveSmallIntegerField(
        _("Mesec objave"),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text=_("Mesec objave izdanja (opciono)"),
    )
    publication_day = models.PositiveSmallIntegerField(
        _("Dan objave"),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text=_("Dan objave izdanja (opciono)"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=IssueStatus.choices,
        default=IssueStatus.DRAFT,
    )

    # === CONFERENCE PROCEEDINGS FIELDS ===
    proceedings_title = models.CharField(
        _("Naslov zbornika"),
        max_length=500,
        blank=True,
        help_text=_("Naslov zbornika (ako se razlikuje od naslova publikacije)"),
    )
    proceedings_publisher_name = models.CharField(
        _("Naziv izdavača zbornika"),
        max_length=255,
        blank=True,
        help_text=_("Naziv izdavača zbornika"),
    )
    proceedings_publisher_place = models.CharField(
        _("Mesto izdavanja"),
        max_length=255,
        blank=True,
        help_text=_("Mesto izdavanja zbornika"),
    )

    # === CROSSREF XML GENERATION FIELDS (Story 5.3) ===
    crossref_xml = models.TextField(
        blank=True,
        verbose_name=_("Crossref XML"),
        help_text=_("Generisani Crossref XML sadržaj"),
    )
    xml_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("XML generisan"),
    )
    xml_generation_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", _("Na čekanju")),
            ("generating", _("Generiše se")),
            ("completed", _("Završeno")),
            ("failed", _("Neuspešno")),
        ],
        default="pending",
        verbose_name=_("Status generisanja"),
    )

    # === XSD VALIDATION FIELDS (Story 5.4) ===
    xsd_valid = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_("XSD validan"),
        help_text=_("Da li je XML validan prema Crossref XSD shemi"),
    )
    xsd_errors = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("XSD greške"),
        help_text=_("Lista grešaka XSD validacije"),
    )
    xsd_validated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("XSD validiran"),
    )

    # === CROSSREF DEPOSIT TRACKING (Story 5.7) ===
    crossref_deposited_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Crossref deponovano"),
        help_text=_("Datum i vreme kada je XML deponovan na Crossref"),
    )
    crossref_deposited_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="crossref_deposits",
        verbose_name=_("Deponovao"),
    )

    # === TIMESTAMPS ===
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)

    # === MANAGERS ===
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = _("Izdanje")
        verbose_name_plural = _("Izdanja")
        ordering = ["-year", "-volume", "-issue_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["publication", "volume", "issue_number"],
                condition=models.Q(is_deleted=False),
                name="unique_issue_per_publication",
            ),
        ]

    @property
    def label(self) -> str:
        """Build issue label showing only populated fields (Vol., No.)."""
        parts = []
        if self.volume:
            parts.append(f"Vol. {self.volume}")
        if self.issue_number:
            parts.append(f"No. {self.issue_number}")
        vol_no = ", ".join(parts)
        if vol_no:
            return f"{vol_no} ({self.year})"
        return f"({self.year})"

    def __str__(self) -> str:
        parts = []
        if self.volume:
            parts.append(f"Vol. {self.volume}")
        if self.issue_number:
            parts.append(f"No. {self.issue_number}")
        vol_no = ", ".join(parts)
        if vol_no:
            return f"{self.publication.title} - {vol_no} ({self.year})"
        return f"{self.publication.title} ({self.year})"

    @property
    def article_count(self) -> int:
        """
        Return count of articles in this issue.

        Uses the 'articles' reverse relation from Article model.

        Returns:
            Number of non-deleted articles in this issue
        """
        return self.articles.count()

    @property
    def is_crossref_deposited(self) -> bool:
        """Return True if this issue has been deposited to Crossref."""
        return self.crossref_deposited_at is not None

    @property
    def status_badge_class(self) -> str:
        """Return Bootstrap CSS class for status badge."""
        badge_classes = {
            IssueStatus.DRAFT: "bg-secondary",
            IssueStatus.SCHEDULED: "bg-info",
            IssueStatus.PUBLISHED: "bg-success",
            IssueStatus.ARCHIVE: "bg-warning",
        }
        return badge_classes.get(self.status, "bg-secondary")
