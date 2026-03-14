# Story 6.4: GDPR Data Request Handling

Status: done

## Story

As a **Superadmin**,
I want **to process GDPR data deletion requests through a dedicated interface**,
So that **the portal complies with privacy regulations and data deletion can be tracked with full audit trail**.

## Acceptance Criteria

1. **AC1: GDPR Requests lista** - Superadmin pristupa stranici "GDPR zahtevi" putem sidebar menija (System > GDPR zahtevi). Stranica prikazuje listu svih zahteva sa kolonama: Zahtev br., Email podnosioca, Tip (pristup/brisanje), Status, Datum prijema, Datum obrade. Paginacija 25 po stranici. Reverse chronological order.

2. **AC2: Kreiranje novog zahteva** - Superadmin kreira novi GDPR zahtev putem forme sa poljima: `requester_email` (EmailField, obavezno), `request_type` (choices: ACCESS/DELETION), `notes` (TextField, opciono), `received_date` (DateField, obavezno, default=today). Status se automatski postavlja na PENDING. HTMX forma ili standardna forma.

3. **AC3: Identifikacija pogodenih podataka** - Kada se zahtev kreira ili pregleda, sistem identifikuje pogodene podatke: User nalog (po email-u, ako postoji), Author zapisi (po email-u, svi clanci gde je osoba autor), Audit log entri (LogEntry gde je actor taj user). Prikaz u detail view-u pod sekcijom "Pogodeni podaci".

4. **AC4: Obrada zahteva za brisanje (DELETION)** - Superadmin odobrava zahtev klikom na "Obradi zahtev". Za User nalog: email se zamenjuje hashom (`deleted_<pk>@anonymized.local`), `name` se brise, `is_active=False`. Za Author zapise: `given_name`, `surname`, `email`, `orcid` se anonimizuju (ime/prezime="[Anonimizirano]", email/orcid prazno). Za audit log: `actor` polje se postavlja na NULL (ali LogEntry ostaje za compliance). Status zahteva se menja u PROCESSING.

5. **AC5: Grace period i soft delete** - Pri obradi deletion zahteva, podaci se PRVO soft-delete-uju (User: `is_active=False`, Author: `soft_delete()`). Permanentna anonimizacija se zakazuje Celery task-om nakon 30 dana. Podnosilac moze otkazati zahtev tokom grace perioda (status CANCELLED, restore soft-deleted podataka). Zahtev prati `grace_period_end` datum.

6. **AC6: Zavrsetak obrade** - Nakon isteka grace perioda, Celery task izvrsava permanentnu anonimizaciju. Status zahteva se menja u COMPLETED. `completed_at` timestamp se zapisuje.

7. **AC7: Confirmation report** - Superadmin moze preuzeti PDF/TXT izvestaj o obradi zahteva. Izvestaj sadrzi: Broj zahteva, email podnosioca, tip zahteva, datum prijema, datum obrade, lista anonimizovanih podataka (tipovi, ne stvarni podaci).

8. **AC8: Pristup samo za Superadmin** - Samo Superadmin moze pristupiti GDPR zahtevima i izvrsavati akcije. Ostali korisnici dobijaju 403 Forbidden.

## Tasks / Subtasks

- [x] Task 1: Kreiraj GdprRequest model (AC: #1, #2, #3)
  - [x] 1.1 Kreiraj `core/models.py` - dodaj `GdprRequest` model sa poljima: `requester_email` (EmailField), `request_type` (CharField, choices: ACCESS/DELETION), `status` (CharField, choices: PENDING/PROCESSING/COMPLETED/CANCELLED), `notes` (TextField, blank=True), `received_date` (DateField), `created_at` (DateTimeField, auto_now_add), `created_by` (FK User), `processed_at` (DateTimeField, null), `processed_by` (FK User, null), `completed_at` (DateTimeField, null), `grace_period_end` (DateField, null), `cancellation_reason` (TextField, blank=True)
  - [x] 1.2 Dodaj `GdprRequestStatus` TextChoices: PENDING, PROCESSING, COMPLETED, CANCELLED
  - [x] 1.3 Dodaj `GdprRequestType` TextChoices: ACCESS, DELETION
  - [x] 1.4 Kreiraj migraciju: `python manage.py makemigrations core`
  - [x] 1.5 Registruj `GdprRequest` sa auditlog: `auditlog.register(GdprRequest)`

- [x] Task 2: Kreiraj GdprRequestForm (AC: #2)
  - [x] 2.1 Kreiraj `core/forms.py` sa `GdprRequestForm(ModelForm)` - polja: requester_email, request_type, notes, received_date
  - [x] 2.2 Labele na srpskom: "Email podnosioca", "Tip zahteva", "Napomene", "Datum prijema"
  - [x] 2.3 Widget za received_date: `DateInput(attrs={"type": "date"})`

- [x] Task 3: Kreiraj GDPR service layer (AC: #3, #4, #5, #6)
  - [x] 3.1 Kreiraj `core/services.py` sa `GdprService` klasom
  - [x] 3.2 `identify_affected_data(requester_email)` - vraca dict sa: `user` (User ili None), `authors` (QuerySet Author po email-u), `audit_entries_count` (int, LogEntry count gde je actor taj user)
  - [x] 3.3 `process_deletion_request(gdpr_request, processed_by)` - soft delete + anonimizacija user/author podataka, zakazuje Celery task za permanentnu anonimizaciju, setuje grace_period_end = today + 30 dana, status = PROCESSING
  - [x] 3.4 `cancel_request(gdpr_request, reason, cancelled_by)` - restore soft-deleted podataka, status = CANCELLED
  - [x] 3.5 `complete_request(gdpr_request)` - permanentna anonimizacija, status = COMPLETED
  - [x] 3.6 `generate_confirmation_report(gdpr_request)` - generise plain text izvestaj

- [x] Task 4: Kreiraj Celery task za permanentnu anonimizaciju (AC: #5, #6)
  - [x] 4.1 U `core/tasks.py` dodaj `gdpr_permanent_anonymize_task(gdpr_request_id)` - shared_task sa bind=True, max_retries=3
  - [x] 4.2 Task proverava da li je status PROCESSING i da je grace_period_end prosao
  - [x] 4.3 User anonimizacija: email -> `deleted_<pk>@anonymized.local`, name -> prazno, password -> unusable
  - [x] 4.4 Author anonimizacija: given_name/surname -> "[Anonimizirano]", email/orcid -> prazno
  - [x] 4.5 Audit log: LogEntry.objects.filter(actor=user).update(actor=None)
  - [x] 4.6 Status -> COMPLETED, completed_at -> now()

- [x] Task 5: Dodaj "GDPR zahtevi" u sidebar meni (AC: #1, #8)
  - [x] 5.1 U `core/menu.py` MENU_ITEMS dodaj `gdpr_requests` POSLE `deleted_items` a PRE `system_settings`: `{"label": "GDPR zahtevi", "icon": "bi-shield-lock", "url_name": "core:gdpr-request-list", "roles": ["Superadmin"]}`

- [x] Task 6: Kreiraj GDPR views (AC: #1, #2, #3, #4, #5, #7, #8)
  - [x] 6.1 `GdprRequestListView(SuperadminRequiredMixin, ListView)` - lista svih zahteva, paginate_by=25
  - [x] 6.2 `GdprRequestCreateView(SuperadminRequiredMixin, CreateView)` - forma za novi zahtev, auto-set created_by
  - [x] 6.3 `GdprRequestDetailView(SuperadminRequiredMixin, DetailView)` - detalj zahteva sa pogodenim podacima
  - [x] 6.4 FBV `gdpr_request_process(request, pk)` - POST only, pokrece obradu deletion zahteva
  - [x] 6.5 FBV `gdpr_request_cancel(request, pk)` - POST only, otkazuje zahtev tokom grace perioda
  - [x] 6.6 FBV `gdpr_request_download_report(request, pk)` - GET, generise i vraca confirmation report

- [x] Task 7: Dodaj URL-ove za GDPR (AC: #1, #2, #3, #4, #5, #7)
  - [x] 7.1 U `core/urls.py` dodaj GDPR URL-ove:
    - `path("gdpr/", views.GdprRequestListView.as_view(), name="gdpr-request-list")`
    - `path("gdpr/create/", views.GdprRequestCreateView.as_view(), name="gdpr-request-create")`
    - `path("gdpr/<int:pk>/", views.GdprRequestDetailView.as_view(), name="gdpr-request-detail")`
    - `path("gdpr/<int:pk>/process/", views.gdpr_request_process, name="gdpr-request-process")`
    - `path("gdpr/<int:pk>/cancel/", views.gdpr_request_cancel, name="gdpr-request-cancel")`
    - `path("gdpr/<int:pk>/report/", views.gdpr_request_download_report, name="gdpr-request-report")`

- [x] Task 8: Kreiraj templates (AC: #1, #2, #3)
  - [x] 8.1 `templates/core/gdpr_request_list.html` - extends `admin_base.html`, tabela zahteva sa badge-ovima za status
  - [x] 8.2 `templates/core/gdpr_request_form.html` - forma za kreiranje zahteva, Bootstrap 5 layout
  - [x] 8.3 `templates/core/gdpr_request_detail.html` - detalj zahteva sa: metapodaci, pogodeni podaci, akcije (Obradi/Otkaži/Preuzmi izveštaj)
  - [x] 8.4 Breadcrumbs: Kontrolna tabla > GDPR zahtevi > [Detalj/Novi]
  - [x] 8.5 Status badge klase: PENDING=bg-warning, PROCESSING=bg-info, COMPLETED=bg-success, CANCELLED=bg-secondary

- [x] Task 9: Testovi za GdprRequest model (AC: #1, #2)
  - [x] 9.1 Test: GdprRequest kreiranje sa svim poljima
  - [x] 9.2 Test: Status choices validacija
  - [x] 9.3 Test: Default status je PENDING

- [x] Task 10: Testovi za GdprService (AC: #3, #4, #5, #6)
  - [x] 10.1 Test: `identify_affected_data` pronalazi User po email-u
  - [x] 10.2 Test: `identify_affected_data` pronalazi Author zapise po email-u
  - [x] 10.3 Test: `identify_affected_data` broji audit log entri-je
  - [x] 10.4 Test: `process_deletion_request` soft-delete-uje user-a (is_active=False)
  - [x] 10.5 Test: `process_deletion_request` soft-delete-uje Author zapise
  - [x] 10.6 Test: `process_deletion_request` postavlja grace_period_end
  - [x] 10.7 Test: `cancel_request` restore-uje podatke i status=CANCELLED
  - [x] 10.8 Test: `complete_request` anonimizuje user email/name
  - [x] 10.9 Test: `complete_request` anonimizuje Author polja
  - [x] 10.10 Test: `generate_confirmation_report` generise tekst sa svim potrebnim podacima

- [x] Task 11: Testovi za views (AC: #1, #2, #7, #8)
  - [x] 11.1 Test: Superadmin moze pristupiti GDPR list stranici (200)
  - [x] 11.2 Test: Non-Superadmin dobija 403
  - [x] 11.3 Test: Kreiranje zahteva funkcionise
  - [x] 11.4 Test: Detail view prikazuje pogodene podatke
  - [x] 11.5 Test: Process endpoint pokrece obradu
  - [x] 11.6 Test: Cancel endpoint otkazuje zahtev
  - [x] 11.7 Test: Download report vraca fajl

- [x] Task 12: Testovi za Celery task (AC: #5, #6)
  - [x] 12.1 Test: Task anonimizuje user podatke nakon grace perioda
  - [x] 12.2 Test: Task ne obradjuje ako grace period nije istekao
  - [x] 12.3 Test: Task ne obradjuje ako status nije PROCESSING
  - [x] 12.4 Test: Task postavlja status COMPLETED

- [x] Task 13: Regression testovi (AC: #8)
  - [x] 13.1 Pokreni kompletnu test suite: `pytest` - svi postojeci testovi moraju proci
  - [x] 13.2 Verifikuj da sidebar meni prikazuje GDPR zahteve samo za Superadmin

## Dev Notes

### KRITIČNO: Postojeca infrastruktura koju MORAS koristiti

| Komponenta | Lokacija | Story |
|------------|----------|-------|
| SuperadminRequiredMixin | `core/views.py` | 6.2 |
| role_required dekorator | `core/permissions.py` | 6.2 |
| SoftDeleteMixin | `core/mixins.py` | 6.3 |
| SoftDeleteManager | `core/mixins.py` | 6.3 |
| Celery task pattern | `core/tasks.py` | 6.1 |
| Sidebar meni | `core/menu.py` | 6.2, 6.3 |
| Core URLs | `core/urls.py` | 6.2, 6.3 |
| AuditlogMiddleware | `core/middleware.py` | 6.1 |

### GdprRequest Model - Detaljan dizajn

Model se dodaje u **postojeci** `core/models.py` (vec sadrzi `SiteSettings`):

```python
class GdprRequestType(models.TextChoices):
    ACCESS = "ACCESS", _("Pristup podacima")
    DELETION = "DELETION", _("Brisanje podataka")

class GdprRequestStatus(models.TextChoices):
    PENDING = "PENDING", _("Na čekanju")
    PROCESSING = "PROCESSING", _("U obradi")
    COMPLETED = "COMPLETED", _("Završeno")
    CANCELLED = "CANCELLED", _("Otkazano")

class GdprRequest(models.Model):
    requester_email = models.EmailField(_("Email podnosioca"))
    request_type = models.CharField(
        _("Tip zahteva"), max_length=20, choices=GdprRequestType.choices
    )
    status = models.CharField(
        _("Status"), max_length=20,
        choices=GdprRequestStatus.choices,
        default=GdprRequestStatus.PENDING,
    )
    notes = models.TextField(_("Napomene"), blank=True)
    received_date = models.DateField(_("Datum prijema"))
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    created_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True,
        related_name="gdpr_requests_created", verbose_name=_("Kreirao"),
    )
    processed_at = models.DateTimeField(_("Obrađeno"), null=True, blank=True)
    processed_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="gdpr_requests_processed", verbose_name=_("Obradio"),
    )
    completed_at = models.DateTimeField(_("Završeno"), null=True, blank=True)
    grace_period_end = models.DateField(_("Kraj grace perioda"), null=True, blank=True)
    cancellation_reason = models.TextField(_("Razlog otkazivanja"), blank=True)

    class Meta:
        verbose_name = _("GDPR zahtev")
        verbose_name_plural = _("GDPR zahtevi")
        ordering = ["-created_at"]

    def __str__(self):
        return f"GDPR-{self.pk}: {self.requester_email} ({self.get_request_type_display()})"
```

### User Model - Anonimizacija

User model (`users/models.py`) koristi `email` kao USERNAME_FIELD. Pri anonimizaciji:
- `email` -> `deleted_<pk>@anonymized.local` (mora biti unique)
- `name` -> prazno
- `is_active` -> False
- `set_unusable_password()`

**VAZNO:** NE brisi User jer ce LogEntry reference pucati. Anonimizuj umesto brisanja.

### Author Model - Anonimizacija

Author (`articles/models.py`) ima personalne podatke:
- `given_name` -> "[Anonimizirano]"
- `surname` -> "[Anonimizirano]"
- `email` -> "" (blank=True, safe to clear)
- `orcid` -> "" (blank=True, safe to clear)
- `orcid_authenticated` -> False

Author vec ima `SoftDeleteMixin` (Story 6.3). Za GDPR: PRVO soft_delete(), pa nakon grace perioda anonimizuj polja.

### Audit Log Entries

`auditlog.models.LogEntry` ima `actor` FK na User. Za anonimizaciju:
```python
from auditlog.models import LogEntry
LogEntry.objects.filter(actor=user).update(actor=None)
```

LogEntry zapisi se NE brisu - ostaju za compliance (NFR13: cuvanje logova 1+ godina). Samo se actor veza uklanja.

### Celery Task Pattern

Koristi isti pattern kao `audit_log_archive_task` u `core/tasks.py`:

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def gdpr_permanent_anonymize_task(self, gdpr_request_id):
    from doi_portal.core.models import GdprRequest, GdprRequestStatus
    # ... implementacija
```

Za zakazivanje task-a sa ETA (30 dana):
```python
from datetime import timedelta
from django.utils import timezone

eta = timezone.now() + timedelta(days=30)
gdpr_permanent_anonymize_task.apply_async(
    args=[gdpr_request.id],
    eta=eta,
)
```

**VAZNO:** Celery `apply_async(eta=...)` zahteva persistent broker (Redis). Task se cuva u brokeru do izvrsenja. Ako se broker restartuje, task se gubi. Zato task u `process_deletion_request` setuje `grace_period_end` datum, a DODATNO moze imati periodic task (Celery Beat) koji proverava expired grace periode.

### Alternativni pristup grace periodu (PREPORUCEN)

Umesto samo `apply_async(eta=30 dana)`, koristi Celery Beat periodic task:

```python
# core/tasks.py
@shared_task
def gdpr_check_grace_periods_task():
    """Periodic task - proverava istekle grace periode."""
    from doi_portal.core.models import GdprRequest, GdprRequestStatus
    from doi_portal.core.services import GdprService

    expired = GdprRequest.objects.filter(
        status=GdprRequestStatus.PROCESSING,
        grace_period_end__lte=timezone.now().date(),
    )
    for request in expired:
        GdprService.complete_request(request)
```

Registruj u `config/settings/base.py` CELERY_BEAT_SCHEDULE:
```python
CELERY_BEAT_SCHEDULE = {
    "gdpr-check-grace-periods": {
        "task": "doi_portal.core.tasks.gdpr_check_grace_periods_task",
        "schedule": crontab(hour=2, minute=0),  # Svaki dan u 2:00
    },
}
```

### Sidebar meni pozicija

U `core/menu.py`, `gdpr_requests` ide POSLE `deleted_items` a PRE `system_settings`:

```python
"deleted_items": { ... },        # Existing (Story 6.3)
"gdpr_requests": {               # NEW (Story 6.4)
    "label": "GDPR zahtevi",
    "icon": "bi-shield-lock",
    "url_name": "core:gdpr-request-list",
    "roles": ["Superadmin"],
},
"system_settings": { ... },      # Existing
```

### URL konfiguracija

Dodaj u postojeci `core/urls.py`. URL-ovi ce biti pod `dashboard/audit-log/gdpr/...`:

```python
urlpatterns = [
    # Existing (Story 6.2, 6.3)
    ...
    # NEW (Story 6.4)
    path("gdpr/", views.GdprRequestListView.as_view(), name="gdpr-request-list"),
    path("gdpr/create/", views.GdprRequestCreateView.as_view(), name="gdpr-request-create"),
    path("gdpr/<int:pk>/", views.GdprRequestDetailView.as_view(), name="gdpr-request-detail"),
    path("gdpr/<int:pk>/process/", views.gdpr_request_process, name="gdpr-request-process"),
    path("gdpr/<int:pk>/cancel/", views.gdpr_request_cancel, name="gdpr-request-cancel"),
    path("gdpr/<int:pk>/report/", views.gdpr_request_download_report, name="gdpr-request-report"),
]
```

### Template struktura

```
templates/core/
├── audit_log_list.html          # Existing (Story 6.2)
├── audit_log_detail.html        # Existing (Story 6.2)
├── deleted_items.html           # Existing (Story 6.3)
├── gdpr_request_list.html       # NEW (Story 6.4)
├── gdpr_request_form.html       # NEW (Story 6.4)
├── gdpr_request_detail.html     # NEW (Story 6.4)
```

### Confirmation Report Format

Plain text (`.txt`) download - NE PDF (ne treba novi dependency):

```
========================================
GDPR ZAHTEV - IZVEŠTAJ O OBRADI
========================================

Zahtev br.: GDPR-42
Email podnosioca: user@example.com
Tip zahteva: Brisanje podataka
Datum prijema: 2026-03-14
Datum obrade: 2026-04-14
Status: Završeno

OBRAĐENI PODACI:
- Korisnički nalog: Anonimizovan
- Autorski zapisi: 3 anonimizovano
- Revizioni log: 15 zapisa - actor veza uklonjena

NAPOMENA: Svi personalni podaci su trajno anonimizovani
u skladu sa GDPR regulativom.
========================================
```

### Anti-patterns (ZABRANJENO)

- NE brisi User nalog fizicki - samo anonimizuj (LogEntry FK reference)
- NE brisi LogEntry zapise - GDPR zahteva audit trail (NFR13)
- NE koristi JSON response za HTMX endpointe - uvek HTML
- NE dodaj PDF library (reportlab, weasyprint) - koristi plain text za izvestaj
- NE stavljaj business logiku u views - koristi `core/services.py`
- NE koristi `role_required` na CBV - koristi `SuperadminRequiredMixin`
- NE dodaj requirements u `requirements/*.txt` - projekat koristi `uv`
- NE kreiraj novi Django app za GDPR - sve ide u `core`
- NE koristi Django Admin za GDPR zahteve - custom views

### Biblioteke i verzije

**NE dodaj nove dependencies.** Sve potrebno je vec instalirano:
- Django 5.2+ (CBV, FBV, ModelForm, migracije)
- Celery (shared_task, apply_async, Beat schedule)
- Redis (Celery broker, persistent za ETA tasks)
- HTMX 2.0.8 (confirmation dialogs)
- Bootstrap 5.3+ (tabele, forme, badge-ovi)
- django-auditlog 3.0.0 (LogEntry model, auto-registracija)

### Project Structure Notes

- `doi_portal/doi_portal/core/models.py` - IZMENI (dodaj GdprRequest, GdprRequestType, GdprRequestStatus)
- `doi_portal/doi_portal/core/forms.py` - KREIRAJ (GdprRequestForm)
- `doi_portal/doi_portal/core/services.py` - KREIRAJ (GdprService)
- `doi_portal/doi_portal/core/views.py` - IZMENI (dodaj GDPR views)
- `doi_portal/doi_portal/core/urls.py` - IZMENI (dodaj GDPR URL-ove)
- `doi_portal/doi_portal/core/menu.py` - IZMENI (dodaj gdpr_requests meni item)
- `doi_portal/doi_portal/core/tasks.py` - IZMENI (dodaj gdpr_permanent_anonymize_task, gdpr_check_grace_periods_task)
- `doi_portal/config/settings/base.py` - IZMENI (dodaj CELERY_BEAT_SCHEDULE za grace period check)
- `doi_portal/doi_portal/templates/core/gdpr_request_list.html` - KREIRAJ
- `doi_portal/doi_portal/templates/core/gdpr_request_form.html` - KREIRAJ
- `doi_portal/doi_portal/templates/core/gdpr_request_detail.html` - KREIRAJ
- `doi_portal/doi_portal/core/tests/test_gdpr.py` - KREIRAJ
- `doi_portal/doi_portal/core/migrations/XXXX_gdpr_request.py` - AUTO-GENERISANA

### References

- [Source: docs/project-context.md#Audit-Logging] - django-auditlog registracija
- [Source: _bmad-output/planning-artifacts/epics.md#Story-6.4] - BDD acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR50] - FR50: Superadmin moze obraditi zahtev za brisanje podataka (GDPR)
- [Source: _bmad-output/planning-artifacts/prd.md#NFR13] - NFR13: GDPR - Soft delete, pravo na brisanje, cuvanje logova 1+ godina
- [Source: _bmad-output/planning-artifacts/architecture.md#Audit-Logging] - django-auditlog, GDPR compliance
- [Source: _bmad-output/implementation-artifacts/6-1-audit-log-integration.md] - Audit log setup, Celery task pattern
- [Source: _bmad-output/implementation-artifacts/6-2-audit-log-viewer.md] - SuperadminRequiredMixin, core URL pattern, sidebar meni
- [Source: _bmad-output/implementation-artifacts/6-3-soft-delete-implementation.md] - SoftDeleteMixin, SoftDeleteManager, Author soft delete
- [Source: doi_portal/core/views.py] - SuperadminRequiredMixin, DeletedItemsView pattern
- [Source: doi_portal/core/urls.py] - Postojeci core URL-ovi
- [Source: doi_portal/core/menu.py] - Sidebar meni konfiguracija
- [Source: doi_portal/core/models.py] - Postojeci SiteSettings model
- [Source: doi_portal/core/tasks.py] - audit_log_archive_task pattern
- [Source: doi_portal/core/mixins.py] - SoftDeleteMixin, soft_delete(), restore()
- [Source: doi_portal/users/models.py] - User model (email=USERNAME_FIELD, name field)
- [Source: doi_portal/articles/models.py#Author] - Author model sa SoftDeleteMixin, personalni podaci
- [Source: doi_portal/core/permissions.py] - role_required dekorator za FBV

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Migration created via `DJANGO_SETTINGS_MODULE=config.settings.test` due to missing local DATABASE_URL env var

### Completion Notes List

- All 13 tasks completed with 31 dedicated GDPR tests + 1763 total suite passing
- GdprRequest model with TextChoices for status/type, auditlog registered via CoreConfig.ready()
- GdprService with 6 static methods: identify_affected_data, process_deletion_request, cancel_request, complete_request, generate_confirmation_report
- Two Celery tasks: gdpr_permanent_anonymize_task (ETA-based) + gdpr_check_grace_periods_task (daily Beat)
- Author.all_objects.filter(email=...) used to catch soft-deleted authors
- TXT report format (no PDF dependency)
- Superadmin-only access enforced via SuperadminRequiredMixin (CBV) and role_required (FBV)

### File List

- `doi_portal/doi_portal/core/models.py` - MODIFIED (GdprRequest, GdprRequestType, GdprRequestStatus)
- `doi_portal/doi_portal/core/apps.py` - MODIFIED (auditlog.register in ready())
- `doi_portal/doi_portal/core/forms.py` - CREATED (GdprRequestForm)
- `doi_portal/doi_portal/core/services.py` - CREATED (GdprService)
- `doi_portal/doi_portal/core/tasks.py` - MODIFIED (gdpr_permanent_anonymize_task, gdpr_check_grace_periods_task)
- `doi_portal/doi_portal/core/views.py` - MODIFIED (GdprRequestListView, CreateView, DetailView, 3 FBVs)
- `doi_portal/doi_portal/core/urls.py` - MODIFIED (6 GDPR URL patterns)
- `doi_portal/doi_portal/core/menu.py` - MODIFIED (gdpr_requests menu item)
- `doi_portal/config/settings/base.py` - MODIFIED (CELERY_BEAT_SCHEDULE gdpr entry)
- `doi_portal/doi_portal/core/migrations/0003_gdpr_request.py` - CREATED (auto-generated)
- `doi_portal/doi_portal/templates/core/gdpr_request_list.html` - CREATED
- `doi_portal/doi_portal/templates/core/gdpr_request_form.html` - CREATED
- `doi_portal/doi_portal/templates/core/gdpr_request_detail.html` - CREATED
- `doi_portal/doi_portal/core/tests/test_gdpr.py` - CREATED (31 tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - MODIFIED (status -> review)
- `_bmad-output/implementation-artifacts/6-4-gdpr-data-request-handling.md` - MODIFIED (checkboxes, status)
