"""
Rendering tests for the shared Crossref deposit page.

The three deposit pages (issue, monograph, component group) share one shell
(``crossref/deposit_base.html``) and one body (``partials/_deposit_page.html``).
These tests pin the contract the views' HTMX responses and the page script
depend on: element ids, family-specific URLs, one "current" step, modal ids.
"""

import re

import pytest
from django.urls import reverse
from django.utils import timezone

from doi_portal.components.tests.factories import ComponentContributorFactory
from doi_portal.components.tests.factories import ComponentFactory
from doi_portal.components.tests.factories import ComponentGroupFactory
from doi_portal.crossref.models import CrossrefExport
from doi_portal.crossref.models import ExportType
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.monographs.tests.factories import MonographFactory
from doi_portal.publications.tests.factories import JournalFactory
from doi_portal.publications.tests.factories import PublisherFactory
from doi_portal.users.tests.factories import UserFactory

VALID_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    "<doi_batch>\n<head/>\n<body/>\n</doi_batch>"
)

STEP_TITLES = [
    "Pre-validacija",
    "Generisanje XML",
    "XSD Validacija",
    "Pregled XML",
    "Preuzimanje XML",
]

FIXED_IDS = [
    'id="crossref-deposit"',
    'id="validation-step-content"',
    'id="generation-step-content"',
    'id="xsd-step-content"',
    'id="deposit-status"',
    'id="regenerateModal"',
    'id="xmlPreviewToast"',
]


@pytest.fixture
def admin_user(db):
    user = UserFactory(email="deposit-pages-admin@test.com")
    user.is_superuser = True
    user.save()
    return user


@pytest.fixture
def publisher(db):
    return PublisherFactory(name="Deposit Pages Publisher", doi_prefix="10.54321")


@pytest.fixture
def issue(publisher):
    publication = JournalFactory(
        title="Deposit Pages Journal",
        publisher=publisher,
        issn_print="1234-5678",
    )
    return IssueFactory(
        publication=publication,
        volume="3",
        issue_number="1",
        year=2026,
        crossref_xml="",
        xsd_valid=None,
    )


@pytest.fixture
def monograph(publisher):
    return MonographFactory(publisher=publisher, title="Deposit Pages Monograph")


@pytest.fixture
def component_group(db):
    cg = ComponentGroupFactory(parent_doi="10.54321/pages.test")
    comp = ComponentFactory(
        component_group=cg,
        doi_suffix="comp.pages",
        title="Pages Test",
        format_mime_type="audio/mpeg",
    )
    ComponentContributorFactory(component=comp, given_name="Test", surname="Author")
    return cg


def _store_xml(obj, *, valid=True):
    obj.crossref_xml = VALID_XML
    obj.xml_generated_at = timezone.now()
    obj.xsd_valid = valid
    obj.xsd_errors = [] if valid else [{"message": "Element not expected", "line": 3}]
    obj.xsd_validated_at = timezone.now()
    obj.save()
    return obj


def _get(client, user, name, pk):
    client.force_login(user)
    response = client.get(reverse(name, args=[pk]))
    assert response.status_code == 200  # noqa: PLR2004
    return response.content.decode()


def _current_steps(html):
    return re.findall(r'class="deposit-step deposit-step--current"', html)


FAMILIES = [
    ("issue", "crossref:issue-deposit", "issue-validate", "issue-generate"),
    (
        "monograph",
        "crossref:monograph-deposit",
        "monograph-validate",
        "monograph-generate",
    ),
    (
        "component_group",
        "crossref:component-group-deposit",
        "component-group-validate",
        "component-group-generate",
    ),
]


@pytest.mark.django_db
class TestSharedDepositPage:
    """All three families render the same shell with their own URLs."""

    @pytest.mark.parametrize(("fixture", "page", "validate", "generate"), FAMILIES)
    def test_page_structure(  # noqa: PLR0913
        self, request, client, admin_user, fixture, page, validate, generate,
    ):
        obj = request.getfixturevalue(fixture)
        html = _get(client, admin_user, page, obj.pk)

        assert "Crossref deponovanje" in html
        for title in STEP_TITLES:
            assert title in html
        for fixed_id in FIXED_IDS:
            assert fixed_id in html
        assert html.count("<h1") == 1
        assert "css/admin-crossref.css" in html

        # step 1 still loads its panel on page load, from the family's own URL
        validate_url = reverse(f"crossref:{validate}", args=[obj.pk])
        assert f'hx-get="{validate_url}"' in html
        assert 'hx-trigger="load"' in html
        # regenerate modal posts to the family's own generate URL
        generate_url = reverse(f"crossref:{generate}", args=[obj.pk])
        assert f'hx-post="{generate_url}"' in html
        assert 'hx-target="#generation-step-content"' in html

    @pytest.mark.parametrize(("fixture", "page", "validate", "generate"), FAMILIES)
    def test_no_inline_styles_or_bootstrap_stepper_colours(  # noqa: PLR0913
        self, request, client, admin_user, fixture, page, validate, generate,
    ):
        obj = request.getfixturevalue(fixture)
        html = _get(client, admin_user, page, obj.pk)
        content = html.split('id="crossref-deposit"', 1)[1]

        assert "<style" not in html
        assert 'style="' not in content
        for colour in ("#0d6efd", "#198754", "#dee2e6", "#e9ecef", "#6c757d"):
            assert colour not in html

    @pytest.mark.parametrize(("fixture", "page", "validate", "generate"), FAMILIES)
    def test_at_most_one_current_step_and_one_primary_button(  # noqa: PLR0913
        self, request, client, admin_user, fixture, page, validate, generate,
    ):
        obj = _store_xml(request.getfixturevalue(fixture))
        html = _get(client, admin_user, page, obj.pk)
        content = html.split('id="crossref-deposit"', 1)[1].split(
            'id="regenerateModal"', 1,
        )[0]

        assert len(_current_steps(html)) <= 1
        assert content.count("btn-primary") <= 1
        assert html.count('aria-current="step"') <= 1

    def test_modals_are_labelled(self, client, admin_user, issue):
        html = _get(client, admin_user, "crossref:issue-deposit", issue.pk)
        assert 'aria-labelledby="regenerateModalLabel"' in html
        assert 'id="regenerateModalLabel"' in html
        assert 'aria-label="Zatvori"' in html


@pytest.mark.django_db
class TestIssueStepStates:
    """The stepper points at the one thing to do next."""

    def test_valid_xml_not_downloaded_points_at_download(
        self, client, admin_user, issue,
    ):
        _store_xml(issue)
        html = _get(client, admin_user, "crossref:issue-deposit", issue.pk)

        assert len(_current_steps(html)) == 1
        download_url = reverse("crossref:xml-download", args=[issue.pk])
        assert re.search(
            rf'<a href="{re.escape(download_url)}" class="btn btn-primary"', html,
        )
        assert 'id="xmlPreviewBtn"' in html
        preview_url = reverse("crossref:xml-preview", args=[issue.pk])
        assert f'data-xml-preview-url="{preview_url}"' in html
        assert "U pripremi" in html

    def test_invalid_xml_points_at_regenerate(self, client, admin_user, issue):
        _store_xml(issue, valid=False)
        html = _get(client, admin_user, "crossref:issue-deposit", issue.pk)

        assert len(_current_steps(html)) == 1
        assert "Nevažeći XML" in html
        assert "Linija 3:" in html
        # download goes through the warning modal, never directly
        warning_url = reverse("crossref:download-warning", args=[issue.pk])
        assert f'hx-get="{warning_url}"' in html
        assert 'hx-target="body"' in html

    def test_ready_points_at_mark_deposited(self, client, admin_user, issue):
        _store_xml(issue)
        CrossrefExport.objects.create(
            issue=issue,
            xml_content=issue.crossref_xml,
            exported_by=admin_user,
            filename="ready.xml",
            xsd_valid_at_export=True,
        )
        html = _get(client, admin_user, "crossref:issue-deposit", issue.pk)

        assert "Spremno za Crossref" in html
        assert len(_current_steps(html)) == 1
        mark_url = reverse("crossref:mark-deposited", args=[issue.pk])
        assert f'hx-post="{mark_url}"' in html
        assert 'hx-target="#deposit-status"' in html
        history_url = reverse("crossref:export-history", args=[issue.pk])
        assert f'hx-get="{history_url}"' in html
        assert 'id="export-history-container"' in html

    def test_deposited_has_no_current_step(self, client, admin_user, issue):
        _store_xml(issue)
        CrossrefExport.objects.create(
            issue=issue,
            xml_content=issue.crossref_xml,
            exported_by=admin_user,
            filename="done.xml",
            xsd_valid_at_export=True,
        )
        issue.crossref_deposited_at = timezone.now()
        issue.crossref_deposited_by = admin_user
        issue.save()
        html = _get(client, admin_user, "crossref:issue-deposit", issue.pk)

        assert "Deponovano" in html
        assert _current_steps(html) == []
        assert 'data-deposit-state="deposited"' in html


@pytest.mark.django_db
class TestFamilyPartials:
    """Partials shared between families resolve the right family's URLs."""

    def test_monograph_preview_modal(self, client, admin_user, monograph):
        _store_xml(monograph)
        html = _get(client, admin_user, "crossref:monograph-xml-preview", monograph.pk)

        assert 'id="xmlPreviewModal"' in html
        assert "language-xml" in html
        assert "line-numbers" in html
        assert reverse("crossref:monograph-xml-download", args=[monograph.pk]) in html

    def test_component_preview_modal(self, client, admin_user, component_group):
        _store_xml(component_group, valid=False)
        html = _get(
            client, admin_user, "crossref:component-xml-preview", component_group.pk,
        )

        assert 'id="xmlPreviewModal"' in html
        assert 'data-line="3"' in html
        assert 'data-error-lines="3"' in html
        assert "Prva greška" in html
        assert (
            reverse("crossref:component-xml-download", args=[component_group.pk])
            in html
        )

    def test_issue_preview_modal_is_labelled(self, client, admin_user, issue):
        _store_xml(issue)
        html = _get(client, admin_user, "crossref:xml-preview", issue.pk)

        assert 'aria-labelledby="xmlPreviewModalLabel"' in html
        assert 'aria-label="Zatvori"' in html
        assert "modal-xl" in html
        assert "<style" not in html
        assert 'style="' not in html
        assert reverse("crossref:xml-download", args=[issue.pk]) in html

    def test_component_download_warning_modal(
        self, client, admin_user, component_group,
    ):
        _store_xml(component_group, valid=False)
        html = _get(
            client,
            admin_user,
            "crossref:component-download-warning",
            component_group.pk,
        )

        assert 'id="downloadWarningModal"' in html
        assert "Preuzmi svejedno" in html
        assert "Otkaži" in html
        assert (
            reverse("crossref:component-xml-download-force", args=[component_group.pk])
            in html
        )

    def test_monograph_download_warning_modal(self, client, admin_user, monograph):
        _store_xml(monograph, valid=False)
        html = _get(
            client, admin_user, "crossref:monograph-download-warning", monograph.pk,
        )

        assert 'aria-labelledby="downloadWarningModalLabel"' in html
        assert (
            reverse("crossref:monograph-xml-download-force", args=[monograph.pk])
            in html
        )

    @pytest.mark.parametrize(
        ("fixture", "history", "redownload", "export_type", "field"),
        [
            ("issue", "export-history", "export-redownload", ExportType.ISSUE, "issue"),
            (
                "monograph",
                "monograph-export-history",
                "monograph-export-redownload",
                ExportType.MONOGRAPH,
                "monograph",
            ),
            (
                "component_group",
                "component-export-history",
                "component-export-redownload",
                ExportType.COMPONENT_GROUP,
                "component_group",
            ),
        ],
    )
    def test_export_history_uses_family_redownload_url(  # noqa: PLR0913
        self,
        request,
        client,
        admin_user,
        fixture,
        history,
        redownload,
        export_type,
        field,
    ):
        obj = request.getfixturevalue(fixture)
        export = CrossrefExport.objects.create(
            xml_content="<xml/>",
            exported_by=admin_user,
            filename="history.xml",
            xsd_valid_at_export=False,
            export_type=export_type,
            **{field: obj},
        )
        html = _get(client, admin_user, f"crossref:{history}", obj.pk)

        assert "history.xml" in html
        assert "Nevažeći" in html
        assert reverse(f"crossref:{redownload}", args=[export.pk]) in html
        assert 'aria-label="Preuzmi ponovo history.xml"' in html

    @pytest.mark.parametrize(
        ("fixture", "mark"),
        [
            ("issue", "mark-deposited"),
            ("monograph", "monograph-mark-deposited"),
            ("component_group", "component-mark-deposited"),
        ],
    )
    def test_mark_deposited_returns_deposited_state(
        self, request, client, admin_user, fixture, mark,
    ):
        obj = request.getfixturevalue(fixture)
        client.force_login(admin_user)
        response = client.post(reverse(f"crossref:{mark}", args=[obj.pk]))

        assert response.status_code == 200  # noqa: PLR2004
        html = response.content.decode()
        assert "Deponovano" in html
        # the page script reloads on this marker to refresh the header and stepper
        assert 'data-deposit-state="deposited"' in html
