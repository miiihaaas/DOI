"""
Core views for DOI Portal.

DashboardView - Admin dashboard with role-based content (Story 1.7).
"""

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from doi_portal.core.menu import get_user_role


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Admin dashboard with role-based content.

    Displays a Bootstrap 5 admin layout with:
    - Collapsible sidebar navigation (AC#1)
    - Role-based menu items (AC#2, #3, #4)
    - Breadcrumbs
    - Welcome message with user info

    AC#2: Authenticated users are redirected here after login.
    """

    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # User info
        context["user"] = user
        context["user_role"] = get_user_role(user)

        # Breadcrumbs - Dashboard is the root
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": None},  # Current page - no link
        ]

        return context
