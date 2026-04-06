"""
Monograph models for DOI Portal.

Crossref book monograph support: Monograph, MonographChapter,
contributors, affiliations, funding, and relations.
Publisher -> Monograph -> MonographChapter hierarchy.
Crossref XSD 5.4.0: <book book_type="monograph"> with <book_metadata>
and optional <content_item component_type="chapter">.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from doi_portal.articles.models import (
    INTER_WORK_TYPES,
    INTRA_WORK_TYPES,
    RELATIONSHIP_TYPE_CHOICES,
    AuthorSequence,
    ContributorRole,
    IdentifierType,
    RelationScope,
)
from doi_portal.articles.validators import validate_orcid
from doi_portal.core.mixins import SoftDeleteManager, SoftDeleteMixin
from doi_portal.publications.validators import validate_isbn

__all__ = [
    "ChapterAffiliation",
    "ChapterContributor",
    "ChapterFunding",
    "ChapterRelation",
    "Monograph",
    "MonographAffiliation",
    "MonographChapter",
    "MonographContributor",
    "MonographFunding",
    "MonographRelation",
    "MonographStatus",
]


# =============================================================================
# Status enum
# =============================================================================


class MonographStatus(models.TextChoices):
    """Monograph/chapter status choices."""

    DRAFT = "DRAFT", _("Nacrt")
    PUBLISHED = "PUBLISHED", _("Objavljeno")
    WITHDRAWN = "WITHDRAWN", _("Povučeno")


# =============================================================================
# Abstract base classes (DRY)
# =============================================================================


class BaseContributor(SoftDeleteMixin, models.Model):
    """
    Abstract contributor model with Crossref-compliant fields.

    Uses SoftDeleteMixin (matching Author pattern in articles app).
    """

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
        help_text=_("npr. Jr., III"),
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
        help_text=_("Format: 0000-0000-0000-000X"),
    )
    orcid_authenticated = models.BooleanField(
        _("ORCID autentifikovan"),
        default=False,
    )
    sequence = models.CharField(
        _("Redosled (Crossref)"),
        max_length=20,
        choices=AuthorSequence.choices,
        default=AuthorSequence.ADDITIONAL,
    )
    contributor_role = models.CharField(
        _("Uloga kontributora"),
        max_length=20,
        choices=ContributorRole.choices,
        default=ContributorRole.AUTHOR,
    )
    is_corresponding = models.BooleanField(
        _("Korespondentan autor"),
        default=False,
    )
    order = models.PositiveIntegerField(
        _("Redni broj"),
        default=0,
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ["order"]

    def __str__(self) -> str:
        parts = []
        if self.given_name:
            parts.append(self.given_name)
        parts.append(self.surname)
        return " ".join(parts)


class BaseAffiliation(models.Model):
    """Abstract affiliation model (no SoftDelete, matching Affiliation pattern)."""

    institution_name = models.CharField(
        _("Naziv institucije"),
        max_length=500,
    )
    institution_ror_id = models.URLField(
        _("ROR ID"),
        blank=True,
        help_text=_("https://ror.org/..."),
    )
    department = models.CharField(
        _("Departman"),
        max_length=500,
        blank=True,
    )
    city = models.CharField(
        _("Grad"),
        max_length=255,
        blank=True,
    )
    country = models.CharField(
        _("Država"),
        max_length=255,
        blank=True,
    )
    order = models.PositiveIntegerField(
        _("Redni broj"),
        default=0,
    )

    class Meta:
        abstract = True
        ordering = ["order"]

    def __str__(self) -> str:
        return self.institution_name


class BaseFunding(models.Model):
    """Abstract funding model (no SoftDelete, matching ArticleFunding pattern)."""

    funder_name = models.CharField(
        _("Naziv finansijera"),
        max_length=500,
    )
    funder_doi = models.URLField(
        _("Funder Registry DOI"),
        blank=True,
        help_text=_("DOI iz Open Funder Registry (npr. https://doi.org/10.13039/501100004564)"),
    )
    funder_ror_id = models.URLField(
        _("Funder ROR ID"),
        blank=True,
    )
    award_number = models.CharField(
        _("Broj projekta"),
        max_length=255,
        blank=True,
    )
    order = models.PositiveIntegerField(
        _("Redosled"),
        default=0,
    )

    class Meta:
        abstract = True
        ordering = ["order"]

    def __str__(self) -> str:
        s = self.funder_name
        if self.award_number:
            s += f" — {self.award_number}"
        return s


class BaseRelation(models.Model):
    """Abstract relation model (no SoftDelete, matching ArticleRelation pattern)."""

    relationship_type = models.CharField(
        max_length=50,
        choices=RELATIONSHIP_TYPE_CHOICES,
        verbose_name=_("Tip relacije"),
    )
    relation_scope = models.CharField(
        max_length=20,
        choices=RelationScope.choices,
        verbose_name=_("Opseg relacije"),
        editable=False,
    )
    identifier_type = models.CharField(
        max_length=10,
        choices=IdentifierType.choices,
        default=IdentifierType.DOI,
        verbose_name=_("Tip identifikatora"),
    )
    target_identifier = models.CharField(
        max_length=500,
        verbose_name=_("Identifikator cilja"),
    )
    description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Opis"),
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["order"]

    def __str__(self):
        return f"{self.relationship_type} → {self.target_identifier}"

    def save(self, *args, **kwargs):
        intra_types = {t[0] for t in INTRA_WORK_TYPES}
        self.relation_scope = (
            RelationScope.INTRA_WORK
            if self.relationship_type in intra_types
            else RelationScope.INTER_WORK
        )
        super().save(*args, **kwargs)


# =============================================================================
# Monograph model
# =============================================================================


class Monograph(SoftDeleteMixin, models.Model):
    """
    Monograph (book) model for Crossref DOI registration.

    Represents a single-author or co-authored book with optional chapters.
    Crossref: <book book_type="monograph"> with <book_metadata>.
    """

    # Core metadata
    title = models.CharField(
        _("Naslov"),
        max_length=500,
    )
    subtitle = models.CharField(
        _("Podnaslov"),
        max_length=500,
        blank=True,
    )
    doi_suffix = models.CharField(
        _("DOI sufiks"),
        max_length=255,
        help_text=_("Deo DOI-ja nakon prefiksa izdavača"),
    )
    slug = models.SlugField(
        _("Slug"),
        max_length=500,
        blank=True,
    )

    # Publisher
    publisher = models.ForeignKey(
        "publishers.Publisher",
        on_delete=models.PROTECT,
        related_name="monographs",
        verbose_name=_("Izdavač"),
    )

    # Publication data
    year = models.PositiveIntegerField(
        _("Godina izdanja"),
    )
    publication_place = models.CharField(
        _("Mesto izdanja"),
        max_length=255,
        blank=True,
        help_text=_("Grad gde je monografija objavljena"),
    )
    language = models.CharField(
        _("Jezik"),
        max_length=10,
        blank=True,
        help_text=_("ISO 639 kod (npr. sr, en)"),
    )
    edition_number = models.CharField(
        _("Broj izdanja"),
        max_length=50,
        blank=True,
    )

    # ISBN
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

    # Content
    abstract = models.TextField(
        _("Apstrakt"),
        blank=True,
    )
    keywords = models.JSONField(
        _("Ključne reči"),
        default=list,
        blank=True,
    )
    total_pages = models.PositiveIntegerField(
        _("Ukupan broj strana"),
        null=True,
        blank=True,
    )

    # Status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=MonographStatus.choices,
        default=MonographStatus.DRAFT,
    )

    # License
    license_url = models.URLField(
        _("URL licence"),
        blank=True,
    )
    license_applies_to = models.CharField(
        _("Licenca se odnosi na"),
        max_length=20,
        blank=True,
    )
    free_to_read = models.BooleanField(
        _("Slobodan pristup"),
        default=False,
    )

    # External resource
    use_external_resource = models.BooleanField(
        _("Koristi eksternu landing stranicu"),
        default=False,
    )
    external_landing_url = models.URLField(
        _("Eksterna landing URL"),
        blank=True,
        help_text=_("Ako izdavač ima sopstvenu landing stranicu za monografiju"),
    )

    # === CROSSREF XML GENERATION FIELDS ===
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

    # === XSD VALIDATION FIELDS ===
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

    # === CROSSREF DEPOSIT TRACKING ===
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
        related_name="monograph_deposits",
        verbose_name=_("Deponovao"),
    )

    # Timestamps
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_monographs",
        verbose_name=_("Kreirao"),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = _("Monografija")
        verbose_name_plural = _("Monografije")
        ordering = ["-created_at"]
        default_manager_name = "objects"
        constraints = [
            models.UniqueConstraint(
                fields=["publisher", "doi_suffix"],
                condition=Q(is_deleted=False),
                name="unique_monograph_doi_suffix_per_publisher",
            ),
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["publisher"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)[:500]
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        """Cascade soft-delete to chapters and contributors."""
        now = timezone.now()
        self.chapters.update(is_deleted=True, deleted_at=now, deleted_by=user)
        self.contributors.update(is_deleted=True, deleted_at=now, deleted_by=user)
        super().soft_delete(user=user)

    def restore(self):
        """Cascade restore chapters and contributors."""
        MonographChapter.all_objects.filter(monograph=self, is_deleted=True).update(
            is_deleted=False, deleted_at=None, deleted_by=None,
        )
        MonographContributor.all_objects.filter(monograph=self, is_deleted=True).update(
            is_deleted=False, deleted_at=None, deleted_by=None,
        )
        super().restore()

    @property
    def full_doi(self) -> str:
        return f"{self.publisher.doi_prefix}/{self.doi_suffix}"

    @property
    def has_chapters(self) -> bool:
        return self.chapters.exists()

    @property
    def has_xml(self) -> bool:
        return bool(self.crossref_xml)

    @property
    def is_crossref_deposited(self) -> bool:
        return self.crossref_deposited_at is not None

    @property
    def resource_url(self) -> str:
        """Return the Crossref <resource> URL for this monograph."""
        if self.use_external_resource and self.external_landing_url:
            return self.external_landing_url
        return ""  # Set by service with site_url context


# =============================================================================
# MonographChapter model
# =============================================================================


class MonographChapter(SoftDeleteMixin, models.Model):
    """
    Chapter within a monograph.

    Crossref: <content_item component_type="chapter"> within <book>.
    Each chapter has its own DOI.
    """

    monograph = models.ForeignKey(
        Monograph,
        on_delete=models.PROTECT,
        related_name="chapters",
        verbose_name=_("Monografija"),
    )
    title = models.CharField(
        _("Naslov"),
        max_length=500,
    )
    subtitle = models.CharField(
        _("Podnaslov"),
        max_length=500,
        blank=True,
    )
    doi_suffix = models.CharField(
        _("DOI sufiks"),
        max_length=255,
        help_text=_("Deo DOI-ja nakon prefiksa izdavača"),
    )
    first_page = models.CharField(
        _("Prva strana"),
        max_length=20,
        blank=True,
    )
    last_page = models.CharField(
        _("Poslednja strana"),
        max_length=20,
        blank=True,
    )
    abstract = models.TextField(
        _("Apstrakt"),
        blank=True,
    )
    language = models.CharField(
        _("Jezik"),
        max_length=10,
        blank=True,
    )
    order = models.PositiveIntegerField(
        _("Redosled"),
        default=0,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=MonographStatus.choices,
        default=MonographStatus.DRAFT,
    )

    # License
    license_url = models.URLField(
        _("URL licence"),
        blank=True,
    )
    license_applies_to = models.CharField(
        _("Licenca se odnosi na"),
        max_length=20,
        blank=True,
    )
    free_to_read = models.BooleanField(
        _("Slobodan pristup"),
        default=False,
    )

    # Timestamps
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = _("Poglavlje monografije")
        verbose_name_plural = _("Poglavlja monografije")
        ordering = ["order"]
        default_manager_name = "objects"
        constraints = [
            models.UniqueConstraint(
                fields=["monograph", "doi_suffix"],
                condition=Q(is_deleted=False),
                name="unique_chapter_doi_suffix_per_monograph",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.order}. {self.title}"

    @property
    def full_doi(self) -> str:
        return f"{self.monograph.publisher.doi_prefix}/{self.doi_suffix}"


# =============================================================================
# Concrete contributor models
# =============================================================================


class MonographContributor(BaseContributor):
    """Contributor (author/editor) at monograph (book) level."""

    monograph = models.ForeignKey(
        Monograph,
        on_delete=models.CASCADE,
        related_name="contributors",
        verbose_name=_("Monografija"),
    )

    class Meta(BaseContributor.Meta):
        verbose_name = _("Kontributor monografije")
        verbose_name_plural = _("Kontributori monografije")
        default_manager_name = "objects"


class ChapterContributor(BaseContributor):
    """Contributor (author/editor) at chapter level."""

    chapter = models.ForeignKey(
        MonographChapter,
        on_delete=models.CASCADE,
        related_name="contributors",
        verbose_name=_("Poglavlje"),
    )

    class Meta(BaseContributor.Meta):
        verbose_name = _("Kontributor poglavlja")
        verbose_name_plural = _("Kontributori poglavlja")
        default_manager_name = "objects"


# =============================================================================
# Concrete affiliation models
# =============================================================================


class MonographAffiliation(BaseAffiliation):
    """Affiliation for a monograph-level contributor."""

    contributor = models.ForeignKey(
        MonographContributor,
        on_delete=models.CASCADE,
        related_name="affiliations",
        verbose_name=_("Kontributor"),
    )

    class Meta(BaseAffiliation.Meta):
        verbose_name = _("Afilijacija kontributora monografije")
        verbose_name_plural = _("Afilijacije kontributora monografije")


class ChapterAffiliation(BaseAffiliation):
    """Affiliation for a chapter-level contributor."""

    contributor = models.ForeignKey(
        ChapterContributor,
        on_delete=models.CASCADE,
        related_name="affiliations",
        verbose_name=_("Kontributor"),
    )

    class Meta(BaseAffiliation.Meta):
        verbose_name = _("Afilijacija kontributora poglavlja")
        verbose_name_plural = _("Afilijacije kontributora poglavlja")


# =============================================================================
# Concrete funding models
# =============================================================================


class MonographFunding(BaseFunding):
    """Funding information at monograph (book) level."""

    monograph = models.ForeignKey(
        Monograph,
        on_delete=models.CASCADE,
        related_name="fundings",
        verbose_name=_("Monografija"),
    )

    class Meta(BaseFunding.Meta):
        verbose_name = _("Finansiranje monografije")
        verbose_name_plural = _("Finansiranja monografije")


class ChapterFunding(BaseFunding):
    """Funding information at chapter level."""

    chapter = models.ForeignKey(
        MonographChapter,
        on_delete=models.CASCADE,
        related_name="fundings",
        verbose_name=_("Poglavlje"),
    )

    class Meta(BaseFunding.Meta):
        verbose_name = _("Finansiranje poglavlja")
        verbose_name_plural = _("Finansiranja poglavlja")


# =============================================================================
# Concrete relation models
# =============================================================================


class MonographRelation(BaseRelation):
    """Relation metadata at monograph (book) level."""

    monograph = models.ForeignKey(
        Monograph,
        on_delete=models.CASCADE,
        related_name="relations",
        verbose_name=_("Monografija"),
    )

    class Meta(BaseRelation.Meta):
        verbose_name = _("Relacija monografije")
        verbose_name_plural = _("Relacije monografije")


class ChapterRelation(BaseRelation):
    """Relation metadata at chapter level."""

    chapter = models.ForeignKey(
        MonographChapter,
        on_delete=models.CASCADE,
        related_name="relations",
        verbose_name=_("Poglavlje"),
    )

    class Meta(BaseRelation.Meta):
        verbose_name = _("Relacija poglavlja")
        verbose_name_plural = _("Relacije poglavlja")
