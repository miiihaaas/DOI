---
title: 'Conference Registration Wizard'
slug: 'conference-registration-wizard'
created: '2026-03-20'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Django 5.x', 'HTMX 2.0.8', 'Alpine.js 3.15.3', 'Bootstrap 5.3', 'PostgreSQL']
files_to_modify:
  # New wizard app
  - 'doi_portal/doi_portal/wizard/__init__.py'
  - 'doi_portal/doi_portal/wizard/apps.py'
  - 'doi_portal/doi_portal/wizard/views.py'
  - 'doi_portal/doi_portal/wizard/forms.py'
  - 'doi_portal/doi_portal/wizard/urls.py'
  - 'doi_portal/doi_portal/wizard/tests/__init__.py'
  - 'doi_portal/doi_portal/wizard/tests/test_views.py'
  # Templates (new)
  - 'doi_portal/doi_portal/templates/wizard/conference_wizard.html'
  - 'doi_portal/doi_portal/templates/wizard/partials/_step_1_conference.html'
  - 'doi_portal/doi_portal/templates/wizard/partials/_step_2_proceedings.html'
  - 'doi_portal/doi_portal/templates/wizard/partials/_step_3_papers.html'
  - 'doi_portal/doi_portal/templates/wizard/partials/_step_4_review.html'
  - 'doi_portal/doi_portal/templates/wizard/partials/_paper_form.html'
  - 'doi_portal/doi_portal/templates/wizard/partials/_paper_item.html'
  - 'doi_portal/doi_portal/templates/wizard/partials/_paper_list.html'
  - 'doi_portal/doi_portal/templates/wizard/partials/_wizard_author_list.html'
  - 'doi_portal/doi_portal/templates/wizard/partials/_wizard_author_form.html'
  # Existing files to modify
  - 'doi_portal/doi_portal/core/views.py'
  - 'doi_portal/config/urls.py'
  - 'doi_portal/config/settings/base.py'
  - 'doi_portal/doi_portal/templates/publications/publication_list.html'
  - 'doi_portal/doi_portal/static/css/admin.css'
code_patterns:
  - 'Django CBV with LoginRequiredMixin + PublisherScopedMixin'
  - 'HTMX partials with _ prefix for step content swapping'
  - 'Alpine.js x-data for stepper state management'
  - 'Database-first: Issue/Article objects created with DRAFT status (Publication has no status field)'
  - 'Wizard-specific author partials with per-article unique DOM IDs'
  - 'Crossref stepper CSS pattern from issue_crossref_deposit.html'
  - 'Article status transition DRAFT→PUBLISHED in step 4 before XML generation'
test_patterns:
  - 'pytest-django with @pytest.mark.django_db'
  - 'factory_boy: PublicationFactory, IssueFactory, ArticleFactory'
  - 'client.force_login(user) + reverse("namespace:name", args=[pk])'
  - 'Test classes per feature: TestWizardStep1, TestWizardStep2, etc.'
---

# Tech-Spec: Conference Registration Wizard

**Created:** 2026-03-20

## Overview

### Problem Statement

Registracija konferencije zahteva 4 odvojena koraka kroz različite sekcije aplikacije (Publication → Issue → Article × N → Authors). Korisnik mora sam da zna redosled, navigira između sekcija, i razume mapiranje "Izdanje"→"Zbornik radova", "Članak"→"Rad". Posebno problematično za korisnike koji registruju konferenciju prvi put.

### Solution

Multi-step wizard koji vodi korisnika kroz kompletan flow: Konferencija → Zbornik → Radovi → Pregled/XML. Database-first pristup (Issue/Article objekti se kreiraju sa DRAFT statusom; Publication nema status polje — kreira se odmah). Custom HTMX multi-step. Wizard-specific author partials sa per-article unique DOM IDs za korak 3. Integracija sa PreValidationService (sa wizard-specific validacijom za DRAFT artikle) i CrossrefService.

### Scope

**In Scope:**
- Wizard entry point (dugme na dashboard-u i publication listi)
- 4 koraka: Konferencija (Publication), Zbornik (Issue), Radovi (Articles), Pregled+XML
- Database-first pristup (Issue/Article sa DRAFT statusom)
- Full page load per step sa stepper header-om
- Wizard-specific author/affiliation partials (NE reuse existing partials — nove partials sa unique DOM IDs)
- Reuse existing author/affiliation backend endpoint-ova (articles:author-add, itd.)
- Vizuelni progress stepper sa navigacijom nazad
- Wizard-specific validacija (uključuje DRAFT artikle, ne samo PUBLISHED)
- Article status transition DRAFT → PUBLISHED pre XML generisanja
- Samo CONFERENCE tip (sa extension point-ima)
- Zavisnost od Spec 3 terminologije (`{% load terminology %}`)

**Out of Scope:**
- CSV import radova
- Wizard za BOOK/JOURNAL tipove
- Deposit na Crossref (korak 4 linkuje na postojeći deposit workflow)
- PDF upload u wizard kontekstu
- Cleanup stale wizard objekata (orphan Publications bez Issue-a)

## Context for Development

### Codebase Patterns

- **App struktura:** `doi_portal.<app_name>` pattern. LOCAL_APPS u `config/settings/base.py` (linije 45-55).
- **URL konvencija:** `dashboard/<resource>/` sa namespace-om. Main urls.py (linije 16-52).
- **Views:** Django CBV sa `LoginRequiredMixin`. Publisher scoping kroz `PublisherScopedMixin`.
- **Forme:** `__init__(self, *args, user=None, **kwargs)` — user za queryset scoping.
- **HTMX partials:** `_` prefix konvencija. Views vraćaju HTML partial.
- **Stepper UI:** Crossref deposit koristi CSS stepper sa `step-completed`/`step-active`/`step-disabled` u `issue_crossref_deposit.html` (linije 12-61).
- **Dashboard quick actions:** `DashboardView._get_quick_actions(flags)` u `core/views.py` (linije 119-150+). **VAŽNO:** Koristi if/elif/elif po roli — tri odvojene grane (admin, urednik, bibliotekar) grade različite liste. Nova akcija mora biti dodata u SVE tri grane.
- **Author HTMX partials — DOM IDs:** `_author_form.html` ima hardkodiran `hx-target="#authors-section-content"` i `#author-form-container`. Ovi ID-ovi postoje samo u `article_form.html`. **NIJE MOGUĆE** reuse-ovati ove partials u wizard-u gde je više radova na jednoj stranici jer bi DOM IDs kolidirali. Wizard mora da ima SOPSTVENE author partials sa per-article unique IDs.
- **PreValidationService:** `validate_issue()` (linije 499-538) filtrira artikle sa `status=ArticleStatus.PUBLISHED, is_deleted=False`. DRAFT artikli su preskočeni. Wizard mora da koristi custom validaciju ili da transitira artikle u PUBLISHED pre validacije.
- **Publication model:** **NEMA status polje.** Samo Issue i Article imaju status (sa DRAFT default). Publication se kreira odmah i ne može se razlikovati od standardno-kreiranih.
- **Publication.title:** Required CharField. `Publication.save()` auto-generiše slug iz title-a. Za Ćirilicu, fallback koristi `f"publication-{self.pk}"` — ali pri prvom save() pk je None, pa generiše `"publication-"`. Workaround: super().save() prvo, pa onda slug generation.
- **IssueForm.clean():** Validira DOI suffix format (linije 256-268) i unique constraint (linije 226-254). WizardProceedingsForm mora da replicira DOI suffix validaciju.
- **Test pattern:** pytest + factory_boy. `@pytest.mark.django_db`. Test fajlovi u `<app>/tests/test_views.py`.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `publications/forms.py` | PublicationForm — CONFERENCE fields (linije 303-341) |
| `publications/models.py` | Publication.save() — slug auto-generation |
| `issues/forms.py` | IssueForm — proceedings fields, DOI suffix validation (linije 256-268) |
| `articles/forms.py` | ArticleForm — fields/widgets reference |
| `articles/views.py` | Author HTMX CRUD (linije 490-643), permission check (linije 81-97) |
| `articles/partials/_author_form.html` | Hardkodirani `hx-target="#authors-section-content"` — NE reuse-ovati |
| `articles/partials/_author_list.html` | Hardkodirani DOM IDs — NE reuse-ovati |
| `crossref/views.py` | CrossrefDepositView (linije 454-559) — stepper pattern |
| `crossref/services.py` | PreValidationService.validate_issue() (linije 499-538) — filtrira PUBLISHED only |
| `crossref/issue_crossref_deposit.html` | Stepper CSS (linije 12-61) |
| `crossref/partials/_validation_panel.html` | Validation results display |
| `core/views.py` | DashboardView._get_quick_actions() (linije 119-150+) — if/elif/elif po roli |
| `templates/dashboard/dashboard.html` | Quick actions sekcija (linije 48-67) |
| `templates/publications/publication_list.html` | "Nova publikacija" dugme (linije 6-14) |
| `config/urls.py` | URL namespace pattern |
| `config/settings/base.py` | LOCAL_APPS lista |

### Technical Decisions

- **Nova app `wizard/`:** Zasebna app bez modela. Registruje se kao `"doi_portal.wizard"` u LOCAL_APPS.
- **Database-first sa ispravkama:** Issue i Article se kreiraju sa DRAFT statusom. **Publication NEMA status polje** — kreira se odmah kao regularna publikacija. Orphan Publications (bez Issue-a) nastaju ako korisnik napusti wizard na koraku 1 — identifikuju se po tome što nemaju Issue-a (ne po statusu).
- **Merged start + step-1:** `wizard_start` view handluje i GET (prazan form) i POST (kreiranje Publication + redirect na step-2). Nema posebnog step-1 URL-a za create mode. `wizard_step_1` se koristi SAMO za edit mode (back navigation sa step 2+). Ovo sprečava orphan-e od double-click-a.
- **URL struktura:** `/dashboard/wizard/conference/` (start/create) → `/dashboard/wizard/conference/<pub_pk>/step-1/` (edit) → `...step-2/` → `...step-3/` → `...step-4/`.
- **Full page load per step:** Svaki korak je full page load, ne HTMX swap. Browser back radi, bookmarkable.
- **Publication.title auto-populate:** `WizardConferenceForm` NE prikazuje `title` polje korisniku. Umesto toga, `save()` automatski setuje `title = conference_name`. Ovo eliminiše zbunjujuću duplikaciju "Naslov" vs "Naziv konferencije".
- **Wizard-specific author partials (F1 fix):** NE koriste se existing `_author_list.html` i `_author_form.html` jer imaju hardkodirane DOM IDs (`#authors-section-content`, `#author-form-container`) koji bi kolidirali kad je više radova na jednoj stranici. Umesto toga, kreirati:
  - `wizard/partials/_wizard_author_list.html` — isti sadržaj ali sa per-article unique IDs: `#wizard-authors-{{ article.pk }}`, `#wizard-author-form-{{ article.pk }}`
  - `wizard/partials/_wizard_author_form.html` — isti sadržaj ali sa `hx-target="#wizard-authors-{{ article.pk }}"`
  - Backend endpoint-i (`articles:author-add`, itd.) ostaju ISTI — samo se menja HTMX response partial. View endpoint-i već vraćaju generic context, a template je odvojen.
  - **PROBLEM:** Existing author endpoint-i hardkodiraju template path `articles/partials/_author_list.html` u return statement-u. Rešenje: dodati wizard-specific author endpoint-e u `wizard/urls.py` koji wrappuju existing logiku ali vraćaju wizard-specific partials. ILI: modifikovati existing endpoints da prihvataju `?template=wizard` query param. Preporučen pristup: **wrapper endpoint-i u wizard app-u.**
- **WizardProceedingsForm — DOI suffix validacija (F4 fix):** Dodati `clean_doi_suffix()` metod koji replicira validaciju iz `IssueForm.clean()` (linije 256-268): no leading `/`, no spaces, valid characters.
- **Wizard-specific validacija za DRAFT artikle (F2 fix):** PreValidationService.validate_issue() preskače DRAFT artikle. Rešenje u dva koraka:
  1. **Korak 4 validacija:** Kreirati `wizard_validate_issue(issue)` helper u `wizard/views.py` koji poziva `PreValidationService` metode ALI sa queryset-om koji uključuje DRAFT artikle (`issue.articles.filter(is_deleted=False)` bez `status=PUBLISHED` filtera). Ovo zahteva da se individual `_validate_article()` i `_validate_author()` metode pozivaju direktno (one su public na klasi).
  2. **Pre XML generisanja:** U `wizard_generate_xml` view-u, **transitionirati sve DRAFT artikle u PUBLISHED** pre poziva `CrossrefService().generate_and_store_xml(issue)`. Ovo osigurava da standardni XML generation pipeline radi ispravno.
- **Quick actions — sve tri grane (F5 fix):** Wizard akcija mora da se doda u SVE TRI grane `_get_quick_actions()`: `if flags["is_admin"]:`, `elif flags["is_urednik"]:`, `elif flags["is_bibliotekar"]:`.
- **Prefill logika u koraku 2:** `proceedings_title` ← `conference_name`, `proceedings_publisher_name` ← `publisher.name`, `year` ← `conference_date.year`.
- **Spec 3 terminologija:** Fallback na hardkodirane "Konferencija", "Zbornik", "Rad" ako Spec 3 nije implementiran.

## Implementation Plan

### Tasks

- [ ] **Task 1: Scaffold wizard app**
  - File: `doi_portal/doi_portal/wizard/__init__.py` (NOVI, prazan)
  - File: `doi_portal/doi_portal/wizard/apps.py` (NOVI)
  - Action: Kreirati Django app:
    ```python
    from django.apps import AppConfig
    class WizardConfig(AppConfig):
        default_auto_field = "django.db.models.BigAutoField"
        name = "doi_portal.wizard"
        verbose_name = "Wizard"
    ```
  - File: `doi_portal/doi_portal/wizard/tests/__init__.py` (NOVI, prazan)
  - File: `doi_portal/config/settings/base.py` — dodati `"doi_portal.wizard"` u LOCAL_APPS.
  - File: `doi_portal/config/urls.py` — dodati:
    ```python
    path("dashboard/wizard/", include("doi_portal.wizard.urls", namespace="wizard")),
    ```

- [ ] **Task 2: Kreiranje wizard formi**
  - File: `doi_portal/doi_portal/wizard/forms.py` (NOVI)
  - Action: Kreirati 3 forme:

  **WizardConferenceForm:**
  - `Meta.model = Publication`
  - `Meta.fields = ["publisher", "conference_name", "conference_acronym", "conference_number", "conference_location", "conference_date", "conference_date_end", "language"]`
  - **NE uključuje `title`** — auto-populate u `save()`
  - `__init__(self, *args, user=None, **kwargs)`: Publisher scoping. Urednik/Bibliotekar → `publisher` field je HiddenInput sa `initial=user.publisher.pk`. Admin/Superadmin → publisher dropdown.
  - `save(commit=True)`: Setuje `instance.publication_type = PublicationType.CONFERENCE` i `instance.title = instance.conference_name` pre save-a.
  - Widgets: reuse attrs iz PublicationForm (TextInput, DateInput, NumberInput, Select)

  **WizardProceedingsForm:**
  - `Meta.model = Issue`
  - `Meta.fields = ["proceedings_title", "proceedings_publisher_name", "proceedings_publisher_place", "year", "isbn_print", "isbn_online", "doi_suffix"]`
  - `__init__(self, *args, publication=None, **kwargs)`: Prefill logika (proceedings_title ← conference_name, itd.)
  - `clean_doi_suffix(self)`: Replicira validaciju iz IssueForm — nema vodećeg `/`, nema razmaka. Implementacija:
    ```python
    def clean_doi_suffix(self):
        value = self.cleaned_data.get("doi_suffix", "").strip()
        if not value:
            return value
        if value.startswith("/"):
            raise ValidationError("DOI sufiks ne sme počinjati sa '/'.")
        if " " in value:
            raise ValidationError("DOI sufiks ne sme sadržati razmake.")
        return value
    ```
  - `save(commit=True)`: Setuje `instance.publication = self._publication`.

  **WizardPaperForm:**
  - `Meta.model = Article`
  - `Meta.fields = ["title", "subtitle", "abstract", "doi_suffix", "first_page", "last_page", "language", "license_url", "free_to_read"]`
  - `__init__(self, *args, issue=None, user=None, **kwargs)`: Čuva issue i user za save.
  - `save(commit=True)`: Setuje `instance.issue = self._issue`, `instance.created_by = self._user` (samo pri kreiranju).

- [ ] **Task 3: Kreiranje wizard URL-ova**
  - File: `doi_portal/doi_portal/wizard/urls.py` (NOVI)
  - Action:
    ```python
    app_name = "wizard"
    urlpatterns = [
        # Start wizard (GET=empty form, POST=create Publication + redirect)
        path("conference/", views.wizard_start, name="conference-start"),
        # Step 1: Edit conference (back navigation only)
        path("conference/<int:pub_pk>/step-1/", views.wizard_step_1, name="conference-step-1"),
        # Step 2: Proceedings
        path("conference/<int:pub_pk>/step-2/", views.wizard_step_2, name="conference-step-2"),
        # Step 3: Papers
        path("conference/<int:pub_pk>/step-3/", views.wizard_step_3, name="conference-step-3"),
        # Step 3 HTMX: Paper CRUD
        path("conference/<int:pub_pk>/papers/add/", views.wizard_paper_add, name="paper-add"),
        path("conference/<int:pub_pk>/papers/<int:article_pk>/edit/", views.wizard_paper_edit, name="paper-edit"),
        path("conference/<int:pub_pk>/papers/<int:article_pk>/delete/", views.wizard_paper_delete, name="paper-delete"),
        # Step 3 HTMX: Wizard author CRUD (wrapper endpoints)
        path("papers/<int:article_pk>/authors/", views.wizard_author_list, name="author-list"),
        path("papers/<int:article_pk>/authors/form/", views.wizard_author_form, name="author-form"),
        path("papers/<int:article_pk>/authors/add/", views.wizard_author_add, name="author-add"),
        path("authors/<int:pk>/edit-form/", views.wizard_author_edit_form, name="author-edit-form"),
        path("authors/<int:pk>/update/", views.wizard_author_update, name="author-update"),
        path("authors/<int:pk>/delete/", views.wizard_author_delete, name="author-delete"),
        # Step 4: Review & XML
        path("conference/<int:pub_pk>/step-4/", views.wizard_step_4, name="conference-step-4"),
        path("conference/<int:pub_pk>/generate-xml/", views.wizard_generate_xml, name="generate-xml"),
    ]
    ```

- [ ] **Task 4: Kreiranje wizard views — korak 1 (Konferencija)**
  - File: `doi_portal/doi_portal/wizard/views.py` (NOVI)
  - Action:

  **wizard_start (GET/POST):**
  - `@login_required`
  - GET: Renderuje prazan WizardConferenceForm u `wizard/conference_wizard.html` (step=1).
  - POST: Validira formu. Ako valid → `form.save()` kreira Publication → **redirect na step-2** (ne step-1). Ako invalid → renderuje sa greškama.
  - Nema intermediate step-1 URL pri kreiranju — sprečava orphan-e od double-click-a.

  **wizard_step_1 (GET/POST):**
  - Samo za EDIT mode (back navigation sa step 2+).
  - GET: Učitava Publication (`pub_pk`), popunjava WizardConferenceForm. Permission check.
  - POST: Validira, update-uje Publication → redirect na step-2.

  **Permission helper:**
  ```python
  def _check_wizard_permission(user, publication):
      """Check user has access to publication's publisher."""
      if user.is_superuser:
          return
      if user.groups.filter(name__in=["Administrator", "Superadmin"]).exists():
          return
      if hasattr(user, "publisher") and user.publisher == publication.publisher:
          return
      raise PermissionDenied
  ```

- [ ] **Task 5: Kreiranje wizard views — korak 2 (Zbornik)**
  - File: `doi_portal/doi_portal/wizard/views.py` (dopuna)
  - Action:

  **wizard_step_2 (GET/POST):**
  - GET: Učitava Publication, traži Issue za tu publication. Ako postoji → edit mode sa popunjenim podacima. Ako ne → create mode sa prefill (conference_name → proceedings_title, itd.).
  - POST: Validira WizardProceedingsForm. Valid → save Issue → redirect na step-3. Invalid → re-render.
  - Permission check: `_check_wizard_permission(user, publication)`.

- [ ] **Task 6: Kreiranje wizard views — korak 3 (Radovi)**
  - File: `doi_portal/doi_portal/wizard/views.py` (dopuna)
  - Action:

  **wizard_step_3 (GET):**
  - Učitava Publication, Issue, Articles (sa authors prefetch) za taj Issue.
  - Prikazuje listu radova + "Dodaj rad" dugme.

  **wizard_paper_add (GET/POST):**
  - GET: Vraća prazan WizardPaperForm partial.
  - POST: Validira, kreira Article sa `issue=issue`, `created_by=user`, `status=DRAFT`. Vraća ažuriranu `_paper_list.html`.

  **wizard_paper_edit (GET/POST):**
  - GET: Popunjen WizardPaperForm partial.
  - POST: Ažurira Article. Vraća ažuriranu `_paper_list.html`.

  **wizard_paper_delete (POST):**
  - Hard-delete Article (wizard DRAFT-ovi se brišu potpuno, ne soft-delete). Vraća ažuriranu `_paper_list.html`.

- [ ] **Task 7: Wizard author wrapper endpoint-i**
  - File: `doi_portal/doi_portal/wizard/views.py` (dopuna)
  - Action: Kreirati wrapper endpoint-e koji koriste ISTU logiku kao `articles/views.py` author endpoint-i ali vraćaju wizard-specific partials sa per-article unique DOM IDs.

  Pristup: Svaki wrapper poziva odgovarajuću articles view funkciju za business logiku (permission check, save, delete, reorder), ali override-uje template path:
  ```python
  @login_required
  def wizard_author_add(request, article_pk):
      """Wrapper around articles author_add that returns wizard-specific partial."""
      article = get_object_or_404(Article, pk=article_pk)
      _check_article_permission(request.user, article)

      if request.method == "POST":
          form = AuthorForm(request.POST)
          if form.is_valid():
              author = form.save(commit=False)
              author.article = article
              author.order = article.authors.count() + 1
              author.sequence = AuthorSequence.FIRST if author.order == 1 else AuthorSequence.ADDITIONAL
              author.save()
              # Return wizard-specific partial (not articles partial)
              authors = article.authors.prefetch_related("affiliations").all()
              return render(request, "wizard/partials/_wizard_author_list.html", {
                  "article": article, "authors": authors,
              })
          return render(request, "wizard/partials/_wizard_author_form.html", {
              "form": form, "article": article,
          })
      # GET: return empty form
      return render(request, "wizard/partials/_wizard_author_form.html", {
          "form": AuthorForm(), "article": article,
      })
  ```
  - Kreirati wrapper-e za: `wizard_author_list`, `wizard_author_form`, `wizard_author_add`, `wizard_author_edit_form`, `wizard_author_update`, `wizard_author_delete`.
  - Notes: Business logika (validation, ordering, sequence calculation) se kopira iz articles views. Alternativno, refaktorisati articles views da ekstraktuju business logiku u servisne funkcije — ali to je van scope-a ovog spec-a.

- [ ] **Task 8: Wizard-specific validacija i XML generisanje (korak 4)**
  - File: `doi_portal/doi_portal/wizard/views.py` (dopuna)
  - Action:

  **wizard_validate_issue(issue) helper:**
  ```python
  def wizard_validate_issue(issue):
      """
      Validate issue for wizard - includes DRAFT articles (not just PUBLISHED).
      Uses PreValidationService internal methods directly.
      """
      service = PreValidationService()
      result = ValidationResult()

      # Standard validations (depositor, type-specific fields)
      result.merge(service._validate_depositor_settings())
      result.merge(service._validate_conference_fields(issue))
      result.merge(service._validate_issue_doi_suffix(issue))

      # Validate ALL articles (not just PUBLISHED) - this is the key difference
      articles = issue.articles.filter(is_deleted=False)
      if not articles.exists():
          result.add_error(
              message="Nema radova za generisanje XML-a.",
              field_name="articles",
          )
      for article in articles:
          result.merge(service._validate_article(article))

      return result
  ```

  **wizard_step_4 (GET):**
  - Učitava Publication, Issue, Articles sa autorima.
  - Poziva `wizard_validate_issue(issue)` (NE standardni `validate_issue()`).
  - Prikazuje summary + validation results + "Generiši XML" dugme.

  **wizard_generate_xml (POST):**
  - **Korak 1: Transitioniraj DRAFT → PUBLISHED:**
    ```python
    issue.articles.filter(
        status=ArticleStatus.DRAFT, is_deleted=False
    ).update(status=ArticleStatus.PUBLISHED)
    ```
  - **Korak 2:** Pozovi `CrossrefService().generate_and_store_xml(issue)`.
  - **Korak 3:** Redirect na `crossref:issue-deposit` sa issue pk-om.
  - Notes: Transition je ireverzibilna u wizard flow-u. Posle generisanja, korisnik nastavlja u standardnom deposit workflow-u.

- [ ] **Task 9: Kreiranje base wizard template-a**
  - File: `doi_portal/doi_portal/templates/wizard/conference_wizard.html` (NOVI)
  - Action: Template koji extenduje `admin_base.html`:
    - Stepper header sa 4 koraka (ikone: `bi-megaphone`, `bi-journal-text`, `bi-file-earmark-text`, `bi-check-circle`)
    - Step labels: "Konferencija", "Zbornik", "Radovi", "Pregled"
    - Svaki korak je link na odgovarajući URL (disabled za buduće korake, completed za prethodne, active za trenutni)
    - Content area: `{% block wizard_content %}{% endblock %}`
    - Breadcrumbs: "Kontrolna tabla" → "Registracija konferencije" → step label
    - Stepper koristi `current_step` i `max_completed_step` context varijable.

- [ ] **Task 10: Kreiranje step partial template-ova**
  - File: `_step_1_conference.html` (NOVI) — Conference form. Card layout. "Nastavi →" dugme.
  - File: `_step_2_proceedings.html` (NOVI) — Proceedings form. "← Nazad" + "Nastavi →". Prefill-ovana polja.
  - File: `_step_3_papers.html` (NOVI) — Paper list + "Dodaj rad" dugme. Author sekcija unutar svakog rada koristi `{% include "wizard/partials/_wizard_author_list.html" %}` (NE articles partial). "← Nazad" + "Nastavi na pregled →".
  - File: `_step_4_review.html` (NOVI) — Summary cards. Validation panel. "Generiši XML" dugme. "← Nazad".

- [ ] **Task 11: Kreiranje paper i author CRUD template-ova**
  - File: `wizard/partials/_paper_form.html` (NOVI) — HTMX partial za rad formu.
  - File: `wizard/partials/_paper_item.html` (NOVI) — Jedan rad u listi sa expand za autore.
  - File: `wizard/partials/_paper_list.html` (NOVI) — Container sa `id="paper-list"`. Iterira articles.
  - File: `wizard/partials/_wizard_author_list.html` (NOVI) — Isti sadržaj kao `articles/partials/_author_list.html` ali sa **per-article unique DOM IDs:**
    - `id="wizard-authors-{{ article.pk }}"` (umesto `#authors-section-content`)
    - Author form container: `id="wizard-author-form-{{ article.pk }}"` (umesto `#author-form-container`)
    - HTMX URLs: koriste `wizard:author-add`, `wizard:author-form`, itd. (ne `articles:...`)
  - File: `wizard/partials/_wizard_author_form.html` (NOVI) — Isti sadržaj kao `articles/partials/_author_form.html` ali sa:
    - `hx-target="#wizard-authors-{{ article.pk }}"` (per-article target)
    - `hx-post="{% url 'wizard:author-add' article.pk %}"` (wizard endpoint)
    - Cancel dugme cilja `#wizard-author-form-{{ article.pk }}`

- [ ] **Task 12: Entry point-ovi (dashboard + publication lista)**
  - File: `doi_portal/doi_portal/core/views.py`
  - Action: U `DashboardView._get_quick_actions()`, dodati wizard akciju u **SVE TRI grane**:
    - U `if flags["is_admin"]:` bloku (oko linije 130+):
      ```python
      {"label": "Registruj konferenciju", "url_name": "wizard:conference-start", "icon": "bi-megaphone"},
      ```
    - U `elif flags["is_urednik"]:` bloku:
      ```python
      {"label": "Registruj konferenciju", "url_name": "wizard:conference-start", "icon": "bi-megaphone"},
      ```
    - U `elif flags["is_bibliotekar"]:` bloku:
      ```python
      {"label": "Registruj konferenciju", "url_name": "wizard:conference-start", "icon": "bi-megaphone"},
      ```

  - File: `doi_portal/doi_portal/templates/publications/publication_list.html`
  - Action: Pored "Nova publikacija" dugmeta (linije 6-14):
    ```html
    {% if can_create %}
    <a href="{% url 'wizard:conference-start' %}" class="btn btn-outline-primary ms-2">
        <i class="bi bi-megaphone me-1"></i>Registruj konferenciju
    </a>
    {% endif %}
    ```

- [ ] **Task 13: Wizard stepper CSS**
  - File: `doi_portal/doi_portal/static/css/admin.css`
  - Action: Dodati wizard stepper CSS. Reuse pattern iz crossref deposit:
    ```css
    .wizard-stepper { display: flex; justify-content: center; gap: 0; margin-bottom: 2rem; }
    .wizard-step { display: flex; flex-direction: column; align-items: center; position: relative; flex: 1; }
    .wizard-step-icon { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; border: 2px solid var(--border-color, #dee2e6); background: white; color: var(--text-muted); z-index: 1; }
    .wizard-step.completed .wizard-step-icon { background: var(--primary, #0d6efd); border-color: var(--primary); color: white; }
    .wizard-step.active .wizard-step-icon { border-color: var(--primary); color: var(--primary); box-shadow: 0 0 0 4px rgba(13,110,253,0.15); }
    .wizard-step.disabled .wizard-step-icon { opacity: 0.5; }
    .wizard-step-label { margin-top: 0.5rem; font-size: 0.875rem; font-weight: 500; }
    .wizard-step-connector { position: absolute; top: 24px; left: 50%; width: 100%; height: 2px; background: var(--border-color); z-index: 0; }
    .wizard-step.completed .wizard-step-connector { background: var(--primary); }
    .wizard-step:last-child .wizard-step-connector { display: none; }
    ```

- [ ] **Task 14: Testovi za wizard views**
  - File: `doi_portal/doi_portal/wizard/tests/test_views.py` (NOVI)
  - Action: Test suite:

  **Fixtures:** publisher, admin_user, urednik_user, conference_publication, conference_issue, draft_article

  **TestWizardStart:**
  - `test_start_requires_login` — redirect to login
  - `test_start_renders_form` — 200, contains conference_name field, NO title field
  - `test_start_creates_publication` — POST → Publication created, type=CONFERENCE, title=conference_name
  - `test_start_redirects_to_step2` — POST → redirect to step-2 (ne step-1)

  **TestWizardStep1Edit:**
  - `test_step1_edit_loads_existing` — GET → form pre-filled
  - `test_step1_edit_updates_publication` — POST → updates, redirect to step-2

  **TestWizardStep2:**
  - `test_step2_prefill_from_conference` — proceedings_title = conference_name
  - `test_step2_creates_issue` — POST → Issue created
  - `test_step2_doi_suffix_validation` — POST with invalid DOI suffix → error

  **TestWizardStep3:**
  - `test_step3_shows_empty_paper_list` — no articles → empty state
  - `test_paper_add_creates_article` — HTMX POST → Article created with DRAFT status
  - `test_paper_delete_removes_article` — HTMX POST → Article deleted

  **TestWizardStep4:**
  - `test_step4_validates_draft_articles` — DRAFT articles included in validation (not skipped)
  - `test_step4_shows_errors_for_missing_authors` — validation shows author warnings
  - `test_generate_xml_transitions_to_published` — POST → articles become PUBLISHED
  - `test_generate_xml_creates_xml` — POST → issue.crossref_xml is not None
  - `test_generate_xml_redirects_to_deposit` — POST → redirect to crossref:issue-deposit

  **TestWizardAuthors:**
  - `test_wizard_author_add` — wizard:author-add endpoint works, returns wizard partial
  - `test_wizard_author_list_unique_ids` — response contains `wizard-authors-{pk}` (not generic ID)

  **TestWizardPermissions:**
  - `test_urednik_auto_publisher` — publisher field hidden
  - `test_admin_sees_publisher_dropdown` — publisher field visible
  - `test_no_publisher_gets_403` — 403 for user without publisher

### Acceptance Criteria

- [ ] **AC 1:** Given autentifikovan korisnik (Urednik), when otvori Dashboard, then vidi "Registruj konferenciju" u quick actions sekciji, i klik vodi na wizard start stranicu.

- [ ] **AC 2:** Given wizard start stranica, when korisnik unese conference_name="EMCE 2026", ostala polja, i submit-uje, then Publication tipa CONFERENCE se kreira sa `title="EMCE 2026"` (auto-populated iz conference_name) i korisnik se redirectuje DIREKTNO na korak 2 (ne na korak 1).

- [ ] **AC 3:** Given wizard korak 2 sa Publication koja ima conference_name="EMCE 2026" i publisher.name="EMCE", when se korak 2 učita, then proceedings_title je prefill-ovan sa "EMCE 2026", proceedings_publisher_name sa "EMCE", i year sa conference_date.year.

- [ ] **AC 4:** Given wizard korak 2, when korisnik unese DOI suffix sa razmakom ("abc def"), then forma prikazuje validacionu grešku "DOI sufiks ne sme sadržati razmake."

- [ ] **AC 5:** Given wizard korak 3, when korisnik klikne "Dodaj rad" i popuni title + doi_suffix, then Article se kreira u bazi sa status=DRAFT vezan za Issue.

- [ ] **AC 6:** Given wizard korak 3 sa kreiranim radom, when korisnik klikne "Dodaj autora" na tom radu, then wizard author form se prikazuje sa HTMX target-om `#wizard-authors-{article_pk}` (unique per rad). Kada doda autora, author list se ažurira samo za taj rad (bez kolidiranja sa drugim radovima na stranici).

- [ ] **AC 7:** Given wizard korak 3 sa 3 rada, when korisnik klikne "Nastavi na pregled", then korak 4 prikazuje summary svih podataka.

- [ ] **AC 8:** Given wizard korak 4 sa DRAFT radovima koji nemaju autore, when korak 4 se učita, then wizard-specific validacija (koja uključuje DRAFT artikle) prikazuje upozorenja o nedostajućim autorima i "Generiši XML" je disabled.

- [ ] **AC 9:** Given wizard korak 4 sa validnim podacima, when korisnik klikne "Generiši XML", then: (1) svi DRAFT artikli se transition-iraju u PUBLISHED, (2) CrossrefService generiše XML, (3) korisnik se redirectuje na crossref deposit workflow.

- [ ] **AC 10:** Given korisnik je na koraku 3, when klikne na "Korak 1" u stepper-u, then se vraća na korak 1 sa popunjenom formom (edit mode).

- [ ] **AC 11:** Given Urednik sa assigned publisher-om, when pokrene wizard, then publisher je automatski setovan (hidden field) i korisnik ne bira publisher-a.

- [ ] **AC 12:** Given Administrator, when pokrene wizard, then publisher dropdown je vidljiv.

- [ ] **AC 13:** Given korisnik bez publisher-a (i nije admin), when pokuša da pristupi wizard-u, then dobije 403.

- [ ] **AC 14:** Given wizard korak 3, when korisnik obriše rad, then Article je potpuno obrisan (hard delete) i lista se ažurira.

- [ ] **AC 15:** Given wizard start forma sa praznim conference_name, when submit, then forma prikazuje validacionu grešku.

## Additional Context

### Dependencies

- Nema novih pip zavisnosti.
- **Spec 3 zavisnost (soft):** Koristi terminologiju ako implementirana. Fallback na hardkodirane "Konferencija", "Zbornik", "Rad".
- Koristi: Publication/Issue/Article modele, PreValidationService (internal methods), CrossrefService, AuthorForm, AffiliationForm.

### Testing Strategy

**Unit testovi:**
- `wizard/tests/test_views.py` — ~22 test metoda u 6 test klasa
- Pokrivaju: CRUD, validaciju, permissije, prefill, status transition, author DOM IDs

**Integration testovi:**
- Wizard author CRUD → wizard-specific partials sa unique IDs
- Wizard validation → DRAFT articles included
- wizard_generate_xml → DRAFT→PUBLISHED transition + XML generation

**Manualno testiranje:**
- Komplet flow: start → step 2 → dodaj 3 rada sa autorima → step 4 → generiši XML
- Proveri da author sekcije ne kolidiraju kad su 2+ rada expanded istovremeno
- Navigacija nazad: step 3 → step 1 → step 3
- Proveri DOI suffix validaciju u koraku 2
- Edge case: napusti wizard na koraku 1, proveri da nema orphan Publication (samo ako korisnik submit-uje)

### Notes

- **Publication nema status polje.** Wizard-kreirane Publications su nerazlučive od standardnih. Orphan Publications (korisnik submit-uje korak 1 ali nikad ne završi) mogu se identifikovati po tome što nemaju Issue-a. Cleanup: van scope-a.
- **Author wrapper endpoint-i** kopiraju business logiku iz articles views. Buduća optimizacija: ekstraktovati shared logiku u servisne funkcije. Ali to je refactoring van scope-a ovog spec-a.
- **DRAFT → PUBLISHED transition** je ireverzibilna u wizard flow-u. Posle generisanja XML-a, korisnik nastavlja u standardnom deposit workflow-u gde su artikli već PUBLISHED.
- **Publication.slug Ćirilica bug:** Postojeći bug u `Publication.save()` — slug fallback za non-Latin koristi `self.pk` koji je None pri prvom save(). Wizard setuje `title = conference_name` — ako je conference_name na latinici (što je uobičajeno za akademske konferencije), slug se generiše normalno. Ako je na ćirilici, bug se triggeruje ali se rešava pri drugom save() (update u step-1 edit).
- **Extension point:** `/wizard/book/`, `/wizard/journal/` za buduće tipove.
- **Extension point:** CSV import → `wizard:papers-import` endpoint.

### Adversarial Review Fixes Applied

- **F1 (Critical):** Kreiranje wizard-specific author partials (`_wizard_author_list.html`, `_wizard_author_form.html`) sa per-article unique DOM IDs (`#wizard-authors-{{ article.pk }}`). Wrapper endpoint-i u wizard app-u koji vraćaju ove partials umesto articles partials. Dodat Task 7 i Task 11.
- **F2 (Critical):** Kreiranje `wizard_validate_issue()` helpera koji validira DRAFT artikle (poziva PreValidationService internal metode bez PUBLISHED filtera). DRAFT→PUBLISHED transition pre XML generisanja u `wizard_generate_xml`. Dodat Task 8. AC 8 i AC 9 ažurirani.
- **F3 (High):** Uklonjene sve reference na "DRAFT status" za Publication. Dokumentovano da Publication nema status polje. Orphan Publications se identifikuju po nedostatku Issue-a. Ažurirani Overview, Technical Decisions, Notes.
- **F4 (High):** Dodata `clean_doi_suffix()` metoda u WizardProceedingsForm sa validacijom iz IssueForm. Dodat AC 4 za DOI suffix validaciju.
- **F5 (High):** Task 12 sada eksplicitno navodi da se akcija mora dodati u SVE TRI grane (admin, urednik, bibliotekar) sa tačnim mestima.
- **F6 (Medium):** Dokumentovan Publication.slug Ćirilica bug u Notes. Workaround: conference_name je tipično na latinici.
- **F7 (Medium):** Merged start + step-1 flow. `wizard_start` POST kreira Publication i redirectuje DIREKTNO na step-2 (ne step-1). Step-1 URL postoji samo za edit mode (back navigation). Sprečava orphan-e od double-click-a. AC 2 ažuriran.
- **F8 (Medium):** `title` uklonjen iz vidljivih polja WizardConferenceForm. Auto-populate `title = conference_name` u `save()` metodi. Dokumentovano u Technical Decisions. AC 2 ažuriran.
