"""
UI contract tests for the superadmin system pages (dashboard redesign).

They pin down the markup other code depends on: element ids and HTMX wiring of
the audit log, the confirmation dialogs that POST the GDPR actions, the
type tabs of the deleted-items page, and "one <h1> per page".

Set DUMP_HTML=<dir> to write each rendered page there for manual inspection.
"""

import json
import os
import re
from pathlib import Path

import pytest
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from doi_portal.core.models import GdprRequest
from doi_portal.core.models import GdprRequestStatus
from doi_portal.core.models import GdprRequestType
from doi_portal.publications.tests.factories import PublisherFactory
from doi_portal.users.tests.factories import UserFactory


def _html(response, name: str) -> str:
    html = response.content.decode()
    dump_dir = os.environ.get("DUMP_HTML")
    if dump_dir:
        Path(dump_dir, f"{name}.html").write_text(html, encoding="utf-8")
    return html


def _main(html: str) -> str:
    """The page content without the shell (sidebar, top bar)."""
    match = re.search(r"<main\b.*?</main>", html, flags=re.DOTALL)
    return match.group(0) if match else html


@pytest.fixture
def superadmin(db):
    return UserFactory(email="root@test.com", is_superuser=True)


@pytest.fixture
def client(superadmin):
    client = Client()
    client.force_login(superadmin)
    return client


@pytest.fixture
def user_ct(db):
    from doi_portal.users.models import User  # noqa: PLC0415

    return ContentType.objects.get_for_model(User)


def _log(user_ct, actor, action, changes, repr_="Petar Petrović", pk=7):  # noqa: PLR0913
    return LogEntry.objects.create(
        content_type=user_ct,
        object_pk=str(pk),
        object_id=pk,
        object_repr=repr_,
        action=action,
        changes=json.dumps(changes),
        actor=actor,
    )


@pytest.mark.django_db
class TestAuditLogListUi:
    def test_filter_bar_and_htmx_wiring(self, client, superadmin, user_ct):
        _log(user_ct, superadmin, LogEntry.Action.UPDATE, {"name": ["A", "B"]})
        html = _html(client.get(reverse("core:audit-log-list")), "audit_list")
        main = _main(html)

        assert html.count("<h1") == 1
        assert 'id="filter-form"' in main
        assert 'class="filter-bar"' in main
        assert 'hx-target="#audit-log-table"' in main
        assert 'id="search-input"' in main
        # one table root, never nested
        assert main.count('id="audit-log-table"') == 1
        # selects keep form-select (searchable-select hook) and their names
        for name in ("actor", "action", "model"):
            assert re.search(
                rf'<select class="form-select" id="{name}" name="{name}"', main,
            ), name
        # legacy tall filter card is gone
        assert "filter-card" not in main
        assert re.search(r'id="audit-log-count"><strong>\d+</strong> zapisa', main)

    def test_htmx_partial_has_single_root_and_oob_state(
        self, client, superadmin, user_ct,
    ):
        _log(user_ct, superadmin, LogEntry.Action.CREATE, {"name": ["", "B"]})
        response = client.get(
            reverse("core:audit-log-list"), {"q": "Petar"}, HTTP_HX_REQUEST="true",
        )
        html = _html(response, "audit_partial")

        assert "<!DOCTYPE html>" not in html
        assert html.count('id="audit-log-table"') == 1
        assert 'id="audit-log-count" hx-swap-oob="true"' in html
        assert 'id="audit-log-reset" hx-swap-oob="true"' in html
        assert "Poništi" in html  # a filter is active

    def test_full_page_has_no_oob_duplicates(self, client, superadmin, user_ct):
        _log(user_ct, superadmin, LogEntry.Action.CREATE, {"name": ["", "B"]})
        html = client.get(reverse("core:audit-log-list")).content.decode()
        assert "hx-swap-oob" not in html
        assert html.count('id="audit-log-count"') == 1
        assert html.count('id="audit-log-reset"') == 1

    def test_pagination_swaps_table_in_place(self, client, superadmin, user_ct):
        for i in range(51):
            _log(user_ct, superadmin, LogEntry.Action.CREATE, {}, pk=i + 1)
        main = _main(client.get(reverse("core:audit-log-list")).content.decode())
        assert "list-pagination" in main
        assert 'hx-target="#audit-log-table"' in main
        assert 'hx-select="#audit-log-table"' in main
        assert re.search(r"1–50 od \d+", main)  # noqa: RUF001

    def test_empty_with_filter_offers_reset(self, client):
        response = client.get(reverse("core:audit-log-list"), {"q": "nema-toga"})
        main = _main(response.content.decode())
        assert "Nema log unosa koji odgovaraju filterima." in main
        assert "Poništi filtere" in main


@pytest.mark.django_db
class TestAuditLogDetailUi:
    def test_update_entry_has_meaningful_title_and_diff(
        self, client, superadmin, user_ct,
    ):
        entry = _log(
            user_ct,
            superadmin,
            LogEntry.Action.UPDATE,
            {"name": ["Staro ime", "Novo ime"], "phone": ["None", "123"]},
        )
        html = _html(
            client.get(reverse("core:audit-log-detail", args=[entry.pk])),
            "audit_detail",
        )
        main = _main(html)

        assert html.count("<h1") == 1
        h1 = re.search(r"<h1.*?</h1>", main, flags=re.DOTALL).group(0)
        assert "Petar Petrović" in h1
        assert f"Detalj #{entry.pk}" not in h1
        # The breadcrumb names the same object as the page title
        assert f"Detalj #{entry.pk}" not in html
        crumb = re.search(
            r'<li class="breadcrumb-item active" aria-current="page">(.*?)</li>', html,
        ).group(1)
        assert crumb == "Petar Petrović"
        assert "Izmena" in main
        assert '<del class="audit-diff__old">Staro ime</del>' in main
        assert '<ins class="audit-diff__new">Novo ime</ins>' in main
        # "None" placeholders from auditlog are not shown as values
        assert '<del class="audit-diff__old">None</del>' not in main
        assert "admin-dl" in main
        assert "admin-system.css" in html

    def test_delete_entry_shows_object(self, client, superadmin, user_ct):
        entry = _log(user_ct, superadmin, LogEntry.Action.DELETE, {}, repr_="Obrisani")
        main = _main(
            client.get(
                reverse("core:audit-log-detail", args=[entry.pk]),
            ).content.decode(),
        )
        assert "Brisanje" in main
        assert "Obrisani objekat" in main


@pytest.mark.django_db
class TestDeletedItemsUi:
    def test_tabs_and_separated_actions(self, client, superadmin):
        publisher = PublisherFactory()
        publisher.soft_delete(user=superadmin)

        html = _html(client.get(reverse("core:deleted-items")), "deleted_items")
        main = _main(html)

        assert html.count("<h1") == 1
        assert "btn-group" not in main
        assert 'class="section-tabs"' in main
        assert main.count('aria-current="page"') == 1
        restore = reverse(
            "core:deleted-item-restore",
            kwargs={"model_type": "publisher", "pk": publisher.pk},
        )
        purge = reverse(
            "core:deleted-item-permanent-delete",
            kwargs={"model_type": "publisher", "pk": publisher.pk},
        )
        assert f'hx-post="{restore}"' in main
        purge_button = re.search(
            rf'<button[^>]*hx-post="{re.escape(purge)}"[^>]*>', main, flags=re.DOTALL,
        ).group(0)
        assert "btn-outline-danger" in purge_button
        assert "hx-confirm=" in purge_button
        assert "nepovratna" in purge_button

    def test_active_tab_follows_type_filter(self, client):
        main = _main(
            client.get(
                reverse("core:deleted-items"), {"type": "article"},
            ).content.decode(),
        )
        active = re.search(
            r'<a[^>]*aria-current="page"[^>]*>.*?</a>', main, flags=re.DOTALL,
        )
        assert "Članci" in active.group(0)
        assert "Nema obrisanih stavki ovog tipa." in main


@pytest.mark.django_db
class TestGdprUi:
    def _request(self, superadmin, status=GdprRequestStatus.PENDING):
        return GdprRequest.objects.create(
            requester_email="osoba@example.com",
            request_type=GdprRequestType.DELETION,
            status=status,
            received_date=timezone.now().date(),
            created_by=superadmin,
        )

    def test_list(self, client, superadmin):
        req = self._request(superadmin)
        html = _html(client.get(reverse("core:gdpr-request-list")), "gdpr_list")
        main = _main(html)
        assert html.count("<h1") == 1
        assert f"GDPR-{req.pk}" in main
        assert "status-badge--pending" in main
        assert "Na čekanju" in main

    def test_form_uses_kit_fields(self, client):
        html = _html(client.get(reverse("core:gdpr-request-create")), "gdpr_form")
        main = _main(html)
        assert html.count("<h1") == 1
        select = re.search(r'<select[^>]*name="request_type"[^>]*>', main).group(0)
        assert "form-select" in select
        for field_id in (
            "id_requester_email",
            "id_request_type",
            "id_notes",
            "id_received_date",
        ):
            assert f'for="{field_id}"' in main, field_id
            assert f'id="{field_id}"' in main, field_id
        assert "form-actions" in main
        assert "Otkaži" in main
        assert "Sačuvaj zahtev" in main

    def test_form_shows_errors(self, client):
        response = client.post(reverse("core:gdpr-request-create"), {"notes": "x"})
        main = _main(response.content.decode())
        assert response.status_code == 200  # noqa: PLR2004
        assert "is-invalid" in main
        assert ">x</textarea>" in main

    def test_process_confirmation_posts_with_csrf(self, client, superadmin):
        req = self._request(superadmin)
        html = _html(
            client.get(reverse("core:gdpr-request-detail", args=[req.pk])),
            "gdpr_detail_pending",
        )
        main = _main(html)
        assert html.count("<h1") == 1
        assert "confirm(" not in main
        assert "gdpr-process-modal" not in main
        url = reverse("core:gdpr-request-process", args=[req.pk])
        form = re.search(
            rf'<form method="post" action="{re.escape(url)}".*?</form>',
            main,
            flags=re.DOTALL,
        ).group(0)
        assert "csrfmiddlewaretoken" in form
        assert 'type="submit"' in form
        # Simple confirmation: handled by the shell's form[data-confirm] listener
        assert "data-confirm=" in form
        assert "gdpr-cancel-modal" not in main

    def test_cancel_confirmation_posts_reason_with_csrf(self, client, superadmin):
        req = self._request(superadmin, status=GdprRequestStatus.PROCESSING)
        html = _html(
            client.get(reverse("core:gdpr-request-detail", args=[req.pk])),
            "gdpr_detail_processing",
        )
        main = _main(html)
        assert "confirm(" not in main
        assert 'data-bs-target="#gdpr-cancel-modal"' in main
        url = reverse("core:gdpr-request-cancel", args=[req.pk])
        form = re.search(
            rf'<form method="post" action="{re.escape(url)}".*?</form>',
            main,
            flags=re.DOTALL,
        ).group(0)
        assert "csrfmiddlewaretoken" in form
        assert 'name="cancellation_reason"' in form
        assert 'for="id_cancellation_reason"' in form
        assert reverse("core:gdpr-request-report", args=[req.pk]) in main


@pytest.mark.django_db
class TestDiagnosticsUi:
    def test_system_health(self, client):
        html = _html(client.get(reverse("core:system-health")), "system_health")
        main = _main(html)
        assert html.count("<h1") == 1
        assert "Status integracija" in main
        assert "Poslednja provera:" in main
        for service in ("Baza podataka", "Redis", "Celery", "S3 skladište"):
            assert service in main

    def test_sentry_test(self, client):
        html = _html(client.get(reverse("core:sentry-test")), "sentry_test")
        main = _main(html)
        assert html.count("<h1") == 1
        assert "Status Sentry integracije" in main
        assert "btn-warning" not in main
