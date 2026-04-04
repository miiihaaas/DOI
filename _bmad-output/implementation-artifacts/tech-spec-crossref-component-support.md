---
title: 'Crossref Component (sa_component) podrška'
slug: 'crossref-component-support'
created: '2026-03-20'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Django 5.2+', 'Python 3.13', 'PostgreSQL 16+', 'Jinja2', 'HTMX 2.0.8', 'Alpine.js 3.15.3', 'Bootstrap 5.3+', 'Celery', 'lxml', 'pytest-django', 'Factory Boy', 'django-auditlog 3.0.0']
files_to_modify:
  - 'doi_portal/doi_portal/crossref/models.py'
  - 'doi_portal/doi_portal/crossref/services.py'
  - 'doi_portal/doi_portal/crossref/urls.py'
  - 'doi_portal/doi_portal/crossref/tasks.py'
  - 'doi_portal/doi_portal/crossref/views.py'
  - 'doi_portal/doi_portal/core/menu.py'
  - 'doi_portal/config/urls.py'
  - 'doi_portal/config/settings/base.py'
  - 'NEW: doi_portal/doi_portal/components/ (app)'
  - 'NEW: doi_portal/doi_portal/crossref/templates/crossref/sa_component.xml.j2'
  - 'NEW: doi_portal/doi_portal/templates/component_groups/ (HTML templates)'
  - 'NEW: doi_portal/doi_portal/templates/crossref/component_crossref_deposit.html'
  - 'NEW: doi_portal/doi_portal/templates/crossref/partials/component_*.html'
  - 'NEW: doi_portal/doi_portal/portal/urls_components.py'
  - 'NEW: doi_portal/doi_portal/templates/portal/component_landing.html'
code_patterns:
  - 'SoftDeleteMixin on all major models'
  - 'Services layer for business logic (not views)'
  - 'HTMX partials with _ prefix'
  - 'Bootstrap 5 widget attrs inline in forms'
  - 'CBV for CRUD, FBV for HTMX endpoints'
  - 'auditlog.register() in apps.py ready()'
  - 'Factory Boy factories in {app}/tests/factories.py'
  - 'PublisherScopedMixin from doi_portal.publishers.mixins (already includes LoginRequiredMixin)'
test_patterns:
  - 'pytest-django with @pytest.mark.django_db'
  - 'Factory Boy: PublisherFactory, ComponentGroupFactory, ComponentFactory, ComponentContributorFactory'
  - 'Fixtures chain: publisher → component_group → component → contributor'
  - 'View tests: client.force_login() + reverse() + response assertions'
  - 'Service tests: direct instantiation + method calls + result assertions'
---

# Tech-Spec: Crossref Component (sa_component) podrška

**Created:** 2026-03-20

## Overview

### Problem Statement

Aplikacija ne podržava Crossref `sa_component` tip sadržaja — ne može se registrovati DOI za supplementary materijale (audio, video, PDF) koji pripadaju već registrovanim DOI-jevima. Crossref XSD 5.4.0 zahteva da `<sa_component>` ide u zasebni XML batch od `<conference>`, `<journal>`, `<book>` jer `<body>` koristi `xs:choice`.

### Solution

Novi nezavisni `Component` model sa `ComponentContributor`, proširenje `CrossrefExport` modela sa `export_type` discriminatorom i nullable component FK, novi `sa_component.xml.j2` Jinja2 template (batch — više component-a u jednom `sa_component` grupisanih po parent_doi), proširenje CrossrefService i PreValidationService, novi views i UI za CRUD + workflow, portal prikaz component-a, i Crossref deposit podrška.

### Scope

**In Scope:**
- Component model (nezavisan, pod Publisher-om) + ComponentContributor model
- ComponentGroup model za grupisanje po parent_doi (analog Issue-u)
- CrossrefExport proširenje (nullable component_group FK + export_type choice field)
- sa_component.xml.j2 template (batch — više component-a u jednom sa_component)
- CrossrefService + PreValidationService proširenje za component tip
- UI za CRUD + workflow (validacija → generisanje → XSD → preview → download → deposit)
- Auto-generisan resource_url za component-e
- Portal (javni) prikaz component-a
- Crossref deposit API integracija za component-e

**Out of Scope:**
- Migracija postojećih Article-a u Component-e
- Promene na postojećim Journal/Conference/Book workflow-ovima

## Context for Development

### Codebase Patterns

- **Model hijerarhija**: Publisher → Publication → Issue → Article → Author/Affiliation/Funding. Component se uvodi kao nova grana: Publisher → ComponentGroup → Component → ComponentContributor
- **SoftDeleteMixin**: Svi major modeli koriste `SoftDeleteMixin` (is_deleted, deleted_at, deleted_by) sa `SoftDeleteManager` kao default manager i `all_objects = models.Manager()` za admin
- **Services layer**: Kompleksna logika u `services.py` — views delegiraju ka servisima. `CrossrefService` koristi Jinja2 `Environment` sa custom filterima, `_build_context()` gradi flat dict za template
- **Template selekcija**: `TEMPLATE_MAP` dict mapira `publication_type` → template fajl. Za component treba nova ruta mimo ovog map-a
- **PreValidation**: `PreValidationService` koristi `ValidationResult` sa `errors` i `warnings` listama, svaki sa `message` i opcionim `fix_url`
- **HTMX partials**: `_` prefiks, uvek vraćaju HTML (nikad JSON). Auto-load sa `hx-trigger="load"`
- **Views**: CBV sa `PublisherScopedMixin` (koji već uključuje `LoginRequiredMixin` — NE duplirati) za CRUD; FBV sa `@login_required` + `@require_POST/GET` za HTMX endpoints. Import: `from doi_portal.publishers.mixins import PublisherScopedMixin, PublisherScopedEditMixin`
- **Permission**: `from doi_portal.core.permissions import has_publisher_access` — Superuser/Administrator bypass, Urednik/Bibliotekar moraju imati `user.publisher == publisher`
- **Forms**: `ModelForm` subclass, Bootstrap 5 widget attrs inline, `add_error_classes()` pattern, user-scoped querysets u `__init__`
- **Auditlog**: Registracija u `apps.py` `ready()` metodi
- **Celery**: Tasks u `tasks.py`, naming `{app}_{action}_task`, `bind=True, max_retries=3`
- **URL konvencija**: kebab-case, plural za liste, `app_name` namespace
- **Lokalizacija**: Srpski (sr-latn) UI sa dijakriticima, engleski kod komentari
- **Dependency management**: `uv` + `pyproject.toml` (NIKAD `requirements.txt`)
- **Jinja2 autoescape**: `CrossrefService` inicijalizuje Jinja2 Environment sa `autoescape=select_autoescape(enabled_extensions=("xml", ".j2"))`. To znači da se sav string sadržaj automatski escapuje. NE koristiti `| xml_escape` filter na element text content-u — samo na attribute values gde `Markup()` nije primenjen. Vrednosti wrappovane u `Markup()` (title, subtitle) prolaze bez escapovanja.
- **Sidebar**: Menu stavke se definišu u `doi_portal/doi_portal/core/menu.py` kao `MENU_ITEMS` dict. Template tag `{% render_sidebar_menu %}` iz `doi_portal/doi_portal/core/templatetags/menu_tags.py` renderuje `components/_sidebar_menu.html` inclusion tag. Dodavanje nove stavke = dodavanje entry-ja u `MENU_ITEMS`.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `doi_portal/doi_portal/articles/models.py` | Article, Author, Affiliation, ArticleFunding modeli — referenca za field tipove i SoftDeleteMixin pattern |
| `doi_portal/doi_portal/publishers/models.py` | Publisher model sa `doi_prefix`, `crossref_username`, `crossref_password` (encrypted) |
| `doi_portal/doi_portal/publishers/mixins.py` | `PublisherScopedMixin`, `PublisherScopedEditMixin` — RBAC mixini za views (već uključuju LoginRequiredMixin) |
| `doi_portal/doi_portal/core/permissions.py` | `has_publisher_access(user, publisher)` — permission check funkcija |
| `doi_portal/doi_portal/core/menu.py` | `MENU_ITEMS` dict i `get_menu_for_user()` — sidebar konfiguracija |
| `doi_portal/doi_portal/publications/models.py` | Publication model sa `publication_type` choices — referenca za type-specific field pattern |
| `doi_portal/doi_portal/issues/models.py` | Issue model sa XML/XSD/deposit fieldovima i odvojenim `year`, `publication_month`, `publication_day` — pattern za parcijalne datume |
| `doi_portal/doi_portal/crossref/models.py` | CrossrefExport — treba proširiti sa nullable FK + export_type + DB constraint |
| `doi_portal/doi_portal/crossref/services.py` | CrossrefService + PreValidationService — treba proširiti za component tip |
| `doi_portal/doi_portal/crossref/views.py` | Crossref workflow views — referenca za HTMX patterns, permission checks, deposit flow. PAŽNJA: `export_redownload` pristupa `export.issue.publication.publisher` — treba null guard |
| `doi_portal/doi_portal/crossref/urls.py` | URL patterns — treba dodati component rute |
| `doi_portal/doi_portal/crossref/tasks.py` | Celery task za async XML generisanje — treba nova task za component |
| `doi_portal/doi_portal/crossref/templates/crossref/conference_paper.xml.j2` | Referentni template — NE koristi `\| xml_escape` na element text, oslanja se na autoescape |
| `doi_portal/doi_portal/articles/views.py` | CRUD + HTMX pattern referenca za contributor management |
| `doi_portal/doi_portal/portal/views.py` | Portal views — referenca za javne stranice |
| `doi_portal/doi_portal/crossref/tests/` | Test patterns — pytest fixtures, Factory Boy, view/service test struktura |
| `docs/project-context.md` | Projekat konvencije i pravila |
| `zanos-margine-component_20260320.xml` | Primer sa_component XML-a — target format za template |

### Technical Decisions

- **Component je potpuno novi model** nezavisan od Article/Issue hijerarhije — živi direktno pod Publisher-om sa `parent_doi` kao string polje (ne FK)
- **ComponentContributor** je novi model (isti fields kao Author, FK ka Component) — minimalan impact na postojeći kod
- **ComponentGroup** koncept — grupisanje component-a po `parent_doi` za batch XML generisanje. XML/XSD/deposit fieldovi žive na ComponentGroup nivou (analog Issue-u). Polja: `publisher` (FK), `parent_doi` (CharField, unique per publisher), `title` (opciono — label za UI), crossref_xml, xml_generated_at, xml_generation_status, xsd_valid, xsd_errors, xsd_validated_at, crossref_deposited_at, crossref_deposited_by
- **CrossrefExport** dobija nullable `component_group` FK + `export_type` choice field (`ISSUE`/`COMPONENT_GROUP`) + DB-level CHECK constraint (tačno jedan od `issue`/`component_group` mora biti non-null) — jedan model za oba tipa exporta
- **resource_url** se auto-generiše: `{site_url}/components/{pk}/` (analog Article pattern-u `{site_url}/articles/{pk}/`)
- **Batch XML** — jedan `<sa_component parent_doi="...">` sa `<component_list>` koji sadrži sve component-e za taj parent_doi
- **Nova Django app `components`** — izolovana od articles/issues, sa sopstvenim models, views, forms, urls, admin, tests. Template directory: `templates/component_groups/` (NE `templates/components/` jer taj folder već sadrži reusable UI komponente: `_sidebar_menu.html`, `_breadcrumbs.html`, `_pagination.html`, `_user_dropdown.html`)
- **Crossref deposit** — isti workflow kao za Issue (5 koraka), sa `mark_deposited` na ComponentGroup nivou
- **Sidebar integracija** — nova stavka "Komponente" u `MENU_ITEMS` dict u `doi_portal/core/menu.py`
- **Parcijalni datumi** — Component koristi odvojene `publication_year`, `publication_month`, `publication_day` polja (kao Issue model) umesto jednog `DateField`, jer Crossref dozvoljava parcijalne datume (samo godina, godina+mesec)
- **Autoescape strategija za XML template** — NE koristiti `| xml_escape` filter na element text. Jinja2 autoescape je uključen za `.xml.j2` fajlove. Koristiti `Markup()` wrapper u context builder-u za vrednosti koje sadrže inline XML (title face markup). Za attribute values koristiti `| xml_escape` samo tamo gde autoescape ne pokriva (atributi u nekim Jinja2 verzijama).

## Implementation Plan

### Tasks

#### Faza 1: Modeli i migracije (lowest level — nema zavisnosti)

- [ ] Task 1: Kreirati `components` Django app
  - File: `doi_portal/doi_portal/components/__init__.py` (NEW)
  - File: `doi_portal/doi_portal/components/apps.py` (NEW)
  - Action: Kreirati app sa `ComponentsConfig(AppConfig)`, `name = "doi_portal.components"`, `verbose_name = _("Komponente")`. U `ready()` registrovati auditlog za Component, ComponentGroup, ComponentContributor.
  - File: `doi_portal/config/settings/base.py` (MODIFY)
  - Action: Dodati `"doi_portal.components"` u `LOCAL_APPS` listu.

- [ ] Task 2: Kreirati ComponentGroup model
  - File: `doi_portal/doi_portal/components/models.py` (NEW)
  - Action: Kreirati `ComponentGroup(SoftDeleteMixin, models.Model)` sa sledećim fieldovima:
    - `publisher` — FK ka `publishers.Publisher`, PROTECT, related_name="component_groups"
    - `parent_doi` — CharField(255), required. Puni DOI roditelja (npr. "10.66117/emce_zapisi.2026.1")
    - `title` — CharField(500), blank. Opcioni label za UI prikaz (npr. "Zapisi sa margine — audio komponente")
    - `crossref_xml` — TextField, blank
    - `xml_generated_at` — DateTimeField, null, blank
    - `xml_generation_status` — CharField(20), choices=[pending, generating, completed, failed], default=pending
    - `xsd_valid` — BooleanField, null, blank
    - `xsd_errors` — JSONField, default=list, blank
    - `xsd_validated_at` — DateTimeField, null, blank
    - `crossref_deposited_at` — DateTimeField, null, blank
    - `crossref_deposited_by` — FK ka users.User, SET_NULL, null, blank, related_name="component_deposits"
    - `created_at` — DateTimeField, auto_now_add
    - `updated_at` — DateTimeField, auto_now
  - Meta: ordering=["-created_at"], UniqueConstraint(fields=["publisher", "parent_doi"], condition=Q(is_deleted=False), name="unique_component_group_parent_doi_per_publisher")
  - Managers: `objects = SoftDeleteManager()`, `all_objects = models.Manager()`
  - Methods: `__str__()` → `self.title or self.parent_doi`, `component_count` (property) → `self.components.count()`, `is_crossref_deposited` (property) → `self.crossref_deposited_at is not None`, `label` (property) → `self.title or f"Komponente za {self.parent_doi}"`

- [ ] Task 3: Kreirati Component model
  - File: `doi_portal/doi_portal/components/models.py` (APPEND)
  - Action: Kreirati `Component(SoftDeleteMixin, models.Model)` sa:
    - `component_group` — FK ka ComponentGroup, CASCADE, related_name="components"
    - `parent_relation` — CharField(50), default="isPartOf". Crossref parent_relation atribut.
    - `title` — CharField(500), blank. Preporučeno ali ne obavezno.
    - `description` — TextField, blank. Crossref `<description>` element.
    - `format_mime_type` — CharField(100), blank. MIME tip (npr. "audio/mpeg", "video/mp4", "application/pdf").
    - `doi_suffix` — CharField(100), required. Sufix za DOI (kompletni DOI = publisher.doi_prefix + "/" + doi_suffix).
    - `resource_url` — URLField(500), blank. Auto-generiše se ako je prazno.
    - `publication_year` — PositiveIntegerField, null, blank. Godina publikacije (obavezna ako se šalje publication_date u XML).
    - `publication_month` — PositiveSmallIntegerField, null, blank, validators=[MinValueValidator(1), MaxValueValidator(12)]. Opciono.
    - `publication_day` — PositiveSmallIntegerField, null, blank, validators=[MinValueValidator(1), MaxValueValidator(31)]. Opciono.
    - `order` — PositiveIntegerField, default=0. Za redosled u listi.
    - `created_at` — DateTimeField, auto_now_add
    - `updated_at` — DateTimeField, auto_now
  - Meta: ordering=["order", "created_at"], UniqueConstraint(fields=["component_group", "doi_suffix"], condition=Q(is_deleted=False), name="unique_component_doi_suffix_per_group")
  - Managers: `objects = SoftDeleteManager()`, `all_objects = models.Manager()`
  - Methods: `__str__()` → `self.title or self.doi_suffix`, `full_doi` (property) → `f"{self.component_group.publisher.doi_prefix}/{self.doi_suffix}"`

- [ ] Task 4: Kreirati ComponentContributor model
  - File: `doi_portal/doi_portal/components/models.py` (APPEND)
  - Action: Kreirati `ComponentContributor(SoftDeleteMixin, models.Model)` sa istim fieldovima kao Author:
    - `component` — FK ka Component, CASCADE, related_name="contributors"
    - `given_name` — CharField(255), blank
    - `surname` — CharField(255), required
    - `suffix` — CharField(50), blank
    - `email` — EmailField, blank
    - `orcid` — CharField(19), blank, validators=[validate_orcid]
    - `orcid_authenticated` — BooleanField, default=False
    - `sequence` — CharField(20), choices=AuthorSequence, default=ADDITIONAL (reuse iz articles.models)
    - `contributor_role` — CharField(20), choices=ContributorRole, default=AUTHOR (reuse iz articles.models)
    - `order` — PositiveIntegerField, default=0
  - Meta: ordering=["order"]
  - Managers: `objects = SoftDeleteManager()`, `all_objects = models.Manager()`, `default_manager_name = "objects"`
  - Methods: `__str__()` → `"{given_name} {surname}"` ili samo `surname`
  - Notes: Importovati `validate_orcid` iz `doi_portal.articles.validators`, `AuthorSequence` i `ContributorRole` iz `doi_portal.articles.models`.

- [ ] Task 5: Kreirati migraciju
  - Action: `python manage.py makemigrations components`
  - Verification: Proveriti da migracija kreira sve tri tabele sa ispravnim constraint-ima.

#### Faza 2: CrossrefExport proširenje

- [ ] Task 6: Proširiti CrossrefExport model
  - File: `doi_portal/doi_portal/crossref/models.py` (MODIFY)
  - Action: Dodati:
    - `ExportType(models.TextChoices)`: `ISSUE = "ISSUE", _("Izdanje")` / `COMPONENT_GROUP = "COMPONENT_GROUP", _("Grupa komponenti")`
    - `component_group` — FK ka `components.ComponentGroup`, CASCADE, null=True, blank=True, related_name="crossref_exports"
    - `export_type` — CharField(20), choices=ExportType, default=ISSUE
  - Action: Promeniti `issue` FK da bude nullable: `null=True, blank=True` (jer ComponentGroup exporti nemaju issue).
  - Action: Dodati DB-level CHECK constraint u `Meta.constraints`:
    ```python
    models.CheckConstraint(
        check=(
            models.Q(issue__isnull=False, component_group__isnull=True, export_type="ISSUE")
            | models.Q(issue__isnull=True, component_group__isnull=False, export_type="COMPONENT_GROUP")
        ),
        name="crossref_export_exactly_one_source",
    )
    ```
  - Action: NE dodavati `clean()` metodu — umesto toga osloniti se na DB constraint. Create paths u views-ovima moraju eksplicitno setovati ispravne FK-ove.
  - Action: `python manage.py makemigrations crossref`
  - Notes: Migracija će automatski dodati default `export_type="ISSUE"` na postojeće redove. Svi postojeći redovi imaju `issue` popunjen i `component_group=NULL`, što zadovoljava CHECK constraint.

- [ ] Task 6a: Ažurirati postojeće CrossrefExport views za nullable issue
  - File: `doi_portal/doi_portal/crossref/views.py` (MODIFY)
  - Action: Ažurirati `export_redownload` view — dodati null guard:
    ```python
    # Permission check — handle both issue and component_group exports
    if export.issue:
        publisher = export.issue.publication.publisher
    elif export.component_group:
        publisher = export.component_group.publisher
    else:
        raise Http404
    if not has_publisher_access(request.user, publisher):
        raise PermissionDenied
    ```
  - Action: Ažurirati `export_history` view — ako se koristi za component_group, filtrirati po `component_group` umesto `issue`:
    ```python
    # Existing issue export history remains unchanged.
    # Component export history uses separate view (Task 17).
    ```
  - Action: Proveriti `CrossrefExport.__str__` — radi sa nullable issue jer koristi `self.filename`.

#### Faza 3: Forme i admin

- [ ] Task 7: Kreirati forme za Component app
  - File: `doi_portal/doi_portal/components/forms.py` (NEW)
  - Action: Kreirati forme po postojećem pattern-u (Bootstrap 5 widget attrs, `add_error_classes()`):
    - `ComponentGroupForm(forms.ModelForm)` — fields: publisher (hidden ili user-scoped), parent_doi, title. `__init__(self, *args, user=None, **kwargs)` za publisher scoping.
    - `ComponentForm(forms.ModelForm)` — fields: title, description, format_mime_type, doi_suffix, resource_url, publication_year, publication_month, publication_day, parent_relation, order. `format_mime_type` sa Select widget i common MIME tipovi kao choices + opcija za ručni unos.
    - `ComponentContributorForm(forms.ModelForm)` — fields: given_name, surname, suffix, email, orcid, orcid_authenticated, sequence, contributor_role, order. Isti layout kao AuthorForm.
  - Notes: Srpske labele sa `_()`. MIME type dropdown sa opcijama: audio/mpeg, video/mp4, application/pdf, image/jpeg, image/png, text/html, application/zip, prazno (ostalo).

- [ ] Task 8: Kreirati admin registraciju
  - File: `doi_portal/doi_portal/components/admin.py` (NEW)
  - Action: Registrovati `ComponentGroup` i `Component` u Django admin (za superadmin pristup). Pratiti pattern iz `publications/admin.py`:
    - `ComponentGroupAdmin`: list_display=[parent_doi, title, publisher, component_count, created_at], list_filter=[publisher], search_fields=[parent_doi, title], readonly_fields za timestamps i soft-delete polja
    - `ComponentAdmin`: list_display=[title, doi_suffix, component_group, format_mime_type, order], list_filter=[component_group__publisher]

#### Faza 4: XML template i service proširenje

- [ ] Task 9: Kreirati sa_component.xml.j2 template
  - File: `doi_portal/doi_portal/crossref/templates/crossref/sa_component.xml.j2` (NEW)
  - Action: Kreirati Jinja2 template po Crossref 5.4.0 šemi. Referenca: `zanos-margine-component_20260320.xml`.
  - **KRITIČNO — Autoescape pravila**: Jinja2 Environment ima `autoescape=True` za `.xml.j2`. NE koristiti `| xml_escape` na element text content — autoescape to radi automatski. Koristiti `Markup()` wrapper u context builder-u za vrednosti koje NE treba escapovati (title face markup). Za atribute koji primaju plain string vrednosti, autoescape ih takođe pokriva.
  - **KRITIČNO — Element ordering po XSD**: titles → contributors → publication_date → description → format → doi_data
  - Struktura:
    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <doi_batch version="5.4.0" xmlns="http://www.crossref.org/schema/5.4.0"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="http://www.crossref.org/schema/5.4.0 https://www.crossref.org/schemas/crossref5.4.0.xsd">
      <head>
        <doi_batch_id>{{ head.doi_batch_id }}</doi_batch_id>
        <timestamp>{{ head.timestamp }}</timestamp>
        <depositor>
          <depositor_name>{{ head.depositor_name }}</depositor_name>
          <email_address>{{ head.depositor_email }}</email_address>
        </depositor>
        <registrant>{{ head.registrant }}</registrant>
      </head>
      <body>
        <sa_component parent_doi="{{ parent_doi }}">
          <component_list>
            {% for component in components %}
            <component parent_relation="{{ component.parent_relation }}">
              {% if component.title %}
              <titles>
                <title>{{ component.title }}</title>
              </titles>
              {% endif %}
              {% if component.contributors %}
              <contributors>
                {% for contributor in component.contributors %}
                <person_name sequence="{{ contributor.sequence }}" contributor_role="{{ contributor.contributor_role }}">
                  {% if contributor.given_name %}<given_name>{{ contributor.given_name }}</given_name>{% endif %}
                  <surname>{{ contributor.surname }}</surname>
                  {% if contributor.suffix %}<suffix>{{ contributor.suffix }}</suffix>{% endif %}
                  {% if contributor.orcid %}<ORCID>{{ contributor.orcid | format_orcid_url }}</ORCID>{% endif %}
                </person_name>
                {% endfor %}
              </contributors>
              {% endif %}
              {% if component.publication_year %}
              <publication_date>
                {% if component.publication_month %}<month>{{ component.publication_month | format_month }}</month>{% endif %}
                {% if component.publication_day %}<day>{{ component.publication_day | format_day }}</day>{% endif %}
                <year>{{ component.publication_year }}</year>
              </publication_date>
              {% endif %}
              {% if component.description %}
              <description>{{ component.description }}</description>
              {% endif %}
              {% if component.format_mime_type %}
              <format mime_type="{{ component.format_mime_type }}"/>
              {% endif %}
              <doi_data>
                <doi>{{ component.doi }}</doi>
                <resource>{{ component.resource_url }}</resource>
              </doi_data>
            </component>
            {% endfor %}
          </component_list>
        </sa_component>
      </body>
    </doi_batch>
    ```
  - Notes: Namespace deklaracije — samo osnovni Crossref namespace + xsi. JATS, ai (AccessIndicators) i fr (FundRef) namespace-ovi NISU potrebni za sa_component. Title u context-u je `Markup()` wrappovan (face markup podrška). Svi ostali string-ovi prolaze kroz autoescape.

- [ ] Task 10: Proširiti CrossrefService za component generisanje
  - File: `doi_portal/doi_portal/crossref/services.py` (MODIFY)
  - Action: Dodati u `CrossrefService`:
    - `SA_COMPONENT_TEMPLATE = "sa_component.xml.j2"` — konstantna, ne koristi TEMPLATE_MAP
    - `_build_component_context(self, component_group: ComponentGroup) -> dict` — novi metod koji gradi kontekst:
      ```python
      {
          "head": self.generate_head_for_component(component_group),
          "parent_doi": component_group.parent_doi,
          "components": [
              {
                  "parent_relation": c.parent_relation,
                  "title": Markup(markup_to_crossref_xml(c.title)) if c.title else None,
                  "contributors": [
                      {"given_name": ct.given_name, "surname": ct.surname, "suffix": ct.suffix,
                       "orcid": ct.orcid, "sequence": ct.sequence, "contributor_role": ct.contributor_role}
                      for ct in c.contributors.filter(is_deleted=False).order_by("order")
                  ],
                  "description": c.description,
                  "format_mime_type": c.format_mime_type,
                  "doi": f"{component_group.publisher.doi_prefix}/{c.doi_suffix}",
                  "resource_url": c.resource_url or f"{self._get_site_url()}/components/{c.pk}/",
                  "publication_year": c.publication_year,
                  "publication_month": c.publication_month,
                  "publication_day": c.publication_day,
              }
              for c in component_group.components.filter(is_deleted=False).order_by("order")
          ],
      }
      ```
    - `generate_head_for_component(self, component_group: ComponentGroup) -> dict` — analog `generate_head(issue)` ali koristi `component_group.publisher` umesto `issue.publication.publisher`
    - `generate_component_xml(self, component_group: ComponentGroup) -> str` — renderuje `sa_component.xml.j2` sa kontekstom
    - `generate_and_store_component_xml(self, component_group: ComponentGroup) -> tuple[bool, str]` — analog `generate_and_store_xml(issue)`, ali čuva na ComponentGroup fieldovima (crossref_xml, xml_generated_at, itd.), poziva `validate_xml()` za XSD
  - Notes: Query treba da koristi `prefetch_related("components__contributors")` za optimizaciju. Contributor fields su plain strings (ne Markup) — autoescape ih pokriva u template-u.

- [ ] Task 11: Proširiti PreValidationService za component validaciju
  - File: `doi_portal/doi_portal/crossref/services.py` (MODIFY)
  - Action: Dodati u `PreValidationService`:
    - `validate_component_group(self, component_group: ComponentGroup) -> ValidationResult` — orkestrira:
      1. `_validate_depositor_settings()` (reuse)
      2. `_validate_component_group_fields(component_group)` — provere: parent_doi obavezan (ERROR), parent_doi format "10.XXXX/..." (ERROR), bar jedan component (ERROR), title preporuka (WARNING)
      3. `_validate_component_parent_doi_exists(component_group)` — WARNING
      4. Za svaki non-deleted component: `_validate_component(component)`
    - `_validate_component_group_fields(self, cg: ComponentGroup) -> ValidationResult`
    - `_validate_component(self, component: Component) -> ValidationResult` — provere:
      - doi_suffix obavezan (ERROR)
      - doi_suffix format bez "/" (ERROR)
      - title preporuka (WARNING ako je prazan)
      - format_mime_type validacija — mora biti valid MIME format "type/subtype" (WARNING ako je nevažeći)
      - bar jedan contributor (WARNING, ne ERROR — contributori su opcioni za component po Crossref šemi)
      - Za svakog contributora: surname obavezan (ERROR), contributor_role obavezan (ERROR)
    - `_validate_component_parent_doi_exists(self, cg: ComponentGroup) -> ValidationResult` — WARNING ako parent_doi ne postoji kao DOI ni u jednom Article-u ni Issue-u u sistemu (lookup: Article.doi_suffix sa publisher prefix match, Issue.doi_suffix sa publisher prefix match). Ovo je samo upozorenje jer parent DOI može biti registrovan van sistema.

#### Faza 5: Celery task

- [ ] Task 12: Kreirati Celery task za component XML generisanje
  - File: `doi_portal/doi_portal/crossref/tasks.py` (MODIFY)
  - Action: Dodati `crossref_generate_component_xml_task(self, component_group_id)` — analog `crossref_generate_xml_task`:
    - `@shared_task(bind=True, max_retries=3, default_retry_delay=60)`
    - Isti pattern: set status "generating" → `CrossrefService().generate_and_store_component_xml(cg)` → return result
    - Exception handling: DoesNotExist → fail bez retry, ostalo → retry sa max 3

#### Faza 6: Admin views (CRUD + workflow)

- [ ] Task 13: Kreirati CRUD views za ComponentGroup
  - File: `doi_portal/doi_portal/components/views.py` (NEW)
  - Action: Kreirati views po Article/Issue CRUD pattern-u. **VAŽNO**: `PublisherScopedMixin` već uključuje `LoginRequiredMixin` — NE duplirati.
    - `ComponentGroupListView(PublisherScopedMixin, ListView)` — lista ComponentGroup-a za publisher, pagination 20. `get_queryset()` poziva `self.get_scoped_queryset(ComponentGroup.objects.all())` — ovo radi jer ComponentGroup ima direktan `publisher` FK.
    - `ComponentGroupCreateView(PublisherScopedEditMixin, CreateView)` — forma za novi ComponentGroup, redirect na detail
    - `ComponentGroupDetailView(PublisherScopedMixin, DetailView)` — prikaz ComponentGroup-a sa listom component-a. Permission check: `has_publisher_access(self.request.user, self.object.publisher)`
    - `ComponentGroupUpdateView(PublisherScopedEditMixin, UpdateView)` — edit ComponentGroup metadata
    - `ComponentGroupDeleteView(PublisherScopedEditMixin, DeleteView)` — soft delete sa `AdministratorRequiredMixin`
  - Imports:
    ```python
    from doi_portal.publishers.mixins import PublisherScopedMixin, PublisherScopedEditMixin
    from doi_portal.core.permissions import has_publisher_access
    ```
  - Notes: Breadcrumbs: Komponente → ComponentGroup.

- [ ] Task 14: Kreirati CRUD views za Component (unutar ComponentGroup)
  - File: `doi_portal/doi_portal/components/views.py` (APPEND)
  - Action: Kreirati:
    - `ComponentCreateView` — forma za novi Component unutar ComponentGroup. Permission: `has_publisher_access(request.user, component_group.publisher)`
    - `ComponentUpdateView` — edit Component polja. Permission: `has_publisher_access(request.user, component.component_group.publisher)`
    - `ComponentDetailView` — prikaz Component-a sa contributor listom
    - `ComponentDeleteView` — soft delete
  - Notes: Svi scoped pod ComponentGroup. URL pattern: `/dashboard/components/groups/<group_pk>/components/<pk>/`. Permission traversal: `component.component_group.publisher`.

- [ ] Task 15: Kreirati HTMX contributor management za Component
  - File: `doi_portal/doi_portal/components/views.py` (APPEND)
  - Action: Kreirati FBV po Article author management pattern-u iz `articles/views.py`:
    - `contributor_add(request, component_pk)` — POST, kreira ComponentContributor. Permission: `has_publisher_access(request.user, component.component_group.publisher)`
    - `contributor_update(request, contributor_pk)` — POST, ažurira contributor
    - `contributor_delete(request, contributor_pk)` — POST, soft delete
    - `contributor_reorder(request, component_pk)` — POST, JSON body sa novim redosledom
    - `contributor_form_view(request, component_pk)` — GET, prazan formular partial
    - `contributor_edit_form_view(request, contributor_pk)` — GET, popunjen formular partial
  - Notes: Isti HTMX pattern kao author management — partials za inline editing. Svaki FBV mora imati permission check: `has_publisher_access(request.user, publisher)` gde se `publisher` dobija traversal-om: `component.component_group.publisher` ili `contributor.component.component_group.publisher`.

- [ ] Task 16: Kreirati URL konfiguraciju za components app
  - File: `doi_portal/doi_portal/components/urls.py` (NEW)
  - Action: `app_name = "components"`, URL patterns:
    - `""` → ComponentGroupListView (`components:group-list`)
    - `"groups/create/"` → ComponentGroupCreateView (`components:group-create`)
    - `"groups/<int:pk>/"` → ComponentGroupDetailView (`components:group-detail`)
    - `"groups/<int:pk>/edit/"` → ComponentGroupUpdateView (`components:group-update`)
    - `"groups/<int:pk>/delete/"` → ComponentGroupDeleteView (`components:group-delete`)
    - `"groups/<int:group_pk>/components/create/"` → ComponentCreateView (`components:component-create`)
    - `"groups/<int:group_pk>/components/<int:pk>/"` → ComponentDetailView (`components:component-detail`)
    - `"groups/<int:group_pk>/components/<int:pk>/edit/"` → ComponentUpdateView (`components:component-update`)
    - `"groups/<int:group_pk>/components/<int:pk>/delete/"` → ComponentDeleteView (`components:component-delete`)
    - `"components/<int:component_pk>/contributors/add/"` → contributor_add (`components:contributor-add`)
    - `"contributors/<int:contributor_pk>/update/"` → contributor_update (`components:contributor-update`)
    - `"contributors/<int:contributor_pk>/delete/"` → contributor_delete (`components:contributor-delete`)
    - `"components/<int:component_pk>/contributors/reorder/"` → contributor_reorder (`components:contributor-reorder`)
    - `"components/<int:component_pk>/contributors/form/"` → contributor_form_view (`components:contributor-form`)
    - `"contributors/<int:contributor_pk>/edit-form/"` → contributor_edit_form_view (`components:contributor-edit-form`)
  - File: `doi_portal/config/urls.py` (MODIFY)
  - Action: Dodati `path("dashboard/components/", include("doi_portal.components.urls", namespace="components"))` u urlpatterns.

#### Faza 7: Crossref workflow views za Component

- [ ] Task 17: Kreirati Crossref workflow views za ComponentGroup
  - File: `doi_portal/doi_portal/crossref/views.py` (MODIFY)
  - Action: Dodati views po istom pattern-u kao Issue workflow, ali za ComponentGroup. **VAŽNO**: Svaki view mora koristiti `has_publisher_access(request.user, component_group.publisher)` za permission check (NE `issue.publication.publisher`).
    - `ComponentGroupValidationView(LoginRequiredMixin, View)` — GET, poziva `PreValidationService().validate_component_group(cg)`, renderuje `crossref/partials/_component_validation_panel.html`. Permission: `has_publisher_access(request.user, cg.publisher)`.
    - `GenerateComponentXMLView(LoginRequiredMixin, View)` — POST, pre-validacija → sync/async generisanje (threshold: >20 components → Celery task, isti kao Article), renderuje `_component_generation_result.html`. Permission: `has_publisher_access(request.user, cg.publisher)`.
    - `component_xml_preview(request, pk)` — GET, FBV, analogno `xml_preview` za ComponentGroup. Permission: `has_publisher_access(request.user, cg.publisher)`.
    - `component_xml_download(request, pk)` — GET, FBV, kreira CrossrefExport sa `export_type=COMPONENT_GROUP`, `component_group=cg`, `issue=None`. Permission: `has_publisher_access(request.user, cg.publisher)`.
    - `component_download_warning(request, pk)` — GET, warning modal. Permission check.
    - `component_xml_download_force(request, pk)` — GET, force download. Permission check.
    - `component_export_redownload(request, pk)` — GET, redownload iz CrossrefExport. Permission: via `export.component_group.publisher`.
    - `component_export_history(request, pk)` — GET, historija exporta za ComponentGroup. Filtrira `CrossrefExport.objects.filter(component_group=cg)`.
    - `ComponentGroupDepositView(LoginRequiredMixin, View)` — GET, 5-step deposit stranica (analog `CrossrefDepositView`). Permission check.
    - `component_mark_deposited(request, pk)` — POST, označava kao deponovano na ComponentGroup. Permission check.
  - File: `doi_portal/doi_portal/crossref/urls.py` (MODIFY)
  - Action: Dodati URL patterns za component workflow:
    - `"component-groups/<int:pk>/validate/"` → ComponentGroupValidationView (`crossref:component-group-validate`)
    - `"component-groups/<int:pk>/generate/"` → GenerateComponentXMLView (`crossref:component-group-generate`)
    - - `"component-groups/<int:pk>/preview/"` → component_xml_preview (`crossref:component-xml-preview`)
    - `"component-groups/<int:pk>/download/"` → component_xml_download (`crossref:component-xml-download`)
    - `"component-groups/<int:pk>/download-warning/"` → component_download_warning (`crossref:component-download-warning`)
    - `"component-groups/<int:pk>/download-force/"` → component_xml_download_force (`crossref:component-xml-download-force`)
    - `"component-groups/<int:pk>/export-history/"` → component_export_history (`crossref:component-export-history`)
    - `"component-groups/<int:pk>/deposit/"` → ComponentGroupDepositView (`crossref:component-group-deposit`)
    - `"component-groups/<int:pk>/mark-deposited/"` → component_mark_deposited (`crossref:component-mark-deposited`)
    - `"component-exports/<int:pk>/redownload/"` → component_export_redownload (`crossref:component-export-redownload`)

#### Faza 8: HTML templates

- [ ] Task 18: Kreirati HTML templates za Component CRUD
  - **VAŽNO**: Template directory je `templates/component_groups/` (NE `templates/components/` — taj folder sadrži reusable UI komponente: `_sidebar_menu.html`, `_breadcrumbs.html`, `_pagination.html`, `_user_dropdown.html`).
  - File: `doi_portal/doi_portal/templates/component_groups/component_group_list.html` (NEW) — lista grupa sa parent_doi, title, component_count, kreiran datum, linkovi ka detail/deposit
  - File: `doi_portal/doi_portal/templates/component_groups/component_group_detail.html` (NEW) — detalji grupe sa listom component-a, HTMX contributor management
  - File: `doi_portal/doi_portal/templates/component_groups/component_group_form.html` (NEW) — create/edit forma za ComponentGroup
  - File: `doi_portal/doi_portal/templates/component_groups/component_form.html` (NEW) — create/edit forma za Component
  - File: `doi_portal/doi_portal/templates/component_groups/component_detail.html` (NEW) — detalji component-a sa contributor listom
  - File: `doi_portal/doi_portal/templates/component_groups/partials/_component_row.html` (NEW) — HTMX partial za component red u listi
  - File: `doi_portal/doi_portal/templates/component_groups/partials/_contributor_row.html` (NEW) — HTMX partial za contributor red
  - File: `doi_portal/doi_portal/templates/component_groups/partials/_contributor_form.html` (NEW) — inline contributor forma
  - Action: Svi templates extend `admin_base.html`, koriste Bootstrap 5, srpske labele, HTMX za inline operacije.

- [ ] Task 19: Kreirati HTML templates za Component Crossref workflow
  - File: `doi_portal/doi_portal/templates/crossref/component_crossref_deposit.html` (NEW) — 5-step deposit stranica, analog `issue_crossref_deposit.html` ali za ComponentGroup
  - File: `doi_portal/doi_portal/templates/crossref/partials/_component_validation_panel.html` (NEW) — analog `_validation_panel.html`
  - File: `doi_portal/doi_portal/templates/crossref/partials/_component_generation_result.html` (NEW) — analog `_generation_result.html`
  - File: `doi_portal/doi_portal/templates/crossref/partials/_component_export_history.html` (NEW) — analog `_export_history.html`
  - File: `doi_portal/doi_portal/templates/crossref/partials/_component_deposit_status.html` (NEW) — analog `_deposit_status.html`
  - Action: Kopirati strukturu iz Issue workflow templates, zameniti Issue reference sa ComponentGroup. Link ka XML preview modal — reuse `_xml_preview_modal.html` (isti modal radi za oba tipa XML-a). Link ka download warning modal — reuse `_download_warning_modal.html`.

- [ ] Task 20: Dodati "Komponente" stavku u sidebar menu
  - File: `doi_portal/doi_portal/core/menu.py` (MODIFY)
  - Action: Dodati novu stavku u `MENU_ITEMS` dict, POSLE "articles" stavke:
    ```python
    "component_groups": {
        "label": "Komponente",
        "icon": "bi-puzzle",
        "url_name": "components:group-list",
        "roles": ["Superadmin", "Administrator", "Urednik", "Bibliotekar"],
    },
    ```
  - Notes: Stavka koristi isti role set kao articles. Sidebar rendering je automatski — `{% render_sidebar_menu %}` tag u `admin_base.html` poziva `get_menu_for_user()` koji čita iz `MENU_ITEMS`.

#### Faza 9: Portal (javni prikaz)

- [ ] Task 21: Kreirati portal view za Component landing page
  - File: `doi_portal/doi_portal/portal/views.py` (MODIFY)
  - Action: Dodati `ComponentLandingView(DetailView)` — javna stranica za Component:
    - Model: Component, queryset filtrira po `is_deleted=False`
    - Template: `portal/component_landing.html`
    - Kontekst: component, full_doi, doi_url, parent_doi, publisher, share_url
  - Notes: Nema status provere kao Article (Component nema workflow statuse).

- [ ] Task 22: Kreirati portal URL i template za Component
  - File: `doi_portal/doi_portal/portal/urls_components.py` (NEW)
  - Action: `app_name = "portal-components"`, pattern: `"<int:pk>/"` → ComponentLandingView (`portal-components:component-detail`)
  - File: `doi_portal/config/urls.py` (MODIFY)
  - Action: Dodati `path("components/", include("doi_portal.portal.urls_components", namespace="portal-components"))`
  - File: `doi_portal/doi_portal/templates/portal/component_landing.html` (NEW)
  - Action: Kreirati landing page sa: title, description, contributors, MIME type badge, DOI link, parent DOI link, publisher info.

#### Faza 10: Testovi

- [ ] Task 23: Kreirati Factory Boy factories za Component app
  - File: `doi_portal/doi_portal/components/tests/__init__.py` (NEW)
  - File: `doi_portal/doi_portal/components/tests/factories.py` (NEW)
  - Action: Kreirati:
    - `ComponentGroupFactory(factory.django.DjangoModelFactory)` — Meta.model = ComponentGroup, publisher = factory.SubFactory(PublisherFactory), parent_doi = factory.Sequence(lambda n: f"10.12345/test.{n}"), title = factory.Faker("sentence")
    - `ComponentFactory(factory.django.DjangoModelFactory)` — Meta.model = Component, component_group = factory.SubFactory(ComponentGroupFactory), doi_suffix = factory.Sequence(lambda n: f"comp.{n}"), title = factory.Faker("sentence"), format_mime_type = "audio/mpeg"
    - `ComponentContributorFactory(factory.django.DjangoModelFactory)` — Meta.model = ComponentContributor, component = factory.SubFactory(ComponentFactory), given_name = factory.Faker("first_name"), surname = factory.Faker("last_name"), sequence = "first", contributor_role = "author"

- [ ] Task 24: Kreirati model testove
  - File: `doi_portal/doi_portal/components/tests/test_models.py` (NEW)
  - Action: Testirati:
    - ComponentGroup kreiranje, __str__, component_count, unique constraint (parent_doi per publisher), soft delete
    - Component kreiranje, __str__, full_doi property, unique constraint (doi_suffix per group), soft delete
    - ComponentContributor kreiranje, ordering, soft delete, ORCID validacija

- [ ] Task 25: Kreirati service testove za component XML generisanje
  - File: `doi_portal/doi_portal/crossref/tests/test_component_services.py` (NEW)
  - Action: Testirati:
    - `CrossrefService.generate_component_xml(cg)` — generiše validan XML sa ispravnom strukturom
    - `CrossrefService.generate_and_store_component_xml(cg)` — čuva XML i XSD rezultat na ComponentGroup
    - `PreValidationService.validate_component_group(cg)` — testirati sve validacione scenarije:
      - Prazan parent_doi → ERROR
      - Nema component-a → ERROR
      - Component bez doi_suffix → ERROR
      - Component bez title → WARNING
      - Nevažeći MIME type → WARNING
      - Parent DOI ne postoji u sistemu → WARNING
      - Valid scenario → is_valid=True
    - XSD validacija generisanog XML-a (integration test sa lxml)
    - Test sa publication_year/month/day → XML sadrži `<publication_date>` sa ispravnim sub-elementima
    - Test sa samo publication_year (bez month/day) → XML sadrži samo `<year>`

- [ ] Task 26: Kreirati view testove
  - File: `doi_portal/doi_portal/components/tests/test_views.py` (NEW)
  - Action: Testirati:
    - CRUD views: list, create, detail, update, delete za ComponentGroup i Component
    - Permission checks: unauthenticated → redirect, wrong publisher → 403
    - Contributor HTMX endpoints: add, update, delete, reorder
  - File: `doi_portal/doi_portal/crossref/tests/test_component_workflow.py` (NEW)
  - Action: Testirati:
    - Validation view: returns correct partial, errors/warnings
    - Generate view: sync generation, returns result partial
    - Preview view: returns XML content
    - Download view: creates CrossrefExport with export_type=COMPONENT_GROUP, issue=None
    - Deposit view: renders 5-step page
    - Mark deposited: sets crossref_deposited_at
    - `export_redownload` sa component_group export — permission check radi bez `export.issue`

- [ ] Task 27: Kreirati portal testove
  - File: `doi_portal/doi_portal/portal/tests/test_component_portal.py` (NEW)
  - Action: Testirati:
    - ComponentLandingView: pristup, kontekst (full_doi, parent_doi), template
    - Nepostojeći component → 404
    - Soft-deleted component → 404

### Acceptance Criteria

#### Model layer
- [ ] AC 1: Given a Publisher, when creating a ComponentGroup with parent_doi and title, then the ComponentGroup is persisted with correct FK to Publisher and timestamps are set.
- [ ] AC 2: Given a ComponentGroup, when creating a Component with doi_suffix and title, then full_doi property returns "{publisher.doi_prefix}/{doi_suffix}".
- [ ] AC 3: Given a ComponentGroup with parent_doi "10.12345/test", when creating another ComponentGroup with same parent_doi for same publisher, then UniqueConstraint raises IntegrityError.
- [ ] AC 4: Given a Component, when soft_delete() is called, then is_deleted=True and component is excluded from default queryset but accessible via all_objects.

#### XML generation
- [ ] AC 5: Given a ComponentGroup with 3 Components (one with contributors, one with description, one minimal), when generate_component_xml() is called, then output XML contains `<sa_component parent_doi="...">` with `<component_list>` containing 3 `<component>` elements in correct order, with element ordering: titles → contributors → publication_date → description → format → doi_data.
- [ ] AC 6: Given generated component XML, when validated against Crossref XSD 5.4.0, then validation passes (xsd_valid=True).
- [ ] AC 7: Given a Component with format_mime_type="audio/mpeg", when XML is generated, then output contains `<format mime_type="audio/mpeg"/>`.
- [ ] AC 8: Given a Component with ORCID on contributor, when XML is generated, then output contains `<ORCID>https://orcid.org/XXXX-XXXX-XXXX-XXXX</ORCID>`.
- [ ] AC 9: Given a Component without explicit resource_url, when XML is generated, then `<resource>` element contains auto-generated URL `{site_url}/components/{pk}/`.
- [ ] AC 22: Given a Component with publication_year=2026, publication_month=3, publication_day=None, when XML is generated, then output contains `<publication_date><month>03</month><year>2026</year></publication_date>` (no `<day>` element).
- [ ] AC 23: Given a Component with description containing "&" character, when XML is generated, then output contains `&amp;` (single escape, not double `&amp;amp;`).

#### Pre-validation
- [ ] AC 10: Given a ComponentGroup with empty parent_doi, when validate_component_group() is called, then result contains ERROR "Parent DOI je obavezan".
- [ ] AC 11: Given a ComponentGroup with no Components, when validate_component_group() is called, then result contains ERROR "Grupa mora sadržati bar jednu komponentu".
- [ ] AC 12: Given a Component with empty doi_suffix, when validated, then result contains ERROR "DOI sufiks je obavezan".
- [ ] AC 13: Given a ComponentGroup whose parent_doi matches no Article/Issue DOI in the system, when validated, then result contains WARNING (not error) about unrecognized parent DOI.

#### CrossrefExport
- [ ] AC 14: Given a ComponentGroup with valid XML, when download is triggered, then CrossrefExport record is created with export_type="COMPONENT_GROUP", component_group FK set, issue FK null, and XML snapshot stored. DB CHECK constraint is satisfied.
- [ ] AC 15: Given CrossrefExport records for both Issue and ComponentGroup, when querying export history, then records are correctly filtered by type.
- [ ] AC 24: Given a CrossrefExport with component_group (no issue), when accessing export_redownload view, then permission check succeeds via component_group.publisher and file is served.

#### Admin UI workflow
- [ ] AC 16: Given an authenticated user with publisher access, when navigating to /dashboard/components/, then ComponentGroup list is displayed showing only groups for accessible publishers.
- [ ] AC 17: Given a ComponentGroup detail page, when user adds a Component via form, then Component appears in the list and can have contributors added via HTMX inline forms.
- [ ] AC 18: Given a ComponentGroup with valid components, when navigating to deposit page, then 5-step stepper is displayed with correct state for each step (validation, generation, XSD, preview, download).
- [ ] AC 19: Given a ComponentGroup with generated and XSD-valid XML, when user clicks "Označi kao deponovano", then crossref_deposited_at is set and deposit status updates via HTMX.
- [ ] AC 25: Given the admin sidebar, when user is authenticated, then "Komponente" menu item is visible with bi-puzzle icon and links to components:group-list.

#### Portal
- [ ] AC 20: Given a Component with pk=42, when accessing /components/42/, then landing page displays title, description, DOI, parent DOI, contributors, and MIME type.
- [ ] AC 21: Given a soft-deleted Component, when accessing its landing page URL, then 404 is returned.

## Additional Context

### Dependencies

- Nema novih Python dependency-ja — sve se radi sa postojećim stack-om (Django, Jinja2, lxml, Celery)
- `SoftDeleteMixin`, `SoftDeleteManager` iz `doi_portal.core.mixins`
- `validate_orcid` iz `doi_portal.articles.validators` (reuse za ComponentContributor)
- `AuthorSequence`, `ContributorRole` iz `doi_portal.articles.models` (reuse za ComponentContributor choices)
- `CrossrefService`, `PreValidationService` iz `doi_portal.crossref.services`
- `ValidationResult` iz `doi_portal.crossref.validation`
- `validate_xml` iz `doi_portal.crossref.validators` (za XSD validaciju)
- `SiteSettings` iz `doi_portal.core.models` (za depositor info)
- `PublisherScopedMixin`, `PublisherScopedEditMixin` iz `doi_portal.publishers.mixins` (NE `core.mixins`)
- `has_publisher_access` iz `doi_portal.core.permissions` (NE `crossref.views`)
- `AdministratorRequiredMixin` iz `doi_portal.publishers.mixins` ili `doi_portal.core.mixins` (proveriti tačnu lokaciju)
- Factory Boy factories iz postojećih app-ova za test fixture chaining (`PublisherFactory` iz `doi_portal.publications.tests.factories`, `UserFactory` iz `doi_portal.users.tests.factories`)

### Testing Strategy

**Unit testovi:**
- Model testovi: constraints, properties, soft delete, __str__
- Form testovi: validacija, required fields, MIME type choices
- Service testovi: PreValidationService za component validaciju (svi error/warning scenariji)

**Integration testovi:**
- XML generisanje + XSD validacija: end-to-end test koji kreira ComponentGroup sa Component-ima, generiše XML, i validira ga protiv Crossref XSD 5.4.0
- Autoescape test: generisati XML sa `&` u description i contributor imenima — proveriti single escape (ne double)
- Publication date test: parcijalni datumi (samo year, year+month, full date)
- View testovi: CRUD operacije, permission checks, HTMX partial responses
- Crossref workflow: validation → generation → preview → download → deposit celokupni tok
- CrossrefExport: kreiranje export zapisa sa ispravnim export_type, DB CHECK constraint
- export_redownload: testirati sa component_group export (nullable issue)

**Manual testing:**
- Proveriti generisani XML vizuelno u preview modal-u
- Testirati XML upload na Crossref test endpoint (ako je dostupan)
- Proveriti sidebar navigaciju ("Komponente" stavka) i breadcrumbs
- Testirati contributor drag-drop reorder
- Proveriti portal landing page sa svim varijantama (sa/bez title, description, contributors, MIME type)

### Notes

- **Referentni XML primer** (`zanos-margine-component_20260320.xml`): `<sa_component parent_doi="10.66117/emce_zapisi.2026.1">` sa jednim `<component parent_relation="isPartOf">` koji ima titles, contributors, description, format (audio/mpeg), doi_data
- **Element ordering u component po XSD**: titles → contributors → publication_date → description → format → doi_data
- **Crossref XSD 5.4.0 constraint**: `<body>` koristi `xs:choice` — `<sa_component>` ne može biti u istom XML-u sa `<conference>`, `<journal>`, `<book>`
- **ComponentGroup** je naš interni koncept (ne postoji u Crossref XSD-u) — mehanizam za grupisanje component-a po parent_doi radi batch obrade i praćenja XML/deposit statusa (analog Issue-u za Article-e)
- **Rizik — XSD validacija**: sa_component template treba testirati protiv XSD 5.4.0 rano u razvoju. Preporučujem da Task 9 (template) i Task 25 (XSD test) budu prioritet u implementaciji.
- **Rizik — Namespace deklaracije**: sa_component XML koristi samo osnovni Crossref namespace (bez JATS, ai, fr). Proveriti da XSD validacija prolazi bez ovih namespace-ova.
- **Rizik — Autoescape double-escaping**: Proveriti da postojeći templates (`conference_paper.xml.j2`, `journal_article.xml.j2`) nemaju isti bug sa `| xml_escape` na text content uz uključen autoescape. Ako imaju, razmotriti globalni fix u zasebnom task-u.
- **Buduće razmatranje**: Ako se pojavi potreba za component-ima koji imaju abstract (JATS), licence info (ai:program), ili funding (fr:program), template i model bi trebalo proširiti. Za sada ovo nije u scope-u jer referentni XML nema ove elemente.
- **Filename generisanje**: Za component XML download, filename format: `component_{parent_doi_slugified}_{YYYYMMDD_HHMMSS}.xml` (analog Issue pattern-u).
- **Template directory napomena**: `templates/components/` sadrži reusable UI partials (`_sidebar_menu.html`, `_breadcrumbs.html`, `_pagination.html`, `_user_dropdown.html`). Nova app koristi `templates/component_groups/` za svoje template-ove da izbegne koliziju.
