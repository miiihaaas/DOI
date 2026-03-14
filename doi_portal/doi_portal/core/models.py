"""
Core models for DOI Portal.

Contains global singleton settings and GDPR request tracking.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

__all__ = [
    "GdprRequest",
    "GdprRequestStatus",
    "GdprRequestType",
    "SiteSettings",
]


class GdprRequestType(models.TextChoices):
    ACCESS = "ACCESS", _("Pristup podacima")
    DELETION = "DELETION", _("Brisanje podataka")


class GdprRequestStatus(models.TextChoices):
    PENDING = "PENDING", _("Na čekanju")
    PROCESSING = "PROCESSING", _("U obradi")
    COMPLETED = "COMPLETED", _("Završeno")
    CANCELLED = "CANCELLED", _("Otkazano")


class GdprRequest(models.Model):
    """
    GDPR data request tracking model.

    Story 6.4: Tracks GDPR access/deletion requests with full audit trail.
    """

    requester_email = models.EmailField(_("Email podnosioca"))
    request_type = models.CharField(
        _("Tip zahteva"),
        max_length=20,
        choices=GdprRequestType.choices,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=GdprRequestStatus.choices,
        default=GdprRequestStatus.PENDING,
    )
    notes = models.TextField(_("Napomene"), blank=True)
    received_date = models.DateField(_("Datum prijema"))
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="gdpr_requests_created",
        verbose_name=_("Kreirao"),
    )
    processed_at = models.DateTimeField(_("Obrađeno"), null=True, blank=True)
    processed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gdpr_requests_processed",
        verbose_name=_("Obradio"),
    )
    completed_at = models.DateTimeField(_("Završeno"), null=True, blank=True)
    grace_period_end = models.DateField(
        _("Kraj grace perioda"), null=True, blank=True
    )
    cancellation_reason = models.TextField(_("Razlog otkazivanja"), blank=True)

    class Meta:
        verbose_name = _("GDPR zahtev")
        verbose_name_plural = _("GDPR zahtevi")
        ordering = ["-created_at"]

    def __str__(self):
        return f"GDPR-{self.pk}: {self.requester_email} ({self.get_request_type_display()})"


class SiteSettings(models.Model):
    """
    Singleton model za globalna podesavanja portala.
    Samo jedna instanca postoji u bazi (pk=1).
    """

    # Crossref Depositor podesavanja
    depositor_name = models.CharField(
        _("Naziv deponenta"),
        max_length=255,
        blank=True,
        help_text=_("Naziv organizacije koja salje XML na Crossref (npr. 'Grma')"),
    )
    depositor_email = models.EmailField(
        _("Email deponenta"),
        blank=True,
        help_text=_("Email za Crossref notifikacije o statusu deposit-a"),
    )

    class Meta:
        verbose_name = _("Podešavanja portala")
        verbose_name_plural = _("Podešavanja portala")

    def __str__(self):
        return "Podešavanja portala"

    def save(self, *args, **kwargs):
        """Enforce singleton - always use pk=1."""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of singleton."""
        pass

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
