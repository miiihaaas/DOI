"""
Template tags for menu rendering in DOI Portal.

Provides role-based menu rendering for the admin sidebar.
"""

from django import template
from django.urls import NoReverseMatch
from django.urls import reverse

from doi_portal.core.menu import get_menu_for_user

register = template.Library()


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

    # Process each menu item to add URL and active state
    processed_items = []
    for item in menu_items:
        url = None
        is_active = False
        is_disabled = False

        if item["url_name"]:
            try:
                url = reverse(item["url_name"])
                # Check if current path starts with this URL (for nested pages)
                is_active = current_path == url or (
                    url != "/" and current_path.startswith(url)
                )
            except NoReverseMatch:
                is_disabled = True
        else:
            is_disabled = True

        processed_items.append(
            {
                "key": item["key"],
                "label": item["label"],
                "icon": item["icon"],
                "url": url,
                "is_active": is_active,
                "is_disabled": is_disabled,
            },
        )

    return {"menu_items": processed_items, "current_path": current_path}
