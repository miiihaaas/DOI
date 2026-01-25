"""
Core views for DOI Portal.

DashboardView - Admin dashboard placeholder (full implementation in Story 1.7).
"""

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Admin dashboard placeholder.

    Full implementation with role-based content will be in Story 1.7.
    For now, this view requires login and displays a simple welcome message.

    AC#2: Authenticated users are redirected here after login.
    """

    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context
