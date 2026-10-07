"""
UI contract tests for the conference wizard (dashboard redesign).

They pin down what HTMX and the forms depend on: element ids, swap targets,
the hidden publisher field, the unchanged language widget, and one consistent
footer per step.

Set DUMP_HTML=<dir> to write each rendered page there for manual inspection.
"""

import os
import re
from pathlib import Path

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.articles.tests.factories import AuthorFactory
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import ConferenceFactory
from doi_portal.publications.tests.factories import PublisherFactory
from doi_portal.users.tests.factories import UserFactory


def _html(response, name: str) -> str:
    html = response.content.decode()
    dump_dir = os.environ.get("DUMP_HTML")
    if dump_dir:
        Path(dump_dir, f"{name}.html").write_text(html, encoding="utf-8")
    return html


def _main(html: str) -> str:
    match = re.search(r"<main\b.*?</main>", html, flags=re.DOTALL)
    return match.group(0) if match else html


def _user(role, publisher, email):
    user = UserFactory(email=email)
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)
    user.publisher = publisher
    user.save()
    return user


@pytest.fixture
def publisher(db):
    return PublisherFactory(name="Test Publisher", doi_prefix="10.9999")


@pytest.fixture
def urednik_client(publisher):
    client = Client()
    client.force_login(_user("Urednik", publisher, "urednik-ui@test.com"))
    return client


@pytest.fixture
def admin_client(publisher):
    client = Client()
    client.force_login(_user("Administrator", publisher, "admin-ui@test.com"))
    return client


@pytest.fixture
def publication(publisher):
    return ConferenceFactory(
        publisher=publisher,
        conference_name="EMCE 2026",
        conference_acronym="EMCE",
        conference_location="Beograd, Srbija",
    )


@pytest.fixture
def issue(publication):
    return IssueFactory(
        publication=publication, proceedings_title="EMCE 2026 Proceedings", year=2026,
    )


@pytest.fixture
def article(issue):
    return ArticleFactory(
        issue=issue,
        title="Test Paper",
        doi_suffix="test.paper.001",
        status=ArticleStatus.DRAFT,
    )


@pytest.mark.django_db
class TestWizardShell:
    def test_single_breadcrumb_single_h1_and_stepper(self, urednik_client):
        html = _html(
            urednik_client.get(reverse("wizard:conference-start")), "wizard_start",
        )
        main = _main(html)

        assert html.count("<h1") == 1
        # the shell prints the breadcrumb; the page must not repeat it
        assert html.count('class="breadcrumb"') == 1
        assert 'class="breadcrumb"' not in main
        assert "wizard-stepper" in main
        assert main.count("wizard-step-icon") == 4  # noqa: PLR2004
        assert main.count('aria-current="step"') == 1
        assert "Korak 1 od 4" in main

    def test_previous_steps_are_links(self, urednik_client, publication, issue):
        url = reverse("wizard:conference-step-3", args=[publication.pk])
        main = _main(_html(urednik_client.get(url), "wizard_step3_empty"))
        assert reverse("wizard:conference-step-1", args=[publication.pk]) in main
        assert reverse("wizard:conference-step-2", args=[publication.pk]) in main
        assert "Korak 3 od 4 · EMCE 2026" in main


@pytest.mark.django_db
class TestWizardStep1:
    def test_publisher_hidden_for_publisher_bound_user(self, urednik_client, publisher):
        main = _main(
            urednik_client.get(reverse("wizard:conference-start")).content.decode(),
        )
        hidden = re.search(r'<input[^>]*name="publisher"[^>]*>', main).group(0)
        assert 'type="hidden"' in hidden
        assert f'value="{publisher.pk}"' in hidden
        assert 'for="id_publisher"' not in main

    def test_admin_gets_publisher_select(self, admin_client):
        main = _main(
            _html(
                admin_client.get(reverse("wizard:conference-start")),
                "wizard_start_admin",
            ),
        )
        select = re.search(r'<select[^>]*name="publisher"[^>]*>', main).group(0)
        assert "form-select" in select
        assert 'for="id_publisher"' in main

    def test_language_stays_a_single_select(self, urednik_client):
        main = _main(
            urednik_client.get(reverse("wizard:conference-start")).content.decode(),
        )
        select = re.search(r'<select[^>]*name="language"[^>]*>', main).group(0)
        assert "form-select" in select
        assert "multiple" not in select

    def test_footer_and_errors(self, urednik_client, publisher):
        response = urednik_client.post(
            reverse("wizard:conference-start"),
            {"publisher": publisher.pk, "conference_name": ""},
        )
        main = _main(response.content.decode())
        assert response.status_code == 200  # noqa: PLR2004
        assert "is-invalid" in main
        assert "form-actions" in main
        assert "Dalje" in main
        assert "Otkaži" in main


@pytest.mark.django_db
class TestWizardStep2:
    def test_fields_have_controls_and_footer(self, urednik_client, publication):
        url = reverse("wizard:conference-step-2", args=[publication.pk])
        main = _main(_html(urednik_client.get(url), "wizard_step2"))
        # every label points at a control that exists on the page
        for field_id in re.findall(r'<label[^>]*for="([^"]+)"', main):
            assert f'id="{field_id}"' in main, field_id
        assert 'name="doi_suffix"' in main
        assert "Nazad" in main
        assert "Dalje" in main


@pytest.mark.django_db
class TestWizardStep3:
    def test_ids_and_targets(self, urednik_client, publication, article):
        AuthorFactory(article=article, given_name="Ana", surname="Anić", order=1)
        url = reverse("wizard:conference-step-3", args=[publication.pk])
        main = _main(_html(urednik_client.get(url), "wizard_step3"))

        assert main.count('id="paper-form-container"') == 1
        assert main.count('id="paper-list"') == 1
        assert main.count(f'id="paper-item-{article.pk}"') == 1
        # exactly one author root per paper (it is swapped with outerHTML)
        assert main.count(f'id="wizard-authors-{article.pk}"') == 1
        assert main.count(f'id="wizard-author-form-{article.pk}"') == 1
        assert f'hx-target="#wizard-authors-{article.pk}"' in main
        assert 'hx-target="#paper-form-container"' in main
        assert "Dodaj rad" in main
        assert "Dodaj autora" in main
        # icon-only buttons are labelled
        for button in re.findall(r'<button[^>]*class="btn-icon[^>]*>', main):
            assert "aria-label=" in button, button

    def test_paper_form_partial(self, urednik_client, publication, issue):
        url = reverse("wizard:paper-add", args=[publication.pk])
        html = _html(urednik_client.get(url), "wizard_paper_form")
        assert f'hx-post="{url}"' in html
        assert 'hx-target="#paper-list"' in html
        assert 'id="id_title"' in html
        assert 'for="id_title"' in html
        assert "Dodaj rad" in html

    def test_author_form_and_list_partials(self, urednik_client, article):
        form_html = _html(
            urednik_client.get(reverse("wizard:author-form", args=[article.pk])),
            "wizard_author_form",
        )
        assert f'hx-target="#wizard-authors-{article.pk}"' in form_html
        assert 'hx-swap="outerHTML"' in form_html
        assert 'id="id_surname"' in form_html

        response = urednik_client.post(
            reverse("wizard:author-add", args=[article.pk]),
            {"given_name": "Ana", "surname": "Anić", "contributor_role": "author"},
        )
        list_html = _html(response, "wizard_author_list")
        assert response.status_code == 200  # noqa: PLR2004
        assert list_html.count(f'id="wizard-authors-{article.pk}"') == 1
        assert "Anić" in list_html


@pytest.mark.django_db
class TestWizardStep4:
    def test_review_uses_definition_grid_and_blocks_on_errors(
        self, urednik_client, publication, article,
    ):
        url = reverse("wizard:conference-step-4", args=[publication.pk])
        main = _main(_html(urednik_client.get(url), "wizard_step4"))

        assert "admin-dl" in main
        assert "EMCE 2026" in main
        assert "Test Paper" in main
        generate = reverse("wizard:generate-xml", args=[publication.pk])
        form = re.search(
            rf'<form method="post" action="{re.escape(generate)}".*?</form>',
            main,
            flags=re.DOTALL,
        ).group(0)
        assert "csrfmiddlewaretoken" in form
        assert "Generiši XML" in form
        # the paper has no authors -> validation error -> action disabled
        assert "alert-danger" in main
        assert "disabled" in form
        assert "btn-success" not in main
