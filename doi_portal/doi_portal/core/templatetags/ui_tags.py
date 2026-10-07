"""
Shared UI kit template tags for the dashboard (everything on admin_base.html).

Load with ``{% load ui_tags %}``.

Block tags
----------
``{% pageheader title=... %}...actions...{% endpageheader %}``
    Page title row. Renders ``components/_page_header.html``; the tag body
    becomes the actions area.

``{% filterbar reset_url=... count=... %}...controls...{% endfilterbar %}``
    One-row list toolbar. Renders ``components/_filter_bar.html``; the tag body
    becomes the controls area.

Simple tags and filters
-----------------------
``{{ status_code|status_tone }}``   status code -> badge tone
``{{ count|sr_plural:"članak,članka,članaka" }}``  Serbian noun form for a number
``{{ crumb.url|crumb_href }}``      URL, URL name or empty -> href or ""
``{% elided_pages page_obj as pages %}``  page numbers with gaps (None)
``{% field_control field help %}``  bound field -> control HTML with classes
``{% field_help field help hide_help as text %}``   help text to show (or "")
``{% field_required field required as flag %}``     show the "*" marker?
``{{ field|field_kind }}``          bound field -> input/select/check/choices/file
"""

from __future__ import annotations

from django import forms
from django import template
from django.template.base import token_kwargs
from django.urls import NoReverseMatch
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()


# =============================================================================
# Block tags: {% pageheader %} and {% filterbar %}
# =============================================================================


class _ComponentBlockNode(template.Node):
    """Render a component template with the tag body passed in as one variable."""

    def __init__(self, template_name, body_var, defaults, nodelist, kwargs):
        self.template_name = template_name
        self.body_var = body_var
        self.defaults = defaults
        self.nodelist = nodelist
        self.kwargs = kwargs

    def render(self, context):
        values = dict(self.defaults)
        values.update(
            {name: value.resolve(context) for name, value in self.kwargs.items()},
        )
        # The body is rendered in the caller's context, so it is already escaped.
        values[self.body_var] = mark_safe(self.nodelist.render(context).strip())  # noqa: S308
        component = context.template.engine.get_template(self.template_name)
        # Isolated context: caller variables named "title", "count" etc. must
        # not leak into the component.
        return component.render(context.new(values))


def _parse_component_block(parser, token, *, allowed):
    bits = token.split_contents()
    tag_name = bits[0]
    remaining = bits[1:]
    kwargs = token_kwargs(remaining, parser)
    if remaining:
        msg = f"{{% {tag_name} %}} accepts only keyword arguments, got {remaining[0]!r}"
        raise template.TemplateSyntaxError(msg)
    unknown = sorted(set(kwargs) - set(allowed))
    if unknown:
        msg = (
            f"{{% {tag_name} %}} got unknown argument(s) {', '.join(unknown)}; "
            f"allowed: {', '.join(sorted(allowed))}"
        )
        raise template.TemplateSyntaxError(msg)
    nodelist = parser.parse((f"end{tag_name}",))
    parser.delete_first_token()
    return nodelist, kwargs


PAGE_HEADER_DEFAULTS = {
    "title": "",
    "icon": "",
    "badge": "",
    "badge_tone": "neutral",
    "meta": "",
}


@register.tag("pageheader")
def do_pageheader(parser, token):
    """
    Page title row with an actions area.

    Usage::

        {% pageheader title=article.title icon="bi-file-earmark-text"
                      badge=article.get_status_display
                      badge_tone=article.status|status_tone
                      meta=article.doi %}
          <a href="..." class="btn btn-outline-secondary">Izmeni</a>
          <a href="..." class="btn btn-primary">Objavi</a>
        {% endpageheader %}

    Arguments (all keyword, all optional except title):
        title       page title (h1); pass a safe string to allow markup
        icon        Bootstrap Icons class, e.g. "bi-journal-text"
        badge       status label shown next to the title
        badge_tone  neutral | pending | success | danger | info
        meta        one short line under the title (DOI, ISSN, parent, ...)
    """
    nodelist, kwargs = _parse_component_block(
        parser,
        token,
        allowed=PAGE_HEADER_DEFAULTS,
    )
    return _ComponentBlockNode(
        "components/_page_header.html",
        "actions",
        PAGE_HEADER_DEFAULTS,
        nodelist,
        kwargs,
    )


FILTER_BAR_DEFAULTS = {
    "action": "",
    "reset_url": "",
    "active": False,
    "count": None,
    "count_label": "",
    "count_forms": "",
    "form_id": "",
    "autosubmit": False,
    "label": "Filteri",
}


@register.tag("filterbar")
def do_filterbar(parser, token):
    """
    One-row list toolbar: controls + apply + reset + result count.

    Usage::

        {% filterbar reset_url=list_url active=current_status
                     count=page_obj.paginator.count
                     count_forms="članak,članka,članaka"
                     autosubmit=True %}
          <div class="filter-bar__search">...</div>
          <select name="status" class="form-select" aria-label="Status">...</select>
        {% endfilterbar %}

    Arguments (all keyword, all optional):
        action       form action; default "" (current URL)
        reset_url    href for the "Poništi" link; link is shown only when
                     ``active`` is truthy
        active       truthy when any filter is applied
        count        number of results; omitted when None
        count_forms  three comma-separated forms of the noun after the count,
                     e.g. "članak,članka,članaka" (1 / 2-4 / 0 and 5+); the
                     right one is picked with ``sr_plural``
        count_label  fixed text after the count; only for nouns that do not
                     inflect. ``count_forms`` wins when both are given
        form_id      id attribute for the <form>
        autosubmit   True: selects/checkboxes/dates submit on change and the
                     apply button is only shown to keyboard users on focus
        label        aria-label of the form; default "Filteri"
    """
    nodelist, kwargs = _parse_component_block(
        parser,
        token,
        allowed=FILTER_BAR_DEFAULTS,
    )
    return _ComponentBlockNode(
        "components/_filter_bar.html",
        "controls",
        FILTER_BAR_DEFAULTS,
        nodelist,
        kwargs,
    )


# =============================================================================
# Serbian plural
# =============================================================================

_PLURAL_FORM_COUNT = 3
_PAUCAL_MAX = 4
_TEENS = range(11, 15)


def sr_plural_form(count, forms) -> str:
    """
    Pick the Serbian noun form that goes with ``count``.

    ``forms`` is ``"članak,članka,članaka"`` (or a 3-item sequence):

    * form 1 - last digit 1, except 11           (1, 21, 101 članak)
    * form 2 - last digit 2-4, except 12-14      (2, 4, 22 članka)
    * form 3 - everything else                   (0, 5-20, 25, 111 članaka)

    Anything that is not exactly three forms is returned unchanged, and a
    count that is not a whole number gets form 3.
    """
    if isinstance(forms, str):
        parts = [part.strip() for part in forms.split(",")]
    else:
        parts = [str(part) for part in forms]
    if len(parts) != _PLURAL_FORM_COUNT:
        return forms if isinstance(forms, str) else " ".join(parts)
    one, few, many = parts
    try:
        number = abs(int(count))
    except (TypeError, ValueError):
        return many
    last_two = number % 100
    last = number % 10
    if last_two in _TEENS:
        return many
    if last == 1:
        return one
    if 2 <= last <= _PAUCAL_MAX:  # noqa: PLR2004
        return few
    return many


@register.filter
def sr_plural(count, forms) -> str:
    """``{{ count|sr_plural:"izdanje,izdanja,izdanja" }}`` -> noun only (no number)."""
    return sr_plural_form(count, forms)


# =============================================================================
# Status tone
# =============================================================================

TONES = ("neutral", "pending", "success", "danger", "info")

# Status code (upper-cased) -> badge tone. Covers ArticleStatus, IssueStatus,
# MonographStatus, GdprRequestStatus and PdfStatus.
STATUS_TONES = {
    "DRAFT": "neutral",
    "REVIEW": "pending",
    "READY": "info",
    "SCHEDULED": "info",
    "PUBLISHED": "success",
    "WITHDRAWN": "danger",
    "ARCHIVE": "neutral",
    "PENDING": "pending",
    "PROCESSING": "info",
    "COMPLETED": "success",
    "CANCELLED": "neutral",
    "NONE": "neutral",
    "UPLOADING": "info",
    "SCANNING": "info",
    "CLEAN": "success",
    "INFECTED": "danger",
    "SCAN_FAILED": "danger",
}


@register.filter
def status_tone(status) -> str:
    """
    Map a status code to a badge tone.

    ``{{ article.status|status_tone }}`` -> "neutral" / "pending" / "success" /
    "danger" / "info". Unknown codes map to "neutral".
    """
    return STATUS_TONES.get(str(status or "").upper(), "neutral")


# =============================================================================
# Breadcrumbs
# =============================================================================


@register.filter
def crumb_href(value) -> str:
    """
    Turn a breadcrumb ``url`` value into an href.

    Views pass three different things as ``crumb["url"]``: a real path
    (``reverse(...)``), a URL *name* (``"dashboard"``, ``"core:audit-log-list"``)
    or nothing (``None`` / ``""``). Returns the path, the reversed name, or ""
    when there is nothing to link to (including names that cannot be reversed
    without arguments).
    """
    if not value:
        return ""
    value = str(value)
    if value.startswith(("/", "?", "#", "http://", "https://")):
        return value
    try:
        return reverse(value)
    except NoReverseMatch:
        return ""


# =============================================================================
# Pagination
# =============================================================================


@register.simple_tag
def elided_pages(page_obj, on_each_side: int = 1, on_ends: int = 1) -> list:
    """
    Page numbers to show in a pager, with ``None`` marking a gap.

    ``{% elided_pages page_obj as pages %}`` -> ``[1, None, 4, 5, 6, None, 12]``
    """
    paginator = getattr(page_obj, "paginator", None)
    if paginator is None:
        return []
    return [
        None if page == paginator.ELLIPSIS else page
        for page in paginator.get_elided_page_range(
            page_obj.number,
            on_each_side=on_each_side,
            on_ends=on_ends,
        )
    ]


# =============================================================================
# Form fields
# =============================================================================


@register.filter
def field_kind(bound_field) -> str:
    """
    Classify a bound field by how it has to be laid out.

    Returns one of: "hidden", "check" (single checkbox), "choices" (radio group
    or checkbox list), "select", "file", "input".
    """
    widget = bound_field.field.widget
    if bound_field.is_hidden:
        return "hidden"
    if isinstance(widget, forms.CheckboxInput):
        return "check"
    if isinstance(widget, (forms.RadioSelect, forms.CheckboxSelectMultiple)):
        return "choices"
    if isinstance(widget, forms.Select):
        return "select"
    if isinstance(widget, forms.FileInput):
        return "file"
    return "input"


_BASE_CONTROL_CLASS = {
    "check": "form-check-input",
    "select": "form-select",
    "file": "form-control",
    "input": "form-control",
}
_KNOWN_CONTROL_CLASSES = {"form-control", "form-select", "form-check-input"}


@register.simple_tag
def field_help(bound_field, help="", hide_help=False):  # noqa: A002, FBT002
    """
    Help text to show under a field: ``""`` when ``hide_help`` is truthy,
    otherwise the ``help`` override, otherwise the form field's ``help_text``.

    ``{% field_help field help hide_help as help_text %}``
    """
    if hide_help:
        return ""
    return help or bound_field.help_text or ""


@register.simple_tag
def field_required(bound_field, required=""):
    """
    Whether to show the "*" marker: the ``required`` override when it is given
    (``True`` / ``False``), otherwise the form field's own ``required``.

    ``{% field_required field required as is_required %}``
    """
    if required in ("", None):
        return bool(bound_field.field.required)
    return bool(required)


@register.simple_tag
def field_control(bound_field, help_text="", rows=""):
    """
    Render the control of a bound field with consistent classes and ARIA.

    * keeps every class/attribute the form already sets on the widget;
    * adds ``form-control`` / ``form-select`` / ``form-check-input`` when the
      widget has none of them;
    * adds ``is-invalid`` and ``aria-invalid`` when the field has errors;
    * points ``aria-describedby`` at ``<auto_id>_helptext`` (when ``help_text``
      is truthy) and ``<auto_id>_error`` (when there are errors);
    * ``rows`` overrides the height of a textarea.
    """
    widget = bound_field.field.widget
    kind = field_kind(bound_field)
    classes = (widget.attrs.get("class") or "").split()

    base_class = _BASE_CONTROL_CLASS.get(kind)
    if base_class and not _KNOWN_CONTROL_CLASSES.intersection(classes):
        classes.append(base_class)

    attrs = {}
    described_by = []
    if help_text and bound_field.auto_id:
        described_by.append(f"{bound_field.auto_id}_helptext")
    if bound_field.errors:
        if "is-invalid" not in classes:
            classes.append("is-invalid")
        attrs["aria-invalid"] = "true"
        if bound_field.auto_id:
            described_by.append(f"{bound_field.auto_id}_error")
    if described_by:
        attrs["aria-describedby"] = " ".join(described_by)
    if classes:
        attrs["class"] = " ".join(classes)
    if rows and isinstance(widget, forms.Textarea):
        attrs["rows"] = rows

    html = bound_field.as_widget(attrs=attrs)
    if not described_by and bound_field.help_text and bound_field.auto_id:
        # Django points aria-describedby at "<id>_helptext" on its own whenever
        # the form field has help_text. With the help hidden that element does
        # not exist, so drop the dangling reference.
        html = mark_safe(  # noqa: S308 - widget output is already safe HTML
            html.replace(f' aria-describedby="{bound_field.auto_id}_helptext"', ""),
        )
    return html
