"""
View/template tests for the monograph back office.

Covers the list search, the detail workflow bar, the delete confirmation,
the licence dropdown on the edit forms, CSRF for bare HTMX buttons and the
drag & drop reorder endpoints wired on the edit page.
"""

import json
import re

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from doi_portal.articles.forms import ArticleForm
from doi_portal.monographs.forms import MonographChapterForm
from doi_portal.monographs.forms import MonographForm
from doi_portal.monographs.models import MonographStatus
from doi_portal.publications.tests.factories import PublisherFactory
from doi_portal.users.tests.factories import UserFactory

from .factories import ChapterContributorFactory
from .factories import MonographChapterFactory
from .factories import MonographContributorFactory
from .factories import MonographFactory
from .factories import MonographFundingFactory
from .factories import MonographRelationFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_user():
    return UserFactory(is_superuser=True, is_staff=True)


@pytest.fixture
def admin_client(admin_user):
    client = Client()
    client.force_login(admin_user)
    return client


def _titles(response):
    return [m.title for m in response.context["monographs"]]


# =============================================================================
# List: search + status filter
# =============================================================================


class TestMonographListSearch:
    def test_search_matches_title(self, admin_client):
        MonographFactory(title="Istorija Balkana")
        MonographFactory(title="Uvod u hemiju")

        response = admin_client.get(reverse("monographs:list"), {"q": "balkan"})

        assert response.status_code == 200  # noqa: PLR2004
        assert _titles(response) == ["Istorija Balkana"]
        assert response.context["search_query"] == "balkan"

    def test_search_matches_subtitle(self, admin_client):
        MonographFactory(title="Prva", subtitle="Ogledi o jeziku")
        MonographFactory(title="Druga")

        response = admin_client.get(reverse("monographs:list"), {"q": "ogledi"})

        assert _titles(response) == ["Prva"]

    def test_search_matches_doi_suffix(self, admin_client):
        MonographFactory(title="Prva", doi_suffix="mono.posebna.77")
        MonographFactory(title="Druga", doi_suffix="mono.obicna.01")

        response = admin_client.get(reverse("monographs:list"), {"q": "posebna"})

        assert _titles(response) == ["Prva"]

    def test_search_matches_isbn_print_and_online(self, admin_client):
        MonographFactory(title="Štampana", isbn_print="978-86-7549-123-4")
        MonographFactory(title="Elektronska", isbn_online="978-86-7549-999-1")
        MonographFactory(title="Treća")

        by_print = admin_client.get(reverse("monographs:list"), {"q": "7549-123"})
        by_online = admin_client.get(reverse("monographs:list"), {"q": "7549-999"})

        assert _titles(by_print) == ["Štampana"]
        assert _titles(by_online) == ["Elektronska"]

    def test_search_combines_with_status_filter(self, admin_client):
        MonographFactory(title="Zbornik nacrt", status=MonographStatus.DRAFT)
        MonographFactory(title="Zbornik objavljen", status=MonographStatus.PUBLISHED)

        response = admin_client.get(
            reverse("monographs:list"),
            {"q": "zbornik", "status": MonographStatus.PUBLISHED},
        )

        assert _titles(response) == ["Zbornik objavljen"]

    def test_blank_search_returns_everything(self, admin_client):
        MonographFactory.create_batch(3)

        response = admin_client.get(reverse("monographs:list"), {"q": "   "})

        assert len(response.context["monographs"]) == 3  # noqa: PLR2004
        assert response.context["filters_active"] is False

    def test_search_keeps_publisher_scoping(self):
        own_publisher = PublisherFactory()
        other_publisher = PublisherFactory()
        MonographFactory(title="Zajednička tema A", publisher=own_publisher)
        MonographFactory(title="Zajednička tema B", publisher=other_publisher)
        user = UserFactory(publisher=own_publisher)
        user.groups.add(Group.objects.get_or_create(name="Urednik")[0])
        client = Client()
        client.force_login(user)

        response = client.get(reverse("monographs:list"), {"q": "zajednička"})

        assert _titles(response) == ["Zajednička tema A"]

    def test_search_without_publisher_returns_nothing(self):
        MonographFactory(title="Nevidljiva")
        user = UserFactory()
        client = Client()
        client.force_login(user)

        response = client.get(reverse("monographs:list"), {"q": "nevidljiva"})

        assert _titles(response) == []

    def test_list_renders_search_field_and_status_badge(self, admin_client):
        MonographFactory(title="Vidljiva", status=MonographStatus.PUBLISHED)

        response = admin_client.get(reverse("monographs:list"), {"q": "vidlj"})
        html = response.content.decode()

        assert 'name="q"' in html
        assert 'value="vidlj"' in html
        assert "Poništi" in html
        assert "Nova monografija" in html
        assert "Kreirano" in html
        assert "bi-eye" not in html  # the title is the link to the detail page

    def test_empty_states(self, admin_client):
        empty = admin_client.get(reverse("monographs:list")).content.decode()
        assert "Nema monografija za prikaz." in empty
        assert "Dodaj prvu monografiju" in empty

        MonographFactory(title="Jedina")
        filtered = admin_client.get(
            reverse("monographs:list"), {"q": "ne-postoji"},
        ).content.decode()
        assert "Nema monografija koje odgovaraju filterima." in filtered
        assert "Poništi filtere" in filtered

    def test_pagination_keeps_search_term(self, admin_client):
        MonographFactory.create_batch(25, title="Serija radova")

        response = admin_client.get(reverse("monographs:list"), {"q": "serija"})
        html = response.content.decode()

        assert response.context["page_obj"].paginator.count == 25  # noqa: PLR2004
        assert re.search(
            r'href="\?[^"]*q=serija[^"]*page=2|href="\?[^"]*page=2[^"]*q=serija', html,
        )


# =============================================================================
# Detail: workflow bar
# =============================================================================


class TestMonographDetail:
    def test_publish_is_rendered_once_as_post_form_with_confirm(self, admin_client):
        monograph = MonographFactory(status=MonographStatus.DRAFT)
        MonographChapterFactory(monograph=monograph)

        html = admin_client.get(
            reverse("monographs:detail", args=[monograph.pk]),
        ).content.decode()

        publish_url = reverse("monographs:publish", args=[monograph.pk])
        assert html.count(f'action="{publish_url}"') == 1
        assert "workflow-bar" in html
        assert "data-confirm=" in html
        assert "Sva poglavlja u statusu Nacrt će takođe biti objavljena." in html
        assert "onclick=" not in html
        assert "Brze akcije" not in html
        assert (
            reverse("crossref:monograph-deposit", kwargs={"pk": monograph.pk}) in html
        )
        assert monograph.full_doi in html

    def test_published_monograph_has_no_publish_or_edit(self, admin_client):
        monograph = MonographFactory(status=MonographStatus.PUBLISHED)

        html = admin_client.get(
            reverse("monographs:detail", args=[monograph.pk]),
        ).content.decode()

        assert reverse("monographs:publish", args=[monograph.pk]) not in html
        assert reverse("monographs:update", args=[monograph.pk]) not in html
        assert (
            reverse("crossref:monograph-deposit", kwargs={"pk": monograph.pk}) in html
        )

    def test_publish_post_still_works(self, admin_client):
        monograph = MonographFactory(status=MonographStatus.DRAFT)

        response = admin_client.post(reverse("monographs:publish", args=[monograph.pk]))

        assert response.status_code == 302  # noqa: PLR2004
        monograph.refresh_from_db()
        assert monograph.status == MonographStatus.PUBLISHED

    def test_delete_confirmation_page(self, admin_client):
        monograph = MonographFactory()

        html = admin_client.get(
            reverse("monographs:delete", args=[monograph.pk]),
        ).content.decode()

        assert "Obriši monografiju" in html
        assert "Otkaži" in html
        assert monograph.title in html


# =============================================================================
# 5c: licence dropdown
# =============================================================================


class TestLicenseAppliesToChoices:
    def test_monograph_form_has_same_options_as_article_form(self):
        expected = list(ArticleForm().fields["license_applies_to"].choices)
        actual = list(MonographForm().fields["license_applies_to"].choices)

        assert [value for value, _label in actual] == ["", "vor", "am", "tdm"]
        assert [value for value, _label in actual] == [
            value for value, _label in expected
        ]
        assert [label for _value, label in actual][1:] == [
            label for _value, label in expected
        ][1:]

    def test_chapter_form_has_same_options(self):
        choices = list(MonographChapterForm().fields["license_applies_to"].choices)

        assert [value for value, _label in choices] == ["", "vor", "am", "tdm"]

    def test_field_stays_optional(self):
        assert MonographForm().fields["license_applies_to"].required is False
        assert MonographChapterForm().fields["license_applies_to"].required is False

    def test_rendered_select_is_not_empty_and_keeps_class(self, admin_client):
        html = admin_client.get(reverse("monographs:create")).content.decode()

        select = re.search(
            r'<select name="license_applies_to".*?</select>', html, flags=re.S,
        ).group(0)
        assert select.count("<option") == 4  # noqa: PLR2004
        assert "form-select" in select

    def test_value_is_saved(self, admin_user):
        publisher = PublisherFactory()
        form = MonographForm(
            data={
                "title": "Sa licencom",
                "doi_suffix": "mono.lic.1",
                "year": 2025,
                "publisher": publisher.pk,
                "keywords": "[]",
                "license_applies_to": "vor",
            },
            user=admin_user,
        )

        assert form.is_valid(), form.errors
        assert form.save().license_applies_to == "vor"

    def test_invalid_value_is_rejected(self, admin_user):
        publisher = PublisherFactory()
        form = MonographForm(
            data={
                "title": "Sa licencom",
                "doi_suffix": "mono.lic.2",
                "year": 2025,
                "publisher": publisher.pk,
                "keywords": "[]",
                "license_applies_to": "bogus",
            },
            user=admin_user,
        )

        assert not form.is_valid()
        assert "license_applies_to" in form.errors

    def test_legacy_stored_value_does_not_break_editing(self, admin_client):
        monograph = MonographFactory(license_applies_to="stm-asf")
        url = reverse("monographs:update", args=[monograph.pk])

        html = admin_client.get(url).content.decode()
        assert re.search(r'<option value="stm-asf"[^>]*selected', html)

        response = admin_client.post(
            url,
            {
                "title": monograph.title,
                "doi_suffix": monograph.doi_suffix,
                "year": monograph.year,
                "publisher": monograph.publisher.pk,
                "keywords": "[]",
                "license_applies_to": "stm-asf",
            },
        )

        assert response.status_code == 302, response.context["form"].errors  # noqa: PLR2004
        monograph.refresh_from_db()
        assert monograph.license_applies_to == "stm-asf"

    def test_chapter_form_ids_do_not_collide_with_main_form(self, admin_client):
        monograph = MonographFactory()

        page = admin_client.get(
            reverse("monographs:update", args=[monograph.pk]),
        ).content.decode()
        chapter_form = admin_client.get(
            reverse("monographs:chapter-form", kwargs={"monograph_pk": monograph.pk}),
        ).content.decode()

        assert 'id="id_license_applies_to"' in page
        assert 'id="id_license_applies_to"' not in chapter_form
        assert 'id="id_chapter_license_applies_to"' in chapter_form
        assert 'for="id_chapter_license_applies_to"' in chapter_form
        # POST keys are unchanged
        assert 'name="license_applies_to"' in chapter_form
        assert 'name="title"' in chapter_form
        chapter_ids = set(re.findall(r'\bid="(id_[^"]+)"', chapter_form))
        page_ids = set(re.findall(r'\bid="(id_[^"]+)"', page))
        assert chapter_ids
        assert not chapter_ids & page_ids


# =============================================================================
# 5a: CSRF for bare hx-post buttons
# =============================================================================


class TestHtmxCsrf:
    def _csrf_client(self, user):
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        return client

    def test_bare_hx_post_is_covered_by_body_header(self, admin_user):
        monograph = MonographFactory()
        contributor = MonographContributorFactory(monograph=monograph)
        client = self._csrf_client(admin_user)

        page = client.get(reverse("monographs:update", args=[monograph.pk]))
        html = page.content.decode()

        # The shell puts the token on <body>; HTMX inherits hx-headers.
        body_tag = re.search(r"<body[^>]*>", html).group(0)
        match = re.search(r"hx-headers='(\{[^']*\})'", body_tag)
        assert match, body_tag
        token = json.loads(match.group(1))["X-CSRFToken"]
        assert token

        # The delete button itself sits outside any <form> and has no own header.
        delete_url = reverse(
            "monographs:contributor-delete", kwargs={"pk": contributor.pk},
        )
        button = re.search(
            rf'<button[^>]*hx-post="{re.escape(delete_url)}"[^>]*>', html,
        ).group(0)
        assert "hx-headers" not in button

        # Without the header the endpoint rejects the request ...
        assert client.post(delete_url).status_code == 403  # noqa: PLR2004
        assert monograph.contributors.count() == 1

        # ... with the header the shell emits it goes through.
        response = client.post(delete_url, headers={"X-CSRFToken": token})
        assert response.status_code == 200  # noqa: PLR2004
        assert monograph.contributors.count() == 0


# =============================================================================
# 5b: reorder wiring
# =============================================================================


class TestReorderWiring:
    def test_edit_page_loads_sortable_and_marks_lists(self, admin_client):
        monograph = MonographFactory()
        MonographContributorFactory(monograph=monograph)
        MonographChapterFactory(monograph=monograph)

        html = admin_client.get(
            reverse("monographs:update", args=[monograph.pk]),
        ).content.decode()

        assert "sortablejs" in html
        for name in (
            "contributor-reorder",
            "funding-reorder",
            "relation-reorder",
            "chapter-reorder",
        ):
            url = reverse(f"monographs:{name}", kwargs={"monograph_pk": monograph.pk})
            assert f'data-reorder-url="{url}"' in html
        assert 'id="contributors-container"' in html
        assert 'id="chapters-container"' in html
        assert "data-chapter-id=" in html

    def test_create_page_does_not_load_sortable(self, admin_client):
        html = admin_client.get(reverse("monographs:create")).content.decode()

        assert "sortablejs" not in html

    def test_contributor_reorder_with_json_body_and_csrf_header(self, admin_user):
        monograph = MonographFactory()
        first = MonographContributorFactory(
            monograph=monograph, order=1, surname="Prvi",
        )
        second = MonographContributorFactory(
            monograph=monograph, order=2, surname="Drugi",
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(admin_user)
        page = client.get(
            reverse("monographs:update", args=[monograph.pk]),
        ).content.decode()
        token = json.loads(
            re.search(r"<body[^>]*hx-headers='(\{[^']*\})'", page).group(1),
        )["X-CSRFToken"]

        response = client.post(
            reverse(
                "monographs:contributor-reorder", kwargs={"monograph_pk": monograph.pk},
            ),
            data=json.dumps({"order": [second.pk, first.pk]}),
            content_type="application/json",
            headers={"X-CSRFToken": token},
        )

        assert response.status_code == 200  # noqa: PLR2004
        first.refresh_from_db()
        second.refresh_from_db()
        assert (second.order, first.order) == (1, 2)
        html = response.content.decode()
        assert html.index("Drugi") < html.index("Prvi")
        # the swapped-in list can be re-initialised
        assert "data-reorder-url=" in html

    def test_chapter_reorder_with_json_body(self, admin_client):
        monograph = MonographFactory()
        first = MonographChapterFactory(monograph=monograph, order=1)
        second = MonographChapterFactory(monograph=monograph, order=2)

        response = admin_client.post(
            reverse(
                "monographs:chapter-reorder", kwargs={"monograph_pk": monograph.pk},
            ),
            data=json.dumps({"order": [second.pk, first.pk]}),
            content_type="application/json",
        )

        assert response.status_code == 200  # noqa: PLR2004
        first.refresh_from_db()
        second.refresh_from_db()
        assert (second.order, first.order) == (1, 2)

    def test_chapter_detail_lists_carry_reorder_urls(self, admin_client):
        chapter = MonographChapterFactory()

        html = admin_client.get(
            reverse("monographs:chapter-detail", kwargs={"pk": chapter.pk}),
        ).content.decode()

        for name in (
            "chapter-contributor-reorder",
            "chapter-funding-reorder",
            "chapter-relation-reorder",
        ):
            url = reverse(f"monographs:{name}", kwargs={"chapter_pk": chapter.pk})
            assert f'data-reorder-url="{url}"' in html


# =============================================================================
# Inline HTMX partials render and keep their labels wired
# =============================================================================


class TestInlinePartialsRender:
    def _assert_labels_wired(self, html):
        ids = set(re.findall(r'\bid="([^"]+)"', html))
        targets = re.findall(r'<label[^>]*\bfor="([^"]*)"', html)
        assert targets
        assert all(target in ids for target in targets), (targets, ids)
        assert "<label class=" not in html  # every label has a for attribute

    def test_monograph_level_forms(self, admin_client):
        monograph = MonographFactory()
        contributor = MonographContributorFactory(monograph=monograph)
        urls = [
            reverse(
                "monographs:contributor-form",
                kwargs={"monograph_pk": monograph.pk},
            ),
            reverse("monographs:contributor-edit-form", kwargs={"pk": contributor.pk}),
            reverse(
                "monographs:affiliation-form",
                kwargs={"contributor_pk": contributor.pk},
            ),
            reverse("monographs:funding-form", kwargs={"monograph_pk": monograph.pk}),
            reverse("monographs:relation-form", kwargs={"monograph_pk": monograph.pk}),
            reverse("monographs:chapter-form", kwargs={"monograph_pk": monograph.pk}),
        ]
        for url in urls:
            response = admin_client.get(url)
            assert response.status_code == 200, url  # noqa: PLR2004
            html = response.content.decode()
            self._assert_labels_wired(html)
            assert 'aria-label="Zatvori formu"' in html
            assert "bg-primary text-white" not in html

    def test_chapter_level_forms(self, admin_client):
        chapter = MonographChapterFactory()
        contributor = ChapterContributorFactory(chapter=chapter)
        urls = [
            reverse("monographs:chapter-edit-form", kwargs={"pk": chapter.pk}),
            reverse(
                "monographs:chapter-contributor-form",
                kwargs={"chapter_pk": chapter.pk},
            ),
            reverse(
                "monographs:chapter-contributor-edit-form",
                kwargs={"pk": contributor.pk},
            ),
            reverse(
                "monographs:chapter-affiliation-form",
                kwargs={"contributor_pk": contributor.pk},
            ),
            reverse(
                "monographs:chapter-funding-form",
                kwargs={"chapter_pk": chapter.pk},
            ),
            reverse(
                "monographs:chapter-relation-form",
                kwargs={"chapter_pk": chapter.pk},
            ),
        ]
        for url in urls:
            response = admin_client.get(url)
            assert response.status_code == 200, url  # noqa: PLR2004
            self._assert_labels_wired(response.content.decode())

    def test_icon_only_buttons_have_accessible_names(self, admin_client):
        monograph = MonographFactory()
        MonographContributorFactory(monograph=monograph)
        MonographFundingFactory(monograph=monograph)
        MonographRelationFactory(monograph=monograph)
        MonographChapterFactory(monograph=monograph, title='Naslov sa "navodnicima"')

        html = admin_client.get(
            reverse("monographs:update", args=[monograph.pk]),
        ).content.decode()

        buttons = re.findall(r'<button[^>]*class="btn-icon[^"]*"[^>]*>', html)
        assert len(buttons) >= 8  # noqa: PLR2004
        assert all("aria-label=" in button for button in buttons)
        assert "Nema dodanih" not in html
