---
title: 'Kontekstualna terminologija i auto-detekcija grešaka'
slug: 'kontekstualna-terminologija-i-auto-detekcija'
created: '2026-03-20'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Django 5.x', 'HTMX 2.0.8', 'Alpine.js 3.15.3', 'Bootstrap 5.3', 'PostgreSQL']
files_to_modify:
  # Terminology system (new)
  - 'doi_portal/doi_portal/core/templatetags/terminology.py'
  - 'doi_portal/doi_portal/core/terminology.py'
  # Admin templates
  - 'doi_portal/doi_portal/templates/articles/article_list.html'
  - 'doi_portal/doi_portal/templates/articles/article_detail.html'
  - 'doi_portal/doi_portal/templates/articles/article_form.html'
  - 'doi_portal/doi_portal/templates/articles/article_confirm_delete.html'
  - 'doi_portal/doi_portal/templates/issues/issue_list.html'
  - 'doi_portal/doi_portal/templates/issues/issue_detail.html'
  - 'doi_portal/doi_portal/templates/issues/issue_form.html'
  - 'doi_portal/doi_portal/templates/issues/issue_confirm_delete.html'
  - 'doi_portal/doi_portal/templates/publications/publication_detail.html'
  - 'doi_portal/doi_portal/templates/components/_breadcrumbs.html'
  # Portal templates
  - 'doi_portal/doi_portal/templates/portal/publications/publication_detail.html'
  - 'doi_portal/doi_portal/templates/portal/publications/issue_detail.html'
  - 'doi_portal/doi_portal/templates/portal/article_detail.html'
  - 'doi_portal/doi_portal/templates/portal/partials/_search_results.html'
  - 'doi_portal/doi_portal/templates/portal/partials/_floating_action_bar.html'
  # Views (messages + context)
  - 'doi_portal/doi_portal/articles/views.py'
  - 'doi_portal/doi_portal/issues/views.py'
  # Forms (widget attrs)
  - 'doi_portal/doi_portal/articles/forms.py'
  - 'doi_portal/doi_portal/issues/forms.py'
  - 'doi_portal/doi_portal/publications/forms.py'
  # Validation
  - 'doi_portal/doi_portal/crossref/services.py'
  - 'doi_portal/doi_portal/crossref/tests/test_validation.py'
  # JavaScript
  - 'doi_portal/doi_portal/static/js/project.js'
  - 'doi_portal/doi_portal/static/css/admin.css'
  # Tests (new)
  - 'doi_portal/doi_portal/core/tests/test_terminology.py'
code_patterns:
  - 'Django custom template tags/filters ({% load terminology %})'
  - 'ValidationResult.add_warning() pattern in PreValidationService'
  - 'Alpine.js x-data components for client-side reactivity'
  - 'JSON data embedding via <script type="application/json">'
  - 'HTMX partials with _ prefix convention'
  - 'Views set breadcrumbs, form_title, submit_text in get_context_data()'
test_patterns:
  - 'pytest-django with factory fixtures'
  - 'PreValidationService tests in crossref/tests/test_validation.py (1138 lines)'
  - 'Test classes per validation method: TestPreValidationServiceJournal, etc.'
---

# Tech-Spec: Kontekstualna terminologija i auto-detekcija grešaka

**Created:** 2026-03-20

## Overview

### Problem Statement

UI koristi generičke srpske termine "Izdanje" i "Članak" za sve tipove publikacija, što je semantički netačno. Za Zbornik (Conference), "Izdanje" bi trebalo da bude "Zbornik radova" a "Članak" bi trebalo da bude "Rad". Za Monografiju (Book), "Izdanje" bi trebalo da bude "Tom" a "Članak" bi trebalo da bude "Poglavlje". Takođe nedostaje client-side detekcija duplih razmaka u naslovima i backend validacija free_to_read konzistentnosti.

### Solution

1. Kreirati centralizovani terminološki sistem (Python modul + Django template tag) koji mapira `publication_type` na srpske termine sa svim gramatičkim padežima.
2. Ažurirati sve admin i portal template-ove da koriste terminološki filter umesto hardkodiranih stringova.
3. Ažurirati view poruke (messages.success) i context varijable (breadcrumbs, form_title, submit_text) da koriste kontekstualne termine.
4. Dodati JavaScript warning za duple razmake u title/subtitle poljima.
5. Dodati `_validate_free_to_read_consistency()` metod u PreValidationService.

### Scope

**In Scope:**
- Dinamička terminologija kroz admin template-ove (breadcrumbs, naslovi, forme, liste, dugmad, confirmation dialozi)
- Dinamička terminologija na portal template-ovima (issue detail, article detail, publication detail)
- Kontekstualne messages.success poruke i context varijable (breadcrumbs, form_title, submit_text) u views.py
- Client-side warning za duple razmake u title/subtitle poljima
- Backend free_to_read konzistentnost warning u PreValidationService

**Out of Scope:**
- DOI preview u formama
- Prioritizacija/reorder polja po tipu publikacije
- Sidebar navigacija (ostaje generička — prikazuje globalne linkove, ne kontekstualne)
- Portal home/about/search stranice (mešoviti kontekst — ostaju generičke)

## Context for Development

### Codebase Patterns

- `PublicationType(TextChoices)`: JOURNAL="Časopis", CONFERENCE="Zbornik", BOOK="Monografija", OTHER="Ostalo"
- Model chain: `Article → Issue → Publication → publication_type`. Views već koriste `select_related("issue", "issue__publication")`.
- HTMX dinamičko swapovanje za type-specific polja u publication formi
- Alpine.js reactivity u issue_form (`issueForm()`), article_form (`autosaveManager()`, `paginationToggle()`)
- JSON data embedding: `<script type="application/json" id="pub-type-map">`
- PreValidationService: `ValidationResult` sa `add_error(message, field_name, article_id, fix_url)` i `add_warning(...)`
- UI lokalizacija: hardkodirani srpski stringovi (ne koriste Django i18n)
- Django messages: `messages.success(request, "Članak uspešno kreiran.")`
- Srpska gramatika: članak/članka/članaka (singular/paucal/plural)
- **Views postavljaju context varijable u `get_context_data()`:**
  - `breadcrumbs` — lista dict-ova sa `label` i `url` ključevima
  - `form_title` — naslov forme (npr. "Novi članak", "Izmeni članak: {title}")
  - `submit_text` — tekst submit dugmeta (npr. "Kreiraj članak", "Sačuvaj izmene")
- **ListView-ovi filtriraju po query param-ima:**
  - `ArticleListView` filtrira po `?issue=<id>` (linija 171) — kad je filtrirano, pub_type je dostupan iz issue-a
  - `IssueListView` filtrira po `?publication=<id>` (linija 72) — kad je filtrirano, pub_type je dostupan iz publication-a
  - Kad NISU filtrirani, prikazuju mešovite tipove — koriste generičke termine
- **CreateView-ovi nemaju `self.object` pre `form_valid()`:**
  - `ArticleCreateView` dobija issue_id iz `?issue=<id>` query param-a u `get_initial()` (linija 243-249)
  - `IssueCreateView` dobija publication_id iz `?publication=<id>` query param-a u `get_initial()` (linija 173-179)
  - pub_type se mora izvući iz query param entity-ja, ne iz self.object
- `admin_base.html` već uključuje `project.js` (linija 48): `<script defer src="{% static 'js/project.js' %}"></script>`
- Form widget attrs su dict-based — `data-check-spaces` se dodaje u `forms.py` attrs dict, NE u template

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `publications/models.py` | PublicationType choices |
| `articles/views.py` | 8 messages + context varijable (breadcrumbs, form_title, submit_text) sa "Članak" |
| `issues/views.py` | 4 messages + context varijable sa "Izdanje" |
| `articles/forms.py` | Widget attrs za title (linija 61-65) i subtitle (linija 67-72) — mesto za `data-check-spaces` |
| `articles/article_list.html` | "Novi članak", "Dodaj prvi članak", "Članci" naslov |
| `articles/article_detail.html` | "Članak" u naslovu, dugmadima |
| `articles/article_form.html` | Form naslov koristi `{{ form_title }}` context var |
| `articles/article_confirm_delete.html` | "Obriši članak" confirmation |
| `issues/issue_list.html` | "Novo izdanje", "Dodaj prvo izdanje", "Izdanja" naslov |
| `issues/issue_detail.html` | "Izdanje" naslov, "Članci" sekcija |
| `issues/issue_form.html` | "Broj izdanja" labele |
| `issues/issue_confirm_delete.html` | "Obriši izdanje" confirmation |
| `publications/publication_detail.html` | "Izdanja" sekcija, "Novo izdanje" dugme |
| `components/_breadcrumbs.html` | Breadcrumb labeli (koristi `{{ crumb.label }}` iz context-a) |
| `portal/publications/publication_detail.html` | "Izdanja" sekcija, count badge sa članak/članka/članaka infleksijom |
| `portal/publications/issue_detail.html` | "Članci" sekcija heading |
| `portal/article_detail.html` | "Povučen članak" |
| `portal/partials/_search_results.html` | Count text sa infleksijom |
| `portal/partials/_floating_action_bar.html` | "Citiraj članak" aria-label |
| `crossref/services.py` | PreValidationService (linije 490-857), validate_issue() (linije 499-538) |
| `crossref/validation.py` | ValidationResult, ValidationIssue (linije 1-177) |
| `crossref/tests/test_validation.py` | Test suite (1138 linija) |
| `static/js/project.js` | Prazan — za project-specific JS. Već uključen u admin_base.html (linija 48) |
| `admin_base.html` | Uključuje project.js na liniji 48 |

### Technical Decisions

- **Centralizovani terminološki modul:** `core/terminology.py` — Python dict sa svim terminima po tipu. Koristi se i iz template tag-ova i iz view-ova.
- **Template filter pristup:** `{% load terminology %}` sa filterom `{{ "article"|term:pub_type }}` koji vraća kontekstualni termin.
- **BOOK terminologija — samo "Tom" (ne "Tom/Edicija"):** Compound termin "Tom/Edicija" stvara gramatičku nekonzistentnost jer je "Tom" muškog a "Edicija" ženskog roda. Dugmad bi bila "Novi tom" ali label "Tom/Edicija" — nekonzistentno. Odluka: koristiti samo **"Tom"** svuda za BOOK tip. Ovo je jednostavnije i gramatički konzistentno.
- **Terminologija mapa (srpski):**

  | Ključ | JOURNAL | CONFERENCE | BOOK | OTHER |
  |-------|---------|------------|------|-------|
  | issue | Izdanje | Zbornik radova | Tom | Izdanje |
  | issue_plural | Izdanja | Zbornici radova | Tomovi | Izdanja |
  | issue_genitive | izdanja | zbornika radova | toma | izdanja |
  | article | Članak | Rad | Poglavlje | Članak |
  | article_plural | Članci | Radovi | Poglavlja | Članci |
  | article_genitive | članaka | radova | poglavlja | članaka |
  | article_genitive_paucal | članka | rada | poglavlja | članka |
  | article_accusative | članak | rad | poglavlje | članak |
  | new_article | Novi članak | Novi rad | Novo poglavlje | Novi članak |
  | create_article | Kreiraj članak | Kreiraj rad | Kreiraj poglavlje | Kreiraj članak |
  | edit_article | Izmeni članak | Izmeni rad | Izmeni poglavlje | Izmeni članak |
  | new_issue | Novo izdanje | Novi zbornik radova | Novi tom | Novo izdanje |
  | create_issue | Kreiraj izdanje | Kreiraj zbornik | Kreiraj tom | Kreiraj izdanje |
  | edit_issue | Izmeni izdanje | Izmeni zbornik | Izmeni tom | Izmeni izdanje |
  | add_first_article | Dodaj prvi članak | Dodaj prvi rad | Dodaj prvo poglavlje | Dodaj prvi članak |
  | add_first_issue | Dodaj prvo izdanje | Dodaj prvi zbornik | Dodaj prvi tom | Dodaj prvo izdanje |
  | delete_article | Obriši članak | Obriši rad | Obriši poglavlje | Obriši članak |
  | delete_issue | Obriši izdanje | Obriši zbornik | Obriši tom | Obriši izdanje |
  | article_created | Članak uspešno kreiran. | Rad uspešno kreiran. | Poglavlje uspešno kreirano. | Članak uspešno kreiran. |
  | article_updated | Članak uspešno ažuriran. | Rad uspešno ažuriran. | Poglavlje uspešno ažurirano. | Članak uspešno ažuriran. |
  | article_deleted | Članak uspešno obrisan. | Rad uspešno obrisan. | Poglavlje uspešno obrisano. | Članak uspešno obrisan. |
  | article_submitted | Članak poslat na pregled. | Rad poslat na pregled. | Poglavlje poslato na pregled. | Članak poslat na pregled. |
  | article_approved | Članak odobren. | Rad odobren. | Poglavlje odobreno. | Članak odobren. |
  | article_returned | Članak vraćen na doradu. | Rad vraćen na doradu. | Poglavlje vraćeno na doradu. | Članak vraćen na doradu. |
  | article_published | Članak objavljen. | Rad objavljen. | Poglavlje objavljeno. | Članak objavljen. |
  | article_withdrawn | Članak povučen. | Rad povučen. | Poglavlje povučeno. | Članak povučen. |
  | issue_created | Izdanje uspešno kreirano. | Zbornik uspešno kreiran. | Tom uspešno kreiran. | Izdanje uspešno kreirano. |
  | issue_updated | Izdanje uspešno ažurirano. | Zbornik uspešno ažuriran. | Tom uspešno ažuriran. | Izdanje uspešno ažurirano. |
  | issue_deleted | Izdanje uspešno obrisano. | Zbornik uspešno obrisan. | Tom uspešno obrisan. | Izdanje uspešno obrisano. |
  | issue_has_articles_warning | Izdanje ima {count} {article_genitive}. Izdanje je označeno kao obrisano ali podaci su sačuvani. | Zbornik ima {count} {article_genitive}. Zbornik je označen kao obrisan ali podaci su sačuvani. | Tom ima {count} {article_genitive}. Tom je označen kao obrisan ali podaci su sačuvani. | Izdanje ima {count} {article_genitive}. Izdanje je označeno kao obrisano ali podaci su sačuvani. |

- **pub_type u template kontekstu — tri scenarija:**
  1. **DetailView/UpdateView/DeleteView:** `pub_type` iz `self.object.issue.publication.publication_type` (article) ili `self.object.publication.publication_type` (issue). `self.object` je dostupan.
  2. **CreateView:** `pub_type` iz query param entity-ja. ArticleCreateView čita `?issue=<id>` → Issue.objects.get(id) → issue.publication.publication_type. IssueCreateView čita `?publication=<id>` → Publication.objects.get(id) → publication.publication_type. Fallback na JOURNAL ako query param ne postoji.
  3. **ListView:** Kad je filtrirano po issue/publication, `pub_type` iz filtriranog entity-ja. Kad NIJE filtrirano (globalna lista), koristi JOURNAL (generičke terme). Template mora da handluje oba slučaja.
- **Breadcrumbs:** `_breadcrumbs.html` koristi `{{ crumb.label }}` iz context-a — terminologija se primenjuje u view-u (get_context_data), ne u template-u.
- **Sidebar:** Ostaje generička ("Izdanja", "Članci") — prikazuje globalne linkove
- **Portal search/home/about:** Ostaju generičke — mešoviti kontekst
- **free_to_read validacija:** Warning, ne error — ne blokira XML generisanje
- **data-check-spaces atribut:** Dodaje se u `forms.py` widget attrs dict (ne u template), jer Django renderuje input elemente iz widget-a.

## Implementation Plan

### Tasks

- [ ] **Task 1: Kreiranje terminološkog modula**
  - File: `doi_portal/doi_portal/core/terminology.py` (NOVI)
  - Action: Kreirati Python modul sa:
    - `TERMINOLOGY_MAP` dict — nested dict `{pub_type: {term_key: value}}` sa svim ključevima iz tabele iznad
    - `get_term(term_key: str, publication_type: str) -> str` funkcija — vraća termin za dati ključ i tip, fallback na JOURNAL ako je tip nepoznat ili None
    - `get_article_count_label(count: int, publication_type: str) -> str` funkcija — vraća gramatički tačan label za broj koristeći srpsku paucal logiku:
      - count == 1: singular (članak/rad/poglavlje)
      - count 2-4: paucal (članka/rada/poglavlja)
      - count 0 ili 5+: genitive plural (članaka/radova/poglavlja)
    - `get_issue_delete_warning(count: int, publication_type: str) -> str` funkcija — vraća compound poruku za brisanje issue-a koji ima artikle. Koristi `get_article_count_label()` i `get_term("issue_has_articles_warning")` sa `.format(count=count, article_genitive=...)`.
  - Notes: Koristiti `PublicationType` konstante iz `publications.models`. Import: `from doi_portal.publications.models import PublicationType`.

- [ ] **Task 2: Kreiranje template tag-a**
  - File: `doi_portal/doi_portal/core/templatetags/terminology.py` (NOVI)
  - Action: Kreirati Django template tag library sa standardnim pattern-om:
    ```python
    from django import template
    from doi_portal.core.terminology import get_term, get_article_count_label

    register = template.Library()

    @register.filter
    def term(term_key, publication_type):
        return get_term(term_key, publication_type)

    @register.simple_tag
    def article_count_label(count, publication_type):
        return get_article_count_label(count, publication_type)
    ```
  - Notes: Filter se koristi kao `{{ "article_plural"|term:pub_type }}`. Simple tag kao `{% article_count_label issue.article_count pub_type %}`.

- [ ] **Task 3: Testovi za terminološki sistem**
  - File: `doi_portal/doi_portal/core/tests/test_terminology.py` (NOVI)
  - Action: Kreirati test suite:
    - `TestGetTerm`: Testira sve ključeve za sve tipove publikacija (JOURNAL, CONFERENCE, BOOK, OTHER)
    - `TestGetTermFallback`: Testira da None, prazan string, i nepoznat tip vraćaju JOURNAL default
    - `TestArticleCountLabel`: Testira srpske gramatičke oblike za sve tipove:
      - JOURNAL: 1 članak, 2 članka, 5 članaka, 0 članaka
      - CONFERENCE: 1 rad, 3 rada, 7 radova
      - BOOK: 1 poglavlje, 4 poglavlja, 10 poglavlja
    - `TestGetIssueDeleteWarning`: Testira compound poruku za svaki tip
    - `TestTermTemplateFilter`: Testira filter rendering u Django template-u koristeći `Template("{% load terminology %}{{ 'article'|term:pub_type }}").render(Context({"pub_type": "JOURNAL"}))`
  - Notes: pytest-django pattern sa `@pytest.mark.django_db` gde je potrebno.

- [ ] **Task 4: Ažuriranje article view-ova — context i poruke**
  - File: `doi_portal/doi_portal/articles/views.py`
  - Action: Dodati `from doi_portal.core.terminology import get_term` na vrh.
  - Action: Helper za dobijanje pub_type — dodati na početak fajla (ili kao metod mixin-a):
    ```python
    def _get_pub_type_from_issue_id(issue_id):
        """Get publication_type from issue_id query param. Returns JOURNAL as fallback."""
        if issue_id:
            try:
                issue = Issue.objects.select_related("publication").get(pk=issue_id)
                return issue.publication.publication_type
            except Issue.DoesNotExist:
                pass
        return PublicationType.JOURNAL
    ```
  - Action: **ArticleListView.get_context_data()** (linija 182-201):
    - Dodati `pub_type` u context. Kad je filtriran po issue (`?issue=<id>`), izvući pub_type iz issue-a. Kad NIJE filtriran, koristiti JOURNAL (default).
    ```python
    issue_id = self.request.GET.get("issue")
    if issue_id:
        pub_type = _get_pub_type_from_issue_id(issue_id)
    else:
        pub_type = PublicationType.JOURNAL
    context["pub_type"] = pub_type
    ```
    - Ažurirati breadcrumbs label "Članci" → `get_term("article_plural", pub_type)`
  - Action: **ArticleCreateView.get_context_data()** (linija 251-261):
    - Izvući pub_type iz `?issue=<id>` query param-a:
    ```python
    issue_id = self.request.GET.get("issue")
    pub_type = _get_pub_type_from_issue_id(issue_id)
    context["pub_type"] = pub_type
    ```
    - Zameniti hardkodirane stringove:
      - breadcrumbs "Članci" → `get_term("article_plural", pub_type)` (linija 255)
      - breadcrumbs "Novi članak" → `get_term("new_article", pub_type)` (linija 256)
      - `form_title` "Novi članak" → `get_term("new_article", pub_type)` (linija 259)
      - `submit_text` "Kreiraj članak" → `get_term("create_article", pub_type)` (linija 260)
  - Action: **ArticleUpdateView.get_context_data()** (linija 334-348):
    - pub_type iz `self.object.issue.publication.publication_type`:
    ```python
    pub_type = self.object.issue.publication.publication_type
    context["pub_type"] = pub_type
    ```
    - Zameniti:
      - breadcrumbs "Članci" → `get_term("article_plural", pub_type)`
      - `form_title` `f"Izmeni članak: {self.object.title}"` → `f"{get_term('edit_article', pub_type)}: {self.object.title}"`
  - Action: **ArticleDetailView.get_context_data()** (linija 395-444):
    - pub_type iz `self.object.issue.publication.publication_type`
    - Ažurirati breadcrumbs "Članci" → kontekstualni termin
  - Action: **ArticleDeleteView.get_context_data()** (linija 464-472):
    - pub_type iz `self.object.issue.publication.publication_type`
    - Ažurirati breadcrumbs
  - Action: **Zameniti 8 hardkodiranih messages.success poruka:**
    - Linija 267-269 (ArticleCreateView.form_valid): `messages.success(self.request, get_term("article_created", self.object.issue.publication.publication_type))`
    - Linija 353-355 (ArticleUpdateView.form_valid): `get_term("article_updated", self.object.issue.publication.publication_type)`
    - Linija 477-479 (ArticleDeleteView.form_valid): `get_term("article_deleted", self.object.issue.publication.publication_type)`
    - Linija 1121 (article_submit_for_review): `get_term("article_submitted", article.issue.publication.publication_type)`
    - Linija 1178 (article_approve): `get_term("article_approved", article.issue.publication.publication_type)`
    - Linija 1232 (article_return_for_revision): `get_term("article_returned", article.issue.publication.publication_type)`
    - Linija 1289 (article_publish): `get_term("article_published", article.issue.publication.publication_type)`
    - Linija 1343 (article_withdraw): `get_term("article_withdrawn", article.issue.publication.publication_type)`
  - Notes: U function-based views (submit, approve, itd.) `article` je već loadovan sa `select_related`. U CBV form_valid(), `self.object` je dostupan posle `super().form_valid()`.

- [ ] **Task 5: Ažuriranje issue view-ova — context i poruke**
  - File: `doi_portal/doi_portal/issues/views.py`
  - Action: Dodati `from doi_portal.core.terminology import get_term, get_issue_delete_warning` na vrh.
  - Action: Helper za dobijanje pub_type iz publication_id:
    ```python
    def _get_pub_type_from_publication_id(publication_id):
        """Get publication_type from publication_id query param. Returns JOURNAL as fallback."""
        if publication_id:
            try:
                pub = Publication.objects.get(pk=publication_id)
                return pub.publication_type
            except Publication.DoesNotExist:
                pass
        return PublicationType.JOURNAL
    ```
  - Action: **IssueListView.get_context_data()** (linija 91-139):
    - Kad je filtriran po publication (`?publication=<id>`), izvući pub_type. Kad NIJE filtriran, JOURNAL default.
    - Ažurirati breadcrumbs "Izdanja" → `get_term("issue_plural", pub_type)`
  - Action: **IssueCreateView.get_context_data()** (linija 181-192):
    - Izvući pub_type iz `?publication=<id>`:
    ```python
    publication_id = self.request.GET.get("publication")
    pub_type = _get_pub_type_from_publication_id(publication_id)
    context["pub_type"] = pub_type
    ```
    - Zameniti:
      - breadcrumbs "Izdanja" → `get_term("issue_plural", pub_type)` (linija 185)
      - breadcrumbs "Novo izdanje" → `get_term("new_issue", pub_type)` (linija 187)
      - `form_title` "Novo izdanje" → `get_term("new_issue", pub_type)` (linija 189)
      - `submit_text` "Kreiraj izdanje" → `get_term("create_issue", pub_type)` (linija 190)
  - Action: **IssueUpdateView.get_context_data()** (linija 247-260):
    - pub_type iz `self.object.publication.publication_type`
    - Zameniti breadcrumbs i `form_title` `f"Izmeni izdanje: {self.object}"` → `f"{get_term('edit_issue', pub_type)}: {self.object}"`
  - Action: **IssueDetailView.get_context_data()** (linija 309-322):
    - pub_type iz `self.object.publication.publication_type`
    - Ažurirati breadcrumbs
  - Action: **IssueDeleteView.get_context_data()** (linija 342-351):
    - pub_type iz `self.object.publication.publication_type`
    - Ažurirati breadcrumbs
  - Action: **Zameniti 4 hardkodirane poruke:**
    - Linija 197-199 (IssueCreateView.form_valid): `get_term("issue_created", self.object.publication.publication_type)`
    - Linija 265-267 (IssueUpdateView.form_valid): `get_term("issue_updated", self.object.publication.publication_type)`
    - Linija 359-363 (IssueDeleteView.form_valid — WARNING, compound poruka):
      ```python
      pub_type = self.object.publication.publication_type
      messages.warning(
          self.request,
          get_issue_delete_warning(article_count, pub_type),
      )
      ```
    - Linija 365-367 (IssueDeleteView.form_valid): `get_term("issue_deleted", pub_type)`

- [ ] **Task 6: Ažuriranje admin template-ova**
  - File: `doi_portal/doi_portal/templates/articles/article_list.html`
  - Action: Dodati `{% load terminology %}` na vrh (posle `{% extends %}`). Zameniti:
    - "Članci" → `{{ "article_plural"|term:pub_type }}`
    - "Novi članak" → `{{ "new_article"|term:pub_type }}`
    - "Dodaj prvi članak" → `{{ "add_first_article"|term:pub_type }}`
    - Sve ostale hardkodirane "članak/članci" reference
  - Notes: `pub_type` dolazi iz context-a (setovan u Task 4).

  - File: `doi_portal/doi_portal/templates/articles/article_detail.html`
  - Action: Dodati `{% load terminology %}`. Zameniti "Članak" u naslovu i dugmadima sa `{{ "article"|term:pub_type }}`.

  - File: `doi_portal/doi_portal/templates/articles/article_form.html`
  - Action: Template već koristi `{{ form_title }}` i `{{ submit_text }}` iz context-a — ove vrednosti su ažurirane u Task 4, pa template NE treba da se menja za naslov i submit dugme. Proveriti da li ima drugih hardkodiranih "članak" referenci u template-u i zameniti ih.

  - File: `doi_portal/doi_portal/templates/articles/article_confirm_delete.html`
  - Action: Dodati `{% load terminology %}`. Zameniti "Obriši članak" i confirmation tekst sa `{{ "delete_article"|term:pub_type }}`.

  - File: `doi_portal/doi_portal/templates/issues/issue_list.html`
  - Action: Dodati `{% load terminology %}`. Zameniti:
    - "Izdanja" → `{{ "issue_plural"|term:pub_type }}`
    - "Novo izdanje" → `{{ "new_issue"|term:pub_type }}`
    - "Dodaj prvo izdanje" → `{{ "add_first_issue"|term:pub_type }}`

  - File: `doi_portal/doi_portal/templates/issues/issue_detail.html`
  - Action: Dodati `{% load terminology %}`. Zameniti "Izdanje" u naslovu i "Članci" u sekciji artikala sa kontekstualnim terminima.

  - File: `doi_portal/doi_portal/templates/issues/issue_form.html`
  - Action: Template koristi `{{ form_title }}` i `{{ submit_text }}` iz context-a (ažurirano u Task 5). Proveriti ostale hardkodirane reference.

  - File: `doi_portal/doi_portal/templates/issues/issue_confirm_delete.html`
  - Action: Dodati `{% load terminology %}`. Zameniti "Obriši izdanje" sa `{{ "delete_issue"|term:pub_type }}`.

  - File: `doi_portal/doi_portal/templates/publications/publication_detail.html`
  - Action: Dodati `{% load terminology %}`. Zameniti "Izdanja" sekciju i "Novo izdanje" dugme sa kontekstualnim terminima. `pub_type` je `publication.publication_type`.

  - File: `doi_portal/doi_portal/templates/components/_breadcrumbs.html`
  - Action: **NE TREBA MENJATI** — breadcrumbs koriste `{{ crumb.label }}` iz context-a, a labeli su ažurirani u Task 4 i Task 5 (u view-ovima).

- [ ] **Task 7: Ažuriranje portal template-ova**
  - File: `doi_portal/doi_portal/templates/portal/publications/publication_detail.html`
  - Action: Dodati `{% load terminology %}`. Zameniti:
    - "Izdanja" sekcija heading → `{{ "issue_plural"|term:publication.publication_type }}`
    - "Nema objavljenih izdanja." → "Nema objavljenih {{ "issue_genitive"|term:publication.publication_type }}."
    - Article count badge — trenutno koristi inline srpsku infleksiju (`{% if issue.article_count == 1 %}članak{% elif ... %}članka{% else %}članaka{% endif %}`). Zameniti sa: `{% article_count_label issue.article_count publication.publication_type %}`
  - Notes: `publication` objekat je dostupan u context-u — `publication.publication_type` se koristi direktno u template-u, ne treba `pub_type` context var.

  - File: `doi_portal/doi_portal/templates/portal/publications/issue_detail.html`
  - Action: Dodati `{% load terminology %}`. Zameniti:
    - "Članci" sekcija heading → `{{ "article_plural"|term:issue.publication.publication_type }}`
    - "Članci će biti dostupni uskoro." empty state → kontekstualno
  - Notes: `issue.publication.publication_type` je dostupan — views koriste `select_related("publication")`.

  - File: `doi_portal/doi_portal/templates/portal/article_detail.html`
  - Action: Dodati `{% load terminology %}`. Zameniti:
    - "Povučen članak" → `"Povučen {{ "article_accusative"|term:article.issue.publication.publication_type }}"`  (ali pazi na rod: "Povučen članak" vs "Povučeno poglavlje" vs "Povučen rad" — treba novi ključ `article_withdrawn_title`)
    - "Ovaj članak je dostupan..." → kontekstualno
  - Notes: Rod se razlikuje — dodati `article_withdrawn_title` ključ u terminologiju: "Povučen članak" / "Povučen rad" / "Povučeno poglavlje". Ili koristiti rodnu neutralnu formu.

  - File: `doi_portal/doi_portal/templates/portal/partials/_floating_action_bar.html`
  - Action: Dodati `{% load terminology %}`. Zameniti:
    - `title="Citiraj članak"` → `title="Citiraj {{ "article_accusative"|term:article.issue.publication.publication_type }}"`
    - `aria-label="Citiraj članak"` → kontekstualno
    - `title="Podeli članak"` → kontekstualno
    - `aria-label="Podeli članak"` → kontekstualno
    - `aria-label="Akcije za članak"` → kontekstualno
  - Notes: Treba novi ključ `cite_article` i `share_article` u terminologiji za čistiju sintaksu, ili koristiti akuzativ.

  - File: `doi_portal/doi_portal/templates/portal/partials/_search_results.html`
  - Action: **OSTAJE GENERIČKO** — search prikazuje mešovite rezultate iz različitih publikacija. Bez promene.

- [ ] **Task 8: Dopuna terminološke mape za portal**
  - File: `doi_portal/doi_portal/core/terminology.py` (ažuriranje Task 1)
  - Action: Dodati dodatne ključeve koji su identifikovani u Task 7:

    | Ključ | JOURNAL | CONFERENCE | BOOK | OTHER |
    |-------|---------|------------|------|-------|
    | article_withdrawn_title | Povučen članak | Povučen rad | Povučeno poglavlje | Povučen članak |
    | cite_article | Citiraj članak | Citiraj rad | Citiraj poglavlje | Citiraj članak |
    | share_article | Podeli članak | Podeli rad | Podeli poglavlje | Podeli članak |
    | article_actions | Akcije za članak | Akcije za rad | Akcije za poglavlje | Akcije za članak |
    | article_available_externally | Ovaj članak je dostupan i na sajtu izdavača | Ovaj rad je dostupan i na sajtu izdavača | Ovo poglavlje je dostupno i na sajtu izdavača | Ovaj članak je dostupan i na sajtu izdavača |

  - Notes: Ovi ključevi nastaju iz portal template analize. Dodati ih u TERMINOLOGY_MAP u Task 1.

- [ ] **Task 9: JavaScript warning za duple razmake**
  - File: `doi_portal/doi_portal/static/js/project.js`
  - Action: Dodati vanilla JS koji:
    1. Na `DOMContentLoaded`, selektuje sve input/textarea elemente sa `data-check-spaces="true"` atributom
    2. Za svaki element, dodaje `input` event listener
    3. Na `input` event proverava da li value sadrži 2+ uzastopna razmaka (regex: `/  +/`)
    4. Ako da — kreira/prikazuje žuto upozorenje ispod polja:
       - Tekst: "Naslov sadrži duple razmake"
       - "Ispravi" dugme (klikom zamenjuje `/ {2,}/g` sa jednim razmakom i ažurira input value)
    5. Ako korisnik ispravi (ručno ili dugmetom) — sakriva upozorenje
    6. Warning element se kreira dinamički kao sibling, sa klasom `.double-space-warning`
    7. Idempotentno — ne kreira duplikat warninga ako već postoji
  - Notes: Koristiti `insertAdjacentHTML('afterend', ...)` za ubacivanje warninga. Warning sadrži Bootstrap Icons `bi-exclamation-triangle` ikonu.

  - File: `doi_portal/doi_portal/static/css/admin.css`
  - Action: Dodati stil za `.double-space-warning`:
    ```css
    .double-space-warning {
      color: var(--warning-text, #856404);
      background-color: var(--warning-bg, #fff3cd);
      border: 1px solid var(--warning-border, #ffc107);
      border-radius: 6px;
      padding: 0.5rem 0.75rem;
      margin-top: 0.25rem;
      font-size: 0.875rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .double-space-warning button {
      background: none;
      border: 1px solid var(--warning-border, #ffc107);
      border-radius: 4px;
      padding: 0.125rem 0.5rem;
      cursor: pointer;
      font-size: 0.8125rem;
      color: inherit;
    }
    ```

  - File: `doi_portal/doi_portal/articles/forms.py`
  - Action: Dodati `"data-check-spaces": "true"` u widget attrs za `title` (linija 61-65) i `subtitle` (linija 67-72):
    ```python
    "title": forms.TextInput(
        attrs={
            "class": "form-control",
            "placeholder": "Unesite naslov članka",
            "data-check-spaces": "true",
        }
    ),
    "subtitle": forms.TextInput(
        attrs={
            "class": "form-control",
            "placeholder": "Opcioni podnaslov",
            "data-check-spaces": "true",
        }
    ),
    ```

  - File: `doi_portal/doi_portal/issues/forms.py`
  - Action: Pronaći title widget attrs i dodati `"data-check-spaces": "true"`. Ako title nema explicit widget, dodati ga u `Meta.widgets`.

  - File: `doi_portal/doi_portal/publications/forms.py`
  - Action: Pronaći title widget attrs i dodati `"data-check-spaces": "true"`.

- [ ] **Task 10: Backend free_to_read konzistentnost validacija**
  - File: `doi_portal/doi_portal/crossref/services.py`
  - Action: Dodati novi metod u PreValidationService klasu (posle `_validate_author`, oko linije 857):
    ```python
    def _validate_free_to_read_consistency(
        self, issue: Issue, published_articles: QuerySet
    ) -> ValidationResult:
        """
        Validate free_to_read field consistency across articles in an issue.

        Warns if some (but not all) articles have free_to_read=True,
        indicating potential inconsistency.
        """
        result = ValidationResult()
        total = published_articles.count()

        if total <= 1:
            return result

        free_count = published_articles.filter(free_to_read=True).count()

        if 0 < free_count < total:
            result.add_warning(
                message=(
                    f"{total - free_count} od {total} artikala nema označeno "
                    f"'Slobodan pristup' — da li je to namerno?"
                ),
                field_name="free_to_read",
            )
        return result
    ```
  - Action: U `validate_issue()` metodu (linije 499-538), POSLE for-petlje koja iterira artikle, dodati poziv. Potrebno je prvo sačuvati queryset u varijablu. Ažurirati `validate_issue()`:
    ```python
    # Pronađi postojeću liniju (oko linije 529):
    #   for article in issue.articles.filter(status=ArticleStatus.PUBLISHED, is_deleted=False):
    # Zameni sa:
    published_articles = issue.articles.filter(
        status=ArticleStatus.PUBLISHED, is_deleted=False
    )
    for article in published_articles:
        # ... postojeći kod za _validate_article() ...

    # Posle for petlje, dodaj:
    result.merge(self._validate_free_to_read_consistency(issue, published_articles))
    ```
  - Notes: Ovo je WARNING, ne ERROR. Ne blokira XML generisanje. `published_articles` queryset se evaluira dva puta (jednom u for petlji, jednom u count), ali je to prihvatljivo jer su u pitanju mali skupovi podataka. Alternativno, evaluirati u listu ako je performans bitan.

- [ ] **Task 11: Testovi za free_to_read validaciju**
  - File: `doi_portal/doi_portal/crossref/tests/test_validation.py`
  - Action: Dodati novu test klasu `TestPreValidationServiceFreeToRead` prateći pattern iz `TestPreValidationServiceJournal`:
    ```python
    class TestPreValidationServiceFreeToRead:
        """Tests for free_to_read consistency validation."""

        def test_all_free_to_read_no_warning(self):
            """No warning when all articles have free_to_read=True."""
            # Kreirati issue sa 3 artikla, svi free_to_read=True
            # Pozvati validate_issue()
            # Assert: result.has_warnings() is False za free_to_read

        def test_none_free_to_read_no_warning(self):
            """No warning when no articles have free_to_read."""
            # Kreirati issue sa 3 artikla, svi free_to_read=False
            # Assert: nema free_to_read warninga

        def test_mixed_free_to_read_shows_warning(self):
            """Warning when some articles have free_to_read and some don't."""
            # Kreirati issue sa 5 artikala: 3 free_to_read=True, 2 False
            # Assert: warning postoji, poruka sadrži "2 od 5"

        def test_single_article_no_warning(self):
            """No warning with single article (can't have inconsistency)."""
            # Kreirati issue sa 1 artiklom
            # Assert: nema free_to_read warninga

        def test_no_published_articles_no_warning(self):
            """No warning when issue has no published articles."""
            # Kreirati issue sa artiklima u DRAFT statusu
            # Assert: nema free_to_read warninga
    ```
  - Notes: Koristiti iste factory fixture-e kao ostali testovi u fajlu. Proveriti koji factory se koristi (npr. `IssueFactory`, `ArticleFactory`) i pratiti isti pattern.

### Acceptance Criteria

- [ ] **AC 1:** Given publikacija tipa CONFERENCE i filtriran issue list (`?publication=<id>`), when korisnik otvori issue list stranicu, then naslov je "Zbornici radova" (ne "Izdanja"), dugme je "Novi zbornik radova" (ne "Novo izdanje"), i empty state je "Dodaj prvi zbornik" (ne "Dodaj prvo izdanje").

- [ ] **AC 2:** Given publikacija tipa BOOK i filtriran article list (`?issue=<id>`), when korisnik otvori article list za issue te publikacije, then naslov je "Poglavlja" (ne "Članci"), dugme je "Novo poglavlje" (ne "Novi članak").

- [ ] **AC 3:** Given publikacija tipa JOURNAL, when korisnik kreira article, then messages.success prikazuje "Članak uspešno kreiran." (generički termin, bez promene), form_title je "Novi članak", submit_text je "Kreiraj članak".

- [ ] **AC 4:** Given publikacija tipa CONFERENCE, when korisnik kreira article (sa `?issue=<conference_issue_id>`), then form_title je "Novi rad", submit_text je "Kreiraj rad", i messages.success prikazuje "Rad uspešno kreiran.".

- [ ] **AC 5:** Given publikacija tipa BOOK, when korisnik obriše article, then confirmation dialog koristi "Obriši poglavlje" (ne "Obriši članak").

- [ ] **AC 6:** Given portal issue detail za CONFERENCE publikaciju, when korisnik vidi listu sadržaja, then sekcija se zove "Radovi" (ne "Članci") i empty state je kontekstualan.

- [ ] **AC 7:** Given portal publication detail za BOOK, when korisnik vidi listu izdanja, then sekcija heading je "Tomovi" (ne "Izdanja") i article count badge koristi kontekstualnu infleksiju ("2 poglavlja" umesto "2 članka"). Count badge sa inflektiranim tekstom postoji u `portal/publications/publication_detail.html` — inline infleksija (`{% if ... %}članak{% elif ... %}`) se zamenjuje sa `{% article_count_label %}` template tag-om.

- [ ] **AC 8:** Given korisnik kuca naslov sa duplim razmacima ("Naslov  sa  razmacima"), when input event se okinuti na title polju article forme (koje ima `data-check-spaces="true"` atribut setovan u forms.py), then žuto upozorenje se prikazuje ispod polja sa tekstom "Naslov sadrži duple razmake" i "Ispravi" dugmetom.

- [ ] **AC 9:** Given korisnik klikne "Ispravi" dugme na double-space warningu, when dugme se klikne, then dupli razmaci su zamenjeni jednim razmakom u input polju i warning nestaje.

- [ ] **AC 10:** Given issue sa 5 PUBLISHED artikala gde 3 imaju free_to_read=True i 2 nemaju, when PreValidationService.validate_issue() se pokrene, then ValidationResult sadrži warning: "2 od 5 artikala nema označeno 'Slobodan pristup' — da li je to namerno?"

- [ ] **AC 11:** Given issue gde svi artikli imaju free_to_read=True (ili svi nemaju), when PreValidationService.validate_issue() se pokrene, then nema free_to_read warninga. Isto važi za issue sa 0 ili 1 PUBLISHED artiklom.

- [ ] **AC 12:** Given publikacija tipa OTHER, when korisnik koristi bilo koji deo admin interfejsa, then svi termini su generički (Izdanje, Članak) — identični kao za JOURNAL.

- [ ] **AC 13:** Given nefiltriran article list (bez `?issue=` query param-a), when korisnik otvori globalnu listu članaka, then naslov je generički "Članci" (JOURNAL default), jer lista prikazuje mešovite tipove publikacija.

## Additional Context

### Dependencies

- Nema novih pip zavisnosti. Koristi postojeći Django template tag sistem, vanilla JavaScript, i PreValidationService infrastrukturu.
- Task 4-7 zavise od Task 1-2 (terminološki sistem mora biti kreiran pre nego što se view-ovi i template-ovi ažuriraju).
- Task 8 je proširenje Task 1 — dodaje dodatne ključeve identifikovane tokom portal template analize.
- Task 9 (JS dupli razmaci) je nezavisan od terminologije.
- Task 10-11 (free_to_read) su nezavisni od terminologije.

### Testing Strategy

**Unit testovi:**
- `core/tests/test_terminology.py` — testira `get_term()`, `get_article_count_label()`, `get_issue_delete_warning()` za sve tipove i ključeve, uključujući fallback ponašanje
- `crossref/tests/test_validation.py` — dodaje `TestPreValidationServiceFreeToRead` klasu sa 5 test metoda

**Manualno testiranje:**
- Kreirati po jednu publikaciju svakog tipa (JOURNAL, CONFERENCE, BOOK, OTHER)
- Za svaku: kreirati issue, dodati article, proveriti sve stranice (list, detail, form, delete)
- Proveriti breadcrumbs, naslove, dugmad, poruke posle CRUD operacija
- Proveriti portal stranice za svaki tip
- **Testirati unfiltered liste:** otvoriti article list i issue list BEZ query param filtera — treba da prikažu generičke termine
- **Testirati CreateView sa query param-om:** otvoriti article create sa `?issue=<id>` gde je issue iz conference publikacije — treba da prikaže "Novi rad"
- Testirati double-space warning na title poljima (article, issue, publication forme)
- Testirati free_to_read warning: kreirati issue sa mešovitim free_to_read vrednostima, pokrenuti XML validaciju

**Edge cases:**
- Publication bez issue-ova (empty state terminologija)
- Issue bez artikala
- Article gde publication_type nije setovan (fallback na JOURNAL)
- CreateView bez query param-a (fallback na JOURNAL)
- Unfiltered ListView (mešoviti tipovi — generički termini)
- Title sa samo jednim razmakom (ne treba da triggeruje warning)
- Title sa razmakom na početku/kraju (ne triggeruje double-space)
- Issue sa jednim artiklom (nema free_to_read inconsistency moguće)
- Issue sa 0 published artikala (nema warninga)

### Notes

- Ukupno ~170+ hardkodiranih stringova u template-ima za ažuriranje
- ~18 hardkodiranih poruka i context varijabli u views.py (8 messages + breadcrumbs/form_title/submit_text u article views, 4 messages + context u issue views)
- PreValidationService ima 1138 linija testova — novi test treba da prati isti pattern
- Portal search, home, i about stranice ostaju sa generičkim terminima
- Srpska gramatika zahteva posebnu pažnju na rod: "Poglavlje" (srednji) vs "Članak"/"Rad"/"Zbornik"/"Tom" (muški)
- BOOK tip koristi samo "Tom" (ne "Tom/Edicija") radi gramatičke konzistentnosti
- `data-check-spaces` atribut se dodaje u forms.py widget attrs, ne u template HTML
- `project.js` je već uključen u `admin_base.html` (linija 48)
- Breadcrumbs se ažuriraju u view-ovima (get_context_data), ne u _breadcrumbs.html template-u

### Adversarial Review Fixes Applied

- **F1 (Critical):** Dodat detaljan opis tri scenarija za pub_type (DetailView, CreateView, ListView) sa concrete code examples. ListView koristi JOURNAL default kad nije filtriran. CreateView izvlači pub_type iz query param entity-ja. Dodat AC 13 za nefiltriran ListView.
- **F2 (High):** Dodat `issue_has_articles_warning` ključ u terminološku mapu i `get_issue_delete_warning()` funkcija u Task 1. Task 5 sada koristi ovu funkciju.
- **F3 (High):** Task 10 sada eksplicitno pokazuje kako izvući `published_articles` queryset u validate_issue() pre for petlje, i prosleđuje ga kao argument.
- **F4 (High):** Task 4 i 5 sada koriste helper funkcije `_get_pub_type_from_issue_id()` i `_get_pub_type_from_publication_id()` za CreateView-ove, sa fallback na JOURNAL.
- **F5 (Medium):** BOOK terminologija promenjena sa "Tom/Edicija" na samo "Tom" svuda. Objašnjenje u Technical Decisions.
- **F6 (Medium):** Potvrđeno da je project.js uključen u admin_base.html (linija 48). data-check-spaces se dodaje u forms.py widget attrs (Task 9), ne u template.
- **F7 (Medium):** Task 4 i 5 sada eksplicitno pokrivaju SVE hardkodirane stringove u get_context_data(): breadcrumbs labele, form_title, submit_text. Ukupan broj ažuriran na ~18.
- **F8 (Low):** Uklonjena obmanjujuća referenca na menu_tags.py konvenciju. Task 2 sada prikazuje standalone code example.
- **F9 (Low):** AC 7 sada precizira da se count badge sa inflektiranim tekstom nalazi u `portal/publications/publication_detail.html` i da se inline infleksija zamenjuje sa `{% article_count_label %}` template tag-om.
