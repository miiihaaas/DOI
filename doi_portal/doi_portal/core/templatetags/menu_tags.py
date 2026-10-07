"""
Template tags for menu rendering in DOI Portal.

Provides role-based menu rendering for the admin sidebar.

Active-state rules (see ``resolve_active_key``):

* an item matches when the request path equals its URL, or - unless the item is
  ``exact`` - when the path is nested below it (prefix match);
* an item with a ``query`` dict matches only on its exact path and only when
  every listed GET parameter has the listed value;
* out of all matching items exactly one is highlighted: the most specific one
  (longest URL path first, then the most matched query parameters).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlencode

from django import template
from django.urls import NoReverseMatch
from django.urls import reverse

from doi_portal.core.menu import get_menu_for_user

if TYPE_CHECKING:
    from collections.abc import Mapping
    from collections.abc import Sequence

register = template.Library()


def _match_score(  # noqa: PLR0911 - one early return per matching rule
    item: Mapping,
    current_path: str,
    current_query: Mapping,
) -> tuple[int, int] | None:
    """
    Return a specificity score if the item matches the current request.

    Args:
        item: Processed menu item with ``path``, ``query`` and ``exact`` keys.
        current_path: ``request.path``
        current_query: ``request.GET`` (or any mapping of param -> value)

    Returns:
        ``(path_length, matched_query_params)`` or None when there is no match.
    """
    path = item.get("path")
    if not path:
        return None

    query = item.get("query") or {}
    is_same_path = current_path == path

    if query:
        if not is_same_path:
            return None
        if any(current_query.get(key) != str(value) for key, value in query.items()):
            return None
        return (len(path), len(query))

    if is_same_path:
        return (len(path), 0)

    if item.get("exact") or path == "/":
        return None

    prefix = path if path.endswith("/") else f"{path}/"
    if current_path.startswith(prefix):
        return (len(path), 0)

    return None


def resolve_active_key(
    items: Sequence[Mapping],
    current_path: str,
    current_query: Mapping | None = None,
) -> str | None:
    """
    Pick the single menu item to highlight for the current request.

    Args:
        items: Menu items, each with ``key``, ``path``, ``query``, ``exact``.
        current_path: ``request.path``
        current_query: ``request.GET``; None is treated as no parameters.

    Returns:
        The key of the most specific matching item, or None.
    """
    current_query = current_query or {}
    best_key = None
    best_score: tuple[int, int] | None = None

    for item in items:
        score = _match_score(item, current_path, current_query)
        # Strict comparison: on a tie the first item in menu order wins.
        if score is not None and (best_score is None or score > best_score):
            best_key = item["key"]
            best_score = score

    return best_key


@register.inclusion_tag("components/_sidebar_menu.html", takes_context=True)
def render_sidebar_menu(context: dict) -> dict:
    """
    Render sidebar menu based on user role.

    Args:
        context: Template context containing 'request'

    Returns:
        Dict with menu_items list for the inclusion tag.
    """
    request = context["request"]
    user = request.user

    if not user.is_authenticated:
        return {"menu_items": []}

    menu_items = get_menu_for_user(user)
    current_path = request.path

    processed_items = []
    for item in menu_items:
        path = None
        url = None
        query = item.get("query") or {}

        if item["url_name"]:
            try:
                path = reverse(item["url_name"])
            except NoReverseMatch:
                path = None

        if path:
            url = f"{path}?{urlencode(query)}" if query else path

        processed_items.append(
            {
                "key": item["key"],
                "label": item["label"],
                "icon": item["icon"],
                "url": url,
                "path": path,
                "query": query,
                "exact": item.get("exact", False),
                "is_active": False,
                "is_disabled": url is None,
                "section": item.get("section", ""),
            },
        )

    active_key = resolve_active_key(processed_items, current_path, request.GET)
    for item in processed_items:
        item["is_active"] = item["key"] == active_key

    return {"menu_items": processed_items, "current_path": current_path}
