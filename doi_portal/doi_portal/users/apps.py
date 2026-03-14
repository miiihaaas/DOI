import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "doi_portal.users"
    verbose_name = _("Users")

    def ready(self):
        """
        Import signal handlers and register with auditlog when Django starts.

        This ensures that signal handlers are connected when the application
        is ready. Specifically loads:
        - Session invalidation on password change (Story 1.5)
        - Publisher permission sync on user save (Story 2.8)
        - Auditlog registration for audit trail (Story 6.1)
        """
        with contextlib.suppress(ImportError):
            import doi_portal.users.signals  # noqa: F401, PLC0415

        # Story 6.1: Register User model with auditlog for audit trail
        try:
            from auditlog.registry import auditlog

            from .models import User

            auditlog.register(User)
        except ImportError:
            pass
