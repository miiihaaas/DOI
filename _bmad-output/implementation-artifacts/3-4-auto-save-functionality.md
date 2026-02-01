# Story 3.4: Auto-Save Functionality

Status: done

## Story

As a **Bibliotekar**,
I want **my changes to be automatically saved while editing an article**,
So that **I never lose my work even if I forget to click save or my browser crashes**.

## Background

Ovo je cetvrta prica u Epiku 3 (Article Workflow). Implementira auto-save funkcionalnost za article edit formu koristeci HTMX `hx-trigger="change delay:2s"` pattern. Postojeca article_form.html koristi standardnu `<form method="post">` sa rucnim submit-om. Ova prica dodaje: auto-save HTMX endpoint, save indicator UI komponentu, unsaved changes detection, i retry logiku pri gresci.

**FR Pokrivenost:** FR27 (Sistem automatski cuva izmene - auto-save)

**Zavisnosti (sve DONE):**
- Story 3.1: Article Model & Basic Metadata Entry - Article model, ArticleForm, article_form.html, ArticleUpdateView
- Story 3.2: Author Management - article_form.html sa edit mode sekcijama, HTMX pattern, Alpine.js integracija
- Story 3.3: PDF Upload - PDF sekcija u article_form.html, HTMX FBV pattern, CSRF token handling

**Blokira:**
- Story 3.5: Submit Article for Review - Bibliotekar mora biti siguran da su sve izmene sacuvane pre submit-a

## Acceptance Criteria

1. **Given** Bibliotekar edituje clanak (edit mode)
   **When** bilo koja vrednost polja se promeni (title, subtitle, abstract, keywords, doi_suffix, first_page, last_page, article_number, language, publication_type, license_url, license_applies_to, free_to_read, free_to_read_start_date)
   **Then** auto-save se aktivira nakon 2 sekunde debounce-a
   **And** HTMX salje parcijalne podatke forme na auto-save endpoint

2. **Given** auto-save je u toku
   **When** HTMX request je poslat
   **Then** save indikator prikazuje "Cuvanje..." sa spinner-om
   **And** indikator je uvek vidljiv u header-u article forme

3. **Given** auto-save se zavrsi uspesno
   **When** server odgovori sa success
   **Then** indikator prikazuje "Sacuvano pre X sekundi"
   **And** timestamp se azurira svaki minut (relativno vreme)
   **And** indikator prikazuje zelenu ikonu checkmark

4. **Given** auto-save ne uspe
   **When** server vrati gresku
   **Then** indikator prikazuje "Cuvanje neuspesno - ponovni pokusaj..."
   **And** retry se pokusava nakon 5 sekundi
   **And** nakon 3 neuspesna pokusaja, korisnik se upozorava sa alert porukom

5. **Given** Bibliotekar napusta stranicu sa nesacuvanim promenama
   **When** navigira na drugu stranicu
   **Then** browser prikazuje confirmation dialog ("Imate nesacuvane promene...")

6. **Given** Bibliotekar se vrati na draft clanak
   **When** otvori edit stranicu
   **Then** svi prethodno sacuvani podaci su ucitani
   **And** poslednji timestamp sacuvanog stanja je prikazan

7. **Given** auto-save forma sadrzi validacione greske
   **When** server validira podatke
   **Then** polja sa greskama se NE cuvaju
   **And** validna polja se cuvaju normalno (parcijalni save)
   **And** indikator prikazuje "Sacuvano (neka polja imaju greske)"

8. **Given** vise promena se desava brzo uzastopno
   **When** korisnik kuca u vise polja
   **Then** debounce osigurava samo jedan request nakon 2s pauze
   **And** poslednja verzija svih polja se salje

9. **Given** manual Save dugme je kliknuto
   **When** korisnik eksplicitno klikne "Sacuvaj izmene"
   **Then** standardni form submit se izvrsava (postojeci ArticleUpdateView)
   **And** auto-save se pauzira tokom manual submit-a
   **And** full page validation se izvrsava (ukljucujuci required polja)

10. **Given** auto-save endpoint primi request
    **When** podatke obradjuje server
    **Then** samo polja koja su PROMENJENA se azuriraju (parcijalni update)
    **And** `updated_at` timestamp se azurira
    **And** auditlog belezi promenu

## Tasks / Subtasks

- [x] Task 1: Kreirati auto-save HTMX FBV endpoint (AC: #1, #2, #3, #4, #7, #10)
  - [x] 1.1 U `articles/views.py` dodati `article_autosave(request, pk)` FBV (POST)
  - [x] 1.2 Koristiti `_check_article_permission()` za publisher scoping
  - [x] 1.3 Prihvatiti parcijalne form podatke (ne zahtevati sva required polja)
  - [x] 1.4 Validirati samo polja koja su prisutna u POST data
  - [x] 1.5 Sacuvati validna polja koristeci `update_fields` za efikasnost
  - [x] 1.6 Vratiti HTML fragment sa save statusom (timestamp, uspeh/greska)
  - [x] 1.7 Ograniciti auto-save samo na DRAFT status (ne dozvoliti za REVIEW, PUBLISHED itd.)
  - [x] 1.8 Obraditi `keywords` JSON polje iz hidden input-a

- [x] Task 2: Kreirati save indicator HTMX partial template (AC: #2, #3, #4, #7)
  - [x] 2.1 Kreirati `templates/articles/partials/_save_indicator.html`
  - [x] 2.2 Prikazati stanja: idle, saving, saved (sa timestamp), error, partial_error
  - [x] 2.3 Koristiti Bootstrap 5 badge/alert za stilizovanje
  - [x] 2.4 Prikazati relativno vreme ("pre X sekundi", "pre X minuta")
  - [x] 2.5 Ukljuciti ikone: spinner (saving), checkmark (saved), warning (error)

- [x] Task 3: Azurirati article_form.html za auto-save (AC: #1, #2, #5, #8, #9)
  - [x] 3.1 Dodati `hx-post` atribut na glavnu article formu za auto-save endpoint
  - [x] 3.2 Dodati `hx-trigger="change delay:2s"` na formu
  - [x] 3.3 Dodati `hx-target="#save-indicator"` za indikator zonu
  - [x] 3.4 Dodati `hx-swap="innerHTML"` za zamenu indikatora
  - [x] 3.5 Dodati save indicator `<div id="save-indicator">` u card header
  - [x] 3.6 Dodati `hx-include` ili form scope da ukljuci sva relevantna polja
  - [x] 3.7 NE menjati postojeci `<form method="post">` za manual submit - dodati auto-save kao ODVOJENI mehanizam
  - [x] 3.8 Dodati `beforeunload` event listener za unsaved changes detection (Alpine.js)

- [x] Task 4: Implementirati retry logiku na klijentu (AC: #4)
  - [x] 4.1 Koristiti Alpine.js komponentu za tracking retry stanja
  - [x] 4.2 Na HTMX `htmx:afterRequest` event, proveriti status
  - [x] 4.3 Na gresku, sacekati 5s i ponoviti (max 3 pokusaja)
  - [x] 4.4 Nakon 3 neuspeha, prikazati alert banner
  - [x] 4.5 Na uspeh resetovati retry counter

- [x] Task 5: Dodati URL route za auto-save endpoint (AC: #1)
  - [x] 5.1 U `articles/urls.py` dodati:
    - `<int:pk>/autosave/` (name: article-autosave) - POST

- [x] Task 6: Kreirati testove (AC: #1-#10)
  - [x] 6.1 View testovi: article_autosave sa validnim podacima (parcijalni update)
  - [x] 6.2 View testovi: article_autosave sa invalid podacima (parcijalni save validnih polja)
  - [x] 6.3 View testovi: article_autosave sa ne-DRAFT statusom (odbijanje)
  - [x] 6.4 Permission testovi: publisher scoping za auto-save endpoint
  - [x] 6.5 View testovi: article_autosave sa keywords JSON parsing
  - [x] 6.6 View testovi: HTMX header provera (`HX-Request`)
  - [x] 6.7 Template testovi: save indicator response content
  - [x] 6.8 Koristiti Factory Boy, pytest-django iz postojeceg test setup-a

## Dev Notes

### KRITICNO: Auto-Save Arhitekturni Pattern

Auto-save koristi **dvojnu formu** pristup:

1. **Postojeca forma** (`<form method="post">`) - ostaje za manual "Sacuvaj izmene" submit sa full page validation
2. **HTMX auto-save** - NOVI mehanizam koji salje parcijalne podatke na dedicated endpoint BEZ full page reload-a

Ovo znaci da article_form.html ima DVA nacina cuvanja:
- Manual: standardni POST na `ArticleUpdateView` (full validation, page reload, success message)
- Auto: HTMX POST na `article_autosave` FBV (parcijalna validacija, fragment response, no page reload)

### Auto-Save Endpoint Implementacija

```python
# articles/views.py - DODATI

@login_required
@require_POST
def article_autosave(request, pk):
    """
    Auto-save article fields via HTMX POST.

    Accepts partial form data - only saves fields that are present in POST.
    Does NOT require all required fields (unlike full form submit).
    Only works for DRAFT articles.
    Returns save indicator HTML fragment.
    """
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=pk,
    )
    _check_article_permission(request.user, article)

    # Only allow auto-save for DRAFT articles
    if article.status != ArticleStatus.DRAFT:
        return render(request, "articles/partials/_save_indicator.html", {
            "status": "error",
            "message": "Auto-save je moguc samo za clanke u statusu Nacrt.",
        })

    # Collect fields to update
    update_fields = []
    errors = []

    # Text fields - direct assignment
    text_fields = [
        "title", "subtitle", "abstract", "doi_suffix",
        "first_page", "last_page", "article_number", "language",
        "publication_type", "license_url", "license_applies_to",
    ]
    for field_name in text_fields:
        if field_name in request.POST:
            value = request.POST[field_name]
            setattr(article, field_name, value)
            update_fields.append(field_name)

    # Boolean field
    if "free_to_read" in request.POST:
        article.free_to_read = request.POST.get("free_to_read") in ("on", "true", "True", "1")
        update_fields.append("free_to_read")
    elif any(k for k in request.POST if k != "csrfmiddlewaretoken"):
        # Checkbox not present means unchecked (only if other fields submitted)
        article.free_to_read = False
        update_fields.append("free_to_read")

    # Date field
    if "free_to_read_start_date" in request.POST:
        date_val = request.POST["free_to_read_start_date"]
        if date_val:
            try:
                from datetime import date
                article.free_to_read_start_date = date.fromisoformat(date_val)
                update_fields.append("free_to_read_start_date")
            except (ValueError, TypeError):
                errors.append("Nevazeci format datuma.")
        else:
            article.free_to_read_start_date = None
            update_fields.append("free_to_read_start_date")

    # Keywords JSON field
    if "keywords" in request.POST:
        import json
        raw = request.POST["keywords"]
        try:
            keywords = json.loads(raw) if raw else []
            if isinstance(keywords, list):
                article.keywords = [kw.strip() for kw in keywords if isinstance(kw, str) and kw.strip()]
                update_fields.append("keywords")
        except (json.JSONDecodeError, TypeError):
            pass  # Ignore invalid JSON, keep existing keywords

    # Issue field - only if present (prevents accidental change)
    if "issue" in request.POST:
        issue_id = request.POST["issue"]
        if issue_id:
            try:
                from doi_portal.issues.models import Issue
                issue = Issue.objects.get(pk=int(issue_id))
                article.issue = issue
                update_fields.append("issue")
            except (Issue.DoesNotExist, ValueError, TypeError):
                errors.append("Nevazece izdanje.")

    # Save if we have fields to update
    if update_fields:
        article.save(update_fields=update_fields)

    status = "saved" if not errors else "partial_error"
    return render(request, "articles/partials/_save_indicator.html", {
        "status": status,
        "errors": errors,
        "saved_at": article.updated_at,
    })
```

### Save Indicator Template

```html
<!-- templates/articles/partials/_save_indicator.html -->
<div id="save-indicator">
    {% if status == "saving" %}
    <span class="badge bg-secondary">
        <span class="spinner-border spinner-border-sm me-1" role="status"></span>
        Cuvanje...
    </span>
    {% elif status == "saved" %}
    <span class="badge bg-success" x-data="relativeTime('{{ saved_at|date:'c' }}')" x-text="display">
        <i class="bi bi-check-lg me-1"></i>Sacuvano
    </span>
    {% elif status == "partial_error" %}
    <span class="badge bg-warning text-dark">
        <i class="bi bi-exclamation-triangle me-1"></i>Sacuvano (neka polja imaju greske)
    </span>
    {% elif status == "error" %}
    <span class="badge bg-danger">
        <i class="bi bi-x-circle me-1"></i>{{ message|default:"Cuvanje neuspesno" }}
    </span>
    {% else %}
    <!-- Idle state - no save yet -->
    {% endif %}
</div>
```

### article_form.html - Auto-Save Integracija

Kljucna izmena: Dodati auto-save HTMX atribute na POSTOJECU formu, NE kreirati novu formu.

```html
<!-- Izmena u article_form.html - EDIT MODE ONLY -->
{% if is_edit %}
<form method="post" novalidate
      hx-post="{% url 'articles:article-autosave' pk=object.pk %}"
      hx-trigger="change delay:2s from:input, change delay:2s from:select, change delay:2s from:textarea"
      hx-target="#save-indicator"
      hx-swap="innerHTML"
      hx-indicator="#save-spinner">
{% else %}
<form method="post" novalidate>
{% endif %}
```

VAZNO: `hx-trigger` koristi `change delay:2s` da debounce-uje auto-save. HTMX ce uciniti POST na auto-save endpoint, ali manual submit dugme "Sacuvaj izmene" i dalje koristi standardni form POST na ArticleUpdateView.

Za razdvajanje manual submit-a od HTMX auto-save:
- Manual submit: standardni `<button type="submit">` koji NE ima `hx-post` - Django obradjuje kao regularni POST
- HTMX auto-save: `hx-post` na formi se triggeruje na `change` event, ali NE na `submit` event

HTMX ce ignorisati standardni form submit jer `hx-trigger` je specifican (`change delay:2s`), ne `submit`.

### Save Indicator Pozicija u Header-u

```html
<!-- article_form.html - card header -->
<div class="card-header d-flex justify-content-between align-items-center">
    <h5 class="card-title mb-0">{{ form_title }}</h5>
    {% if is_edit %}
    <div id="save-indicator">
        <!-- Auto-save indicator will be injected here by HTMX -->
    </div>
    {% endif %}
</div>
```

### Alpine.js Unsaved Changes Detection

```javascript
// U article_form.html inline_javascript block - DODATI
function autosaveManager() {
    return {
        hasUnsavedChanges: false,
        retryCount: 0,
        maxRetries: 3,
        init() {
            // Track form changes
            const form = this.$el;
            form.addEventListener('change', () => {
                this.hasUnsavedChanges = true;
            });

            // Listen for successful auto-save
            document.body.addEventListener('htmx:afterRequest', (evt) => {
                if (evt.detail.elt === form && evt.detail.successful) {
                    this.hasUnsavedChanges = false;
                    this.retryCount = 0;
                }
            });

            // Listen for failed auto-save
            document.body.addEventListener('htmx:responseError', (evt) => {
                if (evt.detail.elt === form) {
                    this.retryCount++;
                    if (this.retryCount < this.maxRetries) {
                        setTimeout(() => {
                            htmx.trigger(form, 'change');
                        }, 5000);
                    }
                }
            });

            // Warn before leaving with unsaved changes
            window.addEventListener('beforeunload', (e) => {
                if (this.hasUnsavedChanges) {
                    e.preventDefault();
                    e.returnValue = '';
                }
            });
        }
    }
}

// Relative time display for save indicator
function relativeTime(isoString) {
    return {
        display: '',
        init() {
            this.update();
            setInterval(() => this.update(), 60000); // Update every minute
        },
        update() {
            const saved = new Date(isoString);
            const now = new Date();
            const diff = Math.floor((now - saved) / 1000);
            if (diff < 5) {
                this.display = 'Upravo sacuvano';
            } else if (diff < 60) {
                this.display = `Sacuvano pre ${diff} sek`;
            } else if (diff < 3600) {
                const mins = Math.floor(diff / 60);
                this.display = `Sacuvano pre ${mins} min`;
            } else {
                const hours = Math.floor(diff / 3600);
                this.display = `Sacuvano pre ${hours}h`;
            }
        }
    }
}
```

### URL Route za Auto-Save

```python
# articles/urls.py - DODATI u urlpatterns

# Auto-save HTMX endpoint (Story 3.4)
path(
    "<int:pk>/autosave/",
    views.article_autosave,
    name="article-autosave",
),
```

### HTMX hx-trigger Pattern (KRITICNO)

Architecture dokument i project-context.md definisu auto-save pattern:

```html
<form hx-post="{% url 'article-autosave' pk=article.pk %}"
      hx-trigger="change delay:2s"
      hx-target="#save-indicator">
```

Ali za nasu formu, trebamo specificirate:
- `change delay:2s from:input` - za text input, date, checkbox polja
- `change delay:2s from:select` - za dropdown polja (issue, publication_type, license_applies_to)
- `change delay:2s from:textarea` - za abstract textarea

Alpine.js `keywordsInput()` koristi hidden `<input type="hidden" name="keywords">` koji se azurira Alpine.js-om. Taj hidden input NE emituje `change` event automatski. Resenje: nakon `addKeyword()` i `removeKeyword()`, eksplicitno emitovati `change` event na hidden input:

```javascript
// Azurirati keywordsInput() - dodati trigger
addKeyword() {
    const trimmed = this.newKeyword.trim();
    if (trimmed && !this.keywords.includes(trimmed)) {
        this.keywords.push(trimmed);
        // Trigger auto-save
        this.$nextTick(() => {
            const hidden = document.querySelector('input[name="keywords"]');
            if (hidden) hidden.dispatchEvent(new Event('change', { bubbles: true }));
        });
    }
    this.newKeyword = '';
},
removeKeyword(index) {
    this.keywords.splice(index, 1);
    this.$nextTick(() => {
        const hidden = document.querySelector('input[name="keywords"]');
        if (hidden) hidden.dispatchEvent(new Event('change', { bubbles: true }));
    });
}
```

### HTMX i Manual Submit Razdvajanje

Problem: Ista `<form>` ima i `hx-post` (auto-save) i `method="post"` (manual submit). Kako spreciti da HTMX preuzme manual submit?

Resenje: HTMX `hx-trigger="change delay:2s"` nece se aktivirati na `submit` event. Kada korisnik klikne "Sacuvaj izmene", browser salje standardni form POST (full page reload). HTMX auto-save se aktivira SAMO na `change` event.

ALI - moramo dodati `hx-disinherit="*"` na submit dugme da HTMX ne interferira:

```html
<button type="submit" class="btn btn-primary" hx-disinherit="*">
    <i class="bi bi-check-lg me-1"></i>{{ submit_text }}
</button>
```

Alternativno, koristiti `hx-disable` na submit dugme. Proveriti HTMX 2.0.8 dokumentaciju za tacan pristup.

### Publisher Scoping za Auto-Save Endpoint

Auto-save endpoint koristi ISTU `_check_article_permission()` helper funkciju koja VEC postoji u `views.py` iz Story 3.2. NE kreirati novi helper.

### Auditlog Integracija

Article model je VEC registrovan sa django-auditlog. Svaki `article.save(update_fields=[...])` automatski kreira LogEntry sa promenama. Auto-save NE zahteva dodatnu auditlog konfiguraciju.

NAPOMENA: Cesti auto-save operacije mogu generisati mnogo audit log zapisa. Ovo je PRIHVATLJIVO jer:
1. Audit log je bitan za compliance (FR49)
2. Korisnik menja polja relativno retko (debounce 2s)
3. `update_fields` ogranicava sta se belezi

### Testovi - Pattern

```python
# articles/tests/test_autosave.py - NOVI FAJL

import json
import pytest
from django.urls import reverse
from django.test import RequestFactory

from doi_portal.articles.models import Article, ArticleStatus


@pytest.mark.django_db
class TestArticleAutosave:
    """Tests for auto-save HTMX endpoint."""

    def test_autosave_updates_title(self, client, bibliotekar_user, draft_article):
        """Auto-save updates title field."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article.pk})
        response = client.post(
            url,
            {"title": "Novi naslov"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article.refresh_from_db()
        assert draft_article.title == "Novi naslov"

    def test_autosave_partial_fields(self, client, bibliotekar_user, draft_article):
        """Auto-save accepts partial form data (only changed fields)."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article.pk})
        original_title = draft_article.title
        response = client.post(
            url,
            {"abstract": "Novi apstrakt"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article.refresh_from_db()
        assert draft_article.abstract == "Novi apstrakt"
        assert draft_article.title == original_title  # Unchanged

    def test_autosave_rejects_non_draft(self, client, bibliotekar_user, review_article):
        """Auto-save is rejected for non-DRAFT articles."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:article-autosave", kwargs={"pk": review_article.pk})
        response = client.post(
            url,
            {"title": "Pokusaj"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert "error" in response.content.decode()

    def test_autosave_keywords_json(self, client, bibliotekar_user, draft_article):
        """Auto-save handles keywords JSON field."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article.pk})
        response = client.post(
            url,
            {"keywords": json.dumps(["django", "python", "doi"])},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article.refresh_from_db()
        assert draft_article.keywords == ["django", "python", "doi"]

    def test_autosave_publisher_scoping(self, client, other_publisher_user, draft_article):
        """Auto-save respects publisher scoping."""
        client.force_login(other_publisher_user)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article.pk})
        response = client.post(
            url,
            {"title": "Hack attempt"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 403
```

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/templates/articles/partials/_save_indicator.html   # Save indicator HTMX partial
doi_portal/doi_portal/articles/tests/test_autosave.py                    # Auto-save testovi
```

### Fajlovi za modifikaciju (POSTOJECI)

- `doi_portal/doi_portal/articles/views.py` - Dodati `article_autosave` FBV
- `doi_portal/doi_portal/articles/urls.py` - Dodati auto-save route
- `doi_portal/doi_portal/templates/articles/article_form.html` - Dodati HTMX auto-save atribute, save indicator, autosaveManager() Alpine.js, relativeTime() Alpine.js, azurirati keywordsInput() za change event dispatch

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

Svi UI tekstovi MORAJU koristiti ispravne srpske dijakritike:

| Kontekst | ISPRAVNO |
|----------|----------|
| Saving state | "Cuvanje..." |
| Saved state | "Sacuvano pre X sekundi" |
| Just saved | "Upravo sacuvano" |
| Saved minutes | "Sacuvano pre X min" |
| Error state | "Cuvanje neuspesno - ponovni pokusaj..." |
| Max retries | "Automatsko cuvanje nije uspelo. Sacuvajte rucno." |
| Partial error | "Sacuvano (neka polja imaju greske)" |
| Draft only | "Auto-save je moguc samo za clanke u statusu Nacrt." |
| Beforeunload | "Imate nesacuvane promene. Da li zelite da napustite stranicu?" |
| Submit button | "Sacuvaj izmene" (vec postoji) |

**NAPOMENA:** U HTML template-ovima KORISTITI ispravne dijakritike:
- "Cuvanje..." -> "Cuvanje..."  (HTMX ce renderovati UTF-8 korektno)
- Ako su template fajlovi vec UTF-8 (jesu - Django default), svi srpski karakteri rade

### Anti-Patterns (ZABRANJENO)

```python
# POGRESNO - Kreirati odvojenu formu za auto-save
<form id="autosave-form" hx-post="...">  # NE! Koristiti ISTU formu

# POGRESNO - Koristiti CBV za auto-save endpoint
class ArticleAutosaveView(UpdateView):  # NE! Koristi FBV

# POGRESNO - Vracati JSON za HTMX response
return JsonResponse({"status": "saved"})  # NE! Vracaj HTML fragment

# POGRESNO - Zahtevati sva required polja u auto-save
form = ArticleForm(request.POST, instance=article)  # NE! Parcijalni save

# POGRESNO - Auto-save bez publisher scoping
def article_autosave(request, pk):
    article = Article.objects.get(pk=pk)  # NE bez permission check!

# POGRESNO - Auto-save za ne-DRAFT clanke
# UVEK proveriti article.status == DRAFT pre save-a

# POGRESNO - Kreirati novu formu umesto azuriranja postojece
# Koristiti hx-trigger na POSTOJECOJ formi

# POGRESNO - Dodavati Alpine.js CDN ponovo
# VEC je ukljucen u article_form.html javascript block

# POGRESNO - Dodavati HTMX CDN ponovo
# VEC je ukljucen u admin_base.html

# POGRESNO - Duplirati CSRF token handling
# VEC postoji htmx:configRequest event listener u article_form.html

# POGRESNO - Menjati ArticleUpdateView za auto-save
# ArticleUpdateView ostaje NEPROMENJEN za manual save
```

### Previous Story Learnings (Story 3.1, 3.2, 3.3)

1. **`_check_article_permission()`** - VEC postoji u views.py. Koristi za auto-save endpoint.
2. **HTMX CSRF token** - VEC reseno u article_form.html (`htmx:configRequest` event listener). NE duplirati.
3. **Alpine.js CDN** - VEC ukljucen u article_form.html `javascript` block. NE duplirati.
4. **`select_related` chain** - Uvek ukljuciti `"issue", "issue__publication", "issue__publication__publisher"` za publisher scoping.
5. **FBV pattern** - Svi HTMX endpoint-i koriste FBV-ove sa `@login_required` i `@require_POST`.
6. **Template include pattern** - `{% include %}` sa `with` za prosledjivanje context-a.
7. **PdfUpload Alpine.js** - `pdfUpload()` i `authorList()` VEC postoje. NE konflikta sa novim `autosaveManager()`.
8. **SortableJS + htmx:afterSwap** - VEC postoji. Auto-save NE sme da interferira sa author drag & drop.
9. **auditlog** - Article je VEC registrovan. Auto-save promene se automatski beleze.
10. **HTMX hx-swap** - Standardni pattern je `innerHTML` za fragment zamenu.
11. **Test pattern** - Factory Boy, pytest-django, `CELERY_TASK_ALWAYS_EAGER=True` u test settings.
12. **Existing ArticleForm** - NE koristiti ArticleForm za auto-save (zahteva required polja). Koristiti direktni field assignment.

### Git Commit Pattern

```
story-3-4: feat(articles): implementiraj Auto-Save funkcionalnost sa HTMX debounced triggerom i save indikatorom (Story 3.4)
```

### NFR Requirements

- **FR27:** Sistem automatski cuva izmene (auto-save) - HTMX `change delay:2s` na article edit formi
- **NFR3:** Admin panel stranice < 5 sekundi - auto-save fragment response je minimalan (badge HTML)
- UX zahtev: "Nikad ne gubim rad" - auto-save kao default, ne feature
- UX zahtev: "Sacuvano pre X sekundi" uvek vidljiv u header-u forme
- UX zahtev: Auto-save na svakom blur/pause (debounced 2s)

### Dependencies (Python/Django)

Nema novih Python zavisnosti! Sve je vec instalirano:
- Django 5.2+ (form handling, views)
- HTMX 2.0.8 (CDN - vec u admin_base.html)
- Alpine.js 3.15.3 (CDN - vec u article_form.html)
- Bootstrap 5 (CSS framework - vec u admin_base.html)
- django-auditlog (automatic logging - vec registrovan)

### Project Structure Notes

- Auto-save FBV ide u `doi_portal/doi_portal/articles/views.py` (uz ostale HTMX FBV-ove)
- Save indicator partial ide u `doi_portal/doi_portal/templates/articles/partials/_save_indicator.html`
- Auto-save testovi idu u `doi_portal/doi_portal/articles/tests/test_autosave.py`
- URL route ostaje u `articles` namespace
- NE kreirati services.py za ovu pricu - auto-save je jednostavan view-level feature
- NE kreirati novi Django app - sve ide u postojeci `articles` app

### Editable Fields za Auto-Save

Kompletna lista polja koja auto-save endpoint prihvata (iz ArticleForm.Meta.fields):

| Polje | Tip | Napomena |
|-------|-----|----------|
| `issue` | FK (select) | Promeni se retko, ali treba podrzati |
| `title` | CharField (text) | Najcesci auto-save trigger |
| `subtitle` | CharField (text) | |
| `abstract` | TextField (textarea) | |
| `keywords` | JSONField (hidden) | JSON string iz Alpine.js |
| `doi_suffix` | CharField (text) | |
| `first_page` | CharField (text) | |
| `last_page` | CharField (text) | |
| `article_number` | CharField (text) | |
| `language` | CharField (text) | |
| `publication_type` | CharField (select) | |
| `license_url` | URLField (text) | |
| `license_applies_to` | CharField (select) | |
| `free_to_read` | BooleanField (checkbox) | |
| `free_to_read_start_date` | DateField (date) | |

NE ukljuciti u auto-save: `status`, `created_by`, `pdf_file`, `pdf_status`, `is_deleted` - ova polja se menjaju kroz druge workflow-e.

### References

- [Source: epics.md#Story 3.4: Auto-Save Functionality]
- [Source: prd.md#5. Article Management - FR27 (Auto-save)]
- [Source: architecture.md#HTMX Use Cases - Auto-save forme]
- [Source: architecture.md#HTMX Patterns - Auto-save Pattern]
- [Source: project-context.md#HTMX Pravila - Auto-save pattern]
- [Source: project-context.md#Naming Konvencije]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri]
- [Source: ux-design-specification.md#Auto-save Indicator - States: Saved, Saving, Error]
- [Source: ux-design-specification.md#Effortless Interactions - Auto-save bez razmisljanja]
- [Source: ux-design-specification.md#Experience Principles - "Nikad ne gubim rad"]
- [Source: ux-design-specification.md#Form Patterns - Auto-save: debounced 2s, indicator uvek vidljiv]
- [Source: 3-3-pdf-upload-with-virus-scanning.md - HTMX FBV patterns, publisher scoping, CSRF handling]
- [Source: 3-2-author-management-with-drag-drop.md - article_form.html structure, Alpine.js patterns]
- [Source: 3-1-article-model-basic-metadata-entry.md - ArticleForm, ArticleUpdateView, article_form.html]
- [Source: articles/views.py - _check_article_permission helper, existing FBV patterns]
- [Source: articles/forms.py - ArticleForm fields and validation]
- [Source: articles/models.py - Article model, ArticleStatus enum, field definitions]
- [Source: articles/urls.py - Existing URL patterns and namespace]
- [Source: templates/articles/article_form.html - Current form structure, Alpine.js components]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 39 auto-save tests pass on first run
- Full article test suite: 270 tests pass, 0 failures
- TDD approach: tests written first, then implementation

### Completion Notes List

- Task 1: article_autosave FBV with partial field updates, DRAFT-only restriction, publisher scoping, keywords JSON, date handling, boolean checkbox handling, update_fields for efficiency
- Task 2: _save_indicator.html with 5 states (idle, saving, saved, partial_error, error), Bootstrap 5 badges, relativeTime Alpine.js
- Task 3: article_form.html updated with hx-post, hx-trigger (change delay:2s from:input/select/textarea), hx-target, save indicator div in card header, hx-disinherit on submit button
- Task 4: autosaveManager() Alpine.js component with hasUnsavedChanges tracking, retry logic (max 3, 5s delay), beforeunload handler, htmx:afterRequest/responseError listeners
- Task 5: URL route <int:pk>/autosave/ with name article-autosave
- Task 6: 39 comprehensive tests across 10 test classes covering all ACs
- keywordsInput() updated to dispatch change events for auto-save trigger

### File List

#### New Files
- `doi_portal/doi_portal/articles/tests/test_autosave.py` - 39 auto-save tests
- `doi_portal/doi_portal/templates/articles/partials/_save_indicator.html` - Save indicator HTMX partial

#### Modified Files
- `doi_portal/doi_portal/articles/views.py` - Added article_autosave FBV
- `doi_portal/doi_portal/articles/urls.py` - Added auto-save URL route
- `doi_portal/doi_portal/templates/articles/article_form.html` - HTMX auto-save integration, Alpine.js components
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Status update
- `_bmad-output/implementation-artifacts/3-4-auto-save-functionality.md` - Task checkboxes, dev record
