"""
Publication models for DOI Portal.

Story 2.3: Publication Model with Type-Specific Fields.
Supports: Journal, Conference proceedings, Book/Monograph, Other.
Each type has specific fields required by Crossref schema 5.4.0.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from doi_portal.publishers.models import Publisher, SoftDeleteManager

from .validators import validate_isbn, validate_issn

if TYPE_CHECKING:
    from doi_portal.users.models import User

__all__ = [
    "Publication",
    "PublicationType",
    "AccessType",
]


class PublicationType(models.TextChoices):
    """Publication type choices for Crossref XML structure selection."""

    JOURNAL = "JOURNAL", _("Časopis")
    CONFERENCE = "CONFERENCE", _("Zbornik")
    BOOK = "BOOK", _("Monografija")
    OTHER = "OTHER", _("Ostalo")


class AccessType(models.TextChoices):
    """Access type choices."""

    OPEN = "OPEN", _("Otvoreni pristup")
    RESTRICTED = "RESTRICTED", _("Ograničeni pristup")


class Publication(models.Model):
    """
    Publication model with type-specific fields for Crossref compliance.

    Supports: Journal, Conference proceedings, Book/Monograph, Other.
    Each type has specific fields required by Crossref schema 5.4.0.
    """

    # === COMMON FIELDS (All types) ===
    title = models.CharField(
        _("Naslov"),
        max_length=500,
        help_text=_("Puni naslov publikacije"),
    )
    slug = models.SlugField(
        _("Slug"),
        max_length=500,
        unique=True,
        blank=True,
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        related_name="publications",
        verbose_name=_("Izdavač"),
    )
    publication_type = models.CharField(
        _("Tip publikacije"),
        max_length=20,
        choices=PublicationType.choices,
        default=PublicationType.JOURNAL,
    )
    description = models.TextField(
        _("Opis"),
        blank=True,
    )
    cover_image = models.ImageField(
        _("Naslovna slika"),
        upload_to="publications/covers/",
        blank=True,
        null=True,
    )
    language = models.CharField(
        _("Jezik"),
        max_length=10,
        default="sr",
        help_text=_("ISO 639-1 kod jezika (npr. 'sr', 'en')"),
    )
    subject_area = models.CharField(
        _("Naučna oblast"),
        max_length=255,
        blank=True,
    )
    access_type = models.CharField(
        _("Tip pristupa"),
        max_length=20,
        choices=AccessType.choices,
        default=AccessType.OPEN,
    )

    # === JOURNAL-SPECIFIC FIELDS ===
    issn_print = models.CharField(
        _("ISSN (štampano)"),
        max_length=9,
        blank=True,
        validators=[validate_issn],
        help_text=_("Format: ####-####"),
    )
    issn_online = models.CharField(
        _("ISSN (online)"),
        max_length=9,
        blank=True,
        validators=[validate_issn],
        help_text=_("Format: ####-####"),
    )
    abbreviation = models.CharField(
        _("Skraćenica"),
        max_length=50,
        blank=True,
        help_text=_("ISO skraćenica časopisa"),
    )
    frequency = models.CharField(
        _("Učestalost izlaženja"),
        max_length=50,
        blank=True,
        help_text=_("npr. 'Kvartalno', 'Godišnje'"),
    )

    # === CONFERENCE-SPECIFIC FIELDS ===
    conference_name = models.CharField(
        _("Naziv konferencije"),
        max_length=500,
        blank=True,
    )
    conference_acronym = models.CharField(
        _("Akronim konferencije"),
        max_length=50,
        blank=True,
    )
    conference_location = models.CharField(
        _("Lokacija konferencije"),
        max_length=255,
        blank=True,
    )
    conference_date = models.DateField(
        _("Datum konferencije"),
        blank=True,
        null=True,
    )
    series_issn = models.CharField(
        _("ISSN serije"),
        max_length=9,
        blank=True,
        validators=[validate_issn],
    )

    # === BOOK-SPECIFIC FIELDS ===
    isbn_print = models.CharField(
        _("ISBN (štampano)"),
        max_length=17,
        blank=True,
        validators=[validate_isbn],
        help_text=_("Format: 978-X-XXXX-XXXX-X"),
    )
    isbn_online = models.CharField(
        _("ISBN (online)"),
        max_length=17,
        blank=True,
        validators=[validate_isbn],
    )
    edition = models.CharField(
        _("Izdanje"),
        max_length=50,
        blank=True,
        help_text=_("npr. '1. izdanje', '2. dopunjeno izdanje'"),
    )
    series_title = models.CharField(
        _("Naslov serije"),
        max_length=500,
        blank=True,
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
        related_name="deleted_publications",
        verbose_name=_("Obrisao"),
    )

    # === MANAGERS ===
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = _("Publikacija")
        verbose_name_plural = _("Publikacije")
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        """Save publication, auto-generating slug if not set."""
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure uniqueness
            original_slug = self.slug
            counter = 1
            while (
                Publication.all_objects.filter(slug=self.slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

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
        """Restore a soft-deleted publication."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    @property
    def issue_count(self) -> int:
        """
        Return count of issues (Story 2.6).

        Returns:
            Number of issues associated with this publication
        """
        if hasattr(self, "issues"):
            return self.issues.count()
        return 0

    @property
    def type_icon(self) -> str:
        """Return Bootstrap icon class for publication type."""
        icons = {
            PublicationType.JOURNAL: "bi-journal-text",
            PublicationType.CONFERENCE: "bi-people",
            PublicationType.BOOK: "bi-book",
            PublicationType.OTHER: "bi-file-earmark",
        }
        return icons.get(self.publication_type, "bi-file-earmark")

    @property
    def type_display(self) -> str:
        """Return display label for publication type."""
        return PublicationType(self.publication_type).label
