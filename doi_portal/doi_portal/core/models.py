"""
Core models for DOI Portal.

Contains global singleton settings used across the portal.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

__all__ = ["SiteSettings"]


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
