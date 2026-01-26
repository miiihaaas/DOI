import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "doi_portal.users"
    verbose_name = _("Users")

    def ready(self):
        """
        Import signal handlers when Django starts.

        This ensures that signal handlers are connected when the application
        is ready. Specifically loads:
        - Session invalidation on password change (Story 1.5)
        """
        with contextlib.suppress(ImportError):
            import doi_portal.users.signals  # noqa: F401, PLC0415
