# Story 6.6: System Health Dashboard

Status: done

## Story

As a **Superadmin**,
I want **to see system health and statistics at a glance**,
So that **I can monitor the overall system status and quickly identify integration issues**.

## Acceptance Criteria

1. **AC1: Health Dashboard stranica** - Superadmin navigira na System > Zdravlje sistema. Stranica se ucitava na URL `dashboard/audit-log/system/health/`. Prikazuje se system health dashboard sa statistikama i status indikatorima. Non-Superadmin korisnici dobijaju 403 Forbidden.

2. **AC2: Content statistike** - Dashboard prikazuje sledece metrike:
   - Ukupno korisnika (aktivni/neaktivni) - format: "X aktivnih / Y neaktivnih"
   - Ukupno izdavaca (Publisher count)
   - Ukupno publikacija (Publication count)
   - Ukupno izdanja (Issue count)
   - Ukupno clanaka (Article count)
   - Clanci po statusu: nacrt (Draft), na pregledu (Review), spreman (Ready), objavljen (Published), povucen (Withdrawn)
   - Nedavna audit log aktivnost (broj LogEntry zapisa u poslednjih 24h)

3. **AC3: Integration status indikatori** - Dashboard prikazuje status indikatore za:
   - Database konekcija: OK/Greska (Django `connection.ensure_connection()`)
   - Redis konekcija: OK/Greska (redis ping via `django.core.cache`)
   - Celery worker-i: Pokrenut/Zaustavljen (Celery inspect ping)
   - S3 skladiste: Dostupno/Greska (boto3 head_bucket ili settings check)
   Svaki indikator ima zeleni badge za OK, crveni za gresku. Uz gresku se prikazuje kratak opis problema i preporuka za resavanje.

4. **AC4: Greska u health check-u** - Kada neka komponenta nije dostupna, crveni indikator se prikazuje sa porukom greske. Preporuke za resavanje:
   - Database: "Proverite PostgreSQL servis i konekcione parametre"
   - Redis: "Proverite Redis servis na konfigurisanom host-u"
   - Celery: "Proverite da li su Celery worker-i pokrenuti"
   - S3: "Proverite AWS kredencijale i S3 bucket konfiguraciju"

5. **AC5: Svezina podataka** - Podaci se ucitavaju svaki put pri ucitavanju stranice (nema agresivnog kesiranja - podaci su uvek svezi). Prikazuje se "Poslednje azuriranje" timestamp u formatu "dd.mm.yyyy HH:MM:SS". Stranica se moze rucno osveziti standardnim browser refresh-om.

6. **AC6: Sidebar meni** - Stavka "Zdravlje sistema" sa ikonom `bi-heart-pulse` se dodaje u sidebar meni POSLE "Sentry test". Vidljiva samo za Superadmin rolu.

## Tasks / Subtasks

- [x] Task 1: Kreiraj health check servis modul (AC: #2, #3, #4)
  - [x] 1.1 Kreiraj `doi_portal/doi_portal/core/health.py` sa funkcijom `get_system_health() -> dict`
  - [x] 1.2 Implementiraj `_check_database() -> dict` - koristi `django.db.connection.ensure_connection()`, vraca `{"status": "ok"|"error", "message": str}`
  - [x] 1.3 Implementiraj `_check_redis() -> dict` - koristi `django.core.cache.cache` (default cache backend), pozovi `cache.set("health_check", "1", 10)` pa `cache.get("health_check")`, vraca status dict
  - [x] 1.4 Implementiraj `_check_celery() -> dict` - koristi `celery_app.control.inspect().ping()` sa timeout=3.0, vraca status dict. Ako nema worker-a ili timeout, vraca error
  - [x] 1.5 Implementiraj `_check_storage() -> dict` - proverava da li je `DEFAULT_FILE_STORAGE` ili `STORAGES["default"]` konfigurisan za S3 (sadrzi "S3" ili "s3" u backend klasi). Ako jeste, pokusava `default_storage.exists("health_check_test")`. Vraca status dict
  - [x] 1.6 Implementiraj `_get_content_statistics() -> dict` - koristi Django ORM aggregate za User (active/inactive count), Publisher count, Publication count, Issue count, Article count po statusu, LogEntry count za poslednjih 24h
  - [x] 1.7 `get_system_health()` poziva sve check funkcije, svaku u try/except, i vraca kompletni dict sa `statistics`, `integrations`, `checked_at` (timezone.now())

- [x] Task 2: Kreiraj SystemHealthView (AC: #1, #5)
  - [x] 2.1 U `doi_portal/doi_portal/core/views.py`, dodaj `SystemHealthView(SuperadminRequiredMixin, TemplateView)`
  - [x] 2.2 `template_name = "core/system_health.html"`
  - [x] 2.3 U `get_context_data()`: pozovi `get_system_health()` iz `core/health.py`, dodaj rezultat u context
  - [x] 2.4 Dodaj breadcrumbs: Kontrolna tabla > Zdravlje sistema

- [x] Task 3: Dodaj URL za health dashboard (AC: #1)
  - [x] 3.1 U `doi_portal/doi_portal/core/urls.py`, dodaj: `path("system/health/", views.SystemHealthView.as_view(), name="system-health")`

- [x] Task 4: Dodaj meni stavku (AC: #6)
  - [x] 4.1 U `doi_portal/doi_portal/core/menu.py`, dodaj `system_health` meni item POSLE `sentry_test`: `{"label": "Zdravlje sistema", "icon": "bi-heart-pulse", "url_name": "core:system-health", "roles": ["Superadmin"]}`

- [x] Task 5: Kreiraj template za health dashboard (AC: #1, #2, #3, #4, #5)
  - [x] 5.1 Kreiraj `doi_portal/doi_portal/templates/core/system_health.html` - extends `admin_base.html`
  - [x] 5.2 Sekcija "Sadrzaj sistema" - Bootstrap 5 kartice sa statistikama: korisnici, izdavaci, publikacije, izdanja, clanci
  - [x] 5.3 Sekcija "Clanci po statusu" - lista sa badge-ovima za svaki status (Draft, Review, Ready, Published, Withdrawn)
  - [x] 5.4 Sekcija "Nedavna aktivnost" - broj audit log zapisa u poslednjih 24h
  - [x] 5.5 Sekcija "Status integracija" - kartice sa zelenim/crvenim badge-ovima za Database, Redis, Celery, S3
  - [x] 5.6 Svaka integracija sa greskom prikazuje preporuku za resavanje u `text-danger` paragrafu
  - [x] 5.7 Footer sa "Poslednje azuriranje" timestamp-om
  - [x] 5.8 Breadcrumbs: Kontrolna tabla > Zdravlje sistema

- [x] Task 6: Testovi za health check servis (AC: #2, #3, #4)
  - [x] 6.1 Kreiraj `doi_portal/doi_portal/core/tests/test_health.py`
  - [x] 6.2 Test: `_check_database()` vraca OK kada je DB dostupan
  - [x] 6.3 Test: `_check_redis()` vraca OK kada cache radi (mock cache.set/get)
  - [x] 6.4 Test: `_check_celery()` vraca error kada nema worker-a (mock inspect().ping() da vraca None)
  - [x] 6.5 Test: `_check_celery()` vraca OK kada worker odgovori (mock inspect().ping() sa validnim response-om)
  - [x] 6.6 Test: `_check_storage()` vraca OK kada storage radi (mock default_storage.exists)
  - [x] 6.7 Test: `_check_storage()` vraca error kada storage nije dostupan (mock exception)
  - [x] 6.8 Test: `_get_content_statistics()` vraca korektne brojeve (kreiraj test data sa factory)
  - [x] 6.9 Test: `get_system_health()` vraca kompletni dict sa svim kljucevima

- [x] Task 7: Testovi za view (AC: #1, #6)
  - [x] 7.1 Kreiraj testove u `doi_portal/doi_portal/core/tests/test_health.py` (isti fajl)
  - [x] 7.2 Test: Superadmin moze pristupiti health dashboard stranici (200)
  - [x] 7.3 Test: Non-Superadmin dobija 403
  - [x] 7.4 Test: Anoniman korisnik dobija redirect na login (302)
  - [x] 7.5 Test: Stranica koristi ispravan template (`core/system_health.html`)
  - [x] 7.6 Test: Context sadrzi `health_data` kljuc

- [x] Task 8: Testovi za meni (AC: #6)
  - [x] 8.1 Test: Sidebar meni prikazuje "Zdravlje sistema" samo za Superadmin
  - [x] 8.2 Test: Non-Superadmin ne vidi "Zdravlje sistema" u meniju

- [x] Task 9: Regression testovi (AC: svi)
  - [x] 9.1 Pokreni kompletnu test suite: `pytest` - svi postojeci testovi moraju proci
  - [x] 9.2 Verifikuj da sidebar meni ispravno prikazuje novu stavku

## Dev Notes

### KRITICNO: Ovo je POSLEDNJA story u Epic 6

Ova story zavrsava Epic 6 (Compliance & Monitoring). Nakon implementacije, epic-6 status se moze promeniti na `done` u sprint-status.yaml.

### Postojeca infrastruktura koju MORAS koristiti

| Komponenta | Lokacija | Story |
|------------|----------|-------|
| SuperadminRequiredMixin | `core/views.py` | 6.2 |
| Sidebar meni | `core/menu.py` | 6.2, 6.3, 6.4, 6.5 |
| Core URLs | `core/urls.py` | 6.2, 6.3, 6.4, 6.5 |
| admin_base.html | `templates/admin_base.html` | 1.7 |
| DashboardView | `core/views.py` | 1.7, 3.8 |
| get_admin_statistics | `dashboard/services.py` | 3.8 |
| ArticleStatus enum | `articles/models.py` | 3.1 |
| User model | `users/models.py` | 1.2 |

### Health Check Servis - Detaljni dizajn

```python
# core/health.py
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone

from auditlog.models import LogEntry


def get_system_health() -> dict:
    """Collect all health check data and content statistics."""
    return {
        "statistics": _get_content_statistics(),
        "integrations": {
            "database": _safe_check(_check_database),
            "redis": _safe_check(_check_redis),
            "celery": _safe_check(_check_celery),
            "storage": _safe_check(_check_storage),
        },
        "checked_at": timezone.now(),
    }


def _safe_check(check_func) -> dict:
    """Wrapper that catches all exceptions from health checks."""
    try:
        return check_func()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _check_database() -> dict:
    connection.ensure_connection()
    return {"status": "ok", "message": "PostgreSQL konekcija aktivna"}


def _check_redis() -> dict:
    cache.set("health_check", "1", 10)
    value = cache.get("health_check")
    if value == "1":
        return {"status": "ok", "message": "Redis konekcija aktivna"}
    return {"status": "error", "message": "Redis cache read/write neuspešan"}


def _check_celery() -> dict:
    from config.celery_app import app as celery_app

    inspector = celery_app.control.inspect(timeout=3.0)
    ping_result = inspector.ping()
    if ping_result:
        worker_count = len(ping_result)
        return {"status": "ok", "message": f"{worker_count} worker(a) aktivno"}
    return {"status": "error", "message": "Nema aktivnih Celery worker-a"}


def _check_storage() -> dict:
    from django.core.files.storage import default_storage

    # Just check if storage is accessible
    default_storage.exists("health_check_test")
    return {"status": "ok", "message": "Skladište dostupno"}


def _get_content_statistics() -> dict:
    from doi_portal.articles.models import Article, ArticleStatus
    from doi_portal.issues.models import Issue
    from doi_portal.publications.models import Publication
    from doi_portal.publishers.models import Publisher
    from doi_portal.users.models import User

    from django.db.models import Count, Q

    # User counts
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()

    # Content counts
    publisher_count = Publisher.objects.count()
    publication_count = Publication.objects.count()
    issue_count = Issue.objects.count()

    # Article counts by status
    article_counts = Article.objects.aggregate(
        total=Count("id"),
        draft=Count("id", filter=Q(status=ArticleStatus.DRAFT)),
        review=Count("id", filter=Q(status=ArticleStatus.REVIEW)),
        ready=Count("id", filter=Q(status=ArticleStatus.READY)),
        published=Count("id", filter=Q(status=ArticleStatus.PUBLISHED)),
        withdrawn=Count("id", filter=Q(status=ArticleStatus.WITHDRAWN)),
    )

    # Recent audit activity (last 24h)
    since = timezone.now() - timedelta(hours=24)
    recent_audit_count = LogEntry.objects.filter(timestamp__gte=since).count()

    return {
        "active_users": active_users,
        "inactive_users": inactive_users,
        "publisher_count": publisher_count,
        "publication_count": publication_count,
        "issue_count": issue_count,
        "article_counts": article_counts,
        "recent_audit_count": recent_audit_count,
    }
```

### SystemHealthView - Dizajn

```python
# U core/views.py
class SystemHealthView(SuperadminRequiredMixin, TemplateView):
    """System health dashboard for Superadmin."""

    template_name = "core/system_health.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from doi_portal.core.health import get_system_health

        context["health_data"] = get_system_health()
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": "dashboard"},
            {"label": "Zdravlje sistema", "url": None},
        ]
        return context
```

### URL Routing

Core app je mountovan na `dashboard/audit-log/` u glavnom urls.py. Novi endpoint ce biti:
`/dashboard/audit-log/system/health/`

```python
# U core/urls.py - dodaj posle sentry-test
path("system/health/", views.SystemHealthView.as_view(), name="system-health"),
```

### Sidebar meni pozicija

U `core/menu.py`, `system_health` ide POSLE `sentry_test` (poslednji item):

```python
"sentry_test": { ... },            # Existing (Story 6.5)
"system_health": {                  # NEW (Story 6.6)
    "label": "Zdravlje sistema",
    "icon": "bi-heart-pulse",
    "url_name": "core:system-health",
    "roles": ["Superadmin"],
},
```

### Template struktura

```
templates/core/
├── system_health.html    # NEW (Story 6.6)
```

Stranica sadrzi:
- Breadcrumbs: Kontrolna tabla > Zdravlje sistema
- Kartica "Korisnici" sa brojem aktivnih/neaktivnih
- Red kartica sa brojevima: izdavaci, publikacije, izdanja, clanci
- Sekcija "Clanci po statusu" sa badge-ovima u boji (success za Published, warning za Review, secondary za Draft, info za Ready, danger za Withdrawn)
- Sekcija "Nedavna aktivnost" sa brojem audit zapisa (24h)
- Sekcija "Status integracija" sa 4 kartice (Database, Redis, Celery, S3) - svaka sa zelenim/crvenim badge-om
- Footer: "Poslednje azuriranje: dd.mm.yyyy HH:MM:SS"

### Celery inspect timeout

`celery_app.control.inspect(timeout=3.0)` - timeout od 3 sekunde je dovoljan za lokalni ping. U produkciji moze biti sporije, ali 3s je razuman kompromis izmedju responsivnosti stranice i detekcije worker-a.

VAZNO: Celery inspect je sinhroni poziv koji ce blokirati request. Ovo je prihvatljivo jer:
- Stranica se ucitava samo za Superadmin (retko)
- Timeout od 3s je kratak
- Nije kriticna stranica za performance

### Anti-patterns (ZABRANJENO)

- NE koristi Django management command za health check - koristi servis modul
- NE koristi JSON response - HTML (HTMX pravila)
- NE dodaj nove Python dependencies - sve potrebno je vec instalirano
- NE dodaj requirements u `requirements/*.txt` - projekat koristi `uv`
- NE koristi `role_required` na CBV - koristi `SuperadminRequiredMixin`
- NE implementiraj auto-refresh sa JavaScript/HTMX polling - standardni page load je dovoljan
- NE kesriaj health check rezultate - podaci moraju biti svezi
- NE koristi Celery task za health check - sinhroni poziv u view-u
- NE pokusavaj da se konektujes na S3 endpoint direktno - koristi `default_storage` API

### Biblioteke i verzije

**NE dodaj nove dependencies.** Sve potrebno je vec instalirano:
- Django 5.2+ (TemplateView, connection, cache)
- Celery (inspect API)
- django-storages (default_storage)
- django-auditlog (LogEntry)
- Bootstrap 5.3+ (kartice, badge-ovi, grid)
- Bootstrap Icons (bi-heart-pulse, bi-check-circle, bi-x-circle)

### Project Structure Notes

- `doi_portal/doi_portal/core/health.py` - KREIRAJ (health check servis)
- `doi_portal/doi_portal/core/views.py` - IZMENI (dodaj SystemHealthView)
- `doi_portal/doi_portal/core/urls.py` - IZMENI (dodaj system-health URL)
- `doi_portal/doi_portal/core/menu.py` - IZMENI (dodaj system_health meni item)
- `doi_portal/doi_portal/templates/core/system_health.html` - KREIRAJ
- `doi_portal/doi_portal/core/tests/test_health.py` - KREIRAJ

### References

- [Source: docs/project-context.md#Tech-Stack] - Django 5.2+, Redis, Celery, Bootstrap 5.3+
- [Source: docs/project-context.md#Celery-Tasks] - Celery app konfiguracija
- [Source: docs/project-context.md#HTMX-Pravila] - Uvek HTML response, nikad JSON
- [Source: _bmad-output/planning-artifacts/epics.md#Story-6.6] - BDD acceptance criteria
- [Source: _bmad-output/implementation-artifacts/6-5-system-monitoring-with-sentry.md] - Prethodna story, SuperadminRequiredMixin pattern, sidebar meni, core URL-ovi
- [Source: doi_portal/doi_portal/dashboard/services.py] - Postojece statistike (get_admin_statistics)
- [Source: doi_portal/doi_portal/core/views.py] - SuperadminRequiredMixin, DashboardView pattern
- [Source: doi_portal/doi_portal/core/urls.py] - Postojeci core URL-ovi (system/ prefix pattern)
- [Source: doi_portal/doi_portal/core/menu.py] - Sidebar meni konfiguracija
