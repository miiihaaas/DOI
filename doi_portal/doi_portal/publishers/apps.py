from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PublishersConfig(AppConfig):
    """App configuration for publishers."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "doi_portal.publishers"
    verbose_name = _("Publishers")
