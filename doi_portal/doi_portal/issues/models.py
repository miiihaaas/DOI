"""
Issue models for DOI Portal.

Story 2.6: Issue Model & Admin CRUD.
Supports: Volume/Issue tracking within Publications for Crossref DOI registration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from doi_portal.publications.models import Publication
from doi_portal.publishers.models import SoftDeleteManager

if TYPE_CHECKING:
    from doi_portal.users.models import User

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


class Issue(models.Model):
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
    publication_date = models.DateField(
        _("Datum objave"),
        blank=True,
        null=True,
        help_text=_("Datum objave izdanja"),
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

    # === TIMESTAMPS ===
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)

    # === SOFT DELETE ===
    is_deleted = models.BooleanField(_("Obrisano"), default=False)
    deleted_at = models.DateTimeField(_("Vreme brisanja"), null=True, blank=True)
    deleted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_issues",
        verbose_name=_("Obrisao"),
    )

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

    def __str__(self) -> str:
        return f"{self.publication.title} - Vol. {self.volume}, No. {self.issue_number} ({self.year})"

    def soft_delete(self, user: User | None = None) -> None:
        """
        Perform soft delete instead of actual deletion.

        Args:
            user: User performing the delete operation
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    def restore(self) -> None:
        """Restore a soft-deleted issue."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    @property
    def article_count(self) -> int:
        """
        Return count of articles (placeholder until Story 3.1).

        Returns:
            Number of articles in this issue (0 until Article model exists)
        """
        return 0

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
