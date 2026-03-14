# Story 6.5: System Monitoring with Sentry

Status: done

## Story

As a **system administrator**,
I want **error tracking and performance monitoring integrated via Sentry**,
So that **issues are detected and resolved quickly with full context**.

## Acceptance Criteria

1. **AC1: Sentry DSN konfiguracija** - `SENTRY_DSN` se cita iz environment varijable. Kada je `SENTRY_DSN` prazan ili nije setovan, Sentry se NE inicijalizuje (graceful degradation). Sentry inicijalizacija koristi try/except za ImportError (vec implementirano u `production.py`).

2. **AC2: Automatski error capture** - Unhandled exceptions se automatski salju u Sentry sa stack trace-om, request data (URL, method, headers), user kontekstom (user ID, email, role). Errors su grupisani po tipu u Sentry dashboard-u.

3. **AC3: Environment i release tagging** - Svaki Sentry event sadrzi `environment` tag (local/staging/production) iz env varijable `SENTRY_ENVIRONMENT`. Release verzija se salje preko `SENTRY_RELEASE` env varijable (opciono). `server_name` je disabled za sigurnost.

4. **AC4: Performance monitoring** - Transaction traces se salju u Sentry. `SENTRY_TRACES_SAMPLE_RATE` kontrolise procenat trace-ova (default: 0.0 = iskljuceno, 1.0 = sve). Spori request-i i query-ji se identifikuju u Sentry Performance tab-u.

5. **AC5: Sensitive data scrubbing** - Lozinke, tokeni, session ID-evi su scrub-ovani iz Sentry events. PII (email, ime) je maskirano po defaultu (`send_default_pii=False`). Request body sa sensitive poljima (password, token, secret, dsn, api_key, credit_card) je filtriran. `before_send` callback uklanja sensitive cookies i headers.

6. **AC6: Celery task error capture** - `CeleryIntegration` je aktivan (vec implementirano). Task errori se salju u Sentry sa task imenom, argumentima i retry informacijama. `CeleryIntegration(propagate_traces=True)` za distribuirani tracing.

7. **AC7: Custom Sentry test endpoint** - Superadmin-only endpoint `GET /dashboard/system/sentry-test/` generise test error koji se salje u Sentry. Response potvrdjuje da li je Sentry konfigurisan i da li je test event poslan. Endpoint je dostupan samo u DEBUG=False modu ili sa eksplicitnim `SENTRY_DSN`.

8. **AC8: Logging integration** - `LoggingIntegration` hvata INFO+ kao breadcrumbs i ERROR+ kao events (vec implementirano). Python `logging` modul radi normalno bez obzira na Sentry status. `sentry_sdk` logger je na ERROR level da spreci rekurziju.

## Tasks / Subtasks

- [x] Task 1: Prosiri Sentry konfiguraciju u production.py (AC: #2, #3, #4, #5, #6, #8)
  - [x] 1.1 U `config/settings/production.py`, prosiri `sentry_sdk.init()` sa: `release=env("SENTRY_RELEASE", default=None)`, `send_default_pii=False`, `server_name=None`
  - [x] 1.2 Dodaj `before_send` callback koji filtrira sensitive data: scrub cookies (`sessionid`, `csrftoken`), scrub `Authorization` header, scrub request body polja koja sadrze `password`, `token`, `secret`, `dsn`, `api_key`
  - [x] 1.3 Update `CeleryIntegration(propagate_traces=True)` za distribuirani tracing
  - [x] 1.4 Dodaj `profiles_sample_rate=env.float("SENTRY_PROFILES_SAMPLE_RATE", default=0.0)` za profiling support

- [x] Task 2: Dodaj Sentry konfiguraciju za local/test settings (AC: #1)
  - [x] 2.1 U `config/settings/local.py`, dodaj komentar da je Sentry disabled u local okruzenju (vec default ponasanje - nema SENTRY_DSN)
  - [x] 2.2 U `config/settings/test.py`, verifikuj da Sentry NIJE aktivan (nema DSN u test env)

- [x] Task 3: Kreiraj Sentry test endpoint (AC: #7)
  - [x] 3.1 U `core/views.py`, dodaj `SentryTestView(SuperadminRequiredMixin, View)` - GET handler
  - [x] 3.2 View proverava da li je `sentry_sdk` inicijalizovan (try import + check DSN)
  - [x] 3.3 Ako je Sentry aktivan: raise `Exception("Sentry test from DOI Portal")`, uhvati sa `sentry_sdk.capture_exception()`, vrati success poruku
  - [x] 3.4 Ako Sentry NIJE aktivan: vrati poruku "Sentry nije konfigurisan"
  - [x] 3.5 Response je HTML stranica (extends admin_base.html), NE JSON

- [x] Task 4: Dodaj URL za Sentry test (AC: #7)
  - [x] 4.1 U `core/urls.py`, dodaj: `path("system/sentry-test/", views.SentryTestView.as_view(), name="sentry-test")`

- [x] Task 5: Dodaj "Sentry test" meni item (AC: #7)
  - [x] 5.1 U `core/menu.py`, dodaj `sentry_test` meni item POSLE `system_settings`: `{"label": "Sentry test", "icon": "bi-bug", "url_name": "core:sentry-test", "roles": ["Superadmin"]}`

- [x] Task 6: Kreiraj template za Sentry test stranicu (AC: #7)
  - [x] 6.1 Kreiraj `templates/core/sentry_test.html` - extends `admin_base.html`
  - [x] 6.2 Prikazi status Sentry-ja (konfigurisan/nije), SENTRY_ENVIRONMENT vrednost (ako postoji), datum i vreme testa, rezultat (event poslan/Sentry nije aktivan)
  - [x] 6.3 Dugme "Posalji test error" sa HTMX POST ili standardni link
  - [x] 6.4 Breadcrumbs: Kontrolna tabla > Sentry test

- [x] Task 7: Kreiraj `before_send` callback modul (AC: #5)
  - [x] 7.1 U `core/sentry.py`, kreiraj `before_send(event, hint)` funkciju
  - [x] 7.2 Filtriranje: scrub request cookies (samo imena, ne vrednosti), scrub Authorization header, scrub body polja sa sensitive imenima
  - [x] 7.3 Import ovu funkciju u `production.py` i dodaj u `sentry_sdk.init(before_send=...)`

- [x] Task 8: Testovi za before_send callback (AC: #5)
  - [x] 8.1 Kreiraj `core/tests/test_sentry.py`
  - [x] 8.2 Test: `before_send` scrub-uje password iz request body
  - [x] 8.3 Test: `before_send` scrub-uje Authorization header
  - [x] 8.4 Test: `before_send` scrub-uje session cookies
  - [x] 8.5 Test: `before_send` ne menja event bez sensitive data
  - [x] 8.6 Test: `before_send` handla event bez request (e.g., Celery task error)

- [x] Task 9: Testovi za Sentry test endpoint (AC: #7, #8)
  - [x] 9.1 Test: Superadmin moze pristupiti Sentry test stranici (200)
  - [x] 9.2 Test: Non-Superadmin dobija 403
  - [x] 9.3 Test: Stranica prikazuje Sentry status informacije

- [x] Task 10: Regression testovi (AC: svi)
  - [x] 10.1 Pokreni kompletnu test suite: `pytest` - svi postojeci testovi moraju proci
  - [x] 10.2 Verifikuj da sidebar meni prikazuje "Sentry test" samo za Superadmin

## Dev Notes

### KRITICNO: Sentry SDK je VEC instaliran i konfigurisan

Cookiecutter Django je generisao Sentry integraciju u `production.py`. Story 6.5 PROSIRUJE postojecu konfiguraciju - NE krece od nule.

**Vec implementirano (NE diraj):**
- `sentry-sdk==2.50.0` u `pyproject.toml`
- Basic `sentry_sdk.init()` u `production.py`
- `DjangoIntegration()`, `CeleryIntegration()`, `RedisIntegration()`, `LoggingIntegration()`
- `SENTRY_DSN` env varijabla
- `SENTRY_ENVIRONMENT` env varijabla
- `SENTRY_TRACES_SAMPLE_RATE` env varijabla
- `SENTRY_LOG_LEVEL` env varijabla
- Graceful ImportError handling (try/except)

**Treba dodati/prosiriti:**
- `send_default_pii=False` (sprecava slanje email-a, IP-a korisnika)
- `server_name=None` (sprecava leak hostname-a)
- `release` parametar iz env varijable
- `before_send` callback za scrubbing sensitive data
- `CeleryIntegration(propagate_traces=True)` (update existing)
- `profiles_sample_rate` za profiling
- Sentry test endpoint za Superadmin

### Postojeca infrastruktura koju MORAS koristiti

| Komponenta | Lokacija | Story |
|------------|----------|-------|
| SuperadminRequiredMixin | `core/views.py` | 6.2 |
| Sidebar meni | `core/menu.py` | 6.2, 6.3, 6.4 |
| Core URLs | `core/urls.py` | 6.2, 6.3, 6.4 |
| admin_base.html | `templates/admin_base.html` | 1.7 |
| Sentry production config | `config/settings/production.py` | Cookiecutter |

### before_send Callback - Detaljni dizajn

```python
# core/sentry.py
SENSITIVE_FIELDS = {"password", "token", "secret", "dsn", "api_key", "credit_card", "authorization"}
SENSITIVE_COOKIES = {"sessionid", "csrftoken", "__Secure-sessionid", "__Secure-csrftoken"}
SENSITIVE_HEADERS = {"Authorization", "Cookie", "X-CSRFToken"}


def before_send(event, hint):
    """Scrub sensitive data from Sentry events before sending."""
    request_data = event.get("request", {})

    # Scrub headers
    headers = request_data.get("headers", {})
    if headers:
        for key in list(headers.keys()):
            if key.lower() in {h.lower() for h in SENSITIVE_HEADERS}:
                headers[key] = "[Filtered]"

    # Scrub cookies
    cookies = request_data.get("cookies", {})
    if cookies:
        for key in list(cookies.keys()):
            if key in SENSITIVE_COOKIES:
                cookies[key] = "[Filtered]"

    # Scrub request body (form data)
    data = request_data.get("data", {})
    if isinstance(data, dict):
        for key in list(data.keys()):
            if any(s in key.lower() for s in SENSITIVE_FIELDS):
                data[key] = "[Filtered]"

    return event
```

### Production settings prosirenje

Izmeni POSTOJECI blok u `config/settings/production.py`:

```python
# DODAJ import na vrh fajla (posle existing imports):
# Nema novih imports - before_send se importuje unutar if bloka

if HAS_SENTRY and SENTRY_DSN:
    from doi_portal.core.sentry import before_send  # NEW

    SENTRY_LOG_LEVEL = env.int("DJANGO_SENTRY_LOG_LEVEL", logging.INFO)

    sentry_logging = LoggingIntegration(
        level=SENTRY_LOG_LEVEL,
        event_level=logging.ERROR,
    )
    integrations = [
        sentry_logging,
        DjangoIntegration(),
        CeleryIntegration(propagate_traces=True),  # UPDATED
        RedisIntegration(),
    ]
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=integrations,
        environment=env("SENTRY_ENVIRONMENT", default="production"),
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
        profiles_sample_rate=env.float("SENTRY_PROFILES_SAMPLE_RATE", default=0.0),  # NEW
        release=env("SENTRY_RELEASE", default=None),  # NEW
        send_default_pii=False,  # NEW - ne salji email/IP
        server_name=None,  # NEW - ne leak-uj hostname
        before_send=before_send,  # NEW - custom scrubbing
    )
```

### Sentry Test View - Dizajn

```python
# U core/views.py
class SentryTestView(SuperadminRequiredMixin, View):
    def get(self, request):
        sentry_active = False
        sentry_dsn_configured = False
        event_id = None

        try:
            import sentry_sdk
            client = sentry_sdk.get_client()
            sentry_dsn_configured = bool(client.dsn)
            sentry_active = client.is_active()
        except ImportError:
            pass

        if sentry_active and request.GET.get("send_test"):
            try:
                raise Exception("DOI Portal - Sentry test event")
            except Exception:
                import sentry_sdk
                event_id = sentry_sdk.capture_exception()

        context = {
            "sentry_active": sentry_active,
            "sentry_dsn_configured": sentry_dsn_configured,
            "event_id": event_id,
        }
        return render(request, "core/sentry_test.html", context)
```

**VAZNO:** `send_test` se triggeruje preko GET parametra (`?send_test=1`) da bi se izbegla potreba za CSRF token handlingom. Ovo je safe jer:
- Endpoint je Superadmin-only
- Test error je benign (ne menja state)
- Event ID se prikazuje za verifikaciju u Sentry UI

### Template za Sentry test

```
templates/core/
├── sentry_test.html    # NEW (Story 6.5)
```

Stranica prikazuje:
- Kartica sa Sentry statusom (aktivan/neaktivan) - zeleni/crveni badge
- Ako je aktivan: dugme "Posalji test error" (link na `?send_test=1`)
- Ako je poslan test: prikaz event_id sa linkom "Proveri u Sentry dashboard-u"
- Informativni tekst o konfiguraciji

### Sidebar meni pozicija

U `core/menu.py`, `sentry_test` ide POSLE `system_settings` (poslednji system item):

```python
"system_settings": { ... },      # Existing
"sentry_test": {                  # NEW (Story 6.5)
    "label": "Sentry test",
    "icon": "bi-bug",
    "url_name": "core:sentry-test",
    "roles": ["Superadmin"],
},
```

### Anti-patterns (ZABRANJENO)

- NE brisi postojecu Sentry konfiguraciju - PROSIRI je
- NE koristi `send_default_pii=True` - GDPR zahteva zastitou PII
- NE hardcode-uj SENTRY_DSN u settings - uvek iz env varijable
- NE koristi JSON response za Sentry test endpoint - HTML (HTMX pravila)
- NE dodaj nove Python dependencies - `sentry-sdk` je vec instaliran
- NE dodaj requirements u `requirements/*.txt` - projekat koristi `uv`
- NE stavljaj `before_send` inline u `production.py` - zasebni `core/sentry.py` modul
- NE koristi `role_required` na CBV - koristi `SuperadminRequiredMixin`
- NE testiraj Sentry init u unit testovima - testiraj samo `before_send` callback i view

### Biblioteke i verzije

**NE dodaj nove dependencies.** Sve potrebno je vec instalirano:
- `sentry-sdk==2.50.0` (vec u `pyproject.toml`)
- Django 5.2+ (CBV, View)
- Bootstrap 5.3+ (kartice, badge-ovi)

### Project Structure Notes

- `doi_portal/config/settings/production.py` - IZMENI (prosiri sentry_sdk.init)
- `doi_portal/doi_portal/core/sentry.py` - KREIRAJ (before_send callback)
- `doi_portal/doi_portal/core/views.py` - IZMENI (dodaj SentryTestView)
- `doi_portal/doi_portal/core/urls.py` - IZMENI (dodaj sentry-test URL)
- `doi_portal/doi_portal/core/menu.py` - IZMENI (dodaj sentry_test meni item)
- `doi_portal/doi_portal/templates/core/sentry_test.html` - KREIRAJ
- `doi_portal/doi_portal/core/tests/test_sentry.py` - KREIRAJ

### References

- [Source: docs/project-context.md#Celery-Tasks] - Celery task naming i retry pattern
- [Source: docs/project-context.md#Audit-Logging] - django-auditlog registracija
- [Source: _bmad-output/planning-artifacts/epics.md#Story-6.5] - BDD acceptance criteria
- [Source: _bmad-output/planning-artifacts/architecture.md#Infrastructure] - Sentry kao monitoring tool
- [Source: doi_portal/config/settings/production.py] - Postojeca Sentry konfiguracija (Cookiecutter)
- [Source: doi_portal/pyproject.toml] - sentry-sdk==2.50.0 dependency
- [Source: _bmad-output/implementation-artifacts/6-4-gdpr-data-request-handling.md] - Prethodna story, SuperadminRequiredMixin pattern, sidebar meni, core URL-ovi
- [Source: _bmad-output/implementation-artifacts/6-2-audit-log-viewer.md] - SuperadminRequiredMixin, admin_base.html template pattern
- [Source: doi_portal/core/views.py] - SuperadminRequiredMixin
- [Source: doi_portal/core/urls.py] - Postojeci core URL-ovi
- [Source: doi_portal/core/menu.py] - Sidebar meni konfiguracija

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Full test suite: 1791 passed, 3 skipped, 0 failures (34.55s)
- Story-specific tests: 21 passed (2.63s)

### Completion Notes List

- Task 7+8 implemented first (before_send + tests) following TDD red-green cycle
- Task 1: Extended production.py sentry_sdk.init() with release, send_default_pii, server_name, profiles_sample_rate, before_send, CeleryIntegration(propagate_traces=True)
- Task 2: Added Sentry disabled comments to local.py and test.py
- Task 3: Created SentryTestView with SuperadminRequiredMixin, sentry_sdk status detection, test event sending via ?send_test=1
- Task 4: Added URL at core/urls.py as `system/sentry-test/` (resolves to `/dashboard/audit-log/system/sentry-test/` since core is mounted at `dashboard/audit-log/`)
- Task 5: Added sentry_test menu item after system_settings in menu.py
- Task 6: Created sentry_test.html template with status cards, test button, config info
- Task 9: View tests (200 for superadmin, 403 for regular, 302 for anon, template check)
- Task 10: Full regression suite passes, menu visibility tests added

### File List

**Created:**
- `doi_portal/doi_portal/core/sentry.py` - before_send callback module
- `doi_portal/doi_portal/core/tests/test_sentry.py` - 21 tests (14 before_send + 5 view + 2 menu)
- `doi_portal/doi_portal/templates/core/sentry_test.html` - Sentry test page template

**Modified:**
- `doi_portal/config/settings/production.py` - Extended sentry_sdk.init() with new params
- `doi_portal/config/settings/local.py` - Added Sentry disabled comment
- `doi_portal/config/settings/test.py` - Added Sentry disabled comment
- `doi_portal/doi_portal/core/views.py` - Added SentryTestView
- `doi_portal/doi_portal/core/urls.py` - Added sentry-test URL
- `doi_portal/doi_portal/core/menu.py` - Added sentry_test menu item
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Status update
- `_bmad-output/implementation-artifacts/6-5-system-monitoring-with-sentry.md` - Checkboxes + record
