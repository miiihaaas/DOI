"""
Core mixins for DOI Portal.

Story 6.3: SoftDeleteMixin and SoftDeleteManager - centralized soft delete functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from doi_portal.users.models import User

__all__ = [
    "SoftDeleteManager",
    "SoftDeleteMixin",
]


class SoftDeleteManager(models.Manager):
    """Manager that filters out soft-deleted records by default."""

    def get_queryset(self):
        """Return queryset excluding soft-deleted records."""
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        """Return queryset including soft-deleted records."""
        return super().get_queryset()

    def deleted_only(self):
        """Return queryset with only soft-deleted records."""
        return super().get_queryset().filter(is_deleted=True)


class SoftDeleteMixin(models.Model):
    """
    Abstract mixin providing soft delete functionality.

    Adds is_deleted, deleted_at, deleted_by fields and
    soft_delete()/restore() methods to any model.
    """

    is_deleted = models.BooleanField(_("Obrisano"), default=False)
    deleted_at = models.DateTimeField(_("Vreme brisanja"), null=True, blank=True)
    deleted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_deleted",
        verbose_name=_("Obrisao"),
    )

    class Meta:
        abstract = True

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
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])
