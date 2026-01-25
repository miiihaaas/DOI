"""
Publisher models for DOI Portal.

This is a placeholder model that will be fully implemented in Epic 2.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Publisher(models.Model):
    """
    Publisher model for DOI Portal.

    Placeholder implementation - full model will be added in Epic 2 (Story 2.1).
    This minimal version exists to support the User.publisher FK relationship.
    """

    name = models.CharField(
        _("Name"),
        max_length=255,
        help_text=_("Publisher name"),
    )
    created_at = models.DateTimeField(
        _("Created at"),
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        _("Updated at"),
        auto_now=True,
    )

    class Meta:
        verbose_name = _("Publisher")
        verbose_name_plural = _("Publishers")

    def __str__(self) -> str:
        return self.name
