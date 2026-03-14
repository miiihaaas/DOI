"""
Publisher models for DOI Portal.

Story 2.1: Publisher Model & Admin CRUD
Story 6.3: Refactored to use SoftDeleteMixin from core.mixins
"""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from doi_portal.core.mixins import SoftDeleteManager, SoftDeleteMixin  # noqa: F401

__all__ = [
    "Publisher",
    "SoftDeleteManager",
    "validate_doi_prefix",
]


def validate_doi_prefix(value: str) -> None:
    """
    Validate DOI prefix format: 10.XXXX (minimum 4 digits after 10.).

    Args:
        value: DOI prefix string to validate

    Raises:
        ValidationError: If format is invalid
    """
    pattern = r"^10\.\d{4,}$"
    if not re.match(pattern, value):
        raise ValidationError(
            _("DOI prefiks mora biti u formatu '10.XXXX' (npr. '10.1234')"),
            code="invalid_doi_prefix",
        )


class Publisher(SoftDeleteMixin, models.Model):
    """
    Publisher model for DOI Portal.

    Represents an organization that publishes scientific content.
    Each publisher has a unique DOI prefix for DOI registration.
    """

    # Basic info
    name = models.CharField(
        _("Naziv"),
        max_length=255,
        help_text=_("Naziv izdavača"),
    )
    slug = models.SlugField(
        _("Slug"),
        max_length=255,
        unique=True,
        blank=True,  # Auto-generated
        help_text=_("URL-friendly verzija naziva"),
    )
    description = models.TextField(
        _("Opis"),
        blank=True,
        help_text=_("Opis izdavača"),
    )
    logo = models.ImageField(
        _("Logo"),
        upload_to="publishers/logos/",
        blank=True,
        null=True,
        help_text=_("Logo izdavača (JPG, PNG, SVG, max 2MB)"),
    )

    # Contact info
    contact_email = models.EmailField(
        _("Kontakt email"),
        blank=True,
        help_text=_("Email adresa za kontakt"),
    )
    contact_phone = models.CharField(
        _("Kontakt telefon"),
        max_length=50,
        blank=True,
        help_text=_("Broj telefona za kontakt"),
    )
    website = models.URLField(
        _("Web sajt"),
        blank=True,
        help_text=_("URL web sajta izdavača"),
    )

    # DOI prefix (REQUIRED, UNIQUE)
    doi_prefix = models.CharField(
        _("DOI prefiks"),
        max_length=20,
        unique=True,
        validators=[validate_doi_prefix],
        help_text=_("DOI prefiks u formatu '10.XXXX' (npr. '10.1234')"),
    )

    # Timestamps
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Includes soft-deleted

    class Meta:
        verbose_name = _("Izdavač")
        verbose_name_plural = _("Izdavači")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        """Save publisher, auto-generating slug if not set."""
        # Auto-generate slug from name if not set
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness
            original_slug = self.slug
            counter = 1
            while (
                Publisher.all_objects.filter(slug=self.slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def publication_count(self) -> int:
        """
        Return count of publications for this publisher.

        Returns:
            Number of publications associated with this publisher
        """
        # Will be implemented when Publication model exists (Story 2.3)
        # For now, return 0 or use hasattr check
        if hasattr(self, "publications"):
            return self.publications.count()
        return 0
