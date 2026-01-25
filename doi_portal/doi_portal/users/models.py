
from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.db.models import EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for DOI Portal.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]

    # NEW: Publisher assignment for row-level permissions (AC#1)
    # String reference - Publisher model created in Epic 2
    publisher = models.ForeignKey(
        "publishers.Publisher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        help_text=_("Publisher assignment for row-level permissions"),
    )

    # NEW: Track last activity for session management (AC#1)
    last_activity = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Last user activity timestamp"),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})
