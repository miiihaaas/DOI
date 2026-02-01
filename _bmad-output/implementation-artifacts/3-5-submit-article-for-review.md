# Story 3.5: Submit Article for Review

Status: done

## Story

As a **Bibliotekar**,
I want **to submit my completed article for editorial review**,
So that **an Urednik can verify the content before publication**.

## Background

Ovo je peta prica u Epiku 3 (Article Workflow). Implementira "Submit for Review" workflow tranziciju - kljucnu tacku u article lifecycle-u. Bibliotekar zavrsava unos clanka (metapodaci, autori, PDF) i salje ga Uredniku na pregled. Sistem validira da su sva obavezna polja popunjena pre tranzicije DRAFT -> REVIEW. Nakon submit-a, clanak prelazi u read-only stanje za Bibliotekara.

**FR Pokrivenost:** FR29 (Urednik moze pregledati clanak za odobrenje - preduslov: Bibliotekar mora moci da posalje clanak na pregled)

**Zavisnosti (sve DONE):**
- Story 3.1: Article Model & Basic Metadata Entry - Article model, ArticleStatus enum, ArticleForm, article_form.html, ArticleDetailView, ArticleUpdateView
- Story 3.2: Author Management - Author/Affiliation modeli, HTMX author CRUD, `_check_article_permission()`, author_count
- Story 3.3: PDF Upload - pdf_file, pdf_status, PdfStatus enum, virus scanning
- Story 3.4: Auto-Save Functionality - auto-save endpoint, save indicator, `article_autosave` FBV

**Blokira:**
- Story 3.6: Editorial Review Process - Urednik mora videti clanke u REVIEW statusu
- Story 3.7: Article Publishing & Withdrawal - zavisi od kompletnog status workflow-a
- Story 3.8: Dashboard Statistics & Pending Items - broji REVIEW i READY clanke

## Acceptance Criteria

1. **Given** Bibliotekar ima zavrsen unos clanka (edit mode)
   **When** pregledava clanak u DRAFT statusu
   **Then** "Pošalji na pregled" dugme je prikazano na article_detail.html stranici
   **And** dugme je vidljivo samo za DRAFT clanke

2. **Given** clanak ima popunjena sva obavezna polja
   **When** Bibliotekar klikne "Pošalji na pregled"
   **Then** sistem validira: naslov postoji, apstrakt postoji, bar jedan autor dodat, PDF otpremljen (pdf_status == CLEAN)
   **And** ako validacija prodje, prikazuje se confirmation modal

3. **Given** validacija ne prodje
   **When** nedostaju obavezna polja
   **Then** prikazuje se lista nedostajucih polja sa jasnim opisom
   **And** svako polje linkuje na odgovarajucu stranicu/sekciju za popunjavanje
   **And** clanak ostaje u DRAFT statusu

4. **Given** validacija prodje i korisnik potvrdi
   **When** submit je potvrdjen
   **Then** status clanka se menja iz DRAFT u REVIEW
   **And** toast notifikacija: "Članak poslat na pregled"
   **And** korisnik se preusmerava na article_detail.html (read-only prikaz)

5. **Given** clanak je u REVIEW statusu
   **When** Bibliotekar pregledava clanak
   **Then** status badge prikazuje "Na pregledu" (bg-info)
   **And** poruka: "Članak čeka odobrenje urednika"
   **And** "Izmeni" dugme NIJE prikazano (read-only)
   **And** "Pošalji na pregled" dugme NIJE prikazano

6. **Given** korisnik nema Bibliotekar/Urednik/Administrator ulogu
   **When** pokusava da pristupi submit endpointu
   **Then** pristup je odbijen sa 403 Forbidden

7. **Given** clanak nije u DRAFT statusu
   **When** korisnik pokusava submit (direktnim URL-om)
   **Then** sistem odbija tranziciju
   **And** prikazuje gresku: "Samo članci u statusu Nacrt mogu biti poslati na pregled"

8. **Given** Business logika za status tranziciju
   **When** submit_article_for_review() se poziva u services.py
   **Then** validira da je status DRAFT
   **And** validira da title, abstract, author_count > 0, pdf_status == CLEAN
   **And** menja status na REVIEW
   **And** cuva submitted_by i submitted_at timestamp
   **And** baca InvalidStatusTransition exception za nevalidne tranzicije

## Tasks / Subtasks

- [x] Task 1: Implementirati `submit_article_for_review()` service funkciju (AC: #4, #7, #8)
  - [x] 1.1 U `articles/services.py` kreirati `submit_article_for_review(article, user)` funkciju
  - [x] 1.2 Validirati da je `article.status == ArticleStatus.DRAFT`
  - [x] 1.3 Validirati obavezna polja: title (non-empty), abstract (non-empty), author_count > 0, pdf_status == CLEAN
  - [x] 1.4 Promeniti status na `ArticleStatus.REVIEW`
  - [x] 1.5 Sacuvati `submitted_by = user` i `submitted_at = timezone.now()`
  - [x] 1.6 Baciti `InvalidStatusTransition` za nevalidne tranzicije
  - [x] 1.7 Vratiti article objekat nakon uspesnog submit-a

- [x] Task 2: Dodati `submitted_by` i `submitted_at` polja na Article model (AC: #4, #8)
  - [x] 2.1 Dodati `submitted_by = ForeignKey(User, null=True, blank=True, related_name="submitted_articles")` na Article model
  - [x] 2.2 Dodati `submitted_at = DateTimeField(null=True, blank=True)` na Article model
  - [x] 2.3 Kreirati migraciju: `makemigrations articles`
  - [x] 2.4 Primeniti migraciju: `migrate`

- [x] Task 3: Kreirati `InvalidStatusTransition` exception (AC: #7, #8)
  - [x] 3.1 U `articles/services.py` ili `core/exceptions.py` kreirati custom exception klasu
  - [x] 3.2 Nasledjuje Exception (ili DOIPortalException ako postoji)

- [x] Task 4: Kreirati validacioni endpoint - `article_submit_check` FBV (AC: #2, #3)
  - [x] 4.1 U `articles/views.py` dodati `article_submit_check(request, pk)` GET FBV
  - [x] 4.2 Proveriti da li clanak prolazi validaciju za submit
  - [x] 4.3 Vratiti HTML fragment sa rezultatom validacije (uspeh ili lista gresaka)
  - [x] 4.4 Koristiti `_check_article_permission()` za publisher scoping
  - [x] 4.5 Samo DRAFT clanci mogu koristiti ovaj endpoint

- [x] Task 5: Kreirati submit FBV endpoint - `article_submit_for_review` (AC: #4, #6, #7)
  - [x] 5.1 U `articles/views.py` dodati `article_submit_for_review(request, pk)` POST FBV
  - [x] 5.2 Pozvati `submit_article_for_review()` service funkciju
  - [x] 5.3 Na uspeh: dodati success poruku, redirect na article detail
  - [x] 5.4 Na gresku (InvalidStatusTransition): dodati error poruku, redirect na article detail
  - [x] 5.5 Koristiti `_check_article_permission()` za publisher scoping
  - [x] 5.6 Dekorisati sa `@login_required` i `@require_POST`

- [x] Task 6: Dodati URL routes za submit endpointe (AC: #2, #4)
  - [x] 6.1 U `articles/urls.py` dodati:
    - `<int:pk>/submit-check/` (name: article-submit-check) - GET
    - `<int:pk>/submit/` (name: article-submit) - POST

- [x] Task 7: Azurirati article_detail.html - "Pošalji na pregled" dugme i validacija (AC: #1, #2, #3, #5)
  - [x] 7.1 Dodati "Pošalji na pregled" dugme u Quick Actions (samo za DRAFT clanke)
  - [x] 7.2 Dugme pokrece HTMX GET na `article-submit-check` endpoint
  - [x] 7.3 HTMX response prikazuje modal sa validacionim rezultatom
  - [x] 7.4 Ako validacija prodje - modal sadrzi formu sa POST na `article-submit` endpoint
  - [x] 7.5 Ako validacija ne prodje - modal prikazuje listu nedostajucih polja
  - [x] 7.6 Dodati "Članak čeka odobrenje urednika" poruku za REVIEW status
  - [x] 7.7 Sakriti "Izmeni" dugme za ne-DRAFT clanke (vec delom postoji u `can_edit` context)

- [x] Task 8: Kreirati HTMX partial template za submit modal (AC: #2, #3)
  - [x] 8.1 Kreirati `templates/articles/partials/_submit_review_modal.html`
  - [x] 8.2 Bootstrap 5 modal sa validation results
  - [x] 8.3 Uspesan scenario: confirmation tekst + "Potvrdi" dugme (POST form)
  - [x] 8.4 Neuspesan scenario: lista gresaka sa linkovima ka popunjavanju

- [x] Task 9: Azurirati ArticleDetailView context (AC: #1, #5)
  - [x] 9.1 Dodati `can_submit` context varijablu (VEC postoji - proveriti da je korektno)
  - [x] 9.2 Dodati `is_in_review` context varijablu za poruku o cekanju
  - [x] 9.3 Dodati `submitted_by` i `submitted_at` u context za prikaz

- [x] Task 10: Kreirati testove (AC: #1-#8)
  - [x] 10.1 Service testovi: `submit_article_for_review` sa validnim DRAFT clankom
  - [x] 10.2 Service testovi: `submit_article_for_review` odbija ne-DRAFT clanak
  - [x] 10.3 Service testovi: `submit_article_for_review` odbija clanak bez autora
  - [x] 10.4 Service testovi: `submit_article_for_review` odbija clanak bez PDF-a (pdf_status != CLEAN)
  - [x] 10.5 Service testovi: `submit_article_for_review` odbija clanak bez naslova/apstrakta
  - [x] 10.6 View testovi: `article_submit_check` za validni DRAFT clanak
  - [x] 10.7 View testovi: `article_submit_check` za nevalidni clanak (nedostaju polja)
  - [x] 10.8 View testovi: `article_submit_for_review` POST sa uspesnim submit-om
  - [x] 10.9 View testovi: `article_submit_for_review` POST sa nevalidnim clankom
  - [x] 10.10 Permission testovi: publisher scoping za submit endpointe
  - [x] 10.11 Permission testovi: ne-DRAFT clanak odbija submit
  - [x] 10.12 Template testovi: dugme vidljivo samo za DRAFT
  - [x] 10.13 Integration testovi: kompletni flow DRAFT -> REVIEW
  - [x] 10.14 Koristiti Factory Boy, pytest-django iz postojeceg test setup-a

## Dev Notes

### KRITICNO: Services Layer Pattern (project-context.md)

Ovo je PRVA prica koja zahteva services.py logiku. `articles/services.py` VEC postoji kao placeholder (kreiran u Story 3.1).

```python
# articles/services.py - IMPLEMENTIRATI

from django.utils import timezone

from .models import Article, ArticleStatus, PdfStatus


class InvalidStatusTransition(Exception):
    """Raised when article status transition is invalid."""
    pass


def submit_article_for_review(article: Article, user) -> Article:
    """
    Submit article for editorial review.

    Validates required fields and transitions DRAFT -> REVIEW.

    Args:
        article: Article instance to submit
        user: User performing the submission

    Returns:
        Updated Article instance

    Raises:
        InvalidStatusTransition: If article is not in DRAFT status or
            required fields are missing
    """
    # Validate status
    if article.status != ArticleStatus.DRAFT:
        raise InvalidStatusTransition(
            "Samo članci u statusu Nacrt mogu biti poslati na pregled."
        )

    # Validate required fields
    errors = []
    if not article.title or not article.title.strip():
        errors.append("Naslov je obavezan.")
    if not article.abstract or not article.abstract.strip():
        errors.append("Apstrakt je obavezan.")
    if article.authors.count() == 0:
        errors.append("Potreban je bar jedan autor.")
    if article.pdf_status != PdfStatus.CLEAN:
        errors.append("PDF fajl mora biti otpremljen i skeniran.")

    if errors:
        raise InvalidStatusTransition(
            "Članak nije spreman za pregled: " + "; ".join(errors)
        )

    # Perform transition
    article.status = ArticleStatus.REVIEW
    article.submitted_by = user
    article.submitted_at = timezone.now()
    article.save(update_fields=["status", "submitted_by", "submitted_at", "updated_at"])

    return article
```

### Submit Check Endpoint (HTMX)

```python
# articles/views.py - DODATI

@login_required
@require_GET
def article_submit_check(request, pk):
    """
    Check article readiness for review submission via HTMX GET.

    Returns modal content with validation results.
    """
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ).prefetch_related("authors"),
        pk=pk,
    )
    _check_article_permission(request.user, article)

    # Validate readiness
    errors = []
    if article.status != ArticleStatus.DRAFT:
        errors.append("Članak nije u statusu Nacrt.")
    if not article.title or not article.title.strip():
        errors.append("Naslov je obavezan.")
    if not article.abstract or not article.abstract.strip():
        errors.append("Apstrakt je obavezan.")
    if article.authors.count() == 0:
        errors.append("Potreban je bar jedan autor.")
    if article.pdf_status != PdfStatus.CLEAN:
        errors.append("PDF fajl mora biti otpremljen i uspešno skeniran.")

    return render(request, "articles/partials/_submit_review_modal.html", {
        "article": article,
        "errors": errors,
        "is_ready": len(errors) == 0,
    })


@login_required
@require_POST
def article_submit_for_review(request, pk):
    """
    Submit article for editorial review via POST.

    Delegates to submit_article_for_review() service function.
    Redirects to article detail with success/error message.
    """
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ).prefetch_related("authors"),
        pk=pk,
    )
    _check_article_permission(request.user, article)

    from .services import InvalidStatusTransition, submit_article_for_review

    try:
        submit_article_for_review(article, request.user)
        messages.success(request, "Članak poslat na pregled.")
    except InvalidStatusTransition as e:
        messages.error(request, str(e))

    return HttpResponseRedirect(reverse("articles:detail", kwargs={"pk": pk}))
```

### URL Routes

```python
# articles/urls.py - DODATI u urlpatterns

# Submit for Review HTMX endpoints (Story 3.5)
path(
    "<int:pk>/submit-check/",
    views.article_submit_check,
    name="article-submit-check",
),
path(
    "<int:pk>/submit/",
    views.article_submit_for_review,
    name="article-submit",
),
```

### Submit Modal Template

```html
<!-- templates/articles/partials/_submit_review_modal.html -->
<div class="modal-dialog">
    <div class="modal-content">
        <div class="modal-header">
            <h5 class="modal-title">
                {% if is_ready %}
                <i class="bi bi-send me-2"></i>Potvrda slanja na pregled
                {% else %}
                <i class="bi bi-exclamation-triangle me-2 text-warning"></i>Članak nije spreman
                {% endif %}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
            {% if is_ready %}
            <p>Članak <strong>{{ article.title }}</strong> će biti poslat uredniku na pregled.</p>
            <p class="text-muted mb-0">
                <i class="bi bi-info-circle me-1"></i>
                Nakon slanja, nećete moći da menjate članak dok ga urednik ne vrati na doradu.
            </p>
            {% else %}
            <p>Pre slanja na pregled, ispravite sledeće:</p>
            <ul class="list-group">
                {% for error in errors %}
                <li class="list-group-item list-group-item-warning">
                    <i class="bi bi-exclamation-circle me-2"></i>{{ error }}
                </li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        <div class="modal-footer">
            {% if is_ready %}
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Otkaži</button>
            <form method="post" action="{% url 'articles:article-submit' pk=article.pk %}" style="display:inline;">
                {% csrf_token %}
                <button type="submit" class="btn btn-primary">
                    <i class="bi bi-send me-1"></i>Pošalji na pregled
                </button>
            </form>
            {% else %}
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Zatvori</button>
            <a href="{% url 'articles:update' article.pk %}" class="btn btn-primary">
                <i class="bi bi-pencil me-1"></i>Izmeni članak
            </a>
            {% endif %}
        </div>
    </div>
</div>
```

### article_detail.html - Izmene

U Quick Actions sekciju dodati "Pošalji na pregled" dugme:

```html
<!-- U Quick Actions card, nakon "Izmeni članak" linka -->
{% if can_submit %}
<button type="button" class="list-group-item list-group-item-action text-primary"
        hx-get="{% url 'articles:article-submit-check' pk=article.pk %}"
        hx-target="#submit-modal-container"
        hx-swap="innerHTML"
        data-bs-toggle="modal"
        data-bs-target="#submitReviewModal">
    <i class="bi bi-send me-2"></i>Pošalji na pregled
</button>
{% endif %}
```

Dodati modal container na dno stranice:

```html
<!-- Submit Review Modal Container -->
<div class="modal fade" id="submitReviewModal" tabindex="-1">
    <div id="submit-modal-container">
        <!-- HTMX will inject modal content here -->
    </div>
</div>
```

Dodati REVIEW status poruku:

```html
{% if article.status == 'REVIEW' %}
<div class="alert alert-info mb-4">
    <i class="bi bi-hourglass-split me-2"></i>
    <strong>Članak čeka odobrenje urednika.</strong>
    {% if article.submitted_at %}
    <br><small class="text-muted">Poslat: {{ article.submitted_at|date:"d.m.Y. H:i" }}
    {% if article.submitted_by %} od {{ article.submitted_by }}{% endif %}</small>
    {% endif %}
</div>
{% endif %}
```

### Article Model Migration

Dodati dva nova polja na Article model:

```python
# U Article modelu, u === TRACKING === sekciji

submitted_by = models.ForeignKey(
    "users.User",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="submitted_articles",
    verbose_name=_("Poslao na pregled"),
)
submitted_at = models.DateTimeField(
    _("Poslat na pregled"),
    null=True,
    blank=True,
)
```

### ArticleDetailView Context Izmene

`can_submit` vec postoji u ArticleDetailView:
```python
context["can_submit"] = (
    flags["is_admin"] or flags["is_urednik"] or flags["is_bibliotekar"]
) and self.object.status == ArticleStatus.DRAFT
```

Dodati:
```python
context["is_in_review"] = self.object.status == ArticleStatus.REVIEW
```

### Publisher Scoping

Submit endpointi koriste ISTU `_check_article_permission()` helper funkciju kao i ostali HTMX FBV-ovi. NE kreirati novi helper.

### Auditlog Integracija

Article model je VEC registrovan sa django-auditlog. Status promena iz DRAFT u REVIEW ce automatski biti zabelezena u audit log sa old/new values. NE zahteva dodatnu konfiguraciju.

### ArticleUpdateView - Ogranicenje na DRAFT

ArticleUpdateView VEC filtrira queryset na `.filter(status=ArticleStatus.DRAFT)`. Ovo znaci da clanak u REVIEW statusu automatski vraca 404 ako se pokusa edit. Ovaj mehanizam VEC postoji, ali treba proveriti da article_detail.html korektno sakriva "Izmeni" dugme za ne-DRAFT clanke.

`can_edit` u ArticleDetailView VEC proverava `self.object.status == ArticleStatus.DRAFT`:
```python
context["can_edit"] = (
    flags["is_admin"] or flags["is_urednik"] or flags["is_bibliotekar"]
) and self.object.status == ArticleStatus.DRAFT
```

### Test Pattern

```python
# articles/tests/test_submit_review.py - NOVI FAJL

import pytest
from django.urls import reverse
from django.utils import timezone

from doi_portal.articles.models import Article, ArticleStatus, PdfStatus
from doi_portal.articles.services import (
    InvalidStatusTransition,
    submit_article_for_review,
)


@pytest.mark.django_db
class TestSubmitArticleForReviewService:
    """Tests for submit_article_for_review service function."""

    def test_submit_valid_draft_article(self, draft_article_with_author_and_pdf, bibliotekar_user):
        """Valid DRAFT article transitions to REVIEW."""
        article = draft_article_with_author_and_pdf
        result = submit_article_for_review(article, bibliotekar_user)
        assert result.status == ArticleStatus.REVIEW
        assert result.submitted_by == bibliotekar_user
        assert result.submitted_at is not None

    def test_submit_rejects_non_draft(self, review_article, bibliotekar_user):
        """Non-DRAFT article raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition):
            submit_article_for_review(review_article, bibliotekar_user)

    def test_submit_rejects_no_authors(self, draft_article_no_authors, bibliotekar_user):
        """Article without authors raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition, match="autor"):
            submit_article_for_review(draft_article_no_authors, bibliotekar_user)

    def test_submit_rejects_no_pdf(self, draft_article_no_pdf, bibliotekar_user):
        """Article without clean PDF raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition, match="PDF"):
            submit_article_for_review(draft_article_no_pdf, bibliotekar_user)

    def test_submit_rejects_empty_title(self, draft_article_no_title, bibliotekar_user):
        """Article without title raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition, match="Naslov"):
            submit_article_for_review(draft_article_no_title, bibliotekar_user)

    def test_submit_rejects_empty_abstract(self, draft_article_no_abstract, bibliotekar_user):
        """Article without abstract raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition, match="Apstrakt"):
            submit_article_for_review(draft_article_no_abstract, bibliotekar_user)


@pytest.mark.django_db
class TestArticleSubmitCheckView:
    """Tests for article_submit_check HTMX GET endpoint."""

    def test_submit_check_valid_article(self, client, bibliotekar_user, draft_article_with_author_and_pdf):
        """Submit check for valid article returns is_ready=True."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:article-submit-check", kwargs={"pk": draft_article_with_author_and_pdf.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "Potvrda slanja" in response.content.decode()

    def test_submit_check_invalid_article(self, client, bibliotekar_user, draft_article):
        """Submit check for incomplete article returns errors."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:article-submit-check", kwargs={"pk": draft_article.pk})
        response = client.get(url)
        assert response.status_code == 200
        # Should show errors about missing requirements
        content = response.content.decode()
        assert "nije spreman" in content or "obavezan" in content.lower()

    def test_submit_check_publisher_scoping(self, client, other_publisher_user, draft_article):
        """Submit check respects publisher scoping."""
        client.force_login(other_publisher_user)
        url = reverse("articles:article-submit-check", kwargs={"pk": draft_article.pk})
        response = client.get(url)
        assert response.status_code == 403


@pytest.mark.django_db
class TestArticleSubmitForReviewView:
    """Tests for article_submit_for_review POST endpoint."""

    def test_submit_success(self, client, bibliotekar_user, draft_article_with_author_and_pdf):
        """Successful submit redirects to detail with success message."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:article-submit", kwargs={"pk": draft_article_with_author_and_pdf.pk})
        response = client.post(url)
        assert response.status_code == 302
        draft_article_with_author_and_pdf.refresh_from_db()
        assert draft_article_with_author_and_pdf.status == ArticleStatus.REVIEW

    def test_submit_rejects_non_draft(self, client, bibliotekar_user, review_article):
        """Submit for non-DRAFT article shows error."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:article-submit", kwargs={"pk": review_article.pk})
        response = client.post(url)
        assert response.status_code == 302  # Redirects with error message

    def test_submit_publisher_scoping(self, client, other_publisher_user, draft_article):
        """Submit respects publisher scoping."""
        client.force_login(other_publisher_user)
        url = reverse("articles:article-submit", kwargs={"pk": draft_article.pk})
        response = client.post(url)
        assert response.status_code == 403
```

### HTMX Modal Pattern (KRITICNO)

Za HTMX + Bootstrap 5 modal pattern:

1. Dugme ima DVA atributa:
   - `hx-get` - ucitava sadrzaj modala sa servera
   - `data-bs-toggle="modal"` i `data-bs-target="#submitReviewModal"` - otvara Bootstrap modal

2. HTMX response ide u `#submit-modal-container` (unutar modal div-a)

3. Modal sadrzi `.modal-dialog` > `.modal-content` strukturu

4. Confirmation forma unutar modala koristi standardni `<form method="post">` (NE HTMX) - jer POST treba da uradi redirect

5. CSRF token: forma unutar modala mora imati `{% csrf_token %}`

NAPOMENA: Postoji alternativa - koristiti HTMX za sve, ali standardni POST + redirect je jednostavniji i konzistentniji sa ostatkom aplikacije.

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/templates/articles/partials/_submit_review_modal.html   # Submit modal HTMX partial
doi_portal/doi_portal/articles/tests/test_submit_review.py                     # Submit for review testovi
```

### Fajlovi za modifikaciju (POSTOJECI)

- `doi_portal/doi_portal/articles/models.py` - Dodati `submitted_by`, `submitted_at` polja
- `doi_portal/doi_portal/articles/services.py` - Implementirati `submit_article_for_review()`, `InvalidStatusTransition`
- `doi_portal/doi_portal/articles/views.py` - Dodati `article_submit_check` i `article_submit_for_review` FBV-ove
- `doi_portal/doi_portal/articles/urls.py` - Dodati submit routes
- `doi_portal/doi_portal/templates/articles/article_detail.html` - Dodati submit dugme, modal, REVIEW poruku

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

Svi UI tekstovi MORAJU koristiti ispravne srpske dijakritike:

| Kontekst | ISPRAVNO |
|----------|----------|
| Submit dugme | "Pošalji na pregled" |
| Confirm dugme | "Potvrdi" |
| Cancel dugme | "Otkaži" |
| Modal title (ready) | "Potvrda slanja na pregled" |
| Modal title (not ready) | "Članak nije spreman" |
| Modal body (ready) | "Članak ... će biti poslat uredniku na pregled." |
| Modal body warning | "Nakon slanja, nećete moći da menjate članak dok ga urednik ne vrati na doradu." |
| Modal errors heading | "Pre slanja na pregled, ispravite sledeće:" |
| Toast success | "Članak poslat na pregled" |
| Error: not DRAFT | "Samo članci u statusu Nacrt mogu biti poslati na pregled." |
| Error: no title | "Naslov je obavezan." |
| Error: no abstract | "Apstrakt je obavezan." |
| Error: no authors | "Potreban je bar jedan autor." |
| Error: no PDF | "PDF fajl mora biti otpremljen i uspešno skeniran." |
| Status info | "Članak čeka odobrenje urednika." |
| Back to edit | "Izmeni članak" |

### Anti-Patterns (ZABRANJENO)

```python
# POGRESNO - Status tranzicija direktno u view-u
def submit_view(request, pk):
    article.status = ArticleStatus.REVIEW
    article.save()  # NE! Koristi services.py

# POGRESNO - Vracati JSON za HTMX response
return JsonResponse({"errors": errors})  # NE! Vracaj HTML fragment

# POGRESNO - Dozvoliti submit bez validacije
if article.status == ArticleStatus.DRAFT:
    article.status = ArticleStatus.REVIEW  # NE! Validirati polja

# POGRESNO - Koristiti CBV za submit endpoint
class ArticleSubmitView(View):  # NE! Koristi FBV za HTMX

# POGRESNO - Kreirati novi permission helper
def _check_submit_permission(user, article):  # NE! Koristi _check_article_permission

# POGRESNO - Menjati ArticleUpdateView
# NE menjati - vec filtrira na DRAFT status

# POGRESNO - Kreirati novi Django app za workflow
# Sve ide u postojeci articles app

# POGRESNO - Dodavati Alpine.js CDN ponovo
# VEC je ukljucen u article_form.html javascript block

# POGRESNO - Skip-ovati auditlog
# VEC radi automatski za Article model
```

### Previous Story Learnings (Story 3.1-3.4)

1. **`_check_article_permission()`** - VEC postoji u views.py. Koristi za submit endpoint. (Story 3.2)
2. **HTMX CSRF token** - za HTMX POST iz modala, koristi standardnu Django formu sa `{% csrf_token %}`, NE HTMX POST. (Story 3.3)
3. **FBV pattern** - Svi HTMX endpoint-i koriste FBV-ove sa `@login_required` i `@require_POST` / `@require_GET`. (Story 3.3)
4. **`select_related` chain** - Uvek ukljuciti `"issue", "issue__publication", "issue__publication__publisher"` za publisher scoping. (Story 3.1)
5. **Django messages** - Koristiti `messages.success()` i `messages.error()` za toast feedback. (Story 3.1)
6. **Template include pattern** - `{% include %}` sa `with` za prosledjivanje context-a. (Story 3.2)
7. **auditlog** - Article je VEC registrovan. Status promene se automatski beleze. (Story 3.4)
8. **Test pattern** - Factory Boy, pytest-django, `HTTP_HX_REQUEST="true"` za HTMX testove. (Story 3.4)
9. **services.py placeholder** - VEC postoji prazan `articles/services.py` sa komentarom koji referencira Story 3.5. (Story 3.1)
10. **ArticleUpdateView queryset** - VEC filtrira `.filter(status=ArticleStatus.DRAFT)`. REVIEW clanci nisu editabilni. (Story 3.1)
11. **Bootstrap 5 modal** - Koristiti `data-bs-toggle="modal"` za otvaranje, `.modal-dialog` > `.modal-content` > `.modal-header/.modal-body/.modal-footer` strukturu.
12. **can_submit context** - VEC postoji u ArticleDetailView, ali NE koristi se u template-u. Ova prica ga aktivira.

### Git Commit Pattern

```
story-3-5: feat(articles): implementiraj Submit Article for Review sa validacijom i DRAFT->REVIEW tranzicijom (Story 3.5)
```

### NFR Requirements

- **FR29:** Urednik moze pregledati clanak za odobrenje - preduslov: Bibliotekar salje clanak na pregled
- **NFR3:** Admin panel stranice < 5 sekundi - modal se ucitava preko HTMX, minimalan payload
- **NFR12:** Audit log - status promena se automatski belezi (django-auditlog)
- UX zahtev: "Status workflow-a uvek vidljiv" - Status badge na article_detail.html
- UX zahtev: "Sistem me vodi" - validacija pre submit-a, jasne poruke o nedostajucim poljima
- UX zahtev: "Confirm modal za destruktivne akcije" - modal pre status tranzicije
- UX zahtev: Status badge boje: Draft (narandzasta/secondary), Review (plava/info), Published (zelena/success)

### Dependencies (Python/Django)

Nema novih Python zavisnosti! Sve je vec instalirano:
- Django 5.2+ (form handling, views, messages)
- HTMX 2.0.8 (CDN - vec u admin_base.html) - za ucitavanje modal sadrzaja
- Bootstrap 5 (CSS framework - vec u admin_base.html) - za modal komponentu
- django-auditlog (automatic logging - vec registrovan)
- Factory Boy + pytest-django (vec u test setup-u)

### Project Structure Notes

- Service logika ide u `doi_portal/doi_portal/articles/services.py` (VEC postoji kao placeholder)
- Submit modal partial ide u `doi_portal/doi_portal/templates/articles/partials/_submit_review_modal.html`
- Submit testovi idu u `doi_portal/doi_portal/articles/tests/test_submit_review.py`
- URL routes ostaju u `articles` namespace
- NE kreirati novi Django app
- NE kreirati core/exceptions.py - exception klasa ide u articles/services.py (lokalno za sada)

### References

- [Source: epics.md#Story 3.5: Submit Article for Review]
- [Source: epics.md#Story 3.6: Editorial Review Process - downstream dependency]
- [Source: prd.md#5. Article Management - FR29 (Pregled za odobrenje)]
- [Source: architecture.md#API & Communication Patterns - HTMX endpoints]
- [Source: architecture.md#Implementation Patterns - HTMX Patterns]
- [Source: project-context.md#Services Layer (Business Logic)]
- [Source: project-context.md#Error Handling - Custom exceptions, InvalidStatusTransition]
- [Source: project-context.md#HTMX Pravila]
- [Source: project-context.md#Naming Konvencije]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri]
- [Source: ux-design-specification.md#Experience Principles - "Sistem me vodi"]
- [Source: ux-design-specification.md#Status workflow - Draft -> Review -> Published]
- [Source: ux-design-specification.md#Decision Patterns - Confirm modal za destruktivne akcije]
- [Source: ux-design-specification.md#Status Badge - Review (plava)]
- [Source: 3-4-auto-save-functionality.md - HTMX FBV patterns, publisher scoping, test patterns]
- [Source: 3-1-article-model-basic-metadata-entry.md - ArticleStatus enum, ArticleDetailView, can_submit]
- [Source: articles/services.py - Placeholder with Story 3.5 reference]
- [Source: articles/views.py - _check_article_permission, ArticleDetailView context]
- [Source: articles/models.py - Article model, ArticleStatus, PdfStatus]
- [Source: articles/urls.py - Existing URL patterns and namespace]
- [Source: templates/articles/article_detail.html - Quick Actions, can_submit flag]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

No debug issues encountered.

### Completion Notes List

- All 10 tasks completed following TDD red-green-refactor cycle
- 40 new tests written and passing (test_submit_review.py)
- 312 total articles tests passing, zero failures
- Services layer pattern implemented per project-context.md guidelines
- Publisher scoping uses existing `_check_article_permission()` helper (no new helpers)
- HTMX + Bootstrap 5 modal pattern for submit confirmation
- All UI text in Serbian with proper diacritics
- Migration 0004 created and applied for submitted_by/submitted_at fields
- auditlog automatically tracks DRAFT -> REVIEW status transition (no config needed)

### File List

**New files:**
- `doi_portal/doi_portal/articles/tests/test_submit_review.py` - 40 tests covering AC #1-#8
- `doi_portal/doi_portal/templates/articles/partials/_submit_review_modal.html` - HTMX modal partial
- `doi_portal/doi_portal/articles/migrations/0004_add_submitted_by_submitted_at_to_article.py` - Migration

**Modified files:**
- `doi_portal/doi_portal/articles/models.py` - Added submitted_by, submitted_at fields
- `doi_portal/doi_portal/articles/services.py` - Implemented InvalidStatusTransition, submit_article_for_review()
- `doi_portal/doi_portal/articles/views.py` - Added article_submit_check, article_submit_for_review FBVs, is_in_review context
- `doi_portal/doi_portal/articles/urls.py` - Added submit-check and submit URL routes
- `doi_portal/doi_portal/templates/articles/article_detail.html` - Submit button, modal container, REVIEW alert
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Story 3.5 status transition
- `_bmad-output/implementation-artifacts/3-5-submit-article-for-review.md` - Task checkboxes marked complete
