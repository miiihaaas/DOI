"""
Article models for DOI Portal.

Story 3.1: Article Model & Basic Metadata Entry.
Supports: Article tracking within Issues for Crossref DOI registration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from doi_portal.publishers.models import SoftDeleteManager

if TYPE_CHECKING:
    from doi_portal.users.models import User

__all__ = [
    "Article",
    "ArticleContentType",
    "ArticleStatus",
    "LicenseAppliesTo",
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
