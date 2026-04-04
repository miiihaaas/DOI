"""
Component models for DOI Portal.

Crossref sa_component support: ComponentGroup, Component, ComponentContributor.
Publisher -> ComponentGroup -> Component -> ComponentContributor hierarchy.
"""

from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from doi_portal.articles.models import AuthorSequence, ContributorRole
from doi_portal.articles.validators import validate_orcid
from doi_portal.core.mixins import SoftDeleteManager, SoftDeleteMixin

__all__ = [
    "Component",
    "ComponentContributor",
    "ComponentGroup",
]


class ComponentGroup(SoftDeleteMixin, models.Model):
    """
    Groups components by parent_doi for batch XML generation.

    Analog to Issue for Articles. Tracks XML generation and deposit status.
    """

    publisher = models.ForeignKey(
        "publishers.Publisher",
        on_delete=models.PROTECT,
        related_name="component_groups",
        verbose_name=_("Izdavač"),
    )
    parent_doi = models.CharField(
        _("Parent DOI"),
        max_length=255,
        help_text=_("Puni DOI roditelja (npr. 10.66117/emce_zapisi.2026.1)"),
    )
    title = models.CharField(
        _("Naslov"),
        max_length=500,
        blank=True,
        help_text=_("Opcioni label za UI prikaz"),
    )

    # XML generation fields
    crossref_xml = models.TextField(
        _("Crossref XML"),
        blank=True,
    )
    xml_generated_at = models.DateTimeField(
        _("XML generisan"),
        null=True,
        blank=True,
    )
    xml_generation_status = models.CharField(
        _("Status generisanja"),
        max_length=20,
        choices=[
            ("pending", _("Na čekanju")),
            ("generating", _("Generisanje")),
            ("completed", _("Završeno")),
            ("failed", _("Neuspešno")),
        ],
        default="pending",
    )

    # XSD validation fields
    xsd_valid = models.BooleanField(
        _("XSD validan"),
        null=True,
        blank=True,
    )
    xsd_errors = models.JSONField(
        _("XSD greške"),
        default=list,
        blank=True,
    )
    xsd_validated_at = models.DateTimeField(
        _("XSD validiran"),
        null=True,
        blank=True,
    )

    # Deposit tracking
    crossref_deposited_at = models.DateTimeField(
        _("Deponovano"),
        null=True,
        blank=True,
    )
    crossref_deposited_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="component_deposits",
        verbose_name=_("Deponovao"),
    )

    # Timestamps
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = _("Grupa komponenti")
        verbose_name_plural = _("Grupe komponenti")
        ordering = ["-created_at"]
        default_manager_name = "objects"
        constraints = [
            models.UniqueConstraint(
                fields=["publisher", "parent_doi"],
                condition=Q(is_deleted=False),
                name="unique_component_group_parent_doi_per_publisher",
            ),
        ]

    def __str__(self):
        return self.title or self.parent_doi

    @property
    def component_count(self):
        """Return number of non-deleted components in this group."""
        return self.components.count()

    @property
    def is_crossref_deposited(self):
        """Check if this group has been deposited to Crossref."""
        return self.crossref_deposited_at is not None

    @property
    def label(self):
        """Return display label for this group."""
        return self.title or f"Komponente za {self.parent_doi}"


class Component(SoftDeleteMixin, models.Model):
    """
    Individual component within a ComponentGroup.

    Represents a supplementary material (audio, video, PDF) with its own DOI.
    """

    component_group = models.ForeignKey(
        ComponentGroup,
        on_delete=models.CASCADE,
        related_name="components",
        verbose_name=_("Grupa komponenti"),
    )
    parent_relation = models.CharField(
        _("Relacija sa roditeljem"),
        max_length=50,
        default="isPartOf",
        help_text=_("Crossref parent_relation atribut"),
    )
    title = models.CharField(
        _("Naslov"),
        max_length=500,
        blank=True,
        help_text=_("Naslov komponente (preporučeno)"),
    )
    description = models.TextField(
        _("Opis"),
        blank=True,
        help_text=_("Crossref description element"),
    )
    format_mime_type = models.CharField(
        _("MIME tip"),
        max_length=100,
        blank=True,
        help_text=_("MIME tip fajla (npr. audio/mpeg, video/mp4, application/pdf)"),
    )
    doi_suffix = models.CharField(
        _("DOI sufiks"),
        max_length=100,
        help_text=_("Sufiks za DOI (kompletni DOI = publisher.doi_prefix + / + doi_suffix)"),
    )
    resource_url = models.URLField(
        _("URL resursa"),
        max_length=500,
        blank=True,
        help_text=_("Auto-generiše se ako je prazno"),
    )

    # Publication date (partial dates supported)
    publication_year = models.PositiveIntegerField(
        _("Godina publikacije"),
        null=True,
        blank=True,
    )
    publication_month = models.PositiveSmallIntegerField(
        _("Mesec publikacije"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    publication_day = models.PositiveSmallIntegerField(
        _("Dan publikacije"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
    )

    # Ordering
    order = models.PositiveIntegerField(
        _("Redosled"),
        default=0,
    )

    # Timestamps
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = _("Komponenta")
        verbose_name_plural = _("Komponente")
        ordering = ["order", "created_at"]
        default_manager_name = "objects"
        constraints = [
            models.UniqueConstraint(
                fields=["component_group", "doi_suffix"],
                condition=Q(is_deleted=False),
                name="unique_component_doi_suffix_per_group",
            ),
        ]

    def __str__(self):
        return self.title or self.doi_suffix

    @property
    def full_doi(self):
        """Return the full DOI string."""
        return f"{self.component_group.publisher.doi_prefix}/{self.doi_suffix}"


class ComponentContributor(SoftDeleteMixin, models.Model):
    """
    Contributor for a Component.

    Same fields as Author model but with FK to Component.
    """

    component = models.ForeignKey(
        Component,
        on_delete=models.CASCADE,
        related_name="contributors",
        verbose_name=_("Komponenta"),
    )
    given_name = models.CharField(
        _("Ime"),
        max_length=255,
        blank=True,
    )
    surname = models.CharField(
        _("Prezime"),
        max_length=255,
    )
    suffix = models.CharField(
        _("Sufiks"),
        max_length=50,
        blank=True,
    )
    email = models.EmailField(
        _("Email"),
        blank=True,
    )
    orcid = models.CharField(
        _("ORCID"),
        max_length=19,
        blank=True,
        validators=[validate_orcid],
    )
    orcid_authenticated = models.BooleanField(
        _("ORCID autentifikovan"),
        default=False,
    )
    sequence = models.CharField(
        _("Redosled"),
        max_length=20,
        choices=AuthorSequence.choices,
        default=AuthorSequence.ADDITIONAL,
    )
    contributor_role = models.CharField(
        _("Uloga"),
        max_length=20,
        choices=ContributorRole.choices,
        default=ContributorRole.AUTHOR,
    )
    order = models.PositiveIntegerField(
        _("Redosled"),
        default=0,
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = _("Kontributor komponente")
        verbose_name_plural = _("Kontributori komponente")
        ordering = ["order"]
        default_manager_name = "objects"

    def __str__(self):
        if self.given_name:
            return f"{self.given_name} {self.surname}"
        return self.surname
