# Story 3.1: Article Model & Basic Metadata Entry

Status: done

## Story

As a **Bibliotekar**,
I want **to create a new article with basic metadata**,
So that **I can start entering article information for DOI registration**.

## Background

Ovo je prva prica u Epiku 3 (Article Workflow) - srzi celokupnog sistema. Article model je centralni entitet koji se koristi za DOI registraciju i Crossref XML generisanje. Ova prica kreira Article model, ArticleStatus enum, ArticleForm za osnovne metapodatke, admin CRUD views sa publisher-scoped permissions i odgovarajuce template-ove.

**FR Pokrivenost:** FR22 (kreiranje clanka), FR23 (metapodaci clanka), FR26 (cuvanje kao draft), FR30a (publication_type izbor), FR30b (license informacije)

**Zavisnosti (sve DONE):**
- Story 2.6: Issue Model & Admin CRUD - Issue FK za Article
- Story 2.8: Row-Level Permissions - publisher-scoped mixins za Article views
- Story 1.7: Admin Dashboard Shell - admin layout, sidebar, breadcrumbs

**Blokira:**
- Story 3.2: Author Management - Author model ce zavisiti od Article FK
- Story 3.3: PDF Upload - pdf_file field na Article
- Story 3.4: Auto-Save - auto-save endpoint za Article form
- Story 3.5: Submit Article for Review - status transition DRAFT->REVIEW

## Acceptance Criteria

1. **Given** Article model je kreiran
   **When** se pregleda struktura modela
   **Then** sadrzi polja: `issue` (FK), `title`, `subtitle`, `abstract`, `keywords` (JSONField), `doi_suffix`, `first_page`, `last_page`, `article_number`, `language`, `publication_type` (content type: full_text, abstract_only, bibliographic_record), `license_url`, `license_applies_to`, `free_to_read`, `free_to_read_start_date`, `pdf_file` (FileField, blank), `status`, `created_by` (FK User), `created_at`, `updated_at`
   **And** status je enum: DRAFT, REVIEW, READY, PUBLISHED, WITHDRAWN
   **And** migracije se uspesno izvrsavaju

2. **Given** ulogovan Bibliotekar
   **When** navigira na izdanje i klikne "Dodaj članak"
   **Then** prikazuje se forma za kreiranje clanka
   **And** izdanje je pred-selektovano iz konteksta
   **And** hijerarhija publikacija se prikazuje u breadcrumbs

3. **Given** Bibliotekar unosi metapodatke clanka
   **When** popunjava naslov, podnaslov, apstrakt, kljucne reci
   **Then** forma koristi Bootstrap 5 styling
   **And** apstrakt polje je textarea sa character count indikatorom
   **And** kljucne reci polje omogucava vise unosa (tag input)

4. **Given** validni podaci clanka su poslati
   **When** forma je obradjena
   **Then** clanak je kreiran sa statusom DRAFT
   **And** `created_by` je postavljen na trenutnog korisnika
   **And** toast notifikacija potvrdjuje kreiranje
   **And** korisnik je preusmeren na edit stranicu clanka

5. **Given** lista clanaka u admin panelu
   **When** Bibliotekar navigira na "Članci"
   **Then** prikazuje se lista clanaka sa naslovom, izdanjem, statusom, datumom kreiranja
   **And** queryset je filtriran po publisher-u koristeci `PublisherScopedMixin`
   **And** Administrator vidi SVE clanke

6. **Given** Article model je kreiran
   **When** `Issue.article_count` property se pozove
   **Then** vraca tacan broj clanaka (zameni placeholder `return 0` iz Story 2.6)

## Tasks / Subtasks

- [x] Task 1: Kreirati `articles` Django app i Article model (AC: #1)
  - [x] 1.1 Kreirati `doi_portal/doi_portal/articles/` app direktorijum sa `__init__.py`, `apps.py`, `models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py`, `validators.py`, `services.py`
  - [x] 1.2 Kreirati `doi_portal/doi_portal/articles/tests/` sa `__init__.py`, `factories.py`, `test_models.py`, `test_views.py`
  - [x] 1.3 Implementirati `ArticleStatus` TextChoices enum (DRAFT, REVIEW, READY, PUBLISHED, WITHDRAWN)
  - [x] 1.4 Implementirati `ArticleContentType` TextChoices enum (FULL_TEXT, ABSTRACT_ONLY, BIBLIOGRAPHIC_RECORD) - za Crossref `publication_type`
  - [x] 1.5 Implementirati `LicenseAppliesTo` TextChoices enum (VOR, AM, TDM)
  - [x] 1.6 Implementirati `Article` model sa svim poljima prema AC#1 i PRD Data Model sekciji
  - [x] 1.7 Dodati SoftDeleteManager, soft_delete(), restore() - isti pattern kao Issue model
  - [x] 1.8 Dodati Meta klasu: verbose_name, verbose_name_plural, ordering, unique constraint na (issue, doi_suffix)
  - [x] 1.9 Dodati `status_badge_class` property (isti pattern kao Issue model)
  - [x] 1.10 Registrovati Article u `apps.py` sa auditlog
  - [x] 1.11 Dodati `"doi_portal.articles"` u LOCAL_APPS u `config/settings/base.py`
  - [x] 1.12 Kreirati i izvrsiti migracije

- [x] Task 2: Azurirati Issue model - zameni `article_count` placeholder (AC: #6)
  - [x] 2.1 U `issues/models.py` azurirati `article_count` property da vraca `self.articles.count()` umesto `return 0`

- [x] Task 3: Kreirati ArticleForm za osnovne metapodatke (AC: #3)
  - [x] 3.1 Kreirati `ArticleForm(ModelForm)` sa poljima: issue, title, subtitle, abstract, keywords, doi_suffix, first_page, last_page, article_number, language, publication_type, license_url, license_applies_to, free_to_read, free_to_read_start_date
  - [x] 3.2 Issue queryset scoping - isti pattern kao IssueForm.publication (koristiti `user` kwarg)
  - [x] 3.3 Bootstrap 5 widget attrs za sva polja (class="form-control" / "form-select" / "form-check-input")
  - [x] 3.4 Srpski labels sa ispravnim dijakritikama
  - [x] 3.5 `add_error_classes()` i `is_valid()` override - isti pattern kao IssueForm

- [x] Task 4: Kreirati Article admin views (AC: #2, #4, #5)
  - [x] 4.1 `ArticleListView(PublisherScopedMixin, ListView)` - sa custom `get_scoped_queryset` filtriranjem preko `issue__publication__publisher`
  - [x] 4.2 `ArticleCreateView(PublisherScopedEditMixin, CreateView)` - issue pre-selection iz query params, `created_by` auto-set
  - [x] 4.3 `ArticleUpdateView(PublisherScopedEditMixin, UpdateView)` - samo DRAFT status dozvoljava edit
  - [x] 4.4 `ArticleDetailView(PublisherScopedMixin, DetailView)` - prikaz svih metapodataka
  - [x] 4.5 `ArticleDeleteView(AdministratorRequiredMixin, DeleteView)` - soft delete
  - [x] 4.6 Breadcrumbs: Kontrolna tabla > Članci > {akcija}
  - [x] 4.7 Role-based action visibility u context (`can_edit`, `can_delete`, `can_submit`)

- [x] Task 5: Kreirati URL routes (AC: #2)
  - [x] 5.1 `articles/urls.py` sa app_name="articles"
  - [x] 5.2 Registrovati u `config/urls.py`: `path("dashboard/articles/", include("doi_portal.articles.urls", namespace="articles"))`

- [x] Task 6: Kreirati template-ove (AC: #2, #3, #4)
  - [x] 6.1 `templates/articles/article_list.html` - tabela sa naslovom, izdanjem, statusom, datumom, akcijama
  - [x] 6.2 `templates/articles/article_form.html` - Bootstrap 5 forma sa breadcrumbs i toast
  - [x] 6.3 `templates/articles/article_detail.html` - prikaz metapodataka sa status badge
  - [x] 6.4 `templates/articles/article_confirm_delete.html` - potvrda brisanja
  - [x] 6.5 Abstract textarea sa character count (Alpine.js `x-data` za real-time count)
  - [x] 6.6 Keywords tag input (Alpine.js component za dodavanje/uklanjanje tagova, cuva se kao JSON)

- [x] Task 7: Kreirati ArticleFactory i testove (AC: #1-#6)
  - [x] 7.1 `ArticleFactory` u `articles/tests/factories.py`
  - [x] 7.2 Model testovi: kreiranje, validacija, soft delete, unique constraint, status choices
  - [x] 7.3 View testovi: CRUD sa razlicitim ulogama (Bibliotekar, Urednik, Administrator)
  - [x] 7.4 Permission testovi: publisher scoping, direct URL access denial
  - [x] 7.5 Form testovi: validacija, issue scoping

- [x] Task 8: Azurirati sidebar navigaciju (AC: #5)
  - [x] 8.1 Dodati "Članci" link u admin sidebar (`templates/dashboard/sidebar.html` ili ekvivalent)

## Dev Notes

### KRITICNO: Pratiti ustanovljene patterns iz Epic 2

Article app MORA pratiti IDENTICNE patterns ustanovljene u `issues/` i `publications/` apps. Ovo znaci:

1. **Model pattern**: SoftDeleteManager, soft_delete(), restore(), status_badge_class property
2. **View pattern**: PublisherScopedMixin/PublisherScopedEditMixin sa custom `get_scoped_queryset`
3. **Form pattern**: `__init__` sa `user` kwarg za queryset scoping, `add_error_classes()`
4. **URL pattern**: app_name namespace, `<int:pk>/` za detail/edit/delete
5. **Template pattern**: Bootstrap 5, breadcrumbs, toast notifikacije, role-based action buttons
6. **Test pattern**: Factory Boy, pytest-django, fixtures sa dva publishera za izolaciju

### Article Model - Kompletna polja specifikacija

```python
# articles/models.py

class ArticleStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Nacrt")
    REVIEW = "REVIEW", _("Na pregledu")
    READY = "READY", _("Spremno za objavu")
    PUBLISHED = "PUBLISHED", _("Objavljeno")
    WITHDRAWN = "WITHDRAWN", _("Povučeno")

class ArticleContentType(models.TextChoices):
    """Crossref publication_type - tip sadrzaja clanka."""
    FULL_TEXT = "full_text", _("Puni tekst")
    ABSTRACT_ONLY = "abstract_only", _("Samo apstrakt")
    BIBLIOGRAPHIC_RECORD = "bibliographic_record", _("Bibliografski zapis")

class LicenseAppliesTo(models.TextChoices):
    VOR = "vor", _("Verzija zapisa (VoR)")
    AM = "am", _("Prihvaćeni rukopis (AM)")
    TDM = "tdm", _("Rudarenje teksta (TDM)")

class Article(models.Model):
    # Core
    issue = models.ForeignKey("issues.Issue", on_delete=models.PROTECT, related_name="articles")
    title = models.CharField(max_length=500)  # OBAVEZNO
    subtitle = models.CharField(max_length=500, blank=True)
    abstract = models.TextField(blank=True)
    keywords = models.JSONField(default=list, blank=True)  # Lista stringova
    doi_suffix = models.CharField(max_length=100)  # OBAVEZNO za Crossref
    first_page = models.CharField(max_length=20, blank=True)
    last_page = models.CharField(max_length=20, blank=True)
    article_number = models.CharField(max_length=50, blank=True)  # Za online-only
    language = models.CharField(max_length=10, default="sr")
    publication_type = models.CharField(choices=ArticleContentType.choices, default=ArticleContentType.FULL_TEXT)

    # License/Access
    license_url = models.URLField(blank=True)
    license_applies_to = models.CharField(choices=LicenseAppliesTo.choices, blank=True, max_length=10)
    free_to_read = models.BooleanField(default=False)
    free_to_read_start_date = models.DateField(null=True, blank=True)

    # File
    pdf_file = models.FileField(upload_to="articles/pdfs/", blank=True)  # Impl u Story 3.3

    # Status
    status = models.CharField(choices=ArticleStatus.choices, default=ArticleStatus.DRAFT, max_length=20)

    # Tracking
    created_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, related_name="created_articles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete (isti pattern kao Issue)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="deleted_articles")

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()
```

### Publisher Scoping Pattern za Article

Article NEMA direktan publisher FK. Scoping ide preko `issue__publication__publisher`:

```python
# articles/views.py
class ArticleListView(PublisherScopedMixin, ListView):
    def get_scoped_queryset(self, queryset):
        flags = self._get_user_role_flags()
        if flags["is_admin"]:
            return queryset
        if flags["has_publisher"]:
            return queryset.filter(
                issue__publication__publisher=self.request.user.publisher
            )
        return queryset.none()
```

**VAZNO:** Isto kao Issue koristi `publication__publisher`, Article mora koristiti `issue__publication__publisher` - TRI nivoa relacije!

### Issue Queryset Scoping u ArticleForm

```python
# articles/forms.py
class ArticleForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            if user.is_superuser or user.groups.filter(
                name__in=["Administrator", "Superadmin"]
            ).exists():
                queryset = Issue.objects.select_related("publication", "publication__publisher")
            elif hasattr(user, "publisher") and user.publisher:
                queryset = Issue.objects.filter(
                    publication__publisher=user.publisher
                ).select_related("publication", "publication__publisher")
            else:
                queryset = Issue.objects.none()
            self.fields["issue"].queryset = queryset
```

### Keywords JSONField - Alpine.js Tag Input

Keywords se cuva kao JSONField (lista stringova). UI koristi Alpine.js za tag input:

```html
<div x-data="keywordsInput()" class="mb-3">
    <label class="form-label">Ključne reči</label>
    <div class="d-flex flex-wrap gap-1 mb-2">
        <template x-for="(keyword, index) in keywords" :key="index">
            <span class="badge bg-primary d-flex align-items-center gap-1">
                <span x-text="keyword"></span>
                <button type="button" class="btn-close btn-close-white"
                        @click="removeKeyword(index)" style="font-size: 0.6em;"></button>
            </span>
        </template>
    </div>
    <div class="input-group">
        <input type="text" class="form-control" x-model="newKeyword"
               @keydown.enter.prevent="addKeyword()"
               placeholder="Unesite ključnu reč i pritisnite Enter">
        <button type="button" class="btn btn-outline-secondary" @click="addKeyword()">Dodaj</button>
    </div>
    <input type="hidden" name="keywords" :value="JSON.stringify(keywords)">
</div>
```

### Abstract Character Count - Alpine.js

```html
<div x-data="{ charCount: 0 }" class="mb-3">
    <label class="form-label">Apstrakt</label>
    <textarea name="abstract" class="form-control" rows="6"
              x-on:input="charCount = $el.value.length"
              x-init="charCount = $el.value.length">{{ form.abstract.value|default:'' }}</textarea>
    <small class="text-muted"><span x-text="charCount"></span> karaktera</small>
</div>
```

### Form `created_by` Auto-Set u CreateView

```python
class ArticleCreateView(PublisherScopedEditMixin, CreateView):
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Članak uspešno kreiran.")
        return response
```

### Auditlog Registration

```python
# articles/apps.py
class ArticlesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "doi_portal.articles"
    verbose_name = "Članci"

    def ready(self):
        from auditlog.registry import auditlog
        from .models import Article
        auditlog.register(Article)
```

### Issue.article_count Update

```python
# issues/models.py - AZURIRATI property
@property
def article_count(self) -> int:
    """Return count of articles in this issue."""
    if hasattr(self, "articles"):
        return self.articles.count()
    return 0
```

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/articles/
├── __init__.py
├── admin.py           # Prazan ili Django admin ako treba
├── apps.py            # ArticlesConfig sa auditlog.register
├── forms.py           # ArticleForm sa issue scoping
├── models.py          # Article, ArticleStatus, ArticleContentType, LicenseAppliesTo
├── services.py        # Prazan za sada (business logic u buducim pricama)
├── urls.py            # app_name="articles", CRUD paths
├── validators.py      # Prazan za sada (ORCID validator u Story 3.2)
├── views.py           # CRUD views sa publisher scoping
└── tests/
    ├── __init__.py
    ├── factories.py   # ArticleFactory
    ├── test_models.py
    └── test_views.py

templates/articles/
├── article_list.html
├── article_form.html
├── article_detail.html
└── article_confirm_delete.html
```

### Fajlovi za modifikaciju (POSTOJECI)

- `doi_portal/config/settings/base.py` - Dodati `"doi_portal.articles"` u LOCAL_APPS
- `doi_portal/config/urls.py` - Dodati `path("dashboard/articles/", ...)`
- `doi_portal/doi_portal/issues/models.py` - Azurirati `article_count` property
- Admin sidebar template - Dodati "Članci" link

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

Svi UI tekstovi MORAJU koristiti ispravne srpske dijakritike:

| Kontekst | ISPRAVNO |
|----------|----------|
| Model verbose_name | "Članak" / "Članci" |
| Form labels | "Naslov", "Apstrakt", "Ključne reči", "Podnaslov" |
| Status labels | "Nacrt", "Na pregledu", "Spremno za objavu", "Objavljeno", "Povučeno" |
| Success message | "Članak uspešno kreiran." |
| Breadcrumbs | "Kontrolna tabla", "Članci" |
| Button text | "Kreiraj članak", "Sačuvaj izmene" |

### Anti-Patterns (ZABRANJENO)

```python
# POGRESNO - Koristiti ArrayField umesto JSONField
keywords = ArrayField(models.CharField(...))  # NE! PostgreSQL-specific

# POGRESNO - Kreirati novi permission mixin
class ArticlePermissionMixin:  # NE! Koristi PublisherScopedMixin

# POGRESNO - Filtrirati po issue.publisher (ne postoji)
queryset.filter(issue__publisher=...)  # NE! Issue nema publisher FK
queryset.filter(issue__publication__publisher=...)  # ISPRAVNO

# POGRESNO - Zaboraviti created_by auto-set
# created_by se NE stavlja u form fields, vec se setuje u form_valid()

# POGRESNO - Staviti business logic u views
# Status transitions, validacije idu u services.py (buduci stories)

# POGRESNO - Koristiti Django Admin za CRUD
# Projekat koristi CUSTOM Bootstrap 5 admin panel (NE Django Admin)

# POGRESNO - JsonResponse za HTMX response
return JsonResponse({...})  # NE! Vracaj HTML fragment
```

### Testing Pattern

```python
# articles/tests/factories.py
from factory.django import DjangoModelFactory
import factory
from doi_portal.articles.models import Article, ArticleStatus

class ArticleFactory(DjangoModelFactory):
    class Meta:
        model = Article

    title = factory.Faker("sentence", nb_words=6)
    abstract = factory.Faker("paragraph")
    doi_suffix = factory.Sequence(lambda n: f"article.2026.{n:03d}")
    status = ArticleStatus.DRAFT
    issue = factory.SubFactory("doi_portal.issues.tests.factories.IssueFactory")
    created_by = factory.SubFactory("doi_portal.users.tests.factories.UserFactory")
    language = "sr"
    publication_type = "full_text"
```

### Dependencies (Python/Django)

Sve zavisnosti VEC postoje u projektu - NEMA novih pip/uv instalacija:
- Django 5.2+ (framework)
- django-guardian 3.2.0 (row-level permissions)
- django-auditlog 3.0.0 (audit logging)
- factory_boy (test factories)
- pytest-django (testing)

### Previous Story Learnings (Story 2.6, 2.7, 2.8)

1. **`get_scoped_queryset()` override** - Issue koristi `publication__publisher`, Article mora koristiti `issue__publication__publisher`. Pattern je ustanovljen i ponovljen.
2. **`_get_user_role_flags()` caching** - PublisherScopedMixin kesira role flags. Koristiti iste flagove.
3. **SoftDeleteManager** - Importovati iz `publishers.models`, NE kreirati novi.
4. **Form `user` kwarg** - Proslediti u `get_form_kwargs()` na CreateView i UpdateView.
5. **Pre-selection iz query params** - `get_initial()` za issue pre-selection (kao IssueCreateView za publication).
6. **Template structure** - Koristiti `admin_base.html` za extend, `components/_breadcrumbs.html`, `components/_toast.html`.
7. **auditlog registration** - U `apps.py` `ready()` metodi, NE u `models.py`.
8. **Test isolation** - UVEK dva publishera za permission testove.
9. **Issue.article_count** je placeholder `return 0` - ova prica ga MORA azurirati.
10. **614 testova** proslo u Story 2.8 - NE sme se regresirati.

### Git Commit Pattern

```
story-3-1: feat(articles): implementiraj Article Model i Basic Metadata Entry formu (Story 3.1)
```

### NFR Requirements

- **NFR12:** Audit log - Article CRUD se automatski belezi kroz auditlog
- **NFR13:** GDPR - Soft delete za Article model
- **NFR3:** Admin panel stranice < 5 sekundi - select_related za FK-ove

### Project Structure Notes

- Articles app ide u `doi_portal/doi_portal/articles/` (isto kao issues, publications, publishers)
- Templates idu u `doi_portal/templates/articles/`
- URL namespace: `articles` (path: `dashboard/articles/`)
- Test files: `articles/tests/` direktorijum pattern (NE flat test file)
- Slediti `from __future__ import annotations` pattern iz svih modela

### References

- [Source: epics.md#Story 3.1: Article Model & Basic Metadata Entry]
- [Source: prd.md#5. Article Management (Clanci) - FR22, FR23, FR26]
- [Source: prd.md#Data Model Update - Clanak (Article) polja]
- [Source: prd.md#Data Model Update - Autor/Kontributor (Author) polja] (za buducu Story 3.2)
- [Source: architecture.md#Data Architecture - Article model]
- [Source: architecture.md#Implementation Patterns - Naming, HTMX, Alpine.js]
- [Source: project-context.md#Django Apps Struktura - articles/]
- [Source: project-context.md#Naming Konvencije]
- [Source: project-context.md#HTMX Pravila]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri]
- [Source: issues/models.py - article_count placeholder]
- [Source: issues/views.py - get_scoped_queryset pattern]
- [Source: issues/forms.py - user kwarg queryset scoping pattern]
- [Source: publishers/models.py - SoftDeleteManager]
- [Source: publishers/mixins.py - PublisherScopedMixin, PublisherScopedEditMixin]
- [Source: 2-8-row-level-permissions-for-content.md - Permission infrastructure]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Implementation resumed after power outage interrupted previous Dev agent (~80% complete)
- Previous agent completed: model, forms, views, urls, apps, menu, settings, templates (list + form)
- This session completed: migrations, detail template, delete template, full test suite (86 tests)
- 2 test adjustments: duplicate DOI suffix test uses IntegrityError (conditional constraint), invalid JSON keywords test expects JSONField validator error
- Full suite: 701 passed, 3 skipped, 0 failures (no regressions from 614 base)

### File List

**Created (new work):**
- `doi_portal/doi_portal/articles/migrations/0001_initial.py` - Article model migration
- `doi_portal/doi_portal/templates/articles/article_detail.html` - Article detail view template
- `doi_portal/doi_portal/templates/articles/article_confirm_delete.html` - Article delete confirmation template
- `doi_portal/doi_portal/articles/tests/factories.py` - ArticleFactory (Factory Boy)
- `doi_portal/doi_portal/articles/tests/test_models.py` - 32 model tests
- `doi_portal/doi_portal/articles/tests/test_views.py` - 34 view tests
- `doi_portal/doi_portal/articles/tests/test_forms.py` - 17 form tests

**Previously created (not modified):**
- `doi_portal/doi_portal/articles/__init__.py`
- `doi_portal/doi_portal/articles/admin.py`
- `doi_portal/doi_portal/articles/apps.py`
- `doi_portal/doi_portal/articles/forms.py`
- `doi_portal/doi_portal/articles/models.py`
- `doi_portal/doi_portal/articles/services.py`
- `doi_portal/doi_portal/articles/urls.py`
- `doi_portal/doi_portal/articles/validators.py`
- `doi_portal/doi_portal/articles/views.py`
- `doi_portal/doi_portal/articles/tests/__init__.py`
- `doi_portal/doi_portal/templates/articles/article_list.html`
- `doi_portal/doi_portal/templates/articles/article_form.html`

**Modified (pre-existing):**
- `doi_portal/config/settings/base.py` - Added doi_portal.articles to INSTALLED_APPS (previous agent)
- `doi_portal/config/urls.py` - Added articles URL include (previous agent)
- `doi_portal/doi_portal/core/menu.py` - Added articles menu item (previous agent)
- `doi_portal/doi_portal/issues/models.py` - Updated article_count property (previous agent)
