---
title: 'Podrška za monografije sa poglavljima - Crossref XSD 5.4.0'
slug: 'monograph-support'
created: '2026-04-05'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Django 5.x', 'PostgreSQL', 'Jinja2 (Crossref XML)', 'HTMX', 'Alpine.js', 'Bootstrap 5']
files_to_modify:
  - 'doi_portal/doi_portal/monographs/ (NOV app)'
  - 'doi_portal/config/settings/base.py'
  - 'doi_portal/config/urls.py'
  - 'doi_portal/doi_portal/core/menu.py'
  - 'doi_portal/doi_portal/core/terminology.py'
  - 'doi_portal/doi_portal/crossref/services.py'
  - 'doi_portal/doi_portal/crossref/models.py'
  - 'doi_portal/doi_portal/crossref/views.py'
  - 'doi_portal/doi_portal/crossref/urls.py'
  - 'doi_portal/doi_portal/crossref/templates/crossref/book_monograph.xml.j2'
  - 'doi_portal/doi_portal/crossref/templates/crossref/book_chapter.xml.j2 (FIX redosled)'
  - 'doi_portal/doi_portal/portal/views.py'
  - 'doi_portal/doi_portal/templates/monographs/'
  - 'doi_portal/doi_portal/templates/portal/monographs/'
code_patterns:
  - 'SoftDeleteMixin(models.Model) + SoftDeleteManager() + all_objects=Manager() — core/mixins.py'
  - 'Abstract base class za kontributore/afilijacije/funding/relacije — novi u monographs/models.py'
  - 'HTMX inline add/delete/reorder — @require_POST, auto-order, HX-Retarget na error'
  - 'CrossrefService.TEMPLATE_MAP + REQUIRED_FIELDS — services.py:~120-147'
  - 'CrossrefService._build_context() — services.py:~296-422, Markup() wrapping za titles'
  - 'CrossrefService.generate_and_store_xml() — services.py:~445-498, atomic transaction'
  - 'CrossrefService.generate_head_for_component() — services.py:~505-526, pattern za monograph head'
  - 'PreValidationService.validate_issue() — services.py:~638-681'
  - 'CrossrefExport discriminator pattern — models.py:25-99, CheckConstraint'
  - 'ComponentGroup pattern — components/models.py:26-142, XML fields + deposit tracking'
  - 'MENU_ITEMS dict — menu.py, label/icon/url_name/roles per item'
  - 'TERMINOLOGY_MAP — terminology.py, keyed by PublicationType, get_term() helper'
  - 'auditlog.register() u apps.py ready() sa try/except ImportError'
  - 'Permission check: _check_article_permission() pattern za role-based access'
  - 'Crossref views: 5-step workflow (validate→generate→XSD→preview→download→deposit)'
  - 'Portal views: Public DetailView/ListView bez auth, prefetch related'
test_patterns:
  - 'Factory Boy: DjangoModelFactory sa SubFactory, Sequence, Faker'
  - 'pytest-django za view/form testove'
  - 'XSD validation: crossref/validators.py:validate_xml() sa lxml schema cache'
---

# Tech-Spec: Podrška za monografije sa poglavljima - Crossref XSD 5.4.0

**Created:** 2026-04-05

## Overview

### Problem Statement

DOI portal trenutno podržava samo Journal, Conference i Book (edited) tipove publikacija kroz hijerarhiju Publication → Issue → Article. Za monografije (jednautorske ili koautorske knjige) ova hijerarhija je semantički pogrešna — monografija NEMA tom/volume nivo, a svi metapodaci treba da budu na jednom mestu. Korisnici moraju kreirati "lažni" Issue samo da bi došli do unosa podataka o knjizi. Crossref XSD 5.4.0 podržava `<book book_type="monograph">` sa `<book_metadata>` i opcionalnim `<content_item>` elementima za poglavlja, što je fundamentalno drugačija struktura od journal/conference.

### Solution

Kreirati novi Django app `monographs/` sa Monograph i MonographChapter modelima koji direktno odražavaju Crossref book/content_item strukturu. Monografija je first-class entitet sa sopstvenim CRUD-om, Crossref XML generacijom, portal prikazom i sidebar meni stavkom. Poglavlja su opcionalana — monografija može imati samo book-level DOI, ili book + chapter DOI-jeve. Abstract base classes obezbeđuju DRY za kontributore, afilijacije, funding i relacije bez GenericForeignKey komplikacija.

### Scope

**In Scope:**
- Novi `monographs/` Django app sa svim modelima (Monograph, MonographChapter, MonographContributor, ChapterContributor, afilijacije, funding, relacije)
- Abstract base classes za zajedničke modele (BaseContributor, BaseAffiliation, BaseFunding, BaseRelation)
- Crossref XML template `book_monograph.xml.j2` za oba režima (sa i bez poglavlja)
- Proširenje CrossrefService za monograph XML generaciju i validaciju
- Proširenje CrossrefExport modela za MONOGRAPH tip
- Admin dashboard CRUD za monografije i poglavlja
- HTMX inline management za kontributore i poglavlja
- Portal javne stranice za monografije i poglavlja
- Sidebar meni stavka "Monografije"
- Terminologija za monografije u core/terminology.py
- Popravka redosleda elemenata u postojećem book_chapter.xml.j2

**Out of Scope:**
- `edited_book` book_type (Phase 2)
- Migracija postojeće BOOK publikacije (ID: 6) — ručno
- Wizard za monografije (može se dodati later)
- Book series metadata (`<book_series_metadata>`)
- Citation list support
- Crossmark integration

## Context for Development

### Codebase Patterns

1. **Model pattern:** `SoftDeleteMixin(models.Model)` sa `objects = SoftDeleteManager()` + `all_objects = models.Manager()`. Soft delete dodaje `is_deleted`, `deleted_at`, `deleted_by` polja. `default_manager_name = "objects"` u Meta. auditlog registracija u `apps.py:ready()` sa `try/except ImportError`.

2. **View pattern:** `LoginRequiredMixin` + custom `_check_permission()` funkcije. HTMX partials: `@login_required @require_POST` za add/delete, `@require_GET` za form. Na form error: `HX-Retarget` + `HX-Reswap` response headers. Breadcrumbs u context-u.

3. **HTMX inline CRUD pattern:** Add → auto-set `order` (Max+1) i `sequence` (FIRST if order==1 else ADDITIONAL). Delete → reorder svih preostalih. Reorder → JSON body `{"order": [pk1, pk2, ...]}`, bulk update. Return: `_list.html` partial sa svim stavkama.

4. **Crossref XML pattern:** `CrossrefService` sa `TEMPLATE_MAP[pub_type]` → Jinja2 template. `_build_context(issue)` vraća dict sa head, publisher, publication, issue, articles. Titles/abstract wrappovani u `Markup()` za face markup. Filters: `xml_escape`, `format_date`, `format_orcid_url`, `format_month`, `format_day`.

5. **Crossref storage pattern:** XML fields direktno na parent modelu (Issue/ComponentGroup): `crossref_xml` (TextField), `xml_generated_at` (DateTimeField), `xml_generation_status` (CharField choices), `xsd_valid` (BooleanField null=True), `xsd_errors` (JSONField default=list), `xsd_validated_at` (DateTimeField), `crossref_deposited_at` (DateTimeField), `crossref_deposited_by` (FK User).

6. **Crossref workflow views:** 5-step: PreValidation → Generate XML → XSD Validate → Preview → Download/Deposit. `CrossrefDepositView` compute step statuses. `mark_deposited()` sets timestamp. Component workflow is parallel implementation (same pattern, different model).

7. **Export pattern:** `CrossrefExport` sa discriminator FKs (issue/component_group, oba null=True) + `export_type` CharField + `CheckConstraint` ensuring exactly one FK set. Za monograph: dodati `monograph` FK + `MONOGRAPH` ExportType.

8. **PreValidation pattern:** `PreValidationService` sa `validate_issue()`/`validate_component_group()`. Checks: depositor settings, publication-specific fields (ISBN za BOOK), article fields, author fields. Returns `ValidationResult` sa errors (blocking) + warnings (informational).

9. **Menu pattern:** `MENU_ITEMS` dict u `core/menu.py`. Ključ = feature name, vrednost = dict sa `label`, `icon` (Bootstrap Icons), `url_name`, `roles` list. `get_menu_for_user(user)` filtrira po role.

10. **Terminology pattern:** `TERMINOLOGY_MAP` u `core/terminology.py` keyed by `PublicationType`. `get_term(key, pub_type)` sa fallback na JOURNAL. Template tag: `{% load terminology %}` + `{{ "article"|term:pub_type }}`. Podržava gramatičke padeže: nominativ, genitiv, paukal, akuzativ.

11. **Portal pattern:** Public views bez auth. `DetailView`/`ListView` sa `select_related`/`prefetch_related`. Slug-based URL routing. Template: `portal/{entity}/` folder. Separate `urls_publications.py`, `urls_articles.py`, `urls_components.py`.

12. **Form pattern:** ModelForm sa Bootstrap 5 widget attrs (`class: "form-control"`). Keywords kao JSONField sa Alpine.js tag input. `clean()` za cross-field validation.

### Files to Reference

| File | Purpose | Key Lines |
| ---- | ------- | --------- |
| `articles/models.py` | Author, Affiliation, ArticleFunding, ArticleRelation — polja za abstract base classes | 365-658 |
| `articles/models.py` | AuthorSequence, ContributorRole, RelationScope, IdentifierType enums | 48-78, 550-609 |
| `articles/models.py` | ArticleStatus choices (DRAFT/REVIEW/READY/PUBLISHED/WITHDRAWN) | 38-45 |
| `articles/validators.py` | validate_orcid — regex 0000-0000-0000-000X | 19-40 |
| `articles/views.py` | HTMX inline author/funding/relation CRUD pattern — add/delete/reorder | full |
| `articles/forms.py` | AuthorForm, AffiliationForm, ArticleFundingForm, ArticleRelationForm | full |
| `articles/urls.py` | URL pattern za HTMX endpoints — author-add, funding-add, relation-add itd. | full |
| `articles/tests/factories.py` | ArticleFactory, AuthorFactory, AffiliationFactory, ArticleRelationFactory | 32-87 |
| `crossref/services.py` | CrossrefService — TEMPLATE_MAP, _build_context(), generate_and_store_xml() | 109-498 |
| `crossref/services.py` | Component methods — generate_component_xml(), _build_component_context() | 501-626 |
| `crossref/services.py` | PreValidationService — validate_issue(), validate_component_group() | 629-1269 |
| `crossref/views.py` | Issue Crossref workflow — validate, generate, preview, download, deposit | 65-619 |
| `crossref/views.py` | Component workflow views — parallel pattern za ComponentGroup | 627-961 |
| `crossref/urls.py` | URL routing — issues/<pk>/validate/ pattern + component-groups/<pk>/ pattern | full |
| `crossref/models.py` | CrossrefExport, ExportType — discriminator FK + CheckConstraint | 18-99 |
| `crossref/validators.py` | validate_xml() — XSD validation sa lxml, schema cache, error line/column | 85-188 |
| `crossref/templates/crossref/book_chapter.xml.j2` | Postojeći book template — referenca + FIX redosled | full |
| `components/models.py` | ComponentGroup — SoftDeleteMixin, XML fields, deposit tracking (analogno Monograph) | 26-142 |
| `publications/models.py` | PublicationType enum, ISBN fields, edition, series_title | 28-34, 173-197 |
| `publications/validators.py` | validate_isbn — 13 digits, 978/979 prefix | 42-73 |
| `core/mixins.py` | SoftDeleteMixin, SoftDeleteManager — soft_delete(), restore() | 24-79 |
| `core/menu.py` | MENU_ITEMS dict, get_menu_for_user(), role-based filtering | full |
| `core/terminology.py` | TERMINOLOGY_MAP, get_term(), get_article_count_label() | full |
| `portal/views.py` | Public views — PublicationPublicDetailView, ArticleLandingView, ComponentLandingView | full |
| `portal/urls_publications.py` | Portal publication URLs — slug-based routing | full |
| `config/urls.py` | Dashboard + portal URL inclusion pattern | 16-58 |
| `config/settings/base.py` | LOCAL_APPS registracija | 89-101 |

### Technical Decisions

1. **Opcija C — Novi modeli:** Monograph i MonographChapter su potpuno novi modeli u novom `monographs/` app-u. Ne diramo Article, Issue, niti njihove FK-ove.
2. **publication_place na Monograph:** CharField na Monograph modelu, ne na Publisher-u. Isti izdavač može imati različita mesta izdanja po monografiji.
3. **Abstract base classes:** BaseContributor, BaseAffiliation, BaseFunding, BaseRelation kao abstract modeli. MonographContributor(BaseContributor) + ChapterContributor(BaseContributor). Bez GenericForeignKey.
4. **Samo monograph book_type u MVP:** book_type="monograph" hardcoded. edited_book je Phase 2.
5. **Nema migracije BOOK zapisa:** Postojeća BOOK publikacija (ID: 6) sa 0 Issues ostaje netaknuta.
6. **Crossref XML na Monograph modelu:** crossref_xml, xml_generated_at, xsd_valid itd. polja direktno na Monograph (kao što Issue ima).

## Implementation Plan

### Tasks

#### Task 1: Kreiranje `monographs/` Django app-a i modela

- [ ] **Task 1.1: App scaffolding**
  - File: `doi_portal/doi_portal/monographs/__init__.py` (NOV)
  - File: `doi_portal/doi_portal/monographs/apps.py` (NOV)
  - File: `doi_portal/doi_portal/monographs/admin.py` (NOV)
  - Action: Kreirati Django app sa `MonographsConfig`. U `apps.py:ready()` registrovati sve modele sa auditlog (try/except ImportError pattern kao `articles/apps.py`).
  - Action: U `admin.py` staviti `pass` — koristimo custom dashboard views, ne Django admin.

- [ ] **Task 1.2: Abstract base classes**
  - File: `doi_portal/doi_portal/monographs/models.py` (NOV)
  - Action: Kreirati abstract base classes na VRHU fajla, pre concrete modela:
    - `BaseContributor(SoftDeleteMixin, models.Model)` — **VAŽNO: Author u codebase koristi SoftDeleteMixin, pa i contributors moraju.** Dodaje `objects = SoftDeleteManager()`, `all_objects = models.Manager()`. Polja kopirana iz `articles/models.py:Author` (~lines 365-450): `given_name` (CharField 255, blank=True), `surname` (CharField 255), `suffix` (CharField 50, blank=True), `email` (EmailField, blank=True), `orcid` (CharField 19, blank=True, validators=[validate_orcid]), `orcid_authenticated` (BooleanField default=False), `sequence` (CharField 20, choices=AuthorSequence.choices, default=ADDITIONAL), `contributor_role` (CharField 20, choices=ContributorRole.choices, default=AUTHOR), `is_corresponding` (BooleanField default=False), `order` (PositiveIntegerField default=0). `class Meta: abstract = True, ordering = ["order"]`.
    - `BaseAffiliation(models.Model)` — **BEZ SoftDeleteMixin** (Affiliation u codebase ne koristi SoftDelete). Polja iz `articles/models.py:Affiliation` (~lines 452-504): `institution_name` (CharField 500), `institution_ror_id` (URLField, blank=True), `department` (CharField 500, blank=True), `city` (CharField 255, blank=True), `country` (CharField 255, blank=True), `order` (PositiveIntegerField default=0). `class Meta: abstract = True, ordering = ["order"]`.
    - `BaseFunding(models.Model)` — **BEZ SoftDeleteMixin** (ArticleFunding u codebase ne koristi SoftDelete). Polja iz `articles/models.py:ArticleFunding` (~lines 506-548): `funder_name` (CharField 500), `funder_doi` (URLField, blank=True), `funder_ror_id` (URLField, blank=True), `award_number` (CharField 255, blank=True), `order` (PositiveIntegerField default=0). `class Meta: abstract = True, ordering = ["order"]`.
    - `BaseRelation(models.Model)` — **BEZ SoftDeleteMixin** (ArticleRelation u codebase ne koristi SoftDelete). Polja iz `articles/models.py:ArticleRelation` (~lines 612-658): `relationship_type` (CharField 50, choices=RELATIONSHIP_TYPE_CHOICES), `relation_scope` (CharField 20, choices=RelationScope.choices, editable=False), `identifier_type` (CharField 10, choices=IdentifierType.choices, default=DOI), `target_identifier` (CharField 500), `description` (CharField 500, blank=True), `order` (PositiveIntegerField default=0). Override `save()` za auto-set `relation_scope` iz `relationship_type` (isti pattern kao ArticleRelation). `class Meta: abstract = True, ordering = ["order"]`.
  - Notes: Import enums (AuthorSequence, ContributorRole, RelationScope, IdentifierType, RELATIONSHIP_TYPE_CHOICES) iz `articles/models.py`. Import `validate_orcid` iz `articles/validators.py`. Import `validate_isbn` iz `publications/validators.py`.

- [ ] **Task 1.3: MonographStatus enum**
  - File: `doi_portal/doi_portal/monographs/models.py`
  - Action: Dodati enum klasu pre modela:
    ```python
    class MonographStatus(models.TextChoices):
        DRAFT = "DRAFT", _("Nacrt")
        PUBLISHED = "PUBLISHED", _("Objavljeno")
        WITHDRAWN = "WITHDRAWN", _("Povučeno")
    ```
  - Notes: Uprošćen u odnosu na ArticleStatus (nema REVIEW/READY jer monografija nema editorial workflow u MVP).

- [ ] **Task 1.4: Monograph model**
  - File: `doi_portal/doi_portal/monographs/models.py`
  - Action: Kreirati `Monograph(SoftDeleteMixin, models.Model)` sa poljima:
    - **Core metadata:** `title` (CharField 500), `subtitle` (CharField 500, blank=True), `doi_suffix` (CharField 255 — **NE globalni unique**, samo UniqueConstraint na `["publisher", "doi_suffix"]` sa condition=Q(is_deleted=False)), `slug` (SlugField, auto-generated from title)
    - **Publisher:** `publisher` (FK to `publishers.Publisher`, on_delete=PROTECT, related_name="monographs")
    - **Publication data:** `year` (PositiveIntegerField), `publication_place` (CharField 255, blank=True), `language` (CharField 10, blank=True), `edition_number` (CharField 50, blank=True)
    - **ISBN:** `isbn_print` (CharField 17, blank=True, validators=[validate_isbn]), `isbn_online` (CharField 17, blank=True, validators=[validate_isbn])
    - **Content:** `abstract` (TextField, blank=True), `keywords` (JSONField default=list, blank=True), `total_pages` (PositiveIntegerField null=True, blank=True)
    - **Status:** `status` (CharField 20, choices=MonographStatus.choices, default=DRAFT)
    - **License:** `license_url` (URLField, blank=True), `license_applies_to` (CharField 20, blank=True), `free_to_read` (BooleanField default=False)
    - **External resource:** `use_external_resource` (BooleanField default=False), `external_landing_url` (URLField, blank=True, help_text="Ako izdavač ima sopstvenu landing stranicu za monografiju"). Koristi se za Crossref `<resource>` URL — ako je set, koristi external URL umesto portal URL-a.
    - **Crossref XML fields** (kopirano iz ComponentGroup pattern, `components/models.py:26-142`): `crossref_xml` (TextField, blank=True), `xml_generated_at` (DateTimeField null=True), `xml_generation_status` (CharField 20, choices pending/generating/completed/failed, default="pending"), `xsd_valid` (BooleanField null=True), `xsd_errors` (JSONField default=list), `xsd_validated_at` (DateTimeField null=True), `crossref_deposited_at` (DateTimeField null=True), `crossref_deposited_by` (FK User, null=True, SET_NULL, related_name="monograph_deposits")
    - **Timestamps:** `created_at` (DateTimeField auto_now_add=True), `updated_at` (DateTimeField auto_now=True), `created_by` (FK User, null=True, SET_NULL)
    - **Managers:** `objects = SoftDeleteManager()`, `all_objects = models.Manager()`
    - **Meta:** `verbose_name = "Monografija"`, `verbose_name_plural = "Monografije"`, `ordering = ["-created_at"]`, `default_manager_name = "objects"`, UniqueConstraint na `["publisher", "doi_suffix"]` sa condition `Q(is_deleted=False)`. **Indexes:** `models.Index(fields=["status"])`, `models.Index(fields=["publisher"])` za query performance.
    - **Properties:** `full_doi` → `f"{self.publisher.doi_prefix}/{self.doi_suffix}"`, `has_chapters` → `self.chapters.exists()`, `has_xml` → `bool(self.crossref_xml)`, `is_crossref_deposited` → `self.crossref_deposited_at is not None`, `resource_url` → `self.external_landing_url if self.use_external_resource else f"{site_url}/monographs/{self.pk}/"`
    - **Override `soft_delete()`:** Cascade soft-delete svih chapters: `self.chapters.all().update(is_deleted=True, deleted_at=timezone.now(), deleted_by=user)`. Isto za contributors: `self.contributors.all().update(is_deleted=True, ...)`.
    - **Override `restore()`:** Cascade restore: `MonographChapter.all_objects.filter(monograph=self, is_deleted=True).update(is_deleted=False, deleted_at=None, deleted_by=None)`. Isto za contributors.
    - **`__str__`:** `self.title`

- [ ] **Task 1.5: MonographChapter model**
  - File: `doi_portal/doi_portal/monographs/models.py`
  - Action: Kreirati `MonographChapter(SoftDeleteMixin, models.Model)`:
    - `monograph` (FK to Monograph, on_delete=PROTECT, related_name="chapters")
    - `title` (CharField 500), `subtitle` (CharField 500, blank=True)
    - `doi_suffix` (CharField 255 — **NE globalni unique**, UniqueConstraint na `["monograph", "doi_suffix"]` sa condition=Q(is_deleted=False), isti scoping pattern kao Article)
    - `first_page` (CharField 20, blank=True), `last_page` (CharField 20, blank=True)
    - `abstract` (TextField, blank=True), `language` (CharField 10, blank=True)
    - `order` (PositiveIntegerField default=0)
    - `status` (CharField 20, choices=MonographStatus.choices, default=DRAFT)
    - `license_url` (URLField, blank=True), `license_applies_to` (CharField 20, blank=True), `free_to_read` (BooleanField default=False)
    - Timestamps: `created_at`, `updated_at`
    - Managers: `objects = SoftDeleteManager()`, `all_objects = models.Manager()`
    - Meta: ordering = ["order"], verbose_name = "Poglavlje monografije"
    - Properties: `full_doi` → `f"{self.monograph.publisher.doi_prefix}/{self.doi_suffix}"`
    - `__str__`: `f"{self.order}. {self.title}"`

- [ ] **Task 1.6: Concrete contributor/affiliation/funding/relation models**
  - File: `doi_portal/doi_portal/monographs/models.py`
  - Action: Kreirati concrete modele koji nasleđuju abstract base classes:
    - `MonographContributor(BaseContributor)` — `monograph` FK to Monograph (CASCADE, related_name="contributors")
    - `MonographAffiliation(BaseAffiliation)` — `contributor` FK to MonographContributor (CASCADE, related_name="affiliations")
    - `ChapterContributor(BaseContributor)` — `chapter` FK to MonographChapter (CASCADE, related_name="contributors")
    - `ChapterAffiliation(BaseAffiliation)` — `contributor` FK to ChapterContributor (CASCADE, related_name="affiliations")
    - `MonographFunding(BaseFunding)` — `monograph` FK to Monograph (CASCADE, related_name="fundings"). **Book-level funding** — Crossref XSD podržava `<fr:program>` unutar `<book_metadata>`.
    - `MonographRelation(BaseRelation)` — `monograph` FK to Monograph (CASCADE, related_name="relations"). **Book-level relations** — Crossref XSD podržava `<rel:program>` unutar `<book_metadata>`.
    - `ChapterFunding(BaseFunding)` — `chapter` FK to MonographChapter (CASCADE, related_name="fundings")
    - `ChapterRelation(BaseRelation)` — `chapter` FK to MonographChapter (CASCADE, related_name="relations")
  - Notes: I monograph-level I chapter-level imaju funding/relations (Crossref XSD podržava oba).

- [ ] **Task 1.7: Migracije**
  - File: `doi_portal/doi_portal/monographs/migrations/0001_initial.py` (AUTO-GENERATED)
  - Action: `python manage.py makemigrations monographs` → `python manage.py migrate`

- [ ] **Task 1.8: App registracija**
  - File: `doi_portal/config/settings/base.py`
  - Action: Dodati `"doi_portal.monographs"` u `LOCAL_APPS` listu (nakon `"doi_portal.wizard"`).

#### Task 2: Forme za monografije i poglavlja

- [ ] **Task 2.1: MonographForm**
  - File: `doi_portal/doi_portal/monographs/forms.py` (NOV)
  - Action: Kreirati `MonographForm(forms.ModelForm)`:
    - Fields: `title`, `subtitle`, `doi_suffix`, `year`, `publisher`, `publication_place`, `isbn_print`, `isbn_online`, `language`, `abstract`, `keywords`, `total_pages`, `edition_number`, `license_url`, `license_applies_to`, `free_to_read`, `use_external_resource`, `external_landing_url`
    - Publisher queryset scoping: Superadmin → all; user sa publisher → filter po publisher; else → empty (isti pattern kao ArticleForm)
    - Bootstrap 5 widget attrs na svim poljima
    - `clean()`: Validacija da `year` nije u budućnosti > 1 godina
    - Keywords: JSONField handling (isti pattern kao ArticleForm)

- [ ] **Task 2.2: MonographChapterForm**
  - File: `doi_portal/doi_portal/monographs/forms.py`
  - Action: Kreirati `MonographChapterForm(forms.ModelForm)`:
    - Fields: `title`, `subtitle`, `doi_suffix`, `first_page`, `last_page`, `abstract`, `language`, `license_url`, `license_applies_to`, `free_to_read`
    - Bootstrap 5 widget attrs

- [ ] **Task 2.3: Contributor i Affiliation forme**
  - File: `doi_portal/doi_portal/monographs/forms.py`
  - Action: Kreirati:
    - `MonographContributorForm(forms.ModelForm)` — fields: `given_name`, `surname`, `suffix`, `email`, `orcid`, `contributor_role`, `is_corresponding`
    - `MonographAffiliationForm(forms.ModelForm)` — fields: `institution_name`, `institution_ror_id`, `department`, `city`, `country`
    - `ChapterContributorForm(forms.ModelForm)` — ista polja kao MonographContributorForm
    - `ChapterAffiliationForm(forms.ModelForm)` — ista polja kao MonographAffiliationForm
    - `MonographFundingForm(forms.ModelForm)` — fields: `funder_name`, `funder_doi`, `funder_ror_id`, `award_number` (book-level funding)
    - `MonographRelationForm(forms.ModelForm)` — fields: `relationship_type`, `identifier_type`, `target_identifier`, `description` (book-level relations)
    - `ChapterFundingForm(forms.ModelForm)` — fields: `funder_name`, `funder_doi`, `funder_ror_id`, `award_number`
    - `ChapterRelationForm(forms.ModelForm)` — fields: `relationship_type`, `identifier_type`, `target_identifier`, `description`

#### Task 3: Admin dashboard views (CRUD + HTMX inline)

- [ ] **Task 3.1: Monograph CRUD views**
  - File: `doi_portal/doi_portal/monographs/views.py` (NOV)
  - Action: Kreirati class-based views:
    - `MonographListView(LoginRequiredMixin, ListView)` — queryset filtered by user's publisher, template `monographs/monograph_list.html`, context: breadcrumbs
    - `MonographCreateView(LoginRequiredMixin, CreateView)` — form_class=MonographForm, template `monographs/monograph_form.html`, auto-set `created_by`, success_url → detail
    - `MonographDetailView(LoginRequiredMixin, DetailView)` — template `monographs/monograph_detail.html`, context: breadcrumbs, chapters, contributors, can_edit, can_delete
    - `MonographUpdateView(LoginRequiredMixin, UpdateView)` — form_class=MonographForm, template `monographs/monograph_form.html`
    - `MonographDeleteView(LoginRequiredMixin, DeleteView)` — soft delete, template `monographs/monograph_confirm_delete.html`
  - Notes: Permission check pattern: `_check_monograph_permission(user, monograph)` — Superadmin/Admin → always OK; Urednik/Bibliotekar → check user.publisher == monograph.publisher

- [ ] **Task 3.2: HTMX inline contributor management (monograph-level)**
  - File: `doi_portal/doi_portal/monographs/views.py`
  - Action: Kreirati function-based views (isti pattern kao `articles/views.py` author CRUD):
    - `contributor_add(request, monograph_pk)` — @require_POST, auto-set order/sequence, return `_contributor_list.html`
    - `contributor_delete(request, pk)` — @require_POST, reorder, return `_contributor_list.html`
    - `contributor_reorder(request, monograph_pk)` — @require_POST, JSON body, return `_contributor_list.html`
    - `contributor_form_view(request, monograph_pk)` — @require_GET, return `_contributor_form.html`
    - `contributor_edit_form_view(request, pk)` — @require_GET, return `_contributor_form.html` prefilled
    - `contributor_update(request, pk)` — @require_POST, return `_contributor_list.html`
    - `affiliation_add/delete/form_view/edit_form_view/update` — isti pattern za MonographAffiliation

- [ ] **Task 3.2b: HTMX inline monograph-level funding/relation management**
  - File: `doi_portal/doi_portal/monographs/views.py`
  - Action: Isti HTMX pattern za book-level funding i relations:
    - `monograph_funding_add/delete/reorder/form_view` — za MonographFunding
    - `monograph_relation_add/delete/reorder/form_view` — za MonographRelation
  - Notes: URL pattern: `<int:monograph_pk>/funding/add/`, `<int:monograph_pk>/relations/add/` itd.

- [ ] **Task 3.3: HTMX inline chapter management**
  - File: `doi_portal/doi_portal/monographs/views.py`
  - Action: Kreirati chapter CRUD views:
    - `chapter_add(request, monograph_pk)` — @require_POST, auto-set order, return `_chapter_list.html`
    - `chapter_delete(request, pk)` — @require_POST, reorder, return `_chapter_list.html`
    - `chapter_reorder(request, monograph_pk)` — @require_POST, JSON body
    - `chapter_form_view(request, monograph_pk)` — @require_GET, return `_chapter_form.html`
    - `chapter_detail(request, pk)` — @require_GET, return `_chapter_detail.html` (expandable)
    - `chapter_edit_form_view(request, pk)` — @require_GET
    - `chapter_update(request, pk)` — @require_POST
  - Notes: Chapter detail je expandable card unutar monograph detail page.

- [ ] **Task 3.4: HTMX inline chapter contributor/funding/relation management**
  - File: `doi_portal/doi_portal/monographs/views.py`
  - Action: Isti HTMX pattern ali za chapter-level:
    - `chapter_contributor_add/delete/reorder/form_view/edit_form/update`
    - `chapter_affiliation_add/delete/form_view/edit_form/update`
    - `chapter_funding_add/delete/reorder/form_view`
    - `chapter_relation_add/delete/reorder/form_view`
  - Notes: URL pattern koristi `chapters/<int:chapter_pk>/contributors/add/` itd.

- [ ] **Task 3.5: URL routing za monographs app**
  - File: `doi_portal/doi_portal/monographs/urls.py` (NOV)
  - Action: Kreirati URL patterns sa `app_name = "monographs"`:
    - CRUD: `""` (list), `"create/"` (create), `"<int:pk>/"` (detail), `"<int:pk>/edit/"` (update), `"<int:pk>/delete/"` (delete)
    - Monograph contributors: `"<int:monograph_pk>/contributors/add/"`, `"contributors/<int:pk>/delete/"`, etc.
    - Monograph affiliations: `"contributors/<int:contributor_pk>/affiliations/add/"`, etc.
    - Chapters: `"<int:monograph_pk>/chapters/add/"`, `"chapters/<int:pk>/..."`, etc.
    - Chapter contributors/affiliations/funding/relations: nested under chapters
  - File: `doi_portal/config/urls.py`
  - Action: Dodati `path("dashboard/monographs/", include("doi_portal.monographs.urls", namespace="monographs"))` posle wizard URL-a.

#### Task 4: Admin dashboard templates

- [ ] **Task 4.1: Monograph list template**
  - File: `doi_portal/doi_portal/templates/monographs/monograph_list.html` (NOV)
  - Action: Kreirati listu monografija sa: title, publisher, year, ISBN, status badge, DOI, chapter count. "Nova monografija" button. Isti card/table layout kao `articles/article_list.html`.

- [ ] **Task 4.2: Monograph form template**
  - File: `doi_portal/doi_portal/templates/monographs/monograph_form.html` (NOV)
  - Action: Jedan formular sa svim metadata poljima. Sekcije: Osnovni podaci (title, subtitle, DOI suffix, year, publisher, place), ISBN (print, online), Sadržaj (abstract, keywords, language, pages, edition), Licenca. U edit modu: + contributor sekcija + chapter sekcija ispod forme.

- [ ] **Task 4.3: Monograph detail template**
  - File: `doi_portal/doi_portal/templates/monographs/monograph_detail.html` (NOV)
  - Action: Detail prikaz sa: metadata card, contributors card, chapters card (expandable), Crossref deposit link. Action buttons: Edit, Delete, Crossref Deposit.

- [ ] **Task 4.4: Monograph partials**
  - File: `doi_portal/doi_portal/templates/monographs/partials/` (NOV folder)
  - Action: Kreirati HTMX partials:
    - `_contributor_list.html` — lista kontributora sa drag-reorder, delete button, expand za affiliations
    - `_contributor_form.html` — inline forma za dodavanje/edit kontributora
    - `_affiliation_form.html` — inline forma za afilijaciju
    - `_funding_list.html`, `_funding_form.html` — monograph-level funding inline
    - `_relation_list.html`, `_relation_form.html` — monograph-level relation inline
    - `_chapter_list.html` — lista poglavlja sa expand/collapse, reorder, delete
    - `_chapter_form.html` — inline forma za dodavanje poglavlja
    - `_chapter_detail.html` — expandable card sa chapter metadata + contributors + funding + relations
    - `_chapter_contributor_list.html`, `_chapter_contributor_form.html`
    - `_chapter_affiliation_form.html`
    - `_chapter_funding_list.html`, `_chapter_funding_form.html`
    - `_chapter_relation_list.html`, `_chapter_relation_form.html`

- [ ] **Task 4.5: Monograph delete confirmation**
  - File: `doi_portal/doi_portal/templates/monographs/monograph_confirm_delete.html` (NOV)
  - Action: Confirm dialog sa warning o broju poglavlja. Isti pattern kao `articles/article_confirm_delete.html`.

#### Task 5: Crossref XML template i servis

- [ ] **Task 5.1: book_monograph.xml.j2 template**
  - File: `doi_portal/doi_portal/crossref/templates/crossref/book_monograph.xml.j2` (NOV)
  - Action: Kreirati Jinja2 template za Crossref XSD 5.4.0 book monograph. Strogi redosled elemenata:
    ```xml
    <doi_batch version="5.4.0" xmlns=... >
      <head>...</head>
      <body>
        <book book_type="monograph">
          <book_metadata language="{{ monograph.language }}">
            {# 1. contributors #}
            {% if contributors %}
            <contributors>
              {% for c in contributors %}
              <person_name sequence="{{ c.sequence }}" contributor_role="{{ c.contributor_role }}">
                {% if c.given_name %}<given_name>{{ c.given_name|xml_escape }}</given_name>{% endif %}
                <surname>{{ c.surname|xml_escape }}</surname>
                {% if c.suffix %}<suffix>{{ c.suffix|xml_escape }}</suffix>{% endif %}
                {% if c.affiliations %}
                <affiliations>
                  {% for aff in c.affiliations %}
                  <institution>
                    <institution_name>{{ aff.institution_name|xml_escape }}</institution_name>
                    {% if aff.institution_ror_id %}<institution_id type="ror">{{ aff.institution_ror_id }}</institution_id>{% endif %}
                    {% if aff.department %}<institution_department>{{ aff.department|xml_escape }}</institution_department>{% endif %}
                  </institution>
                  {% endfor %}
                </affiliations>
                {% endif %}
                {% if c.orcid %}<ORCID{% if c.orcid_authenticated %} authenticated="true"{% endif %}>{{ c.orcid|format_orcid_url }}</ORCID>{% endif %}
              </person_name>
              {% endfor %}
            </contributors>
            {% endif %}
            {# 2. titles (REQUIRED) #}
            <titles>
              <title>{{ monograph.title }}</title>
              {% if monograph.subtitle %}<subtitle>{{ monograph.subtitle }}</subtitle>{% endif %}
            </titles>
            {# 3. abstract #}
            {% if monograph.abstract %}
            <jats:abstract><jats:p>{{ monograph.abstract }}</jats:p></jats:abstract>
            {% endif %}
            {# 4. edition_number #}
            {% if monograph.edition_number %}
            <edition_number>{{ monograph.edition_number }}</edition_number>
            {% endif %}
            {# 5. publication_date (REQUIRED) #}
            <publication_date media_type="print">
              <year>{{ monograph.year }}</year>
            </publication_date>
            {# 7. isbn/noisbn (REQUIRED) #}
            {% if monograph.isbn_print %}
            <isbn media_type="print">{{ monograph.isbn_print|xml_escape }}</isbn>
            {% endif %}
            {% if monograph.isbn_online %}
            <isbn media_type="electronic">{{ monograph.isbn_online|xml_escape }}</isbn>
            {% endif %}
            {% if not monograph.isbn_print and not monograph.isbn_online %}
            <noisbn reason="monograph"/>
            {% endif %}
            {# 8. publisher (REQUIRED) #}
            <publisher>
              <publisher_name>{{ publisher.name|xml_escape }}</publisher_name>
              {% if monograph.publication_place %}
              <publisher_place>{{ monograph.publication_place|xml_escape }}</publisher_place>
              {% endif %}
            </publisher>
            {# 10. fr:program + ai:program (XSD: crossmark OR (fr:program + ai:program)) #}
            {% if monograph.fundings %}
            <fr:program name="fundref">
              {% for f in monograph.fundings %}
              <fr:assertion name="fundgroup">
                <fr:assertion name="funder_name">{{ f.funder_name|xml_escape }}
                  {% if f.funder_doi %}<fr:assertion name="funder_identifier">{{ f.funder_doi }}</fr:assertion>{% endif %}
                </fr:assertion>
                {% if f.award_number %}<fr:assertion name="award_number">{{ f.award_number|xml_escape }}</fr:assertion>{% endif %}
              </fr:assertion>
              {% endfor %}
            </fr:program>
            {% endif %}
            {% if monograph.license_url %}
            <ai:program name="AccessIndicators">
              {% if monograph.free_to_read %}<ai:free_to_read/>{% endif %}
              <ai:license_ref{% if monograph.license_applies_to %} applies_to="{{ monograph.license_applies_to }}"{% endif %}>{{ monograph.license_url }}</ai:license_ref>
            </ai:program>
            {% endif %}
            {# 11. rel:program #}
            {% if monograph.relations %}
            <rel:program name="relations">
              {% for r in monograph.relations %}
              <rel:related_item>
                {% if r.description %}<rel:description>{{ r.description|xml_escape }}</rel:description>{% endif %}
                <rel:{{ r.scope }}_relation relationship-type="{{ r.relationship_type }}" identifier-type="{{ r.identifier_type }}">{{ r.identifier|xml_escape }}</rel:{{ r.scope }}_relation>
              </rel:related_item>
              {% endfor %}
            </rel:program>
            {% endif %}
            {# 13. doi_data (REQUIRED) #}
            <doi_data>
              <doi>{{ publisher.doi_prefix }}/{{ monograph.doi_suffix }}</doi>
              <resource>{{ monograph.resource_url }}</resource>
            </doi_data>
          </book_metadata>
          {# content_items (chapters) #}
          {% for chapter in chapters %}
          <content_item component_type="chapter"{% if chapter.language %} language="{{ chapter.language }}"{% endif %}>
            {# chapter contributors #}
            {% if chapter.contributors %}
            <contributors>
              {% for c in chapter.contributors %}
              <person_name sequence="{{ c.sequence }}" contributor_role="{{ c.contributor_role }}">
                {% if c.given_name %}<given_name>{{ c.given_name|xml_escape }}</given_name>{% endif %}
                <surname>{{ c.surname|xml_escape }}</surname>
                {% if c.suffix %}<suffix>{{ c.suffix|xml_escape }}</suffix>{% endif %}
                {% if c.affiliations %}
                <affiliations>
                  {% for aff in c.affiliations %}
                  <institution>
                    <institution_name>{{ aff.institution_name|xml_escape }}</institution_name>
                    {% if aff.institution_ror_id %}<institution_id type="ror">{{ aff.institution_ror_id }}</institution_id>{% endif %}
                    {% if aff.department %}<institution_department>{{ aff.department|xml_escape }}</institution_department>{% endif %}
                  </institution>
                  {% endfor %}
                </affiliations>
                {% endif %}
                {% if c.orcid %}<ORCID{% if c.orcid_authenticated %} authenticated="true"{% endif %}>{{ c.orcid|format_orcid_url }}</ORCID>{% endif %}
              </person_name>
              {% endfor %}
            </contributors>
            {% endif %}
            <titles>
              <title>{{ chapter.title }}</title>
              {% if chapter.subtitle %}<subtitle>{{ chapter.subtitle }}</subtitle>{% endif %}
            </titles>
            {% if chapter.abstract %}
            <jats:abstract><jats:p>{{ chapter.abstract }}</jats:p></jats:abstract>
            {% endif %}
            {% if chapter.first_page or chapter.last_page %}
            <pages>
              {% if chapter.first_page %}<first_page>{{ chapter.first_page }}</first_page>{% endif %}
              {% if chapter.last_page %}<last_page>{{ chapter.last_page }}</last_page>{% endif %}
            </pages>
            {% endif %}
            {% if chapter.fundings %}
            <fr:program name="fundref">
              {% for f in chapter.fundings %}
              <fr:assertion name="fundgroup">
                <fr:assertion name="funder_name">{{ f.funder_name|xml_escape }}
                  {% if f.funder_doi %}<fr:assertion name="funder_identifier">{{ f.funder_doi }}</fr:assertion>{% endif %}
                </fr:assertion>
                {% if f.award_number %}<fr:assertion name="award_number">{{ f.award_number|xml_escape }}</fr:assertion>{% endif %}
              </fr:assertion>
              {% endfor %}
            </fr:program>
            {% endif %}
            {% if chapter.license_url %}
            <ai:program name="AccessIndicators">
              {% if chapter.free_to_read %}<ai:free_to_read/>{% endif %}
              <ai:license_ref{% if chapter.license_applies_to %} applies_to="{{ chapter.license_applies_to }}"{% endif %}>{{ chapter.license_url }}</ai:license_ref>
            </ai:program>
            {% endif %}
            {% if chapter.relations %}
            <rel:program name="relations">
              {% for r in chapter.relations %}
              <rel:related_item>
                {% if r.description %}<rel:description>{{ r.description|xml_escape }}</rel:description>{% endif %}
                <rel:{{ r.scope }}_relation relationship-type="{{ r.relationship_type }}" identifier-type="{{ r.identifier_type }}">{{ r.identifier|xml_escape }}</rel:{{ r.scope }}_relation>
              </rel:related_item>
              {% endfor %}
            </rel:program>
            {% endif %}
            <doi_data>
              <doi>{{ publisher.doi_prefix }}/{{ chapter.doi_suffix }}</doi>
              <resource>{{ chapter.resource_url }}</resource>
            </doi_data>
          </content_item>
          {% endfor %}
        </book>
      </body>
    </doi_batch>
    ```
  - Notes: Template mora poštovati TAČAN XSD redosled. Titles/abstract wrappovati u `Markup()` u context builderu (face markup support).
  - **VAŽNO — Razgraničenje sa book_chapter.xml.j2:** Postojeći `book_chapter.xml.j2` se koristi za Publication type=BOOK (edited books sa chapters) preko `TEMPLATE_MAP["BOOK"]`. Novi `book_monograph.xml.j2` se koristi ISKLJUČIVO za Monograph model (novi app). Nema preklapanja — različiti modeli, različiti template-i, različiti service metodi. `book_chapter.xml.j2` treba popraviti `book_type` atribut na `"edited_book"` (Task 5.5) da reflektuje njegovu stvarnu namenu. U budućnosti (Phase 2) `book_chapter.xml.j2` se može koristiti za edited_book tip sa ispravnim book_type.

- [ ] **Task 5.2: CrossrefService proširenje**
  - File: `doi_portal/doi_portal/crossref/services.py`
  - Action: Dodati metode u CrossrefService (posle component metoda, ~line 626):
    - `MONOGRAPH_TEMPLATE = "book_monograph.xml.j2"`
    - `generate_head_for_monograph(monograph)` — **NOVI metod** (isti pattern kao `generate_head_for_component()` ~line 505). Razlog: postojeći `generate_head()` zahteva Issue objekat. Monograph nema Issue. Metod čita depositor settings iz SiteSettings, registrant iz `monograph.publisher.name`. Vraća head dict.
    - `_build_monograph_context(monograph)` — assembles context dict: `head` (via generate_head_for_monograph), `publisher` (dict sa name, doi_prefix), `monograph` (dict sa Markup() wrapping za title/subtitle/abstract, + resource_url property), `contributors` (sa affiliations prefetch), `chapters` (**FILTRIRANO po status=PUBLISHED** — DRAFT chapters se NE uključuju u XML), `site_url`. Za svaki chapter: contributors, affiliations, fundings (normalize funder DOIs), relations. Za monograph: fundings, relations.
    - `generate_monograph_xml(monograph)` — loads template, renders context
    - `generate_and_store_monograph_xml(monograph)` — full pipeline: generate → XSD validate → atomic store na Monograph model (isti pattern kao `generate_and_store_xml` za Issue i `generate_and_store_component_xml` za ComponentGroup)

- [ ] **Task 5.3: PreValidationService proširenje**
  - File: `doi_portal/doi_portal/crossref/services.py`
  - Action: Dodati metode u PreValidationService:
    - `validate_monograph(monograph)` — orchestrator: calls _validate_depositor_settings(), _validate_monograph_fields(), za svako PUBLISHED poglavlje: _validate_chapter()
    - `_validate_monograph_fields(monograph)` — errors: title required, year required, doi_suffix required, publisher required, isbn_print OR isbn_online (else warning: noisbn će se koristiti). Warnings: abstract recommended, min 1 contributor recommended.
    - `_validate_chapter(chapter)` — errors: title required, doi_suffix required, min 1 contributor. Warnings: pages recommended.
    - `_validate_monograph_contributor(contributor)` — errors: surname required, contributor_role required. First contributor must have sequence="first". Warnings: given_name recommended.

- [ ] **Task 5.4: CrossrefExport proširenje**
  - File: `doi_portal/doi_portal/crossref/models.py`
  - Action:
    - Dodati `MONOGRAPH = "MONOGRAPH", _("Monografija")` u ExportType enum
    - Dodati `monograph` FK (null=True, blank=True) ka `monographs.Monograph` na CrossrefExport model
    - Ažurirati CheckConstraint da uključi monograph (exactly one of issue/component_group/monograph set)
    - **Pokrenuti `python manage.py makemigrations crossref`** — ova promena zahteva sopstvenu migraciju za crossref app (odvojena od monographs migracije u Task 1.7)

- [ ] **Task 5.5: Popravka book_chapter.xml.j2 redosleda (DVE greške)**
  - File: `doi_portal/doi_portal/crossref/templates/crossref/book_chapter.xml.j2`
  - Action: Ispraviti DVE XSD ordering greške:
    - **Greška 1 u `<book_metadata>`:** Trenutno: titles → edition → isbn → publisher → publication_date → doi_data. **Ispravno:** contributors → titles → abstract → edition_number → **publication_date** → isbn/noisbn → publisher → (fr:program + ai:program) → doi_data. `publication_date` mora biti PRE `isbn`, ne posle `publisher`.
    - **Greška 2 u `<content_item>`:** Trenutno: titles → contributors → abstract → pages → doi_data. **Ispravno:** **contributors** → titles → abstract → pages → (fr:program + ai:program) → (rel:program) → doi_data. `contributors` mora biti PRE `titles`, ne posle.
  - Action: Promeniti `book_type` atribut sa `"monograph"` na placeholder koji se čita iz context-a: `book_type="{{ book_type|default('edited_book') }}"` — pripremiti za Phase 2 razdvajanje. Trenutno BOOK flow će slati `book_type="edited_book"`, a novi monograph flow koristi `book_monograph.xml.j2`.
  - Notes: Ova popravka MORA se testirati sa postojećim BOOK publikacijama pre deploymenta. Generisati XML za Issue-e koji koriste BOOK tip i verifikovati XSD validnost.

#### Task 6: Crossref workflow views za monografije

- [ ] **Task 6.1: Monograph Crossref workflow views**
  - File: `doi_portal/doi_portal/crossref/views.py`
  - Action: Dodati views (parallel sa Component workflow, lines 627-961):
    - `MonographValidationView(LoginRequiredMixin, View)` — GET, runs PreValidationService.validate_monograph(), returns `_monograph_validation_panel.html`
    - `GenerateMonographXMLView(LoginRequiredMixin, View)` — POST, calls service.generate_and_store_monograph_xml(), returns `_monograph_generation_result.html`
    - `monograph_xml_preview(request, pk)` — GET, returns `_xml_preview_modal.html` (reuse existing)
    - `monograph_xml_download(request, pk)`, `monograph_xml_download_force(request, pk)` — creates CrossrefExport sa export_type=MONOGRAPH
    - `monograph_download_warning(request, pk)` — returns warning modal
    - `monograph_export_history(request, pk)` — last 10 exports
    - `monograph_export_redownload(request, pk)` — re-download stored XML
    - `MonographDepositView(LoginRequiredMixin, View)` — 5-step workflow page, template `monograph_crossref_deposit.html`
    - `monograph_mark_deposited(request, pk)` — POST, sets timestamps

- [ ] **Task 6.2: Crossref URL routing za monografije**
  - File: `doi_portal/doi_portal/crossref/urls.py`
  - Action: Dodati monograph routes (parallel sa component routes):
    - `monographs/<int:pk>/validate/` → MonographValidationView
    - `monographs/<int:pk>/generate/` → GenerateMonographXMLView
    - `monographs/<int:pk>/preview/` → monograph_xml_preview
    - `monographs/<int:pk>/download/` → monograph_xml_download
    - `monographs/<int:pk>/download-warning/` → monograph_download_warning
    - `monographs/<int:pk>/download-force/` → monograph_xml_download_force
    - `monographs/<int:pk>/export-history/` → monograph_export_history
    - `monographs/<int:pk>/deposit/` → MonographDepositView
    - `monographs/<int:pk>/mark-deposited/` → monograph_mark_deposited
    - `monograph-exports/<int:pk>/redownload/` → monograph_export_redownload

- [ ] **Task 6.3: Crossref workflow templates za monografije**
  - File: `doi_portal/doi_portal/templates/crossref/monograph_crossref_deposit.html` (NOV)
  - File: `doi_portal/doi_portal/templates/crossref/partials/_monograph_validation_panel.html` (NOV)
  - File: `doi_portal/doi_portal/templates/crossref/partials/_monograph_generation_result.html` (NOV)
  - Action: Kreirati templates za 5-step workflow (isti layout kao issue_crossref_deposit.html ali sa monograph kontekstom).

#### Task 7: Portal javne stranice

- [ ] **Task 7.1: Portal views za monografije**
  - File: `doi_portal/doi_portal/portal/views.py`
  - Action: Dodati:
    - `MonographPublicListView(ListView)` — model=Monograph, filter PUBLISHED only, template `portal/monographs/monograph_list.html`, paginate_by=12
    - `MonographPublicDetailView(DetailView)` — model=Monograph, template `portal/monographs/monograph_detail.html`, context: contributors, chapters (PUBLISHED), full_doi, doi_url
    - `ChapterLandingView(DetailView)` — model=MonographChapter, template `portal/monographs/chapter_detail.html`, context: contributors, full_doi, monograph

- [ ] **Task 7.2: Portal URL routing**
  - File: `doi_portal/doi_portal/portal/urls_monographs.py` (NOV)
  - Action: Kreirati URL patterns sa `app_name = "portal-monographs"`:
    - `""` → MonographPublicListView
    - `"<int:pk>/"` → MonographPublicDetailView
    - `"<int:pk>/chapters/<int:chapter_pk>/"` → ChapterLandingView
  - File: `doi_portal/config/urls.py`
  - Action: Dodati `path("monographs/", include("doi_portal.portal.urls_monographs", namespace="portal-monographs"))` u portal routes.

- [ ] **Task 7.3: Portal templates**
  - File: `doi_portal/doi_portal/templates/portal/monographs/monograph_list.html` (NOV)
  - Action: Grid/card layout za monografije. Card: title, author(s), year, publisher, ISBN, DOI badge.
  - File: `doi_portal/doi_portal/templates/portal/monographs/monograph_detail.html` (NOV)
  - Action: Full detail page: title, subtitle, contributors sa afilijacijama, abstract, ISBN, DOI (clickable), publisher+place, year, edition, keywords, license. + chapters list (if any) sa linkovima na chapter landing.
  - File: `doi_portal/doi_portal/templates/portal/monographs/chapter_detail.html` (NOV)
  - Action: Chapter landing: title, contributors, abstract, pages, DOI, parent monograph link.

#### Task 8: Menu, terminologija, i integracija

- [ ] **Task 8.1: Sidebar meni**
  - File: `doi_portal/doi_portal/core/menu.py`
  - Action: Dodati u MENU_ITEMS (posle `"component_groups"` stavke):
    ```python
    "monographs": {
        "label": "Monografije",
        "icon": "bi-book",
        "url_name": "monographs:list",
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
    },
    ```

- [ ] **Task 8.2: Terminologija**
  - File: `doi_portal/doi_portal/core/terminology.py`
  - Action: TERMINOLOGY_MAP ne treba menjati za MVP — monographs app koristi sopstvenu terminologiju hardcoded u templates/views (ne zavisi od PublicationType). BOOK terminologija ostaje za postojeći edited_book flow.
  - Notes: Ako se u budućnosti doda MONOGRAPH kao zaseban PublicationType, tada dodati terminologiju.

#### Task 9: Test factories i testovi

- [ ] **Task 9.1: Test factories**
  - File: `doi_portal/doi_portal/monographs/tests/__init__.py` (NOV)
  - File: `doi_portal/doi_portal/monographs/tests/factories.py` (NOV)
  - Action: Kreirati factories:
    - `MonographFactory(DjangoModelFactory)` — title=Faker("sentence"), doi_suffix=Sequence("mono.{n}"), year=2026, publisher=SubFactory(PublisherFactory), status=DRAFT
    - `MonographChapterFactory` — monograph=SubFactory(MonographFactory), title=Faker("sentence"), doi_suffix=Sequence("ch.{n}"), order=Sequence(lambda n: n+1)
    - `MonographContributorFactory` — monograph=SubFactory(MonographFactory), given_name=Faker("first_name"), surname=Faker("last_name"), contributor_role=AUTHOR, sequence=ADDITIONAL, order=Sequence
    - `ChapterContributorFactory`, `ChapterFundingFactory`, `ChapterRelationFactory` — analogno

- [ ] **Task 9.2: Model testovi**
  - File: `doi_portal/doi_portal/monographs/tests/test_models.py` (NOV)
  - Action: Testovi za:
    - Monograph kreiranje sa svim obaveznim poljima
    - ISBN validacija (valid, invalid, both blank → OK za noisbn)
    - DOI suffix uniqueness constraint
    - MonographChapter ordering
    - Soft delete behavior
    - `full_doi` property
    - `has_chapters` property
    - BaseRelation `save()` auto-set relation_scope

- [ ] **Task 9.3: Crossref XML testovi**
  - File: `doi_portal/doi_portal/monographs/tests/test_crossref.py` (NOV)
  - Action: Testovi za:
    - XML generacija za monografiju bez poglavlja → valid XSD
    - XML generacija za monografiju sa poglavljima → valid XSD
    - Element ordering u generisanom XML-u
    - noisbn fallback kada nema ISBN-a
    - Contributor, affiliation, funding, relation rendering u XML-u
    - PreValidation errors i warnings

- [ ] **Task 9.4: View testovi**
  - File: `doi_portal/doi_portal/monographs/tests/test_views.py` (NOV)
  - Action: Testovi za:
    - CRUD operacije (create, read, update, delete)
    - Permission checks (unauthorized user → 403)
    - HTMX contributor add/delete/reorder
    - HTMX chapter add/delete/reorder
    - Crossref workflow views (validate, generate, preview, download)

### Acceptance Criteria

#### Monograph CRUD
- [ ] AC 1: Given korisnik je ulogovan sa rolom Urednik, when klikne "Nova monografija" i popuni title/year/publisher/DOI suffix, then monografija je kreirana sa statusom DRAFT.
- [ ] AC 2: Given monografija postoji, when korisnik otvori detail stranicu, then vidi sve metadata (title, subtitle, ISBN, DOI, publisher, year, place, language, abstract, keywords, pages, edition, license, contributors, chapters).
- [ ] AC 3: Given monografija je u DRAFT statusu, when korisnik klikne Edit i izmeni polja, then promene su sačuvane.
- [ ] AC 4: Given monografija nema poglavlja, when korisnik klikne Delete i potvrdi, then monografija je soft-deleted.
- [ ] AC 5: Given monografija ima poglavlja, when korisnik pokuša Delete, then dobija warning sa brojem poglavlja pre brisanja.

#### Contributors (monograph-level)
- [ ] AC 6: Given monografija je otvorena u edit modu, when korisnik klikne "Dodaj kontributora" i popuni surname/role, then kontributor je dodat na listu sa auto-incremented order.
- [ ] AC 7: Given prvi kontributor je dodat, then sequence je automatski "first". Svi naredni su "additional".
- [ ] AC 8: Given kontributor ima ORCID, when se unese neispravan format, then form prikazuje validation error.
- [ ] AC 9: Given lista kontributora postoji, when korisnik drag-and-drop reorder-uje, then order i sequence su ažurirani.

#### Chapters
- [ ] AC 10: Given monografija je otvorena, when korisnik klikne "Dodaj poglavlje" i popuni title/DOI suffix, then poglavlje je kreirano sa auto-incremented order.
- [ ] AC 11: Given poglavlje postoji, when korisnik expand-uje poglavlje, then vidi metadata + contributors + funding + relations inline sekcije.
- [ ] AC 12: Given poglavlje ima kontributore, when korisnik doda funding sa funder_name, then funding je sačuvan i vidljiv na listi.

#### Crossref XML
- [ ] AC 13: Given monografija bez poglavlja sa svim obaveznim poljima, when se pokrene XML generacija, then generisani XML prolazi XSD 5.4.0 validaciju.
- [ ] AC 14: Given monografija sa 3 poglavlja i kontributorima, when se pokrene XML generacija, then XML sadrži `<book_metadata>` + 3 × `<content_item component_type="chapter">` i prolazi XSD validaciju.
- [ ] AC 15: Given monografija bez ISBN-a, when se generiše XML, then XML sadrži `<noisbn reason="monograph"/>` umesto `<isbn>`.
- [ ] AC 16: Given monografija sa kontributorom koji ima ORCID i afilijaciju, when se generiše XML, then XML sadrži `<ORCID>` i `<affiliations><institution>` elemente.
- [ ] AC 17: Given poglavlje sa funding informacijom, when se generiše XML, then `<content_item>` sadrži `<fr:program>` sa `<funder_name>` i `<award_number>`.

#### Pre-validation
- [ ] AC 18: Given monografija bez naslova, when se pokrene pre-validacija, then error: "Naslov monografije je obavezan".
- [ ] AC 19: Given monografija bez ISBN-a, when se pokrene pre-validacija, then warning: "ISBN nije unet — koristiće se <noisbn>".
- [ ] AC 20: Given poglavlje bez kontributora, when se pokrene pre-validacija, then error: "Poglavlje mora imati bar jednog kontributora".

#### Crossref Workflow
- [ ] AC 21: Given monografija sa validnim podacima, when korisnik otvori Crossref Deposit stranicu, then vidi 5 koraka: Pre-validacija, Generisanje, XSD, Pregled, Preuzimanje.
- [ ] AC 22: Given XML je generisan i XSD validan, when korisnik klikne Download, then dobija XML fajl i CrossrefExport zapis je kreiran sa export_type=MONOGRAPH.
- [ ] AC 23: Given monografija je deponovana, when korisnik klikne "Označi kao deponovano", then crossref_deposited_at i crossref_deposited_by su popunjeni.

#### Portal
- [ ] AC 24: Given monografija je PUBLISHED, when anonimni korisnik poseti portal monograph list, then vidi monografiju u listi sa title, author, year, DOI.
- [ ] AC 25: Given monografija sa poglavljima je PUBLISHED, when korisnik poseti monograph detail, then vidi sve metadata + listu poglavlja sa linkovima.
- [ ] AC 26: Given poglavlje ima DOI, when korisnik klikne na poglavlje, then vidi chapter landing page sa title, contributors, abstract, DOI, parent monograph link.

#### Error paths (Crossref)
- [ ] AC 27: Given monografija sa nepotpunim podacima (bez naslova), when se pokrene XML generacija, then generisanje NE uspeva, `xml_generation_status` je "failed", i korisnik vidi error poruku.
- [ ] AC 28: Given generisani XML nije XSD validan, when korisnik otvori workflow stranicu, then XSD step prikazuje greške sa brojevima linija i korisnik NE može preuzeti XML bez force download-a.
- [ ] AC 29: Given monografija je soft-deleted, when se proveri da li chapters postoje, then svi chapters su takođe soft-deleted (cascade).
- [ ] AC 30: Given monografija je restored, when se proveri chapters, then svi prethodno soft-deleted chapters su restored.

#### Menu i navigacija
- [ ] AC 31: Given korisnik je ulogovan, when otvori sidebar, then vidi "Monografije" stavku sa bi-book ikonom.
- [ ] AC 32: Given korisnik klikne "Monografije" u sidebar-u, then navigira na monograph list stranicu.

## Additional Context

### Dependencies

- `publications/validators.py:validate_isbn` — reuse za ISBN validaciju (import, ne kopija)
- `articles/validators.py:validate_orcid` — reuse za ORCID validaciju (import, ne kopija)
- `articles/models.py` — import AuthorSequence, ContributorRole, RelationScope, IdentifierType, RELATIONSHIP_TYPE_CHOICES enums
- `core/mixins.py` — import SoftDeleteMixin, SoftDeleteManager
- `crossref/services.py:CrossrefService` — proširiti sa monograph metodima (ne novi servis)
- `crossref/services.py:PreValidationService` — proširiti sa monograph validacijom
- `crossref/models.py:CrossrefExport` — dodati MONOGRAPH ExportType + FK
- `crossref/validators.py:validate_xml` — reuse za XSD validaciju
- Crossref XSD 5.4.0 schema fajl: `crossref/schemas/crossref5.4.0.xsd` (već postoji)

### Testing Strategy

- **Unit testovi (test_models.py):** Model kreiranje, validacija, constraints, properties, soft delete
- **Factory testovi (factories.py):** MonographFactory, ChapterFactory, ContributorFactory chain
- **Crossref testovi (test_crossref.py):** XML generacija oba režima, XSD validacija, element ordering, edge cases (noisbn, empty chapters, etc.)
- **View testovi (test_views.py):** CRUD, permissions, HTMX partial responses, Crossref workflow
- **Manual testing:** Full flow: create monograph → add contributors → add chapters → validate → generate XML → XSD validate → preview → download

### Notes

- **Redosled implementacije:** Models → Migrations → Forms → Views → Templates → Crossref XML → Crossref Views → Portal → Menu. **Testovi treba pisati UZ odgovarajuće taskove:** Task 9.1 (factories) + Task 9.2 (model tests) uz Task 1; Task 9.3 (XML tests) uz Task 5; Task 9.4 (view tests) uz Task 3/6. Ne odlagati sve testove na kraj.
- **Risk: XSD element ordering.** Najkritičniji deo je Jinja2 template sa tačnim redosledom. XSD testovi moraju pokrivati oba režima.
- **Risk: HTMX nesting.** Chapter contributors su nested HTMX within chapter detail within monograph form. Testirati da HTMX targets ne konfliktuuju (koristiti unique IDs per chapter: `#chapter-{pk}-contributors`).
- **Postojeća BOOK publikacija (ID: 6)** ostaje netaknuta. PublicationType.BOOK i terminologija za BOOK se ne menjaju.
- **Risk: book_chapter.xml.j2 popravka.** Task 5.5 menja redosled elemenata u postojećem template-u. Ovo utiče na SVE BOOK publikacije. Pre deploymenta: generisati XML za postojeću BOOK publikaciju (ID: 6, iako nema Issues) i verifikovati da fix ne kvari ništa.
- **Budući rad:** edited_book support (Phase 2), monograph wizard, book series metadata, citation lists.
