# Story 6.2: Audit Log Viewer

Status: done

## Story

As a **Superadmin**,
I want **to view and search the audit log**,
So that **I can investigate changes and track user activity**.

## Acceptance Criteria

1. **AC1: Audit Log stranica dostupna** - Navigacijom na System > Audit Log (sidebar meni) prikazuje se stranica sa listom audit log unosa u obrnutom hronološkom redosledu. URL: `dashboard/audit-log/`.

2. **AC2: Prikaz log unosa** - Svaki unos prikazuje: timestamp (formatirano), actor (korisnik email), akcija (CREATE/UPDATE/DELETE), model tip, object representation. Lista je paginirana sa 50 unosa po stranici.

3. **AC3: Filtriranje logova** - Logovi se mogu filtrirati po:
   - Datumski opseg (od/do) - date input polja
   - Korisnik (actor) - select dropdown sa svim korisnicima
   - Tip akcije (CREATE/UPDATE/DELETE) - select dropdown
   - Tip modela (Publisher, Article, itd.) - select dropdown sa registrovanim modelima
   - Object ID - text input

4. **AC4: Detaljan prikaz log unosa** - Klikom na log unos otvara se detaljan prikaz. Za UPDATE akcije: stare vrednosti vs nove vrednosti prikazane side by side. JSON changes su formatirani za čitljivost.

5. **AC5: Pretraga logova** - Pretraga po object representation i actor imenu/emailu. HTMX search sa `hx-trigger="keyup changed delay:300ms"`.

6. **AC6: Pristup samo za Superadmin** - Samo korisnici sa Superadmin ulogom mogu pristupiti Audit Log stranici. Ostali korisnici dobijaju 403 Forbidden.

## Tasks / Subtasks

- [x] Task 1: Dodaj Audit Log u sidebar meni (AC: #1, #6)
  - [x] 1.1 U `core/menu.py` dodaj novi meni item `audit_log` sa `url_name: "core:audit-log-list"`, `roles: ["Superadmin"]`, `icon: "bi-clock-history"`, `label: "Revizioni log"` - pozicioniraj POSLE `users` a PRE `system_settings`
  - [x] 1.2 Verifikuj da se meni item prikazuje samo za Superadmin korisnike

- [x] Task 2: Kreiraj URL konfiguraciju za core app (AC: #1)
  - [x] 2.1 Kreiraj `core/urls.py` sa namespace `core`
  - [x] 2.2 Dodaj URL patterne: `audit-log/` (list), `audit-log/<int:pk>/` (detail)
  - [x] 2.3 Registruj u `config/urls.py`: `path("dashboard/audit-log/", include("doi_portal.core.urls", namespace="core"))`

- [x] Task 3: Implementiraj AuditLogListView (AC: #1, #2, #3, #5, #6)
  - [x] 3.1 Kreiraj CBV `AuditLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView)` u `core/views.py`
  - [x] 3.2 `test_func()` proverava da je korisnik Superadmin (pattern iz `role_required` u `core/permissions.py`): `user.is_superuser or user.groups.filter(name="Superadmin").exists()`
  - [x] 3.3 `model = LogEntry` (iz `auditlog.models`), `paginate_by = 50`, `ordering = ["-timestamp"]`
  - [x] 3.4 `get_queryset()` implementira filtriranje: timestamp__date__gte, timestamp__date__lte, actor (FK), action, content_type, object_id
  - [x] 3.5 `get_queryset()` implementira pretragu: `object_repr__icontains` i `actor__email__icontains` sa Q objektima (OR)
  - [x] 3.6 `get_context_data()` dodaje: filter vrednosti za form persistence, listu korisnika za actor dropdown, listu registrovanih content_type-ova za model dropdown, ACTION_CHOICES
  - [x] 3.7 HTMX support: ako je `HX-Request` header prisutan, renderuj partial `core/partials/_audit_log_table.html`

- [x] Task 4: Implementiraj AuditLogDetailView (AC: #4, #6)
  - [x] 4.1 Kreiraj CBV `AuditLogDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView)` u `core/views.py`
  - [x] 4.2 `test_func()` - ista Superadmin provera kao list view
  - [x] 4.3 `model = LogEntry`
  - [x] 4.4 `get_context_data()` parsira `changes` JSON i priprema ga za side-by-side prikaz (old vs new vrednosti)

- [x] Task 5: Kreiraj template za listu (AC: #2, #3, #5)
  - [x] 5.1 Kreiraj `templates/core/audit_log_list.html` (extends `admin_base.html`)
  - [x] 5.2 Filter forma na vrhu stranice sa svim filter poljima (datum od/do, actor, akcija, model, object ID)
  - [x] 5.3 Search input polje sa HTMX: `hx-get`, `hx-trigger="keyup changed delay:300ms"`, `hx-target="#audit-log-table"`
  - [x] 5.4 Tabela sa kolonama: Vreme, Korisnik, Akcija, Model, Objekat
  - [x] 5.5 Akcija kolona koristi Bootstrap badge boje: CREATE=success, UPDATE=warning, DELETE=danger
  - [x] 5.6 Paginacija (koristi projekat pagination pattern iz `components/_pagination.html` ako postoji)
  - [x] 5.7 Breadcrumbs: Kontrolna tabla > Revizioni log

- [x] Task 6: Kreiraj HTMX partial za tabelu (AC: #3, #5)
  - [x] 6.1 Kreiraj `templates/core/partials/_audit_log_table.html` - samo tabela + paginacija bez layout-a
  - [x] 6.2 Tabela se renderuje identično kao u full template (DRY - include partial iz list template-a)

- [x] Task 7: Kreiraj template za detalj (AC: #4)
  - [x] 7.1 Kreiraj `templates/core/audit_log_detail.html` (extends `admin_base.html`)
  - [x] 7.2 Prikaži metapodatke: timestamp, actor email, akcija, model, object ID, object repr, remote addr
  - [x] 7.3 Za UPDATE akcije: side-by-side tabela sa kolonama Polje, Stara vrednost, Nova vrednost
  - [x] 7.4 Za CREATE akcije: lista svih postavljenih polja sa vrednostima
  - [x] 7.5 Za DELETE akcije: prikaz object representation koji je sačuvan
  - [x] 7.6 Breadcrumbs: Kontrolna tabla > Revizioni log > Detalj #{{pk}}
  - [x] 7.7 "Nazad na listu" dugme

- [x] Task 8: Testovi za pristup i permisije (AC: #6)
  - [x] 8.1 Test: Superadmin može pristupiti audit-log-list (200)
  - [x] 8.2 Test: Administrator dobija 403
  - [x] 8.3 Test: Urednik dobija 403
  - [x] 8.4 Test: Bibliotekar dobija 403
  - [x] 8.5 Test: Neautentifikovan korisnik redirectovan na login
  - [x] 8.6 Test: Superadmin može pristupiti audit-log-detail (200)
  - [x] 8.7 Test: Non-Superadmin dobija 403 na detail view

- [x] Task 9: Testovi za listu i filtriranje (AC: #2, #3, #5)
  - [x] 9.1 Test: Lista prikazuje LogEntry zapise u obrnutom hronološkom redosledu
  - [x] 9.2 Test: Paginacija sa 50 po stranici
  - [x] 9.3 Test: Filter po datumskom opsegu
  - [x] 9.4 Test: Filter po actor-u
  - [x] 9.5 Test: Filter po akciji (CREATE/UPDATE/DELETE)
  - [x] 9.6 Test: Filter po modelu (content_type)
  - [x] 9.7 Test: Filter po object_id
  - [x] 9.8 Test: Pretraga po object_repr
  - [x] 9.9 Test: Pretraga po actor email
  - [x] 9.10 Test: HTMX request vraća partial template

- [x] Task 10: Testovi za detaljan prikaz (AC: #4)
  - [x] 10.1 Test: Detail view prikazuje LogEntry metapodatke
  - [x] 10.2 Test: UPDATE entry prikazuje old vs new vrednosti
  - [x] 10.3 Test: CREATE entry prikazuje postavljene vrednosti
  - [x] 10.4 Test: DELETE entry prikazuje sačuvani object_repr

## Dev Notes

### Kritično: Sta je VEC implementirano (Story 6.1)

`django-auditlog` je potpuno konfigurisan u projektu:
- `auditlog` u `INSTALLED_APPS` (`config/settings/base.py` linija 86)
- `AuditlogMiddleware` u MIDDLEWARE (`config/settings/base.py` linija 163)
- 8 modela registrovano: Publisher, Publication, Issue, Article, Author, Affiliation, User, CrossrefExport
- `LogEntry` tabela vec postoji u bazi sa kolonama: `id`, `content_type`, `object_pk`, `object_id`, `object_repr`, `action`, `changes`, `actor`, `remote_addr`, `timestamp`
- Archive task u `core/tasks.py` (ne dirati)

### LogEntry model - django-auditlog API

```python
from auditlog.models import LogEntry

# Action konstante (int vrednosti)
LogEntry.Action.CREATE  # 0
LogEntry.Action.UPDATE  # 1
LogEntry.Action.DELETE  # 2

# Vazna polja
entry.timestamp        # DateTimeField
entry.actor            # FK na User (nullable)
entry.content_type     # FK na ContentType
entry.object_pk        # CharField (primarni kljuc objekta kao string)
entry.object_id        # BigIntegerField (primarni kljuc kao int, nullable)
entry.object_repr      # CharField (string reprezentacija objekta)
entry.action           # SmallIntegerField (0=CREATE, 1=UPDATE, 2=DELETE)
entry.changes          # TextField (JSON string)
entry.remote_addr      # GenericIPAddressField (nullable)

# Pristup changes kao dict
entry.changes_dict     # Property - vraca parsed JSON dict
# Format: {"field_name": ["old_value", "new_value"]}
```

### URL i View pattern

Core app NEMA `urls.py` - treba ga kreirati. Pattern iz ostalih apps:

```python
# core/urls.py
from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.AuditLogListView.as_view(), name="audit-log-list"),
    path("<int:pk>/", views.AuditLogDetailView.as_view(), name="audit-log-detail"),
]
```

Registracija u `config/urls.py` (dodaj posle crossref):
```python
path("dashboard/audit-log/", include("doi_portal.core.urls", namespace="core")),
```

### Meni konfiguracija

U `core/menu.py` MENU_ITEMS dict dodaj POSLE `users` a PRE `system_settings`:

```python
"audit_log": {
    "label": "Revizioni log",
    "icon": "bi-clock-history",
    "url_name": "core:audit-log-list",
    "roles": ["Superadmin"],
},
```

**VAZNO:** MENU_ITEMS je OrderedDict-like (Python 3.7+ dict cuva redosled). Pozicija u kodu odredjuje poziciju u meniju. Dodaj izmedju `users` i `system_settings`.

### Permission pattern - Superadmin only

Koristi `UserPassesTestMixin` sa `test_func()`:

```python
class AuditLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    def test_func(self):
        return self.request.user.is_superuser or \
            self.request.user.groups.filter(name="Superadmin").exists()
```

NE koristi `role_required` dekorator - to je za FBV. Za CBV koristi `UserPassesTestMixin`.

### HTMX pattern za pretragu i filtriranje

```html
<!-- Search input -->
<input type="text" name="q"
       hx-get="{% url 'core:audit-log-list' %}"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#audit-log-table"
       hx-include="[name='date_from'],[name='date_to'],[name='actor'],[name='action'],[name='model'],[name='object_id']"
       placeholder="Pretraži po objekatu ili korisniku...">
```

View mora u `get()` proveriti `HX-Request` header i renderovati partial:
```python
def get(self, request, *args, **kwargs):
    self.object_list = self.get_queryset()
    context = self.get_context_data()
    if request.headers.get("HX-Request"):
        return render(request, "core/partials/_audit_log_table.html", context)
    return render(request, "core/audit_log_list.html", context)
```

### Content Type za filter dropdown

Za model filter dropdown, koristiti ContentType objekte registrovanih modela:

```python
from django.contrib.contenttypes.models import ContentType
from auditlog.registry import auditlog

# Dobij content_type-ove samo za registrovane modele
registered_models = auditlog.get_models()  # ili list(auditlog._registry.keys())
content_types = ContentType.objects.get_for_models(*registered_models)
```

**VAZNO:** Proveri auditlog API verziju u projektu. `auditlog.get_models()` mozda nije dostupan - alternativa je `list(auditlog._registry.keys())` za dobijanje registrovanih modela.

### Template struktura

```
templates/
  core/
    audit_log_list.html        # Full page (extends admin_base.html)
    audit_log_detail.html      # Full page (extends admin_base.html)
    partials/
      _audit_log_table.html    # HTMX partial (samo tabela + paginacija)
```

### Action badge boje (Bootstrap)

```html
{% if entry.action == 0 %}
  <span class="badge bg-success">Kreiranje</span>
{% elif entry.action == 1 %}
  <span class="badge bg-warning text-dark">Izmena</span>
{% elif entry.action == 2 %}
  <span class="badge bg-danger">Brisanje</span>
{% endif %}
```

### Testovi - organizacija

Svi testovi u `core/tests/test_audit_log_views.py`:
- Koristi `pytest-django` sa `@pytest.mark.django_db`
- Factory Boy za test data (`UserFactory` iz `users/tests/factories.py`)
- `LogEntry.objects.create()` ili `LogEntry.objects.log_create()` za kreiranje test log unosa
- `client.force_login(user)` za autentifikaciju u testovima

### Biblioteke i verzije

| Biblioteka | Verzija | Napomena |
|------------|---------|----------|
| django-auditlog | 3.0.0 | Vec instaliran - `pyproject.toml` |
| Django | 5.2+ | ListView, DetailView, UserPassesTestMixin |
| HTMX | 2.0.8 | Pretraga i filtriranje bez reload-a |
| Bootstrap | 5.3+ | Badge boje, tabele, forme |

**NE dodaj nove dependencies.** Sve potrebno je vec instalirano.

### Anti-patterns (ZABRANJENO)

- NE returnaj JSON iz HTMX endpointa - uvek HTML
- NE koristi Django Admin za audit log viewer - custom views u admin panelu
- NE koristi `role_required` dekorator na CBV - koristi `UserPassesTestMixin`
- NE menjaj postojeci `core/views.py` DashboardView
- NE kreiraj novi Django app za audit log - koristi postojeci `core` app
- NE brisaj ili menjaj `core/tasks.py` (Story 6.1 implementacija)
- NE dodaj requirements u `requirements/*.txt` - projekat koristi `uv`

### Project Structure Notes

- `doi_portal/doi_portal/core/views.py` - DODAJ nove view klase (DashboardView vec postoji)
- `doi_portal/doi_portal/core/urls.py` - KREIRAJ (ne postoji)
- `doi_portal/doi_portal/core/menu.py` - IZMENI (dodaj audit_log meni item)
- `doi_portal/config/urls.py` - IZMENI (dodaj core URL include)
- `doi_portal/doi_portal/templates/core/` - KREIRAJ direktorijum i template fajlove
- `doi_portal/doi_portal/core/tests/test_audit_log_views.py` - KREIRAJ
- Svi UI tekstovi na srpskom sa pravilnim dijakritičkim znacima

### References

- [Source: docs/project-context.md#Audit-Logging] - django-auditlog registracija i konfiguracija
- [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture] - django-auditlog 3.4.1 izbor
- [Source: _bmad-output/planning-artifacts/epics.md#Story-6.2] - BDD acceptance criteria
- [Source: _bmad-output/implementation-artifacts/6-1-audit-log-integration.md] - Prethodna story (middleware, registracija, tasks)
- [Source: doi_portal/core/menu.py] - Sidebar meni konfiguracija
- [Source: doi_portal/core/permissions.py] - role_required, UserPassesTestMixin pattern
- [Source: doi_portal/core/views.py] - DashboardView (postojeci view u core app)
- [Source: config/urls.py] - URL routing pattern za dashboard/*
- [Source: templates/admin_base.html] - Admin base template sa sidebar, breadcrumbs, messages

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

None.

### Completion Notes List

- Used `SuperadminRequiredMixin` base class to DRY the Superadmin permission check across both views
- Used `auditlog._registry.keys()` for registered models (auditlog.get_models() not available in 3.0.0)
- All UI text in Serbian with proper diacritics (č, ć, š, đ, ž)
- DRY template pattern: list template includes the partial, HTMX returns partial only
- Full test suite: 1707 passed, 3 skipped, 0 failures

### File List

- `doi_portal/doi_portal/core/menu.py` - MODIFIED (added audit_log menu item)
- `doi_portal/doi_portal/core/urls.py` - CREATED (core app URL config with namespace)
- `doi_portal/doi_portal/core/views.py` - MODIFIED (added AuditLogListView, AuditLogDetailView, SuperadminRequiredMixin)
- `doi_portal/config/urls.py` - MODIFIED (registered core URLs under dashboard/audit-log/)
- `doi_portal/doi_portal/templates/core/audit_log_list.html` - CREATED (list page with filters, search, HTMX)
- `doi_portal/doi_portal/templates/core/audit_log_detail.html` - CREATED (detail page with changes display)
- `doi_portal/doi_portal/templates/core/partials/_audit_log_table.html` - CREATED (HTMX partial for table+pagination)
- `doi_portal/doi_portal/core/tests/test_audit_log_views.py` - CREATED (26 tests: permissions, filtering, search, detail)
