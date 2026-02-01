"""
Article models for DOI Portal.

Story 3.1: Article Model & Basic Metadata Entry.
Story 3.2: Author & Affiliation models with Crossref-compliant fields.
Story 3.3: PDF Upload with virus scanning - PdfStatus tracking.
Story 3.6: Editorial Review Process - reviewed_by, reviewed_at, revision_comment, returned_by, returned_at.
Story 3.7: Article Publishing & Withdrawal - published_by, published_at, withdrawal_reason, withdrawn_by, withdrawn_at.
Supports: Article tracking within Issues for Crossref DOI registration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from doi_portal.publishers.models import SoftDeleteManager

from .validators import validate_orcid

if TYPE_CHECKING:
    from doi_portal.users.models import User

__all__ = [
    "Affiliation",
    "Article",
    "ArticleContentType",
    "ArticleStatus",
    "Author",
    "AuthorSequence",
    "ContributorRole",
    "LicenseAppliesTo",
    "PdfStatus",
]


class ArticleStatus(models.TextChoices):
    """Article status choices."""

    DRAFT = "DRAFT", _("Nacrt")
    REVIEW = "REVIEW", _("Na pregledu")
    READY = "READY", _("Spremno za objavu")
    PUBLISHED = "PUBLISHED", _("Objavljeno")
    WITHDRAWN = "WITHDRAWN", _("Povučeno")


class ArticleContentType(models.TextChoices):
    """Crossref publication_type - tip sadrzaja clanka."""

    FULL_TEXT = "full_text", _("Puni tekst")
    ABSTRACT_ONLY = "abstract_only", _("Samo apstrakt")
    BIBLIOGRAPHIC_RECORD = "bibliographic_record", _("Bibliografski zapis")


class LicenseAppliesTo(models.TextChoices):
    """License applies to choices for Crossref."""

    VOR = "vor", _("Verzija zapisa (VoR)")
    AM = "am", _("Prihvaćeni rukopis (AM)")
    TDM = "tdm", _("Rudarenje teksta (TDM)")


class AuthorSequence(models.TextChoices):
    """Crossref sequence atribut za kontributore."""

    FIRST = "first", _("Glavni (first)")
    ADDITIONAL = "additional", _("Ostali (additional)")


class ContributorRole(models.TextChoices):
    """Crossref contributor_role atribut."""

    AUTHOR = "author", _("Autor")
    EDITOR = "editor", _("Urednik")
    CHAIR = "chair", _("Predsedavajući")
    TRANSLATOR = "translator", _("Prevodilac")
    REVIEWER = "reviewer", _("Recenzent")


class PdfStatus(models.TextChoices):
    """PDF processing status."""

    NONE = "none", _("Nema PDF-a")
    UPLOADING = "uploading", _("Otpremanje")
    SCANNING = "scanning", _("Skeniranje")
    CLEAN = "clean", _("Čist")
    INFECTED = "infected", _("Inficiran")
    SCAN_FAILED = "scan_failed", _("Skeniranje neuspešno")


class Article(models.Model):
    """
    Article model for DOI Portal.

    Represents a single article within an issue.
    Part of the hierarchy: Publisher > Publication > Issue > Article.
    Central entity for DOI registration and Crossref XML generation.
    """

    # === CORE FIELDS ===
    issue = models.ForeignKey(
        "issues.Issue",
        on_delete=models.PROTECT,
        related_name="articles",
        verbose_name=_("Izdanje"),
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
    abstract = models.TextField(
        _("Apstrakt"),
        blank=True,
    )
    keywords = models.JSONField(
        _("Ključne reči"),
        default=list,
        blank=True,
    )
    doi_suffix = models.CharField(
        _("DOI sufiks"),
        max_length=100,
    )
    first_page = models.CharField(
        _("Prva stranica"),
        max_length=20,
        blank=True,
    )
    last_page = models.CharField(
        _("Poslednja stranica"),
        max_length=20,
        blank=True,
    )
    article_number = models.CharField(
        _("Broj članka"),
        max_length=50,
        blank=True,
        help_text=_("Za online-only članke"),
    )
    language = models.CharField(
        _("Jezik"),
        max_length=10,
        default="sr",
    )
    publication_type = models.CharField(
        _("Tip sadržaja"),
        max_length=30,
        choices=ArticleContentType.choices,
        default=ArticleContentType.FULL_TEXT,
    )

    # === LICENSE/ACCESS FIELDS ===
    license_url = models.URLField(
        _("URL licence"),
        blank=True,
    )
    license_applies_to = models.CharField(
        _("Licenca se odnosi na"),
        max_length=10,
        choices=LicenseAppliesTo.choices,
        blank=True,
    )
    free_to_read = models.BooleanField(
        _("Slobodan pristup"),
        default=False,
    )
    free_to_read_start_date = models.DateField(
        _("Datum početka slobodnog pristupa"),
        null=True,
        blank=True,
    )

    # === FILE FIELD ===
    pdf_file = models.FileField(
        _("PDF fajl"),
        upload_to="articles/pdfs/",
        blank=True,
    )
    pdf_status = models.CharField(
        _("PDF status"),
        max_length=20,
        choices=PdfStatus.choices,
        default=PdfStatus.NONE,
    )
    pdf_original_filename = models.CharField(
        _("Originalni naziv fajla"),
        max_length=500,
        blank=True,
    )

    # === STATUS ===
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ArticleStatus.choices,
        default=ArticleStatus.DRAFT,
    )

    # === TRACKING ===
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_articles",
        verbose_name=_("Kreirao"),
    )
    submitted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_articles",
        verbose_name=_("Poslao na pregled"),
    )
    submitted_at = models.DateTimeField(
        _("Poslat na pregled"),
        null=True,
        blank=True,
    )
    reviewed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_articles",
        verbose_name=_("Odobrio"),
    )
    reviewed_at = models.DateTimeField(
        _("Odobreno"),
        null=True,
        blank=True,
    )
    revision_comment = models.TextField(
        _("Komentar za doradu"),
        blank=True,
        help_text=_("Komentar urednika pri vraćanju članka na doradu."),
    )
    returned_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="returned_articles",
        verbose_name=_("Vratio na doradu"),
    )
    returned_at = models.DateTimeField(
        _("Vraćeno na doradu"),
        null=True,
        blank=True,
    )
    published_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_articles",
        verbose_name=_("Objavio"),
    )
    published_at = models.DateTimeField(
        _("Objavljeno"),
        null=True,
        blank=True,
    )
    withdrawal_reason = models.TextField(
        _("Razlog povlačenja"),
        blank=True,
        help_text=_("Razlog povlačenja objavljenog članka."),
    )
    withdrawn_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="withdrawn_articles",
        verbose_name=_("Povukao"),
    )
    withdrawn_at = models.DateTimeField(
        _("Povučeno"),
        null=True,
        blank=True,
    )
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
        related_name="deleted_articles",
        verbose_name=_("Obrisao"),
    )

    # === MANAGERS ===
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = _("Članak")
        verbose_name_plural = _("Članci")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["issue", "doi_suffix"],
                condition=models.Q(is_deleted=False),
                name="unique_article_doi_suffix_per_issue",
            ),
        ]

    def __str__(self) -> str:
        return self.title

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
        """Restore a soft-deleted article."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    @property
    def status_badge_class(self) -> str:
        """Return Bootstrap CSS class for status badge."""
        badge_classes = {
            ArticleStatus.DRAFT: "bg-secondary",
            ArticleStatus.REVIEW: "bg-info",
            ArticleStatus.READY: "bg-primary",
            ArticleStatus.PUBLISHED: "bg-success",
            ArticleStatus.WITHDRAWN: "bg-danger",
        }
        return badge_classes.get(self.status, "bg-secondary")

    @property
    def author_count(self) -> int:
        """Return count of authors for this article."""
        return self.authors.count()


class Author(models.Model):
    """
    Author/Contributor model for articles.

    Stores Crossref-compliant contributor data including
    sequence, contributor_role, and ORCID.
    Part of hierarchy: Article -> Author -> Affiliation.
    """

    article = models.ForeignKey(
        "articles.Article",
        on_delete=models.CASCADE,
        related_name="authors",
        verbose_name=_("Članak"),
    )
    # Identification
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

    # Crossref required
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

    # Status
    is_corresponding = models.BooleanField(
        _("Korespondentan autor"),
        default=False,
    )
    order = models.PositiveIntegerField(
        _("Redni broj"),
        default=0,
    )

    class Meta:
        verbose_name = _("Autor")
        verbose_name_plural = _("Autori")
        ordering = ["order"]

    def __str__(self) -> str:
        if self.given_name:
            return f"{self.given_name} {self.surname}"
        return self.surname


class Affiliation(models.Model):
    """
    Affiliation model for authors.

    Stores institution data with optional ROR ID for Crossref.
    One author can have multiple affiliations.
    """

    author = models.ForeignKey(
        "articles.Author",
        on_delete=models.CASCADE,
        related_name="affiliations",
        verbose_name=_("Autor"),
    )
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
    order = models.PositiveIntegerField(
        _("Redni broj"),
        default=0,
    )

    class Meta:
        verbose_name = _("Afilijacija")
        verbose_name_plural = _("Afilijacije")
        ordering = ["order"]

    def __str__(self) -> str:
        if self.department:
            return f"{self.department}, {self.institution_name}"
        return self.institution_name
