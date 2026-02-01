# Story 3.6: Editorial Review Process

Status: done

## Story

As an **Urednik (Editor)**,
I want **to review submitted articles and approve or return them for revision**,
So that **only quality content proceeds to publication**.

## Background

Ovo je sesta prica u Epiku 3 (Article Workflow). Implementira editorial review proces - Urednik pregledava clanke u REVIEW statusu i moze ih odobriti (REVIEW -> READY) ili vratiti na doradu (REVIEW -> DRAFT). Ovo je direktan nastavak Story 3.5 (Submit Article for Review) koja implementira DRAFT -> REVIEW tranziciju.

**FR Pokrivenost:** FR29 (Urednik moze pregledati clanak za odobrenje)

**Zavisnosti (sve DONE):**
- Story 3.1: Article Model & Basic Metadata Entry - Article model, ArticleStatus enum (DRAFT, REVIEW, READY, PUBLISHED, WITHDRAWN), ArticleDetailView, ArticleListView
- Story 3.2: Author Management - Author/Affiliation modeli, HTMX author CRUD, `_check_article_permission()`
- Story 3.3: PDF Upload - pdf_file, pdf_status, PdfStatus enum
- Story 3.4: Auto-Save Functionality - auto-save endpoint
- Story 3.5: Submit Article for Review - `submit_article_for_review()` service, `InvalidStatusTransition`, `validate_article_for_submit()`, submitted_by/submitted_at polja, HTMX submit modal pattern

**Blokira:**
- Story 3.7: Article Publishing & Withdrawal - zavisi od READY statusa (READY -> PUBLISHED)
- Story 3.8: Dashboard Statistics & Pending Items - broji REVIEW i READY clanke

## Acceptance Criteria

1. **Given** ulogovan Urednik
   **When** pregledava listu clanaka ili article detail
   **Then** clanci sa statusom REVIEW su vidljivo oznaceni
   **And** Urednik moze filtrirati listu clanaka po statusu REVIEW

2. **Given** Urednik otvara clanak u statusu REVIEW
   **When** pregledava article detail stranicu
   **Then** svi metapodaci, autori i PDF su prikazani
   **And** prikazana su dva akciona dugmeta: "Odobri" i "Vrati na doradu"
   **And** dugmad su vidljiva SAMO za REVIEW status

3. **Given** Urednik klikne "Odobri"
   **When** potvrdi akciju u confirmation modalu
   **Then** status clanka se menja iz REVIEW u READY
   **And** cuva se `reviewed_by` i `reviewed_at` timestamp
   **And** toast notifikacija: "Članak odobren"
   **And** Bibliotekar moze videti azurirani status

4. **Given** Urednik klikne "Vrati na doradu"
   **When** unese komentar sa razlogom vracanja
   **Then** status clanka se menja iz REVIEW u DRAFT
   **And** cuva se `revision_comment`, `returned_by`, `returned_at`
   **And** toast notifikacija: "Članak vraćen na doradu"
   **And** Bibliotekar moze videti komentar i ponovo editovati clanak

5. **Given** clanak je u READY statusu
   **When** Urednik pregledava clanak
   **Then** status badge prikazuje "Spremno za objavu" (bg-primary)
   **And** nema daljih urednickih akcija (Administrator preuzima)

6. **Given** clanak je vracen na doradu (REVIEW -> DRAFT)
   **When** Bibliotekar otvara clanak
   **Then** revision komentar je vidljiv na article_detail.html
   **And** Bibliotekar moze editovati clanak (edit dugme vidljivo)
   **And** moze ponovo poslati na pregled

7. **Given** korisnik nema Urednik/Administrator/Superadmin ulogu
   **When** pokusava da pristupi review endpointima
   **Then** pristup je odbijen sa 403 Forbidden

8. **Given** clanak NIJE u REVIEW statusu
   **When** korisnik pokusava approve ili return (direktnim URL-om)
   **Then** sistem odbija tranziciju
   **And** prikazuje gresku: "Samo članci na pregledu mogu biti odobreni ili vraćeni."

## Tasks / Subtasks

- [x] Task 1: Dodati `reviewed_by`, `reviewed_at`, `revision_comment`, `returned_by`, `returned_at` polja na Article model (AC: #3, #4)
  - [x] 1.1 U `articles/models.py` dodati nova polja u TRACKING sekciju
  - [x] 1.2 `reviewed_by = ForeignKey(User, null=True, blank=True, related_name="reviewed_articles")`
  - [x] 1.3 `reviewed_at = DateTimeField(null=True, blank=True)`
  - [x] 1.4 `revision_comment = TextField(blank=True)` - komentar urednika pri vracanju
  - [x] 1.5 `returned_by = ForeignKey(User, null=True, blank=True, related_name="returned_articles")`
  - [x] 1.6 `returned_at = DateTimeField(null=True, blank=True)`
  - [x] 1.7 Kreirati migraciju: `makemigrations articles` (0005)
  - [x] 1.8 Primeniti migraciju: `migrate`

- [x] Task 2: Implementirati `approve_article()` service funkciju (AC: #3, #8)
  - [x] 2.1 U `articles/services.py` dodati `approve_article(article, user)` funkciju
  - [x] 2.2 Validirati da je `article.status == ArticleStatus.REVIEW`
  - [x] 2.3 Promeniti status na `ArticleStatus.READY`
  - [x] 2.4 Sacuvati `reviewed_by = user` i `reviewed_at = timezone.now()`
  - [x] 2.5 Ocistiti prethodni `revision_comment` (ako postoji od ranijeg vracanja)
  - [x] 2.6 Baciti `InvalidStatusTransition` za nevalidne tranzicije
  - [x] 2.7 Koristiti `transaction.atomic()` kao u `submit_article_for_review()`

- [x] Task 3: Implementirati `return_article_for_revision()` service funkciju (AC: #4, #8)
  - [x] 3.1 U `articles/services.py` dodati `return_article_for_revision(article, user, comment)` funkciju
  - [x] 3.2 Validirati da je `article.status == ArticleStatus.REVIEW`
  - [x] 3.3 Validirati da je `comment` neprazan string
  - [x] 3.4 Promeniti status na `ArticleStatus.DRAFT`
  - [x] 3.5 Sacuvati `revision_comment = comment`, `returned_by = user`, `returned_at = timezone.now()`
  - [x] 3.6 Ocistiti `submitted_by` i `submitted_at` (reset za novi submit ciklus)
  - [x] 3.7 Baciti `InvalidStatusTransition` za nevalidne tranzicije
  - [x] 3.8 Koristiti `transaction.atomic()`

- [x] Task 4: Kreirati approve HTMX check endpoint - `article_approve_check` FBV (AC: #2, #3)
  - [x] 4.1 U `articles/views.py` dodati `article_approve_check(request, pk)` GET FBV
  - [x] 4.2 Proveriti da je clanak u REVIEW statusu
  - [x] 4.3 Vratiti HTML modal fragment sa confirmation sadrzajem
  - [x] 4.4 Koristiti `_check_article_permission()` za publisher scoping
  - [x] 4.5 Dodatno proveriti da korisnik ima Urednik/Admin ulogu

- [x] Task 5: Kreirati approve POST endpoint - `article_approve` FBV (AC: #3, #7, #8)
  - [x] 5.1 U `articles/views.py` dodati `article_approve(request, pk)` POST FBV
  - [x] 5.2 Pozvati `approve_article()` service funkciju
  - [x] 5.3 Na uspeh: dodati success poruku, redirect na article detail
  - [x] 5.4 Na gresku (InvalidStatusTransition): dodati error poruku, redirect
  - [x] 5.5 Koristiti `_check_article_permission()` i role check
  - [x] 5.6 Dekorisati sa `@login_required` i `@require_POST`

- [x] Task 6: Kreirati return-for-revision HTMX check endpoint - `article_return_check` FBV (AC: #2, #4)
  - [x] 6.1 U `articles/views.py` dodati `article_return_check(request, pk)` GET FBV
  - [x] 6.2 Proveriti da je clanak u REVIEW statusu
  - [x] 6.3 Vratiti HTML modal fragment sa textarea za komentar
  - [x] 6.4 Koristiti `_check_article_permission()` za publisher scoping
  - [x] 6.5 Dodatno proveriti da korisnik ima Urednik/Admin ulogu

- [x] Task 7: Kreirati return-for-revision POST endpoint - `article_return_for_revision` FBV (AC: #4, #7, #8)
  - [x] 7.1 U `articles/views.py` dodati `article_return_for_revision(request, pk)` POST FBV
  - [x] 7.2 Pozvati `return_article_for_revision()` service funkciju
  - [x] 7.3 Na uspeh: dodati success poruku, redirect na article detail
  - [x] 7.4 Na gresku (InvalidStatusTransition ili prazan komentar): dodati error poruku, redirect
  - [x] 7.5 Koristiti `_check_article_permission()` i role check
  - [x] 7.6 Dekorisati sa `@login_required` i `@require_POST`

- [x] Task 8: Dodati URL routes za review endpointe (AC: #2, #3, #4)
  - [x] 8.1 U `articles/urls.py` dodati:
    - `<int:pk>/approve-check/` (name: article-approve-check) - GET
    - `<int:pk>/approve/` (name: article-approve) - POST
    - `<int:pk>/return-check/` (name: article-return-check) - GET
    - `<int:pk>/return/` (name: article-return) - POST

- [x] Task 9: Azurirati ArticleDetailView context za review akcije (AC: #1, #2, #5, #6)
  - [x] 9.1 Dodati `can_review` context varijablu (Urednik/Admin + REVIEW status)
  - [x] 9.2 Dodati `is_ready` context varijablu (status == READY)
  - [x] 9.3 Dodati `has_revision_comment` i `revision_comment` u context za prikaz komentara
  - [x] 9.4 Dodati `returned_by` i `returned_at` u context za prikaz informacija o vracanju

- [x] Task 10: Azurirati article_detail.html - review akcije i revision komentar (AC: #2, #3, #4, #5, #6)
  - [x] 10.1 Dodati "Odobri" dugme u Quick Actions (samo za REVIEW + Urednik/Admin)
  - [x] 10.2 Dodati "Vrati na doradu" dugme u Quick Actions (samo za REVIEW + Urednik/Admin)
  - [x] 10.3 "Odobri" dugme pokrece HTMX GET na `article-approve-check` endpoint
  - [x] 10.4 "Vrati na doradu" dugme pokrece HTMX GET na `article-return-check` endpoint
  - [x] 10.5 Dodati alert za READY status: "Članak je odobren i spreman za objavu"
  - [x] 10.6 Dodati alert za revision komentar (kada je clanak vracen na doradu)
  - [x] 10.7 Dodati modal containere za approve i return modale

- [x] Task 11: Kreirati HTMX partial template za approve modal (AC: #3)
  - [x] 11.1 Kreirati `templates/articles/partials/_approve_modal.html`
  - [x] 11.2 Bootstrap 5 modal sa confirmation sadrzajem
  - [x] 11.3 Confirmation tekst + "Odobri" dugme (POST form na `article-approve`)
  - [x] 11.4 Cancel dugme za zatvaranje modala

- [x] Task 12: Kreirati HTMX partial template za return modal (AC: #4)
  - [x] 12.1 Kreirati `templates/articles/partials/_return_revision_modal.html`
  - [x] 12.2 Bootstrap 5 modal sa textarea za komentar
  - [x] 12.3 Textarea je obavezno polje (frontend validacija + backend)
  - [x] 12.4 "Vrati na doradu" dugme (POST form na `article-return`)
  - [x] 12.5 Cancel dugme za zatvaranje modala

- [x] Task 13: Kreirati role check helper za Urednik/Admin (AC: #7)
  - [x] 13.1 Kreirati `_check_reviewer_permission(user)` helper u views.py
  - [x] 13.2 Proverava da korisnik pripada grupi Urednik, Administrator, ili je Superadmin
  - [x] 13.3 Baca PermissionDenied ako nema odgovarajucu ulogu
  - [x] 13.4 Poziva se NAKON `_check_article_permission()` (publisher scoping + role check)

- [x] Task 14: Kreirati testove (AC: #1-#8)
  - [x] 14.1 Service testovi: `approve_article` sa validnim REVIEW clankom
  - [x] 14.2 Service testovi: `approve_article` odbija ne-REVIEW clanak
  - [x] 14.3 Service testovi: `return_article_for_revision` sa validnim REVIEW clankom i komentarom
  - [x] 14.4 Service testovi: `return_article_for_revision` odbija ne-REVIEW clanak
  - [x] 14.5 Service testovi: `return_article_for_revision` odbija prazan komentar
  - [x] 14.6 Service testovi: `return_article_for_revision` resetuje submitted_by/submitted_at
  - [x] 14.7 View testovi: `article_approve_check` GET za REVIEW clanak (Urednik)
  - [x] 14.8 View testovi: `article_approve_check` odbija za Bibliotekar (403)
  - [x] 14.9 View testovi: `article_approve` POST sa uspesnim approve-om
  - [x] 14.10 View testovi: `article_approve` POST sa ne-REVIEW clankom
  - [x] 14.11 View testovi: `article_return_check` GET za REVIEW clanak (Urednik)
  - [x] 14.12 View testovi: `article_return_for_revision` POST sa komentarom
  - [x] 14.13 View testovi: `article_return_for_revision` POST bez komentara (greska)
  - [x] 14.14 Permission testovi: publisher scoping za review endpointe
  - [x] 14.15 Permission testovi: Bibliotekar ne moze approve/return
  - [x] 14.16 Permission testovi: Administrator moze approve/return
  - [x] 14.17 Template testovi: dugmad vidljiva samo za REVIEW + Urednik/Admin
  - [x] 14.18 Integration testovi: kompletni flow REVIEW -> READY (approve)
  - [x] 14.19 Integration testovi: kompletni flow REVIEW -> DRAFT (return)
  - [x] 14.20 Integration testovi: DRAFT -> REVIEW -> DRAFT -> REVIEW -> READY (resubmit ciklus)
  - [x] 14.21 Koristiti Factory Boy, pytest-django iz postojeceg test setup-a

## Dev Notes

### KRITICNO: Services Layer Pattern (project-context.md)

Sva business logika za status tranzicije ide u `articles/services.py`. VEC postoji `submit_article_for_review()` i `InvalidStatusTransition` - ova prica DODAJE nove service funkcije u isti fajl.

```python
# articles/services.py - DODATI uz postojece funkcije

def approve_article(article: Article, user) -> Article:
    """
    Approve article for publication (REVIEW -> READY).

    Args:
        article: Article instance to approve
        user: User performing the approval (Urednik/Admin)

    Returns:
        Updated Article instance

    Raises:
        InvalidStatusTransition: If article is not in REVIEW status
    """
    if article.status != ArticleStatus.REVIEW:
        raise InvalidStatusTransition(
            "Samo članci na pregledu mogu biti odobreni."
        )

    with transaction.atomic():
        article.status = ArticleStatus.READY
        article.reviewed_by = user
        article.reviewed_at = timezone.now()
        # Ocisti prethodni revision komentar ako postoji
        article.revision_comment = ""
        article.save(update_fields=[
            "status", "reviewed_by", "reviewed_at",
            "revision_comment", "updated_at",
        ])

    return article


def return_article_for_revision(article: Article, user, comment: str) -> Article:
    """
    Return article for revision (REVIEW -> DRAFT).

    Args:
        article: Article instance to return
        user: User performing the return (Urednik/Admin)
        comment: Revision comment explaining what needs to change

    Returns:
        Updated Article instance

    Raises:
        InvalidStatusTransition: If article is not in REVIEW status
            or comment is empty
    """
    if article.status != ArticleStatus.REVIEW:
        raise InvalidStatusTransition(
            "Samo članci na pregledu mogu biti vraćeni na doradu."
        )

    if not comment or not comment.strip():
        raise InvalidStatusTransition(
            "Komentar je obavezan pri vraćanju članka na doradu."
        )

    with transaction.atomic():
        article.status = ArticleStatus.DRAFT
        article.revision_comment = comment.strip()
        article.returned_by = user
        article.returned_at = timezone.now()
        # Reset submit tracking za novi ciklus
        article.submitted_by = None
        article.submitted_at = None
        article.save(update_fields=[
            "status", "revision_comment", "returned_by",
            "returned_at", "submitted_by", "submitted_at",
            "updated_at",
        ])

    return article
```

### Article Model Migracija

Dodati nova polja u TRACKING sekciju Article modela:

```python
# U Article modelu, u === TRACKING === sekciji, NAKON submitted_by/submitted_at

reviewed_by = models.ForeignKey(
    "users.User",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="reviewed_articles",
    verbose_name=_("Odobrio"),
)
reviewed_at = models.DateTimeField(
    _("Odobreno"),
    null=True,
    blank=True,
)
revision_comment = models.TextField(
    _("Komentar za doradu"),
    blank=True,
    help_text=_("Komentar urednika pri vraćanju članka na doradu."),
)
returned_by = models.ForeignKey(
    "users.User",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="returned_articles",
    verbose_name=_("Vratio na doradu"),
)
returned_at = models.DateTimeField(
    _("Vraćeno na doradu"),
    null=True,
    blank=True,
)
```

### Role Check Helper

```python
# articles/views.py - DODATI pored _check_article_permission()

def _check_reviewer_permission(user):
    """
    Check if user has reviewer (Urednik/Admin) role.

    Raises PermissionDenied if user is not Urednik, Administrator, or Superadmin.
    This is a ROLE check (not publisher scoping) - call AFTER _check_article_permission().
    """
    if user.is_superuser:
        return
    if user.groups.filter(name__in=["Administrator", "Superadmin", "Urednik"]).exists():
        return
    raise PermissionDenied
```

**VAZNO:** Bibliotekar NE moze odobriti ili vratiti clanak. Samo Urednik, Administrator i Superadmin.
Redosled provere u endpointu:
1. `_check_article_permission(user, article)` - publisher scoping
2. `_check_reviewer_permission(user)` - role check

### Review Endpoints (HTMX FBV)

```python
# articles/views.py - DODATI

@login_required
@require_GET
def article_approve_check(request, pk):
    """
    Check/confirm article approval via HTMX GET.
    Returns modal content for approve confirmation.
    """
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=pk,
    )
    _check_article_permission(request.user, article)
    _check_reviewer_permission(request.user)

    errors = []
    if article.status != ArticleStatus.REVIEW:
        errors.append("Članak nije u statusu Na pregledu.")

    return render(request, "articles/partials/_approve_modal.html", {
        "article": article,
        "errors": errors,
        "is_ready": len(errors) == 0,
    })


@login_required
@require_POST
def article_approve(request, pk):
    """
    Approve article (REVIEW -> READY) via POST.
    Delegates to approve_article() service function.
    """
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=pk,
    )
    _check_article_permission(request.user, article)
    _check_reviewer_permission(request.user)

    try:
        approve_article(article, request.user)
        messages.success(request, "Članak odobren.")
    except InvalidStatusTransition as e:
        messages.error(request, str(e))

    return HttpResponseRedirect(reverse("articles:detail", kwargs={"pk": pk}))


@login_required
@require_GET
def article_return_check(request, pk):
    """
    Check/prepare return-for-revision form via HTMX GET.
    Returns modal content with comment textarea.
    """
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=pk,
    )
    _check_article_permission(request.user, article)
    _check_reviewer_permission(request.user)

    errors = []
    if article.status != ArticleStatus.REVIEW:
        errors.append("Članak nije u statusu Na pregledu.")

    return render(request, "articles/partials/_return_revision_modal.html", {
        "article": article,
        "errors": errors,
        "is_ready": len(errors) == 0,
    })


@login_required
@require_POST
def article_return_for_revision(request, pk):
    """
    Return article for revision (REVIEW -> DRAFT) via POST.
    Delegates to return_article_for_revision() service function.
    """
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=pk,
    )
    _check_article_permission(request.user, article)
    _check_reviewer_permission(request.user)

    comment = request.POST.get("revision_comment", "").strip()

    try:
        return_article_for_revision(article, request.user, comment)
        messages.success(request, "Članak vraćen na doradu.")
    except InvalidStatusTransition as e:
        messages.error(request, str(e))

    return HttpResponseRedirect(reverse("articles:detail", kwargs={"pk": pk}))
```

### URL Routes

```python
# articles/urls.py - DODATI u urlpatterns

# Editorial Review HTMX endpoints (Story 3.6)
path(
    "<int:pk>/approve-check/",
    views.article_approve_check,
    name="article-approve-check",
),
path(
    "<int:pk>/approve/",
    views.article_approve,
    name="article-approve",
),
path(
    "<int:pk>/return-check/",
    views.article_return_check,
    name="article-return-check",
),
path(
    "<int:pk>/return/",
    views.article_return_for_revision,
    name="article-return",
),
```

### Approve Modal Template

```html
<!-- templates/articles/partials/_approve_modal.html -->
<div class="modal-dialog">
    <div class="modal-content">
        <div class="modal-header">
            <h5 class="modal-title">
                {% if is_ready %}
                <i class="bi bi-check-circle me-2 text-success"></i>Potvrda odobrenja
                {% else %}
                <i class="bi bi-exclamation-triangle me-2 text-warning"></i>Nije moguće odobriti
                {% endif %}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
            {% if is_ready %}
            <p>Članak <strong>{{ article.title }}</strong> će biti odobren i označen kao spreman za objavu.</p>
            <p class="text-muted mb-0">
                <i class="bi bi-info-circle me-1"></i>
                Nakon odobrenja, Administrator može objaviti članak.
            </p>
            {% else %}
            {% for error in errors %}
            <div class="alert alert-warning mb-2">
                <i class="bi bi-exclamation-circle me-2"></i>{{ error }}
            </div>
            {% endfor %}
            {% endif %}
        </div>
        <div class="modal-footer">
            {% if is_ready %}
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Otkaži</button>
            <form method="post" action="{% url 'articles:article-approve' pk=article.pk %}" style="display:inline;">
                {% csrf_token %}
                <button type="submit" class="btn btn-success">
                    <i class="bi bi-check-circle me-1"></i>Odobri
                </button>
            </form>
            {% else %}
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Zatvori</button>
            {% endif %}
        </div>
    </div>
</div>
```

### Return for Revision Modal Template

```html
<!-- templates/articles/partials/_return_revision_modal.html -->
<div class="modal-dialog">
    <div class="modal-content">
        <div class="modal-header">
            <h5 class="modal-title">
                {% if is_ready %}
                <i class="bi bi-arrow-return-left me-2 text-warning"></i>Vrati na doradu
                {% else %}
                <i class="bi bi-exclamation-triangle me-2 text-warning"></i>Nije moguće vratiti
                {% endif %}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        {% if is_ready %}
        <form method="post" action="{% url 'articles:article-return' pk=article.pk %}">
            {% csrf_token %}
            <div class="modal-body">
                <p>Članak <strong>{{ article.title }}</strong> će biti vraćen Bibliotekaru na doradu.</p>
                <div class="mb-3">
                    <label for="revision_comment" class="form-label fw-bold">Komentar za doradu <span class="text-danger">*</span></label>
                    <textarea class="form-control" id="revision_comment" name="revision_comment"
                              rows="4" required
                              placeholder="Opišite šta treba ispraviti ili dopuniti..."></textarea>
                    <div class="form-text">Bibliotekar će videti ovaj komentar na stranici članka.</div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Otkaži</button>
                <button type="submit" class="btn btn-warning">
                    <i class="bi bi-arrow-return-left me-1"></i>Vrati na doradu
                </button>
            </div>
        </form>
        {% else %}
        <div class="modal-body">
            {% for error in errors %}
            <div class="alert alert-warning mb-2">
                <i class="bi bi-exclamation-circle me-2"></i>{{ error }}
            </div>
            {% endfor %}
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Zatvori</button>
        </div>
        {% endif %}
    </div>
</div>
```

### article_detail.html - Izmene

U Quick Actions sekciju dodati review dugmad (NAKON postojecih):

```html
<!-- U Quick Actions card, nakon submit dugmeta -->
{% if can_review %}
<button type="button" class="list-group-item list-group-item-action text-success"
        hx-get="{% url 'articles:article-approve-check' pk=article.pk %}"
        hx-target="#approve-modal-container"
        hx-swap="innerHTML">
    <i class="bi bi-check-circle me-2"></i>Odobri
</button>
<button type="button" class="list-group-item list-group-item-action text-warning"
        hx-get="{% url 'articles:article-return-check' pk=article.pk %}"
        hx-target="#return-modal-container"
        hx-swap="innerHTML">
    <i class="bi bi-arrow-return-left me-2"></i>Vrati na doradu
</button>
{% endif %}
```

Dodati modal containere na dno stranice (pored postojeceg submitReviewModal):

```html
<!-- Approve Modal Container (Story 3.6) -->
<div class="modal fade" id="approveModal" tabindex="-1">
    <div id="approve-modal-container">
        <!-- HTMX will inject modal content here -->
    </div>
</div>

<!-- Return for Revision Modal Container (Story 3.6) -->
<div class="modal fade" id="returnRevisionModal" tabindex="-1">
    <div id="return-modal-container">
        <!-- HTMX will inject modal content here -->
    </div>
</div>
```

Dodati JavaScript za otvaranje modala (prosiriti postojeci htmx:afterSwap listener):

```html
<script>
    document.body.addEventListener('htmx:afterSwap', function(event) {
        if (event.detail.target.id === 'submit-modal-container') {
            new bootstrap.Modal(document.getElementById('submitReviewModal')).show();
        }
        if (event.detail.target.id === 'approve-modal-container') {
            new bootstrap.Modal(document.getElementById('approveModal')).show();
        }
        if (event.detail.target.id === 'return-modal-container') {
            new bootstrap.Modal(document.getElementById('returnRevisionModal')).show();
        }
    });
</script>
```

Dodati READY status poruku (ISPOD postojeceg is_in_review alert-a):

```html
{% if is_ready %}
<div class="alert alert-primary mb-4">
    <i class="bi bi-check2-circle me-2"></i>
    <strong>Članak je odobren i spreman za objavu.</strong>
    {% if article.reviewed_at %}
    <br><small class="text-muted">Odobren: {{ article.reviewed_at|date:"d.m.Y. H:i" }}
    {% if article.reviewed_by %} od {{ article.reviewed_by }}{% endif %}</small>
    {% endif %}
</div>
{% endif %}
```

Dodati revision komentar alert (ISPOD READY alert-a, vidljiv kada je clanak vracen na doradu):

```html
{% if has_revision_comment %}
<div class="alert alert-warning mb-4">
    <i class="bi bi-chat-left-text me-2"></i>
    <strong>Komentar urednika:</strong>
    <p class="mb-0 mt-1">{{ article.revision_comment }}</p>
    {% if article.returned_at %}
    <small class="text-muted">Vraćeno: {{ article.returned_at|date:"d.m.Y. H:i" }}
    {% if article.returned_by %} od {{ article.returned_by }}{% endif %}</small>
    {% endif %}
</div>
{% endif %}
```

### ArticleDetailView Context Izmene

```python
# U ArticleDetailView.get_context_data(), DODATI:

# Story 3.6: Review action context
context["can_review"] = (
    flags["is_admin"]
    or user.groups.filter(name="Urednik").exists()
) and self.object.status == ArticleStatus.REVIEW

context["is_ready"] = self.object.status == ArticleStatus.READY

# Revision comment display (visible for DRAFT articles that were returned)
context["has_revision_comment"] = bool(
    self.object.revision_comment
    and self.object.status == ArticleStatus.DRAFT
)
```

**NAPOMENA:** `revision_comment` se prikazuje SAMO kada je clanak u DRAFT statusu (vracen na doradu). Kada se clanak odobri, `revision_comment` se ocisti.

### Publisher Scoping

Review endpointi koriste ISTU `_check_article_permission()` helper funkciju kao i ostali HTMX FBV-ovi. NE kreirati novi publisher scoping helper.

### Auditlog Integracija

Article model je VEC registrovan sa django-auditlog. Status promena iz REVIEW u READY/DRAFT ce automatski biti zabelezena u audit log sa old/new values. NE zahteva dodatnu konfiguraciju.

### HTMX Modal Pattern (KRITICNO)

ISTI pattern kao Story 3.5:

1. Dugme ima `hx-get` atribut - ucitava sadrzaj modala sa servera
2. HTMX response ide u odgovarajuci modal container (approve-modal-container ili return-modal-container)
3. JavaScript `htmx:afterSwap` listener otvara Bootstrap modal
4. Confirmation/submit forma unutar modala koristi standardni `<form method="post">` (NE HTMX POST) - jer POST treba da uradi redirect
5. CSRF token: forma unutar modala MORA imati `{% csrf_token %}`
6. Return modal ima `<textarea required>` za obavezan komentar

### Status Tranzicije Sumirane

```
DRAFT -> REVIEW   (Story 3.5: submit_article_for_review)
REVIEW -> READY   (Story 3.6: approve_article)
REVIEW -> DRAFT   (Story 3.6: return_article_for_revision)
READY -> PUBLISHED (Story 3.7: buduci)
PUBLISHED -> WITHDRAWN (Story 3.7: buduci)
```

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/templates/articles/partials/_approve_modal.html        # Approve confirmation modal
doi_portal/doi_portal/templates/articles/partials/_return_revision_modal.html # Return for revision modal sa textarea
doi_portal/doi_portal/articles/tests/test_editorial_review.py                # Editorial review testovi
doi_portal/doi_portal/articles/migrations/0005_*.py                          # Migration za nova polja
```

### Fajlovi za modifikaciju (POSTOJECI)

- `doi_portal/doi_portal/articles/models.py` - Dodati reviewed_by, reviewed_at, revision_comment, returned_by, returned_at polja
- `doi_portal/doi_portal/articles/services.py` - Dodati approve_article(), return_article_for_revision()
- `doi_portal/doi_portal/articles/views.py` - Dodati 4 nova FBV-a + _check_reviewer_permission() + context updates
- `doi_portal/doi_portal/articles/urls.py` - Dodati 4 nova URL route-a
- `doi_portal/doi_portal/templates/articles/article_detail.html` - Review dugmad, modali, READY alert, revision komentar

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

Svi UI tekstovi MORAJU koristiti ispravne srpske dijakritike:

| Kontekst | ISPRAVNO |
|----------|----------|
| Approve dugme | "Odobri" |
| Return dugme | "Vrati na doradu" |
| Cancel dugme | "Otkaži" |
| Close dugme | "Zatvori" |
| Approve modal title | "Potvrda odobrenja" |
| Return modal title | "Vrati na doradu" |
| Approve modal body | "Članak ... će biti odobren i označen kao spreman za objavu." |
| Return modal body | "Članak ... će biti vraćen Bibliotekaru na doradu." |
| Comment label | "Komentar za doradu" |
| Comment placeholder | "Opišite šta treba ispraviti ili dopuniti..." |
| Comment help | "Bibliotekar će videti ovaj komentar na stranici članka." |
| Toast approve | "Članak odobren." |
| Toast return | "Članak vraćen na doradu." |
| Error: not REVIEW | "Samo članci na pregledu mogu biti odobreni." |
| Error: not REVIEW return | "Samo članci na pregledu mogu biti vraćeni na doradu." |
| Error: no comment | "Komentar je obavezan pri vraćanju članka na doradu." |
| READY alert | "Članak je odobren i spreman za objavu." |
| Revision alert | "Komentar urednika:" |

### Anti-Patterns (ZABRANJENO)

```python
# POGRESNO - Status tranzicija direktno u view-u
def approve_view(request, pk):
    article.status = ArticleStatus.READY
    article.save()  # NE! Koristi services.py

# POGRESNO - Vracati JSON za HTMX response
return JsonResponse({"success": True})  # NE! Vracaj HTML fragment

# POGRESNO - Dozvoliti approve bez REVIEW statusa
if article.status in [ArticleStatus.REVIEW, ArticleStatus.DRAFT]:
    article.status = ArticleStatus.READY  # NE! Samo REVIEW -> READY

# POGRESNO - Dozvoliti Bibliotekaru da odobri clanak
# Bibliotekar moze samo submit-ovati, NE review-ovati

# POGRESNO - Kreirati novi permission helper za publisher scoping
def _check_review_publisher(user, article):  # NE! Koristi _check_article_permission

# POGRESNO - Koristiti CBV za review endpoint
class ArticleApproveView(View):  # NE! Koristi FBV za HTMX

# POGRESNO - Dozvoliti vracanje na doradu BEZ komentara
if comment:  # komentar je OBAVEZAN, baciti gresku ako prazan

# POGRESNO - NE resetovati submitted_by/submitted_at pri return
# OBAVEZNO resetovati da Bibliotekar moze ponovo submit-ovati

# POGRESNO - Kreirati novi Django app za workflow
# Sve ide u postojeci articles app

# POGRESNO - Dodavati Alpine.js CDN ponovo
# VEC je ukljucen u article_form.html javascript block
```

### Previous Story Learnings (Story 3.1-3.5)

1. **`_check_article_permission()`** - VEC postoji u views.py. Koristi za review endpoint publisher scoping. (Story 3.2)
2. **HTMX CSRF token** - za HTMX POST iz modala, koristi standardnu Django formu sa `{% csrf_token %}`, NE HTMX POST. (Story 3.3/3.5)
3. **FBV pattern** - Svi HTMX endpoint-i koriste FBV-ove sa `@login_required` i `@require_POST` / `@require_GET`. (Story 3.3)
4. **`select_related` chain** - Uvek ukljuciti `"issue", "issue__publication", "issue__publication__publisher"` za publisher scoping. (Story 3.1)
5. **Django messages** - Koristiti `messages.success()` i `messages.error()` za toast feedback. (Story 3.1)
6. **auditlog** - Article je VEC registrovan. Status promene se automatski beleze. (Story 3.4)
7. **Test pattern** - Factory Boy, pytest-django. (Story 3.4)
8. **services.py** - VEC postoji sa `submit_article_for_review()`, `validate_article_for_submit()`, `InvalidStatusTransition`. Dodati nove funkcije u ISTI fajl. (Story 3.5)
9. **`transaction.atomic()`** - Koristiti za status tranzicije. (Story 3.5)
10. **Modal pattern** - Bootstrap 5 modal + HTMX GET za ucitavanje + htmx:afterSwap JS listener. (Story 3.5)
11. **`can_submit` context** - VEC postoji u ArticleDetailView. Dodati analogni `can_review` context. (Story 3.5)
12. **`is_in_review` context** - VEC postoji. Dodati `is_ready` i `has_revision_comment` po istom patternu. (Story 3.5)
13. **`submitted_by` select_related** - ArticleDetailView VEC ima `select_related("submitted_by")`. Dodati `reviewed_by`, `returned_by`. (Story 3.5)

### Git Commit Pattern

```
story-3-6: feat(articles): implementiraj Editorial Review Process sa approve/return workflow i revision komentarima (Story 3.6)
```

### NFR Requirements

- **FR29:** Urednik moze pregledati clanak za odobrenje - direktna implementacija
- **NFR3:** Admin panel stranice < 5 sekundi - modal se ucitava preko HTMX, minimalan payload
- **NFR12:** Audit log - status promena se automatski belezi (django-auditlog)
- UX zahtev: "Brz pregled, jasne akcije approve/reject, efikasan workflow" - dva jasna dugmeta
- UX zahtev: "Confirm modal za destruktivne akcije" - modal pre approve/return
- UX zahtev: Status badge boje: Draft (narandzasta/secondary), Review (plava/info), Ready (primary), Published (zelena/success)

### Dependencies (Python/Django)

Nema novih Python zavisnosti! Sve je vec instalirano:
- Django 5.2+ (form handling, views, messages)
- HTMX 2.0.8 (CDN - vec u admin_base.html) - za ucitavanje modal sadrzaja
- Bootstrap 5 (CSS framework - vec u admin_base.html) - za modal komponentu
- django-auditlog (automatic logging - vec registrovan)
- Factory Boy + pytest-django (vec u test setup-u)

### Project Structure Notes

- Service logika ide u `doi_portal/doi_portal/articles/services.py` (VEC postoji sa Story 3.5 funkcijama)
- Modal partial-i idu u `doi_portal/doi_portal/templates/articles/partials/` (vec postoji `_submit_review_modal.html`)
- Testovi idu u `doi_portal/doi_portal/articles/tests/test_editorial_review.py` (NOVI fajl)
- URL routes ostaju u `articles` namespace
- NE kreirati novi Django app
- NE kreirati core/exceptions.py - `InvalidStatusTransition` VEC postoji u articles/services.py

### Test Pattern

```python
# articles/tests/test_editorial_review.py - NOVI FAJL

import pytest
from django.urls import reverse

from doi_portal.articles.models import Article, ArticleStatus
from doi_portal.articles.services import (
    InvalidStatusTransition,
    approve_article,
    return_article_for_revision,
)


@pytest.mark.django_db
class TestApproveArticleService:
    """Tests for approve_article service function."""

    def test_approve_valid_review_article(self, review_article, urednik_user):
        """Valid REVIEW article transitions to READY."""
        result = approve_article(review_article, urednik_user)
        assert result.status == ArticleStatus.READY
        assert result.reviewed_by == urednik_user
        assert result.reviewed_at is not None

    def test_approve_rejects_non_review(self, draft_article, urednik_user):
        """Non-REVIEW article raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition):
            approve_article(draft_article, urednik_user)

    def test_approve_clears_revision_comment(self, review_article_with_comment, urednik_user):
        """Approve clears previous revision comment."""
        result = approve_article(review_article_with_comment, urednik_user)
        assert result.revision_comment == ""


@pytest.mark.django_db
class TestReturnArticleForRevisionService:
    """Tests for return_article_for_revision service function."""

    def test_return_valid_review_article(self, review_article, urednik_user):
        """Valid REVIEW article with comment returns to DRAFT."""
        result = return_article_for_revision(review_article, urednik_user, "Dodaj apstrakt")
        assert result.status == ArticleStatus.DRAFT
        assert result.revision_comment == "Dodaj apstrakt"
        assert result.returned_by == urednik_user
        assert result.returned_at is not None

    def test_return_rejects_non_review(self, draft_article, urednik_user):
        """Non-REVIEW article raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition):
            return_article_for_revision(draft_article, urednik_user, "Komentar")

    def test_return_rejects_empty_comment(self, review_article, urednik_user):
        """Empty comment raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition, match="Komentar"):
            return_article_for_revision(review_article, urednik_user, "")

    def test_return_resets_submit_tracking(self, review_article, urednik_user):
        """Return resets submitted_by and submitted_at."""
        result = return_article_for_revision(review_article, urednik_user, "Ispraviti")
        assert result.submitted_by is None
        assert result.submitted_at is None


@pytest.mark.django_db
class TestArticleApproveCheckView:
    """Tests for article_approve_check HTMX GET endpoint."""

    def test_approve_check_valid(self, client, urednik_user, review_article):
        """Approve check for REVIEW article returns is_ready=True."""
        client.force_login(urednik_user)
        url = reverse("articles:article-approve-check", kwargs={"pk": review_article.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "Potvrda odobrenja" in response.content.decode()

    def test_approve_check_rejects_bibliotekar(self, client, bibliotekar_user, review_article):
        """Bibliotekar cannot access approve check."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:article-approve-check", kwargs={"pk": review_article.pk})
        response = client.get(url)
        assert response.status_code == 403


@pytest.mark.django_db
class TestArticleApproveView:
    """Tests for article_approve POST endpoint."""

    def test_approve_success(self, client, urednik_user, review_article):
        """Successful approve redirects with success message."""
        client.force_login(urednik_user)
        url = reverse("articles:article-approve", kwargs={"pk": review_article.pk})
        response = client.post(url)
        assert response.status_code == 302
        review_article.refresh_from_db()
        assert review_article.status == ArticleStatus.READY


@pytest.mark.django_db
class TestArticleReturnForRevisionView:
    """Tests for article_return_for_revision POST endpoint."""

    def test_return_success(self, client, urednik_user, review_article):
        """Successful return with comment redirects with success message."""
        client.force_login(urednik_user)
        url = reverse("articles:article-return", kwargs={"pk": review_article.pk})
        response = client.post(url, {"revision_comment": "Dodaj reference"})
        assert response.status_code == 302
        review_article.refresh_from_db()
        assert review_article.status == ArticleStatus.DRAFT
        assert review_article.revision_comment == "Dodaj reference"

    def test_return_without_comment_fails(self, client, urednik_user, review_article):
        """Return without comment shows error."""
        client.force_login(urednik_user)
        url = reverse("articles:article-return", kwargs={"pk": review_article.pk})
        response = client.post(url, {"revision_comment": ""})
        assert response.status_code == 302  # Redirects with error message
        review_article.refresh_from_db()
        assert review_article.status == ArticleStatus.REVIEW  # Unchanged
```

### References

- [Source: epics.md#Story 3.6: Editorial Review Process]
- [Source: epics.md#Story 3.5: Submit Article for Review - upstream dependency]
- [Source: epics.md#Story 3.7: Article Publishing & Withdrawal - downstream dependency]
- [Source: prd.md#5. Article Management - FR29 (Pregled za odobrenje)]
- [Source: architecture.md#API & Communication Patterns - HTMX endpoints]
- [Source: architecture.md#Implementation Patterns - HTMX Patterns]
- [Source: architecture.md#Data Architecture - RBAC Model]
- [Source: project-context.md#Services Layer (Business Logic)]
- [Source: project-context.md#Error Handling - Custom exceptions, InvalidStatusTransition]
- [Source: project-context.md#HTMX Pravila]
- [Source: project-context.md#Naming Konvencije]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri]
- [Source: ux-design-specification.md#Urednik - Brz pregled, jasne akcije approve/reject]
- [Source: ux-design-specification.md#Decision Patterns - Confirm modal za destruktivne akcije]
- [Source: ux-design-specification.md#Status Badge - Review (plava), Ready (primary)]
- [Source: 3-5-submit-article-for-review.md - HTMX modal pattern, services.py, InvalidStatusTransition]
- [Source: articles/services.py - submit_article_for_review, validate_article_for_submit, InvalidStatusTransition]
- [Source: articles/views.py - _check_article_permission, ArticleDetailView context, FBV patterns]
- [Source: articles/models.py - Article model, ArticleStatus, submitted_by/submitted_at]
- [Source: articles/urls.py - Existing URL patterns and namespace]
- [Source: templates/articles/article_detail.html - Quick Actions, modal containers, htmx:afterSwap]
- [Source: templates/articles/partials/_submit_review_modal.html - Modal template pattern reference]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

No debug issues encountered. All 54 tests passed on first run. All 372 articles tests passed (no regressions).

### Completion Notes List

- Task 1: Added reviewed_by, reviewed_at, revision_comment, returned_by, returned_at fields to Article model. Created and applied migration 0005.
- Task 2: Implemented approve_article() service function with REVIEW->READY transition, reviewed_by/reviewed_at tracking, revision_comment cleanup, transaction.atomic().
- Task 3: Implemented return_article_for_revision() service function with REVIEW->DRAFT transition, revision_comment, returned_by/returned_at, submitted_by/submitted_at reset, comment validation, transaction.atomic().
- Task 4: Created article_approve_check GET FBV with publisher scoping + role check.
- Task 5: Created article_approve POST FBV with service delegation, messages, redirect.
- Task 6: Created article_return_check GET FBV with publisher scoping + role check.
- Task 7: Created article_return_for_revision POST FBV with service delegation, messages, redirect.
- Task 8: Added 4 URL routes for review endpoints (approve-check, approve, return-check, return).
- Task 9: Updated ArticleDetailView context with can_review, is_ready, has_revision_comment. Added select_related for reviewed_by, returned_by.
- Task 10: Updated article_detail.html with review buttons, READY alert, revision comment alert, modal containers, JS.
- Task 11: Created _approve_modal.html with Bootstrap 5 modal, confirmation content, CSRF form.
- Task 12: Created _return_revision_modal.html with Bootstrap 5 modal, required textarea, CSRF form.
- Task 13: Created _check_reviewer_permission() helper for Urednik/Administrator/Superadmin role check.
- Task 14: Created 54 comprehensive tests covering all 21 subtasks: service (15), view (16), permission (11), template (8), integration (4).

### File List

**New Files:**
- `doi_portal/doi_portal/articles/migrations/0005_add_review_tracking_fields_to_article.py`
- `doi_portal/doi_portal/templates/articles/partials/_approve_modal.html`
- `doi_portal/doi_portal/templates/articles/partials/_return_revision_modal.html`
- `doi_portal/doi_portal/articles/tests/test_editorial_review.py`

**Modified Files:**
- `doi_portal/doi_portal/articles/models.py` - Added 5 review tracking fields
- `doi_portal/doi_portal/articles/services.py` - Added approve_article(), return_article_for_revision()
- `doi_portal/doi_portal/articles/views.py` - Added 4 FBVs, _check_reviewer_permission(), ArticleDetailView context updates
- `doi_portal/doi_portal/articles/urls.py` - Added 4 URL routes
- `doi_portal/doi_portal/templates/articles/article_detail.html` - Review buttons, alerts, modals, JS
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Status update
- `_bmad-output/implementation-artifacts/3-6-editorial-review-process.md` - Task checkboxes, Dev Agent Record
