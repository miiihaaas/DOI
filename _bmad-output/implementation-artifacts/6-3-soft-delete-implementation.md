# Story 6.3: Soft Delete Implementation

Status: done

## Story

As a **system**,
I want **to consolidate soft delete into a reusable mixin, extend it to the Author model, and provide a Superadmin UI for managing deleted items**,
So that **data can be recovered, GDPR deletion can be reversible during grace period, and code duplication is eliminated**.

## Acceptance Criteria

1. **AC1: SoftDeleteMixin u core app** - `SoftDeleteMixin` klasa u `core/mixins.py` sa poljima: `is_deleted` (BooleanField, default=False), `deleted_at` (DateTimeField, null=True), `deleted_by` (FK User, null=True). Sadrži `soft_delete(user)` i `restore()` metode. Svi modeli koriste mixin umesto dupliciranog koda.

2. **AC2: SoftDeleteManager u core app** - `SoftDeleteManager` klasa premještena iz `publishers/models.py` u `core/mixins.py`. Default queryset isključuje soft-deleted zapise. `all_with_deleted()` vraća sve zapise. `deleted_only()` vraća samo obrisane zapise.

3. **AC3: Author model ima soft delete** - Author model u `articles/models.py` ima `is_deleted`, `deleted_at`, `deleted_by` polja, `SoftDeleteManager` kao default manager, `soft_delete()` i `restore()` metode. Migracija kreirana.

4. **AC4: Refaktoring postojećih modela** - Publisher, Publication, Issue, Article modeli koriste `SoftDeleteMixin` iz `core/mixins.py` umesto dupliciranih polja i metoda. `SoftDeleteManager` importovan iz `core/mixins.py`. Sve postojeće funkcionalnosti ostaju nepromenjene (zero regressions).

5. **AC5: Deleted Items stranica** - Superadmin može pristupiti "Obrisane stavke" stranici putem sidebar menija (System > Obrisane stavke). Stranica prikazuje soft-deleted zapise svih modela grupisane po tipu (Izdavači, Publikacije, Izdanja, Članci, Autori). Svaki zapis prikazuje: naziv/reprezentaciju, ko je obrisao, kada je obrisano.

6. **AC6: Restore funkcionalnost** - Superadmin može vratiti (restore) obrisani zapis klikom na "Vrati" dugme. HTMX POST request poziva restore endpoint. Zapis se vraća u normalne upite (is_deleted=False, deleted_at=None, deleted_by=None). Success poruka se prikazuje.

7. **AC7: Permanent delete funkcionalnost** - Superadmin može trajno obrisati zapis klikom na "Trajno obriši" dugme. Confirmation modal se prikazuje pre trajnog brisanja. Zapis se fizički briše iz baze. Akcija je logirana u audit log.

8. **AC8: Pristup samo za Superadmin** - Samo Superadmin može pristupiti Deleted Items stranici i izvršavati restore/permanent delete akcije. Ostali korisnici dobijaju 403 Forbidden.

## Tasks / Subtasks

- [x] Task 1: Kreiraj SoftDeleteMixin i premesti SoftDeleteManager u core (AC: #1, #2)
  - [x] 1.1 Kreiraj `core/mixins.py` sa `SoftDeleteMixin(models.Model)` abstract model - polja: `is_deleted`, `deleted_at`, `deleted_by` (FK na `settings.AUTH_USER_MODEL`)
  - [x] 1.2 Dodaj `soft_delete(user=None)` metodu u mixin: setuje `is_deleted=True`, `deleted_at=timezone.now()`, `deleted_by=user`, save sa `update_fields`
  - [x] 1.3 Dodaj `restore()` metodu u mixin: setuje `is_deleted=False`, `deleted_at=None`, `deleted_by=None`, save sa `update_fields`
  - [x] 1.4 Premesti `SoftDeleteManager` iz `publishers/models.py` u `core/mixins.py` (zadrži backward-compatible import u publishers/models.py)
  - [x] 1.5 Dodaj `class Meta: abstract = True` na SoftDeleteMixin

- [x] Task 2: Refaktoruj Publisher model (AC: #4)
  - [x] 2.1 Publisher nasledi `SoftDeleteMixin` - ukloni duplicirana polja (`is_deleted`, `deleted_at`, `deleted_by`) i metode (`soft_delete()`, `restore()`)
  - [x] 2.2 Update `publishers/models.py` - `SoftDeleteManager` import iz `core/mixins` (zadrži re-export u `__all__` za backward compatibility)
  - [x] 2.3 Verifikuj da svi postojeći testovi prolaze bez promene

- [x] Task 3: Refaktoruj Publication model (AC: #4)
  - [x] 3.1 Publication nasledi `SoftDeleteMixin` - ukloni duplicirana polja i metode
  - [x] 3.2 Update import `SoftDeleteManager` iz `core/mixins`
  - [x] 3.3 Verifikuj da svi postojeći testovi prolaze bez promene

- [x] Task 4: Refaktoruj Issue model (AC: #4)
  - [x] 4.1 Issue nasledi `SoftDeleteMixin` - ukloni duplicirana polja i metode
  - [x] 4.2 Update import `SoftDeleteManager` iz `core/mixins`
  - [x] 4.3 Verifikuj da svi postojeći testovi prolaze bez promene

- [x] Task 5: Refaktoruj Article model (AC: #4)
  - [x] 5.1 Article nasledi `SoftDeleteMixin` - ukloni duplicirana polja i metode
  - [x] 5.2 Update import `SoftDeleteManager` iz `core/mixins`
  - [x] 5.3 Verifikuj da svi postojeći testovi prolaze bez promene

- [x] Task 6: Dodaj soft delete na Author model (AC: #3)
  - [x] 6.1 Author nasledi `SoftDeleteMixin`, dodaj `objects = SoftDeleteManager()` i `all_objects = models.Manager()`
  - [x] 6.2 Kreiraj migraciju: `python manage.py makemigrations articles`
  - [x] 6.3 Verifikuj da Author queryset default isključuje soft-deleted zapise
  - [x] 6.4 Proveri impact na `article.authors.all()` - ForeignKey related manager NEĆE automatski koristiti SoftDeleteManager. Razmotriti da li treba custom related manager ili filter u view-u.

- [x] Task 7: Dodaj "Obrisane stavke" u sidebar meni (AC: #5, #8)
  - [x] 7.1 U `core/menu.py` MENU_ITEMS dodaj `deleted_items` POSLE `audit_log` a PRE `system_settings`: `{"label": "Obrisane stavke", "icon": "bi-trash", "url_name": "core:deleted-items", "roles": ["Superadmin"]}`

- [x] Task 8: Kreiraj DeletedItemsView (AC: #5, #8)
  - [x] 8.1 Dodaj CBV `DeletedItemsView(SuperadminRequiredMixin, TemplateView)` u `core/views.py`
  - [x] 8.2 `get_context_data()` učitava soft-deleted zapise iz svih modela koristeći `Model.all_objects.filter(is_deleted=True)` ili `Model.objects.deleted_only()`
  - [x] 8.3 Grupiši po modelu sa count-om: publishers, publications, issues, articles, authors
  - [x] 8.4 Za svaki zapis prikaži: `__str__()` reprezentaciju, `deleted_by` email, `deleted_at` formatirano
  - [x] 8.5 Opcioni filter po tipu modela (query param `?type=publisher`)

- [x] Task 9: Kreiraj restore i permanent delete endpoint-e (AC: #6, #7, #8)
  - [x] 9.1 FBV `deleted_item_restore(request, model_type, pk)` - POST only, Superadmin only
  - [x] 9.2 FBV `deleted_item_permanent_delete(request, model_type, pk)` - POST only, Superadmin only
  - [x] 9.3 `model_type` parametar mapira na model klasu: `{"publisher": Publisher, "publication": Publication, "issue": Issue, "article": Article, "author": Author}`
  - [x] 9.4 Restore: koristi `instance.restore()`, HTMX response uklanja red iz tabele
  - [x] 9.5 Permanent delete: koristi `instance.delete()` (Django hard delete), HTMX response uklanja red
  - [x] 9.6 `@role_required("Superadmin")` dekorator za obe FBV funkcije

- [x] Task 10: Dodaj URL-ove za deleted items (AC: #5, #6, #7)
  - [x] 10.1 U `core/urls.py` dodaj: `path("deleted/", views.DeletedItemsView.as_view(), name="deleted-items")`
  - [x] 10.2 Dodaj: `path("deleted/<str:model_type>/<int:pk>/restore/", views.deleted_item_restore, name="deleted-item-restore")`
  - [x] 10.3 Dodaj: `path("deleted/<str:model_type>/<int:pk>/permanent-delete/", views.deleted_item_permanent_delete, name="deleted-item-permanent-delete")`

- [x] Task 11: Kreiraj templates za deleted items (AC: #5, #6, #7)
  - [x] 11.1 Kreiraj `templates/core/deleted_items.html` (extends `admin_base.html`) - prikazuje tabele obrisanih stavki grupisane po tipu modela
  - [x] 11.2 Svaka grupa ima collapsible sekciju sa badge count-om
  - [x] 11.3 Tabela kolone: Naziv, Obrisao, Datum brisanja, Akcije (Vrati | Trajno obriši)
  - [x] 11.4 "Vrati" dugme: `hx-post` na restore URL, `hx-target="closest tr"`, `hx-swap="outerHTML"`, `hx-confirm="Da li ste sigurni da želite da vratite ovu stavku?"`
  - [x] 11.5 "Trajno obriši" dugme: `hx-post` na permanent-delete URL, `hx-target="closest tr"`, `hx-swap="outerHTML"`, `hx-confirm="PAŽNJA: Ova akcija je nepovratna! Da li ste sigurni da želite trajno obrisati ovu stavku?"`
  - [x] 11.6 Breadcrumbs: Kontrolna tabla > Obrisane stavke
  - [x] 11.7 Prazno stanje: "Nema obrisanih stavki" poruka kada nema soft-deleted zapisa

- [x] Task 12: Testovi za SoftDeleteMixin (AC: #1, #2)
  - [x] 12.1 Test: SoftDeleteMixin `soft_delete()` setuje is_deleted, deleted_at, deleted_by
  - [x] 12.2 Test: SoftDeleteMixin `restore()` resetuje is_deleted, deleted_at, deleted_by
  - [x] 12.3 Test: SoftDeleteManager default queryset isključuje obrisane
  - [x] 12.4 Test: `all_with_deleted()` uključuje sve zapise
  - [x] 12.5 Test: `deleted_only()` vraća samo obrisane zapise

- [x] Task 13: Testovi za Author soft delete (AC: #3)
  - [x] 13.1 Test: Author `soft_delete()` funkcioniše
  - [x] 13.2 Test: Author `restore()` funkcioniše
  - [x] 13.3 Test: Obrisani autori isključeni iz default queryset-a

- [x] Task 14: Testovi za Deleted Items views (AC: #5, #6, #7, #8)
  - [x] 14.1 Test: Superadmin može pristupiti deleted-items stranici (200)
  - [x] 14.2 Test: Non-Superadmin dobija 403
  - [x] 14.3 Test: Neautentifikovan korisnik redirectovan na login
  - [x] 14.4 Test: Stranica prikazuje soft-deleted zapise svih modela
  - [x] 14.5 Test: Restore endpoint vraća zapis u normalno stanje
  - [x] 14.6 Test: Permanent delete endpoint fizički briše zapis
  - [x] 14.7 Test: Filter po tipu modela funkcioniše
  - [x] 14.8 Test: Restore/permanent delete zahtevaju POST metodu
  - [x] 14.9 Test: Restore/permanent delete zahtevaju Superadmin pristup

- [x] Task 15: Regression testovi (AC: #4)
  - [x] 15.1 Pokreni kompletnu test suite: `pytest` - svi postojeći testovi moraju proći
  - [x] 15.2 Verifikuj da Publisher, Publication, Issue, Article soft delete i dalje radi identično
  - [x] 15.3 Verifikuj da portal views i dalje isključuju obrisane zapise

## Dev Notes

### KRITIČNO: Šta je VEĆ implementirano

Soft delete polja i metode VEĆ postoje na 4 modela - **NE kreiraj ih ponovo, samo refaktoruj u mixin**:

| Model | is_deleted | deleted_at | deleted_by | soft_delete() | restore() | SoftDeleteManager |
|-------|-----------|-----------|-----------|--------------|----------|-------------------|
| Publisher | DA | DA | DA | DA | DA | DA (definisan ovde) |
| Publication | DA | DA | DA | DA | DA | DA (importovan iz publishers) |
| Issue | DA | DA | DA | DA | DA | DA (importovan iz publishers) |
| Article | DA | DA | DA | DA | DA | DA (importovan iz publishers) |
| **Author** | **NE** | **NE** | **NE** | **NE** | **NE** | **NE** |

### SoftDeleteManager lokacija

`SoftDeleteManager` je TRENUTNO definisan u `doi_portal/publishers/models.py` (linija 46-59). Ostali modeli ga importuju odatle:

```python
# publications/models.py
from doi_portal.publishers.models import Publisher, SoftDeleteManager

# issues/models.py
from doi_portal.publishers.models import SoftDeleteManager

# articles/models.py
from doi_portal.publishers.models import SoftDeleteManager
```

**REFAKTORING STRATEGIJA:**
1. Kreiraj `core/mixins.py` sa `SoftDeleteMixin` i `SoftDeleteManager`
2. U `publishers/models.py` ukloni SoftDeleteManager klasu, dodaj backward-compatible re-export:
   ```python
   from doi_portal.core.mixins import SoftDeleteManager, SoftDeleteMixin  # noqa: F401
   ```
3. Ostali modeli postepeno prebace import na `core/mixins` ali i stari import radi

### KRITIČNO: Migracije

Refaktoring NE zahteva nove migracije za Publisher, Publication, Issue, Article jer se polja ne menjaju - samo se izvor koda menja (mixin umesto inline). Django migracije prate polja, ne Python klase.

**JEDINA nova migracija:** Author model dobija 3 nova polja (`is_deleted`, `deleted_at`, `deleted_by`).

### KRITIČNO: Author model i related manager

Author koristi `ForeignKey` na Article sa `related_name="authors"`. Django related manager (`article.authors.all()`) koristi **default manager** modela. Ako je `objects = SoftDeleteManager()`, tada `article.authors.all()` automatski isključuje soft-deleted autore - ovo je ŽELJENO ponašanje.

Ali `all_objects = models.Manager()` mora biti definisan KAO DRUGI manager, NE kao `default_manager_name` jer bi to promenilo ponašanje related managers-a.

```python
class Author(SoftDeleteMixin, models.Model):
    # ... polja ...
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        default_manager_name = "objects"  # Eksplicitno - za related manager
```

### SuperadminRequiredMixin

VEĆ postoji u `core/views.py` (Story 6.2). Koristi ga za DeletedItemsView:

```python
class SuperadminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or \
            self.request.user.groups.filter(name="Superadmin").exists()
```

### role_required dekorator

Za FBV (restore, permanent delete) koristi `@role_required("Superadmin")` iz `core/permissions.py`:

```python
from doi_portal.core.permissions import role_required

@role_required("Superadmin")
def deleted_item_restore(request, model_type, pk):
    ...
```

### Model type mapping za URL-ove

```python
MODEL_TYPE_MAP = {
    "publisher": Publisher,
    "publication": Publication,
    "issue": Issue,
    "article": Article,
    "author": Author,
}
```

Koristi `model_type` string u URL-u umesto content_type ID-a - čitljivije i bezbednije.

### HTMX pattern za restore/delete akcije

Restore i permanent delete vraćaju prazan response koji uklanja red iz tabele:

```python
def deleted_item_restore(request, model_type, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    model_class = MODEL_TYPE_MAP.get(model_type)
    if not model_class:
        raise Http404
    instance = get_object_or_404(model_class.all_objects, pk=pk, is_deleted=True)
    instance.restore()
    messages.success(request, f"Stavka '{instance}' je uspešno vraćena.")
    return HttpResponse("")  # HTMX uklanja <tr> sa hx-swap="outerHTML"
```

### Existing delete views - NE MENJAJ

Postojeći DeleteView-ovi (PublisherDeleteView, PublicationDeleteView, IssueDeleteView, ArticleDeleteView) VEĆ koriste `soft_delete()` - NE menjaj ih. Oni ostaju isti.

### Sidebar meni pozicija

U `core/menu.py`, `deleted_items` ide POSLE `audit_log` a PRE `system_settings`:

```python
"audit_log": { ... },        # Existing (Story 6.2)
"deleted_items": {            # NEW (Story 6.3)
    "label": "Obrisane stavke",
    "icon": "bi-trash",
    "url_name": "core:deleted-items",
    "roles": ["Superadmin"],
},
"system_settings": { ... },  # Existing
```

### URL konfiguracija - core app

`core/urls.py` VEĆ postoji (Story 6.2). Dodaj NOVE URL-ove za deleted items:

```python
urlpatterns = [
    # Existing (Story 6.2)
    path("", views.AuditLogListView.as_view(), name="audit-log-list"),
    path("<int:pk>/", views.AuditLogDetailView.as_view(), name="audit-log-detail"),
    # NEW (Story 6.3)
    path("deleted/", views.DeletedItemsView.as_view(), name="deleted-items"),
    path("deleted/<str:model_type>/<int:pk>/restore/", views.deleted_item_restore, name="deleted-item-restore"),
    path("deleted/<str:model_type>/<int:pk>/permanent-delete/", views.deleted_item_permanent_delete, name="deleted-item-permanent-delete"),
]
```

**VAŽNO:** Core URLs su registrovane pod `dashboard/audit-log/` u `config/urls.py`. Deleted items URL će biti `dashboard/audit-log/deleted/`. Ako želiš čistiju putanju, razmotriti promenu registracije na `dashboard/system/` ili dodaj posebnu registraciju.

Alternativa - dodaj novi include u `config/urls.py`:
```python
path("dashboard/deleted/", include("doi_portal.core.deleted_urls")),
```

Ali jednostavnije je koristiti postojeći core namespace dodavanjem URL-ova u `core/urls.py`.

### Template struktura

```
templates/core/
├── audit_log_list.html          # Existing (Story 6.2)
├── audit_log_detail.html        # Existing (Story 6.2)
├── deleted_items.html           # NEW (Story 6.3)
├── partials/
│   ├── _audit_log_table.html    # Existing (Story 6.2)
│   └── _deleted_items_table.html # OPTIONAL: HTMX partial za filter po tipu
```

### Testovi - organizacija

Svi testovi u `core/tests/test_deleted_items.py`:
- `pytest-django` sa `@pytest.mark.django_db`
- Factory Boy za test data (koristi postojeće factories)
- `client.force_login(user)` za autentifikaciju

Za SoftDeleteMixin testove: `core/tests/test_mixins.py`
- Testiraj mixin kroz realne modele (Publisher, Article) - NE kreiraj test-only modele

### Biblioteke i verzije

**NE dodaj nove dependencies.** Sve potrebno je već instalirano:
- Django 5.2+ (CBV, FBV, migracije)
- HTMX 2.0.8 (restore/delete bez reload-a)
- Bootstrap 5.3+ (tabele, dugmad, modali, collapse)
- django-auditlog 3.0.0 (permanent delete se logira automatski)

### Anti-patterns (ZABRANJENO)

- NE kreiraj abstract model sa custom Meta.app_label - koristi `class Meta: abstract = True` samo
- NE menjaj postojeće migracije - samo kreiraj nove
- NE menjaj postojeće DeleteView-ove (PublisherDeleteView, itd.)
- NE koristi Django Admin za deleted items viewer
- NE returnaj JSON iz HTMX endpointa - uvek HTML
- NE koristi `role_required` na CBV - koristi `SuperadminRequiredMixin`
- NE dodaj requirements u `requirements/*.txt` - projekat koristi `uv`
- NE uklanjaj `SoftDeleteManager` iz `publishers/models.py` `__all__` - zadrži backward compatibility
- NE kreiraj test-only modele za SoftDeleteMixin - testiraj kroz realne modele

### Project Structure Notes

- `doi_portal/doi_portal/core/mixins.py` - KREIRAJ (SoftDeleteMixin, SoftDeleteManager)
- `doi_portal/doi_portal/core/views.py` - IZMENI (dodaj DeletedItemsView, deleted_item_restore, deleted_item_permanent_delete)
- `doi_portal/doi_portal/core/urls.py` - IZMENI (dodaj deleted items URL-ove)
- `doi_portal/doi_portal/core/menu.py` - IZMENI (dodaj deleted_items meni item)
- `doi_portal/doi_portal/publishers/models.py` - IZMENI (ukloni SoftDeleteManager klasu, Publisher koristi SoftDeleteMixin, zadrži re-export)
- `doi_portal/doi_portal/publications/models.py` - IZMENI (Publication koristi SoftDeleteMixin, update import)
- `doi_portal/doi_portal/issues/models.py` - IZMENI (Issue koristi SoftDeleteMixin, update import)
- `doi_portal/doi_portal/articles/models.py` - IZMENI (Article i Author koriste SoftDeleteMixin, update import)
- `doi_portal/doi_portal/templates/core/deleted_items.html` - KREIRAJ
- `doi_portal/doi_portal/core/tests/test_mixins.py` - KREIRAJ
- `doi_portal/doi_portal/core/tests/test_deleted_items.py` - KREIRAJ
- `doi_portal/doi_portal/articles/migrations/XXXX_author_soft_delete.py` - AUTO-GENERISANA

### References

- [Source: docs/project-context.md#Audit-Logging] - django-auditlog registracija
- [Source: _bmad-output/planning-artifacts/epics.md#Story-6.3] - BDD acceptance criteria
- [Source: _bmad-output/implementation-artifacts/6-1-audit-log-integration.md] - Audit log setup
- [Source: _bmad-output/implementation-artifacts/6-2-audit-log-viewer.md] - SuperadminRequiredMixin, core URL pattern, sidebar meni
- [Source: doi_portal/publishers/models.py#SoftDeleteManager] - Trenutna lokacija SoftDeleteManager (linija 46-59)
- [Source: doi_portal/publishers/models.py#Publisher] - Soft delete implementacija na Publisher
- [Source: doi_portal/publications/models.py#Publication] - Soft delete implementacija na Publication
- [Source: doi_portal/issues/models.py#Issue] - Soft delete implementacija na Issue
- [Source: doi_portal/articles/models.py#Article] - Soft delete implementacija na Article
- [Source: doi_portal/articles/models.py#Author] - Author model BEZ soft delete
- [Source: doi_portal/core/views.py] - SuperadminRequiredMixin, DashboardView
- [Source: doi_portal/core/urls.py] - Postojeći core URL-ovi (audit log)
- [Source: doi_portal/core/menu.py] - Sidebar meni konfiguracija
- [Source: doi_portal/core/permissions.py] - role_required dekorator za FBV

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

N/A

### Completion Notes List

- SoftDeleteMixin and SoftDeleteManager centralized in core/mixins.py
- All 4 existing models (Publisher, Publication, Issue, Article) refactored to use mixin - duplicated fields and methods removed
- Author model extended with soft delete via mixin inheritance
- Backward-compatible re-export of SoftDeleteManager in publishers/models.py maintained
- Django generated metadata-only migrations for related_name changes on existing models (no DB schema changes)
- Author migration adds 3 new fields (is_deleted, deleted_at, deleted_by)
- DeletedItemsView with SuperadminRequiredMixin provides grouped display of all soft-deleted records
- restore/permanent-delete FBV endpoints with @require_POST and @role_required("Superadmin")
- Lazy model imports in views to avoid circular dependencies
- Template uses Bootstrap 5 collapsible sections with badge counts and HTMX actions
- article.authors.all() correctly uses SoftDeleteManager as default manager (confirmed by test)
- Full test suite: 1731 passed, 0 failed, 3 skipped (pre-existing)
- Task 6.4 finding: With default_manager_name="objects" on Author, article.authors.all() DOES use SoftDeleteManager, so deleted authors are automatically excluded from related querysets - desired behavior confirmed by test

### File List

**Created:**
- `doi_portal/doi_portal/core/mixins.py` - SoftDeleteMixin, SoftDeleteManager
- `doi_portal/doi_portal/core/tests/test_mixins.py` - 10 tests for mixin + Author soft delete
- `doi_portal/doi_portal/core/tests/test_deleted_items.py` - 12 tests for views/endpoints
- `doi_portal/doi_portal/templates/core/deleted_items.html` - Deleted items management page
- `doi_portal/doi_portal/articles/migrations/0010_alter_author_options_author_deleted_at_and_more.py` - Author soft delete fields
- `doi_portal/doi_portal/publishers/migrations/0006_alter_publisher_deleted_by.py` - related_name metadata update
- `doi_portal/doi_portal/publications/migrations/0004_alter_publication_deleted_by.py` - related_name metadata update
- `doi_portal/doi_portal/issues/migrations/0005_alter_issue_deleted_by.py` - related_name metadata update
- `doi_portal/doi_portal/core/migrations/0002_alter_sitesettings_options.py` - unrelated core meta change

**Modified:**
- `doi_portal/doi_portal/publishers/models.py` - Publisher uses SoftDeleteMixin, SoftDeleteManager re-exported from core.mixins
- `doi_portal/doi_portal/publications/models.py` - Publication uses SoftDeleteMixin, imports from core.mixins
- `doi_portal/doi_portal/issues/models.py` - Issue uses SoftDeleteMixin, imports from core.mixins
- `doi_portal/doi_portal/articles/models.py` - Article and Author use SoftDeleteMixin, imports from core.mixins
- `doi_portal/doi_portal/core/views.py` - Added DeletedItemsView, deleted_item_restore, deleted_item_permanent_delete
- `doi_portal/doi_portal/core/urls.py` - Added 3 URL patterns for deleted items
- `doi_portal/doi_portal/core/menu.py` - Added deleted_items menu entry
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Status updated to review
