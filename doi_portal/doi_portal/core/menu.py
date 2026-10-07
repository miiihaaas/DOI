"""
Menu configuration for DOI Portal admin panel.

Role-based menu structure for sidebar navigation with logical sections.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from doi_portal.users.models import User

__all__ = [
    "MENU_ITEMS",
    "ROLE_HIERARCHY",
    "get_menu_for_user",
    "get_user_role",
]

# Menu items configuration, grouped by logical sections.
#
# Keys per item:
#   label, icon, roles, section  - as before
#   url_name    - URL name to reverse; None means the feature is not implemented
#                 yet (rendered as a visibly unavailable, non-clickable entry)
#   query       - optional dict of GET params appended to the URL. An item with
#                 ``query`` is only "active" when the request path equals its URL
#                 *and* every listed param matches the request's query string.
#   exact       - optional bool; when True the item is active only on an exact
#                 path match (no prefix matching for nested pages)
#   requires_publisher - optional bool; when True the item is hidden from
#                 non-admin roles that have no publisher assigned
#
# Active-state resolution lives in ``core/templatetags/menu_tags.py``: among all
# matching items only the single most specific one is highlighted.
MENU_ITEMS: dict[str, dict] = {
    # --- Pregled ---
    "dashboard": {
        "label": "Kontrolna tabla",
        "icon": "bi-house-door",
        "url_name": "dashboard",
        "exact": True,
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
        "section": "Pregled",
    },
    "my_drafts": {
        "label": "Moji nacrti",
        "icon": "bi-pencil-square",
        "url_name": "articles:list",
        # mine=1 -> ArticleListView shows only articles created by the user,
        # the same set the dashboard "Moji nacrti" count is based on.
        "query": {"status": "DRAFT", "mine": "1"},
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
        "section": "Pregled",
    },
    "pending_review": {
        "label": "Na pregledu",
        "icon": "bi-hourglass-split",
        "url_name": "articles:list",
        "query": {"status": "REVIEW"},
        "roles": ["Superadmin", "Administrator", "Urednik"],
        "section": "Pregled",
    },
    # --- Sadržaj ---
    "publications": {
        "label": "Publikacije",
        "icon": "bi-journal-text",
        "url_name": "publications:list",
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
        "section": "Sadržaj",
    },
    "issues": {
        "label": "Izdanja",
        "icon": "bi-collection",
        "url_name": "issues:list",
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
        "section": "Sadržaj",
    },
    "articles": {
        "label": "Članci",
        "icon": "bi-file-earmark-text",
        "url_name": "articles:list",
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
        "section": "Sadržaj",
    },
    "monographs": {
        "label": "Monografije",
        "icon": "bi-book",
        "url_name": "monographs:list",
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
        "section": "Sadržaj",
    },
    "component_groups": {
        "label": "Komponente",
        "icon": "bi-puzzle",
        "url_name": "components:group-list",
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
        "section": "Sadržaj",
    },
    "conference_wizard": {
        "label": "Registracija konferencije",
        "icon": "bi-megaphone",
        "url_name": "wizard:conference-start",
        # Mirrors the permission check in wizard.views.wizard_start
        "requires_publisher": True,
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
        "section": "Sadržaj",
    },
    # --- Upravljanje ---
    "publishers": {
        "label": "Izdavači",
        "icon": "bi-building",
        "url_name": "publishers:list",
        "roles": ["Superadmin", "Administrator"],
        "section": "Upravljanje",
    },
    "users": {
        "label": "Korisnici",
        "icon": "bi-people",
        "url_name": "users:manage-list",
        "roles": ["Superadmin"],
        "section": "Upravljanje",
    },
    # --- Sistem ---
    "audit_log": {
        "label": "Revizioni log",
        "icon": "bi-clock-history",
        "url_name": "core:audit-log-list",
        "roles": ["Superadmin"],
        "section": "Sistem",
    },
    "deleted_items": {
        "label": "Obrisane stavke",
        "icon": "bi-trash",
        "url_name": "core:deleted-items",
        "roles": ["Superadmin"],
        "section": "Sistem",
    },
    "gdpr_requests": {
        "label": "GDPR zahtevi",
        "icon": "bi-shield-lock",
        "url_name": "core:gdpr-request-list",
        "roles": ["Superadmin"],
        "section": "Sistem",
    },
    "sentry_test": {
        "label": "Sentry test",
        "icon": "bi-bug",
        "url_name": "core:sentry-test",
        "roles": ["Superadmin"],
        "section": "Sistem",
    },
    "system_health": {
        "label": "Zdravlje sistema",
        "icon": "bi-heart-pulse",
        "url_name": "core:system-health",
        "roles": ["Superadmin"],
        "section": "Sistem",
    },
    "system_settings": {
        "label": "Podešavanja sistema",
        "icon": "bi-gear",
        "url_name": None,  # Not implemented yet
        "roles": ["Superadmin"],
        "section": "Sistem",
    },
}

# Role hierarchy for determining user's effective role
ROLE_HIERARCHY = ["Superadmin", "Administrator", "Urednik", "Bibliotekar"]

# Roles that are not tied to a single publisher
ADMIN_ROLES = frozenset({"Superadmin", "Administrator"})


def get_user_role(user: User) -> str | None:
    """
    Determine the user's highest role based on group membership.

    Args:
        user: The User object

    Returns:
        The role name or None if no valid role found.
    """
    if not user.is_authenticated:
        return None

    # is_superuser implies Superadmin role
    if user.is_superuser:
        return "Superadmin"

    # Check group membership in hierarchy order
    user_groups = set(user.groups.values_list("name", flat=True))

    for role in ROLE_HIERARCHY:
        if role in user_groups:
            return role

    return None


def get_menu_for_user(user: User) -> Sequence[dict]:
    """
    Return menu items visible to the given user based on their role.

    Args:
        user: The User object

    Returns:
        List of menu items the user can access.
    """
    user_role = get_user_role(user)

    if not user_role:
        return []

    is_admin = user_role in ADMIN_ROLES
    has_publisher = bool(getattr(user, "publisher", None))

    return [
        {
            "key": key,
            "label": item["label"],
            "icon": item["icon"],
            "url_name": item["url_name"],
            "roles": item["roles"],
            "section": item.get("section", ""),
            "query": item.get("query") or {},
            "exact": bool(item.get("exact", False)),
        }
        for key, item in MENU_ITEMS.items()
        if user_role in item["roles"]
        and (not item.get("requires_publisher") or is_admin or has_publisher)
    ]
