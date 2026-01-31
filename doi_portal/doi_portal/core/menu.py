"""
Menu configuration for DOI Portal admin panel.

Role-based menu structure for sidebar navigation.
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

# Menu items configuration
# url_name: None means the feature is not yet implemented (will show as disabled)
MENU_ITEMS: dict[str, dict] = {
    "dashboard": {
        "label": "Kontrolna tabla",
        "icon": "bi-house-door",
        "url_name": "dashboard",
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
    },
    "publishers": {
        "label": "Izdavači",
        "icon": "bi-building",
        "url_name": "publishers:list",  # Story 2.1 - Implemented
        "roles": ["Superadmin", "Administrator"],
    },
    "publications": {
        "label": "Publikacije",
        "icon": "bi-journal-text",
        "url_name": "publications:list",  # Story 2.3 - Implemented
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
    },
    "issues": {
        "label": "Izdanja",
        "icon": "bi-collection",
        "url_name": "issues:list",  # Story 2.6 - Implemented
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
    },
    "articles": {
        "label": "Članci",
        "icon": "bi-file-earmark-text",
        "url_name": "articles:list",  # Story 3.1 - Implemented
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
    },
    "my_drafts": {
        "label": "Moji nacrti",
        "icon": "bi-pencil-square",
        "url_name": None,  # Epic 3 - Not implemented yet
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
    },
    "pending_review": {
        "label": "Na čekanju",
        "icon": "bi-hourglass-split",
        "url_name": None,  # Epic 3 - Not implemented yet
        "roles": ["Superadmin", "Administrator", "Urednik"],
    },
    "users": {
        "label": "Korisnici",
        "icon": "bi-people",
        "url_name": "users:manage-list",  # Implemented in Story 1.6
        "roles": ["Superadmin"],
    },
    "system_settings": {
        "label": "Podešavanja sistema",
        "icon": "bi-gear",
        "url_name": None,  # Not implemented yet
        "roles": ["Superadmin"],
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
        }
        for key, item in MENU_ITEMS.items()
        if user_role in item["roles"]
    ]
