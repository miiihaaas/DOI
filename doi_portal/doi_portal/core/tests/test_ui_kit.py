"""
Dashboard UI kit tests: shared components, template tags and shell behaviour.

The kit lives in ``templates/components/`` and ``core/templatetags/ui_tags.py``.
"""

from http import HTTPStatus
from pathlib import Path

import pytest
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.paginator import Paginator
from django.template import Context
from django.template import Template
from django.template import TemplateSyntaxError
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.test import Client
from django.test import RequestFactory
from django.urls import reverse

from doi_portal.core.templatetags.ui_tags import crumb_href
from doi_portal.core.templatetags.ui_tags import sr_plural_form
from doi_portal.core.templatetags.ui_tags import status_tone

User = get_user_model()


def _render(source: str, context: dict | None = None) -> str:
    return Template("{% load ui_tags %}" + source).render(Context(context or {}))


# =============================================================================
# Every template compiles
# =============================================================================


def _all_template_names() -> list[str]:
    names = []
    for template_dir in settings.TEMPLATES[0]["DIRS"]:
        root = Path(template_dir)
        names.extend(
            str(path.relative_to(root))
            for path in sorted(root.rglob("*"))
            if path.suffix in {".html", ".txt", ".xml"}
        )
    return names


@pytest.mark.parametrize("template_name", _all_template_names())
def test_template_compiles(template_name):
    """A syntax error in any project template fails here, not in production."""
    get_template(template_name)


# =============================================================================
# Filters
# =============================================================================


class TestStatusTone:
    @pytest.mark.parametrize(
        ("status", "tone"),
        [
            ("DRAFT", "neutral"),
            ("REVIEW", "pending"),
            ("READY", "info"),
            ("PUBLISHED", "success"),
            ("WITHDRAWN", "danger"),
            ("SCHEDULED", "info"),
            ("ARCHIVE", "neutral"),
            ("PENDING", "pending"),
            ("COMPLETED", "success"),
            ("infected", "danger"),
            ("clean", "success"),
            ("something-else", "neutral"),
            ("", "neutral"),
            (None, "neutral"),
        ],
    )
    def test_mapping(self, status, tone):
        assert status_tone(status) == tone


class TestSerbianPlural:
    FORMS = "članak,članka,članaka"

    @pytest.mark.parametrize(
        ("count", "expected"),
        [
            (0, "članaka"),
            (1, "članak"),
            (2, "članka"),
            (3, "članka"),
            (4, "članka"),
            (5, "članaka"),
            (10, "članaka"),
            (11, "članaka"),
            (12, "članaka"),
            (13, "članaka"),
            (14, "članaka"),
            (15, "članaka"),
            (20, "članaka"),
            (21, "članak"),
            (22, "članka"),
            (24, "članka"),
            (25, "članaka"),
            (100, "članaka"),
            (101, "članak"),
            (102, "članka"),
            (111, "članaka"),
            (112, "članaka"),
            (114, "članaka"),
            (121, "članak"),
            (1001, "članak"),
        ],
    )
    def test_rule(self, count, expected):
        assert sr_plural_form(count, self.FORMS) == expected

    def test_filter_renders_the_noun_only(self):
        html = _render('{{ n }} {{ n|sr_plural:"izdanje,izdanja,izdanja" }}', {"n": 1})
        assert html == "1 izdanje"

    def test_forms_may_be_a_sequence_and_spaces_are_trimmed(self):
        assert sr_plural_form(3, ["grupa", "grupe", "grupa"]) == "grupe"
        assert sr_plural_form(3, "grupa, grupe, grupa") == "grupe"

    def test_string_count_and_garbage(self):
        assert sr_plural_form("21", self.FORMS) == "članak"
        assert sr_plural_form(None, self.FORMS) == "članaka"
        assert sr_plural_form("", self.FORMS) == "članaka"

    def test_not_three_forms_is_returned_unchanged(self):
        assert sr_plural_form(1, "zapisa") == "zapisa"


class TestCrumbHref:
    def test_path_is_returned_unchanged(self):
        assert crumb_href("/dashboard/articles/3/") == "/dashboard/articles/3/"

    def test_url_name_is_reversed(self):
        assert crumb_href("dashboard") == reverse("dashboard")
        assert crumb_href("core:audit-log-list") == reverse("core:audit-log-list")

    @pytest.mark.parametrize("value", [None, "", "no-such-url-name", "articles:detail"])
    def test_unlinkable_values_give_empty_href(self, value):
        assert crumb_href(value) == ""


class TestBreadcrumbsComponent:
    def test_url_names_and_paths_both_render_as_links(self):
        html = render_to_string(
            "components/_breadcrumbs.html",
            {
                "breadcrumbs": [
                    {"label": "Kontrolna tabla", "url": "dashboard"},
                    {"label": "Članci", "url": "/dashboard/articles/"},
                    {"label": "Bez linka", "url": None},
                    {"label": "Trenutna", "url": "/ignored/"},
                ],
            },
        )
        assert f'<a href="{reverse("dashboard")}">Kontrolna tabla</a>' in html
        assert '<a href="/dashboard/articles/">Članci</a>' in html
        assert "<span>Bez linka</span>" in html
        assert 'href="dashboard"' not in html
        assert (
            '<li class="breadcrumb-item active" aria-current="page">Trenutna</li>'
            in html
        )
        assert "/ignored/" not in html

    def test_renders_nothing_without_breadcrumbs(self):
        assert render_to_string("components/_breadcrumbs.html", {}).strip() == ""


# =============================================================================
# Block tags
# =============================================================================


class TestPageHeaderTag:
    def test_title_actions_badge_and_meta(self):
        html = _render(
            '{% pageheader title=title icon="bi-book" badge="Nacrt" '
            'badge_tone=status|status_tone meta="10.1234/abc" %}'
            '<a href="/x/" class="btn btn-primary">Sačuvaj</a>'
            "{% endpageheader %}",
            {"title": "Naslov <b>rada</b>", "status": "DRAFT"},
        )
        assert '<header class="page-header">' in html
        assert "Naslov &lt;b&gt;rada&lt;/b&gt;" in html
        assert html.count("<h1") == 1
        assert 'class="bi bi-book"' in html
        assert "status-badge--neutral" in html
        assert "Nacrt" in html
        assert '<p class="page-header__meta">10.1234/abc</p>' in html
        assert (
            '<div class="page-header__actions">'
            '<a href="/x/" class="btn btn-primary">Sačuvaj</a></div>'
            in html
        )

    def test_no_actions_area_when_body_is_empty(self):
        html = _render('{% pageheader title="Samo naslov" %}   {% endpageheader %}')
        assert "page-header__actions" not in html
        assert "status-badge" not in html
        assert "page-header__meta" not in html

    def test_caller_context_does_not_leak_in(self):
        html = _render(
            '{% pageheader title="A" %}{% endpageheader %}',
            {"meta": "LEAK", "badge": "LEAK", "icon": "bi-leak"},
        )
        assert "LEAK" not in html
        assert "bi-leak" not in html

    def test_body_sees_caller_context(self):
        html = _render(
            '{% pageheader title="A" %}{{ label }}{% endpageheader %}',
            {"label": "Iz konteksta"},
        )
        assert "Iz konteksta" in html

    def test_unknown_argument_is_a_syntax_error(self):
        with pytest.raises(TemplateSyntaxError):
            _render('{% pageheader titel="A" %}{% endpageheader %}')


class TestFilterBarTag:
    def test_controls_count_and_reset(self):
        html = _render(
            '{% filterbar reset_url="/list/" active=status count=42 '
            'count_label="članaka" form_id="f" autosubmit=True %}'
            '<select name="status" class="form-select"></select>'
            "{% endfilterbar %}",
            {"status": "DRAFT"},
        )
        assert '<form method="get" id="f" class="filter-bar"' in html
        assert "data-autosubmit" in html
        assert '<select name="status" class="form-select"></select>' in html
        assert 'href="/list/"' in html
        assert "<strong>42</strong> članaka" in html
        assert 'type="submit"' in html

    @pytest.mark.parametrize(
        ("count", "text"),
        [
            (1, "1</strong> članak<"),
            (3, "3</strong> članka<"),
            (12, "12</strong> članaka<"),
        ],
    )
    def test_count_forms_pick_the_plural(self, count, text):
        html = _render(
            '{% filterbar count=n count_forms="članak,članka,članaka" '
            'count_label="ignorisano" %}{% endfilterbar %}',
            {"n": count},
        )
        assert text in html
        assert "ignorisano" not in html

    def test_reset_hidden_when_no_filter_is_active(self):
        html = _render(
            '{% filterbar reset_url="/list/" active=status count=0 %}'
            "{% endfilterbar %}",
            {"status": ""},
        )
        assert 'href="/list/"' not in html
        assert "<strong>0</strong>" in html
        assert "data-autosubmit" not in html

    def test_count_omitted_when_not_given(self):
        html = _render("{% filterbar %}{% endfilterbar %}", {"count": 99})
        assert "filter-bar__count" not in html


# =============================================================================
# Includes
# =============================================================================


class TestStatusBadge:
    def test_tone_and_label(self):
        html = render_to_string(
            "components/_status_badge.html",
            {"label": "Objavljeno", "tone": "success"},
        )
        assert 'class="status-badge status-badge--success"' in html
        assert "Objavljeno" in html
        assert "status-badge__dot" in html

    def test_default_tone_is_neutral(self):
        html = render_to_string("components/_status_badge.html", {"label": "X"})
        assert "status-badge--neutral" in html

    def test_icon_replaces_dot(self):
        html = render_to_string(
            "components/_status_badge.html",
            {"label": "X", "tone": "info", "icon": "bi-check2"},
        )
        assert "bi-check2" in html
        assert "status-badge__dot" not in html


class TestEmptyState:
    def test_text_only(self):
        html = render_to_string(
            "components/_empty_state.html", {"text": "Nema stavki."},
        )
        assert "Nema stavki." in html
        assert "bi-inbox" in html
        assert "<a " not in html

    def test_primary_action(self):
        html = render_to_string(
            "components/_empty_state.html",
            {
                "text": "Nema članaka.",
                "icon": "bi-file-earmark-text",
                "action_url": "/dashboard/articles/create/",
                "action_label": "Dodaj prvi članak",
                "action_primary": True,
            },
        )
        assert 'href="/dashboard/articles/create/"' in html
        assert "btn-primary" in html
        assert "Dodaj prvi članak" in html


class _KitForm(forms.Form):
    title = forms.CharField(label="Naslov", help_text="Kratak naslov.")
    kind = forms.ChoiceField(
        label="Tip",
        choices=[("a", "A"), ("b", "B")],
        required=False,
        widget=forms.Select(attrs={"class": "form-select custom-x"}),
    )
    active = forms.BooleanField(label="Aktivno", required=False)
    secret = forms.CharField(widget=forms.HiddenInput, required=False)
    notes = forms.CharField(widget=forms.Textarea, required=False)


class TestFieldComponent:
    def _field(self, form, name, **extra):
        return render_to_string(
            "components/_field.html", {"field": form[name], **extra},
        )

    def test_unbound_text_field(self):
        html = self._field(_KitForm(), "title")
        assert '<label class="field__label" for="id_title">Naslov' in html
        assert 'class="form-control"' in html
        assert 'class="field__req"' in html
        assert (
            '<div class="field__help" id="id_title_helptext">Kratak naslov.</div>'
            in html
        )
        assert 'aria-describedby="id_title_helptext"' in html
        assert "is-invalid" not in html
        assert "field__error" not in html

    def test_errors_mark_control_invalid(self):
        html = self._field(_KitForm(data={"title": ""}), "title")
        assert "form-control is-invalid" in html
        assert 'aria-invalid="true"' in html
        assert 'aria-describedby="id_title_helptext id_title_error"' in html
        assert 'id="id_title_error"' in html
        assert "has-error" in html

    def test_existing_widget_classes_are_kept(self):
        html = self._field(_KitForm(), "kind")
        assert 'class="form-select custom-x"' in html
        assert "field__req" not in html

    def test_checkbox_layout(self):
        html = self._field(_KitForm(), "active", **{"class": "col-12"})
        assert "field--check" in html
        assert "col-12" in html
        assert 'class="form-check-input"' in html
        assert html.index("<input") < html.index("<label")
        assert '<label class="form-check-label" for="id_active">Aktivno' in html

    def test_hidden_field_renders_bare(self):
        html = self._field(_KitForm(), "secret")
        assert 'type="hidden"' in html
        assert "<label" not in html

    def test_label_and_help_overrides(self):
        html = self._field(_KitForm(), "title", label="Drugi naziv", help="Druga pomoć")
        assert "Drugi naziv" in html
        assert "Druga pomoć" in html
        assert "Kratak naslov." not in html


    def test_hide_help_drops_the_form_help_text(self):
        html = self._field(_KitForm(), "title", hide_help=True)
        assert "field__help" not in html
        assert "Kratak naslov." not in html
        assert "aria-describedby" not in html

    def test_hide_help_wins_over_help_override(self):
        html = self._field(_KitForm(), "title", help="Druga pomoć", hide_help=True)
        assert "field__help" not in html

    def test_required_marker_override(self):
        assert "field__req" not in self._field(_KitForm(), "title", required=False)
        assert "field__req" in self._field(_KitForm(), "kind", required=True)

    def test_rows_override_only_for_textareas(self):
        html = self._field(_KitForm(), "notes", rows=2)
        assert 'rows="2"' in html
        assert "rows=" not in self._field(_KitForm(), "title", rows=2)


class TestPagination:
    def _html(self, query: str, per_page: int = 20, total: int = 205, **extra):
        request = RequestFactory().get("/dashboard/articles/" + query)
        page_number = request.GET.get("page", 1)
        page_obj = Paginator(range(total), per_page).get_page(page_number)
        return render_to_string(
            "components/_pagination.html",
            {"page_obj": page_obj, "is_paginated": True, **extra},
            request=request,
        )

    def test_summary_range(self):
        html = self._html("?page=2")
        assert "21–40 od 205" in html  # noqa: RUF001

    def test_keeps_filters_and_replaces_page(self):
        html = self._html("?status=DRAFT&sort=-created_at&page=2")
        assert 'href="?status=DRAFT&amp;sort=-created_at&amp;page=3"' in html
        assert 'href="?status=DRAFT&amp;sort=-created_at&amp;page=1"' in html
        assert "page=2&amp;page" not in html

    def test_keeps_multi_valued_params(self):
        html = self._html("?type=a&type=b")
        assert 'href="?type=a&amp;type=b&amp;page=2"' in html

    def test_elides_long_ranges(self):
        html = self._html("?page=6")
        assert "&hellip;" in html
        assert 'aria-current="page"><span class="page-link">6</span>' in html
        assert ">11</a>" in html
        assert ">1</a>" in html
        assert ">3</a>" not in html

    def test_first_page_has_no_previous_link(self):
        html = self._html("")
        assert 'rel="prev"' not in html
        assert 'rel="next"' in html

    def test_single_page_renders_nothing(self):
        assert self._html("", total=5).strip() == ""

    def test_htmx_attributes_are_opt_in(self):
        assert "hx-get" not in self._html("")
        html = self._html("", hx_target="#list")
        assert 'hx-get="?page=2"' in html
        assert 'hx-target="#list"' in html


# =============================================================================
# Shell
# =============================================================================


@pytest.mark.django_db
class TestShell:
    @pytest.fixture
    def content(self, client: Client) -> str:
        user = User.objects.create_user(
            email="shell@test.com",
            password="testpass123!",  # noqa: S106
            is_superuser=True,
        )
        client.force_login(user)
        response = client.get(reverse("dashboard"))
        assert response.status_code == HTTPStatus.OK
        return response.content.decode("utf-8")

    def test_ids_and_hooks_used_by_the_shell_script(self, content):
        for hook in (
            'id="wrapper"',
            'id="sidebar-wrapper"',
            'id="sidebarToggle"',
            'id="sidebarOverlay"',
            "sidebar-collapsed",
            "'toggled'",
        ):
            assert hook in content

    def test_toggle_is_labelled_in_serbian(self, content):
        assert 'aria-label="Prikaži ili sakrij glavni meni"' in content
        assert 'aria-controls="sidebar-wrapper"' in content
        assert "aria-expanded=" in content
        assert "Toggle sidebar" not in content

    def test_brand_links_to_dashboard_and_public_site_is_separate(self, content):
        assert f'<a href="{reverse("dashboard")}" class="sidebar-brand"' in content
        assert f'class="topbar__link" href="{reverse("home")}"' in content
        assert "Javni sajt" in content

    def test_single_breakpoint(self, content):
        """JS and CSS agree on 992px; the old 768px check is gone."""
        assert "(max-width: 991.98px)" in content
        assert "innerWidth <= 768" not in content

    def test_htmx_csrf_header_on_body(self, content):
        assert "<body hx-headers='{\"X-CSRFToken\": \"" in content
        assert 'id="htmxProgress"' in content

    def test_breadcrumb_is_inside_the_top_bar(self, content):
        topbar = content[
            content.index('<header class="topbar">') : content.index("</header>")
        ]
        assert 'class="breadcrumb"' in topbar
        assert "Kontrolna tabla" in topbar

    def test_no_inline_styles_in_sidebar(self, content):
        sidebar = content[
            content.index('<aside id="sidebar-wrapper">') : content.index("</aside>")
        ]
        assert "style=" not in sidebar


@pytest.mark.django_db
class TestFlashMessages:
    def _render(self, level, text, extra_tags=""):
        user = User.objects.create_user(email="flash@test.com", password="testpass123!")  # noqa: S106
        request = RequestFactory().get("/dashboard/")
        request.user = user
        request.session = {}
        request._messages = FallbackStorage(request)  # noqa: SLF001
        messages.add_message(request, level, text, extra_tags=extra_tags)
        html = Template(
            '{% extends "admin_base.html" %}{% block content %}{% endblock %}',
        ).render(
            Context(
                {
                    "request": request,
                    "messages": messages.get_messages(request),
                    "user": user,
                },
            ),
        )
        start = html.index('<div class="admin-messages"')
        return html[start : html.index("<main", start)]

    def test_region_is_polite_live_region(self):
        assert 'aria-live="polite"' in self._render(messages.SUCCESS, "Sačuvano.")

    def test_error_maps_to_danger(self):
        html = self._render(messages.ERROR, "Greška.")
        assert "alert-danger" in html
        assert "alert-error" not in html
        assert 'role="alert"' in html

    def test_success_keeps_its_class(self):
        html = self._render(messages.SUCCESS, "Sačuvano.")
        assert "alert-success" in html
        assert 'aria-label="Zatvori poruku"' in html
