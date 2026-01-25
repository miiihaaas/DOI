from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    """App configuration for core utilities."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "doi_portal.core"
    verbose_name = _("Core")
