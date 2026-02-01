"""
Core views for DOI Portal.

DashboardView - Admin dashboard with role-based content (Story 1.7, 3.8).
Story 3.8: Dashboard Statistics & Pending Items with role-based statistics and pending lists.
"""

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from doi_portal.core.menu import get_user_role
from doi_portal.dashboard.services import (
    get_dashboard_statistics,
    get_my_draft_articles,
    get_pending_review_articles,
    get_ready_to_publish_articles,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Admin dashboard with role-based content.

    Story 1.7: Base dashboard shell.
    Story 3.8: Full statistics, pending items, quick actions.

    Displays a Bootstrap 5 admin layout with:
    - Role-based statistic cards (AC#1, #4, #5)
    - Pending review articles (AC#2)
    - Ready to publish articles (AC#3)
    - My drafts section for Bibliotekar (AC#5)
    - Quick actions (AC#8)
    - Empty state messages (AC#7)
    """

    template_name = "dashboard/dashboard.html"

    def _get_role_flags(self) -> dict[str, bool]:
        """
        Get cached role flags for current user.

        Returns:
            Dict with is_admin, is_urednik, is_bibliotekar, has_publisher keys.
        """
        if hasattr(self, "_role_flags"):
            return self._role_flags

        user = self.request.user
        flags = {
            "is_admin": False,
            "is_urednik": False,
            "is_bibliotekar": False,
            "has_publisher": hasattr(user, "publisher") and user.publisher is not None,
        }

        if user.is_superuser:
            flags["is_admin"] = True
        else:
            user_groups = set(user.groups.values_list("name", flat=True))
            if "Administrator" in user_groups or "Superadmin" in user_groups:
                flags["is_admin"] = True
            if "Urednik" in user_groups:
                flags["is_urednik"] = True
            if "Bibliotekar" in user_groups:
                flags["is_bibliotekar"] = True

        self._role_flags = flags
        return flags

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user
        flags = self._get_role_flags()

        # Basic user info
        context["user"] = user
        context["user_role"] = get_user_role(user)
        context["role_flags"] = flags

        # Breadcrumbs - Dashboard is the root
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": None},
        ]

        # Statistics
        context["stats"] = get_dashboard_statistics(user, flags)

        # Pending items based on role
        if flags["is_admin"] or flags["is_urednik"]:
            context["pending_review_articles"] = get_pending_review_articles(
                user, flags
            )
        if flags["is_admin"]:
            context["ready_to_publish_articles"] = get_ready_to_publish_articles(
                user, flags
            )
        if flags["is_bibliotekar"]:
            context["my_draft_articles"] = get_my_draft_articles(user)

        # Quick actions
        context["quick_actions"] = self._get_quick_actions(flags)

        return context

    def _get_quick_actions(self, flags: dict[str, bool]) -> list[dict[str, str]]:
        """
        Return role-appropriate quick action links.

        Args:
            flags: Role flags dict.

        Returns:
            List of action dicts with label, url_name, icon keys.
        """
        actions = []
        if flags["is_admin"]:
            actions = [
                {
                    "label": "Svi članci",
                    "url_name": "articles:list",
                    "icon": "bi-file-earmark-text",
                },
                {
                    "label": "Publikacije",
                    "url_name": "publications:list",
                    "icon": "bi-journal-text",
                },
                {
                    "label": "Izdavači",
                    "url_name": "publishers:list",
                    "icon": "bi-building",
                },
            ]
        elif flags["is_urednik"]:
            actions = [
                {
                    "label": "Članci na pregledu",
                    "url_name": "articles:list",
                    "icon": "bi-hourglass-split",
                },
                {
                    "label": "Izdanja",
                    "url_name": "issues:list",
                    "icon": "bi-collection",
                },
            ]
        elif flags["is_bibliotekar"]:
            actions = [
                {
                    "label": "Novi članak",
                    "url_name": "articles:create",
                    "icon": "bi-plus-circle",
                },
                {
                    "label": "Moji nacrti",
                    "url_name": "articles:list",
                    "icon": "bi-pencil-square",
                },
            ]
        return actions
