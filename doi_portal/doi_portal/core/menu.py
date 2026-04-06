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
# url_name: None means the feature is not yet implemented (will show as disabled)
MENU_ITEMS: dict[str, dict] = {
    # --- Pregled ---
    "dashboard": {
        "label": "Kontrolna tabla",
        "icon": "bi-house-door",
        "url_name": "dashboard",
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
        "section": "Pregled",
    },
    "my_drafts": {
        "label": "Moji nacrti",
        "icon": "bi-pencil-square",
        "url_name": "articles:list",  # Story 3.8 - filter via query param
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
        "section": "Pregled",
    },
    "pending_review": {
        "label": "Na čekanju",
        "icon": "bi-hourglass-split",
        "url_name": "articles:list",  # Story 3.8 - filter via query param
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
    "system_settings": {
        "label": "Podešavanja sistema",
        "icon": "bi-gear",
        "url_name": None,  # Not implemented yet
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
    "sentry_test": {
        "label": "Sentry test",
        "icon": "bi-bug",
        "url_name": "core:sentry-test",
        "roles": ["Superadmin"],
        "section": "Sistem",
    },
}

# Role hierarchy for determining user's effective role
ROLE_HIERARCHY = ["Superadmin", "Administrator", "Urednik", "Bibliotekar"]


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

    return [
        {
            "key": key,
            "label": item["label"],
            "icon": item["icon"],
            "url_name": item["url_name"],
            "roles": item["roles"],
            "section": item.get("section", ""),
        }
        for key, item in MENU_ITEMS.items()
        if user_role in item["roles"]
    ]
