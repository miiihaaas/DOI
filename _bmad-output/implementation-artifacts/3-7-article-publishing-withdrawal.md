# Story 3.7: Article Publishing & Withdrawal

Status: done

## Story

As an **Administrator**,
I want **to publish approved articles and withdraw published articles with reason tracking**,
So that **content lifecycle is properly managed and withdrawn articles remain visible with appropriate notices**.

## Background

Ovo je sedma prica u Epiku 3 (Article Workflow). Implementira poslednje dve status tranzicije u article workflow-u: READY -> PUBLISHED (objava) i PUBLISHED -> WITHDRAWN (povlacenje). Administrator moze objaviti clanak koji je Urednik odobrio, a takodje moze povuci vec objavljeni clanak uz obavezan razlog povlacenja.

**FR Pokrivenost:**
- FR30: Administrator moze objaviti clanak
- FR31: Administrator moze povuci (withdraw) objavljeni clanak
- FR32: Sistem prikazuje withdrawn clanke sa oznakom

**Zavisnosti (sve DONE):**
- Story 3.1: Article Model & Basic Metadata Entry - Article model, ArticleStatus enum (DRAFT, REVIEW, READY, PUBLISHED, WITHDRAWN), ArticleDetailView, ArticleListView
- Story 3.2: Author Management - Author/Affiliation modeli, `_check_article_permission()`
- Story 3.3: PDF Upload - pdf_file, pdf_status, PdfStatus enum
- Story 3.5: Submit Article for Review - `submit_article_for_review()` service, `InvalidStatusTransition`
- Story 3.6: Editorial Review Process - `approve_article()`, `return_article_for_revision()`, `_check_reviewer_permission()`, HTMX modal pattern

**Blokira:**
- Story 3.8: Dashboard Statistics & Pending Items - broji PUBLISHED i WITHDRAWN clanke
- Epic 4 (Public Portal) - prikazuje PUBLISHED clanke javno, prikazuje WITHDRAWN sa oznakom

## Acceptance Criteria

1. **Given** ulogovan Administrator
   **When** pregledava listu clanaka ili article detail
   **Then** clanci sa statusom READY su vidljivo oznaceni kao spremni za objavu
   **And** "Objavi" akcija je dostupna SAMO za READY status

2. **Given** Administrator klikne "Objavi" na READY clanku
   **When** potvrdi akciju u confirmation modalu
   **Then** status clanka se menja iz READY u PUBLISHED
   **And** cuva se `published_by` i `published_at` timestamp
   **And** toast notifikacija: "Clanak objavljen."
   **And** clanak postaje vidljiv na javnom portalu (buduci Epic 4)

3. **Given** clanak je PUBLISHED
   **When** Administrator pregledava clanak
   **Then** status badge prikazuje "Objavljeno" (bg-success)
   **And** "Povuci" akcija je dostupna
   **And** upozorenje o implikacijama povlacenja je prikazano u modalu

4. **Given** Administrator klikne "Povuci"
   **When** unese razlog povlacenja (obavezan)
   **Then** status clanka se menja iz PUBLISHED u WITHDRAWN
   **And** cuva se `withdrawal_reason`, `withdrawn_by`, `withdrawn_at`
   **And** toast notifikacija: "Clanak povucen."
   **And** clanak ostaje vidljiv na javnom portalu sa "POVUCENO" oznakom

5. **Given** clanak je WITHDRAWN
   **When** Administrator ili korisnik pregledava clanak u admin panelu
   **Then** status badge prikazuje "Povuceno" (bg-danger)
   **And** withdrawal razlog i datum su vidljivi
   **And** nema daljih status akcija (terminal state)

6. **Given** korisnik nema Administrator/Superadmin ulogu
   **When** pokusava da pristupi publish ili withdraw endpointima
   **Then** pristup je odbijen sa 403 Forbidden

7. **Given** clanak NIJE u ocekivanom statusu (npr. DRAFT za publish, READY za withdraw)
   **When** korisnik pokusava publish ili withdraw (direktnim URL-om)
   **Then** sistem odbija tranziciju
   **And** prikazuje odgovarajucu gresku

8. **Given** Urednik ili Bibliotekar
   **When** pregledava READY ili PUBLISHED clanak
   **Then** ne vide publish/withdraw dugmad (samo Administrator/Superadmin)

## Tasks / Subtasks

- [x]Task 1: Dodati `published_by`, `published_at`, `withdrawal_reason`, `withdrawn_by`, `withdrawn_at` polja na Article model (AC: #2, #4)
  - [x]1.1 U `articles/models.py` dodati nova polja u TRACKING sekciju, NAKON `returned_at`
  - [x]1.2 `published_by = ForeignKey(User, null=True, blank=True, related_name="published_articles")`
  - [x]1.3 `published_at = DateTimeField(null=True, blank=True)`
  - [x]1.4 `withdrawal_reason = TextField(blank=True)` - razlog povlacenja
  - [x]1.5 `withdrawn_by = ForeignKey(User, null=True, blank=True, related_name="withdrawn_articles")`
  - [x]1.6 `withdrawn_at = DateTimeField(null=True, blank=True)`
  - [x]1.7 Kreirati migraciju: `makemigrations articles` (0006)
  - [x]1.8 Primeniti migraciju: `migrate`

- [x]Task 2: Implementirati `publish_article()` service funkciju (AC: #2, #7)
  - [x]2.1 U `articles/services.py` dodati `publish_article(article, user)` funkciju
  - [x]2.2 Validirati da je `article.status == ArticleStatus.READY`
  - [x]2.3 Promeniti status na `ArticleStatus.PUBLISHED`
  - [x]2.4 Sacuvati `published_by = user` i `published_at = timezone.now()`
  - [x]2.5 Baciti `InvalidStatusTransition` za nevalidne tranzicije
  - [x]2.6 Koristiti `transaction.atomic()` sa `select_for_update()` (kao approve_article)

- [x]Task 3: Implementirati `withdraw_article()` service funkciju (AC: #4, #7)
  - [x]3.1 U `articles/services.py` dodati `withdraw_article(article, user, reason)` funkciju
  - [x]3.2 Validirati da je `article.status == ArticleStatus.PUBLISHED`
  - [x]3.3 Validirati da je `reason` neprazan string
  - [x]3.4 Promeniti status na `ArticleStatus.WITHDRAWN`
  - [x]3.5 Sacuvati `withdrawal_reason = reason`, `withdrawn_by = user`, `withdrawn_at = timezone.now()`
  - [x]3.6 Baciti `InvalidStatusTransition` za nevalidne tranzicije ili prazan razlog
  - [x]3.7 Koristiti `transaction.atomic()` sa `select_for_update()`

- [x]Task 4: Kreirati publish HTMX check endpoint - `article_publish_check` FBV (AC: #1, #2)
  - [x]4.1 U `articles/views.py` dodati `article_publish_check(request, pk)` GET FBV
  - [x]4.2 Proveriti da je clanak u READY statusu
  - [x]4.3 Vratiti HTML modal fragment sa confirmation sadrzajem
  - [x]4.4 Koristiti `_check_article_permission()` za publisher scoping
  - [x]4.5 Koristiti `_check_admin_permission(user)` helper za Administrator/Superadmin check

- [x]Task 5: Kreirati publish POST endpoint - `article_publish` FBV (AC: #2, #6, #7)
  - [x]5.1 U `articles/views.py` dodati `article_publish(request, pk)` POST FBV
  - [x]5.2 Pozvati `publish_article()` service funkciju
  - [x]5.3 Na uspeh: dodati success poruku, redirect na article detail
  - [x]5.4 Na gresku (InvalidStatusTransition): dodati error poruku, redirect
  - [x]5.5 Koristiti `_check_article_permission()` i `_check_admin_permission()`
  - [x]5.6 Dekorisati sa `@login_required` i `@require_POST`

- [x]Task 6: Kreirati withdraw HTMX check endpoint - `article_withdraw_check` FBV (AC: #3, #4)
  - [x]6.1 U `articles/views.py` dodati `article_withdraw_check(request, pk)` GET FBV
  - [x]6.2 Proveriti da je clanak u PUBLISHED statusu
  - [x]6.3 Vratiti HTML modal fragment sa textarea za razlog i upozorenjem
  - [x]6.4 Koristiti `_check_article_permission()` i `_check_admin_permission()`

- [x]Task 7: Kreirati withdraw POST endpoint - `article_withdraw` FBV (AC: #4, #6, #7)
  - [x]7.1 U `articles/views.py` dodati `article_withdraw(request, pk)` POST FBV
  - [x]7.2 Pozvati `withdraw_article()` service funkciju
  - [x]7.3 Na uspeh: dodati success poruku, redirect na article detail
  - [x]7.4 Na gresku: dodati error poruku, redirect
  - [x]7.5 Koristiti `_check_article_permission()` i `_check_admin_permission()`
  - [x]7.6 Dekorisati sa `@login_required` i `@require_POST`

- [x]Task 8: Dodati URL routes za publish/withdraw endpointe (AC: #1, #2, #3, #4)
  - [x]8.1 U `articles/urls.py` dodati:
    - `<int:pk>/publish-check/` (name: article-publish-check) - GET
    - `<int:pk>/publish/` (name: article-publish) - POST
    - `<int:pk>/withdraw-check/` (name: article-withdraw-check) - GET
    - `<int:pk>/withdraw/` (name: article-withdraw) - POST

- [x]Task 9: Kreirati `_check_admin_permission(user)` helper (AC: #6, #8)
  - [x]9.1 U `articles/views.py` dodati helper pored `_check_reviewer_permission()`
  - [x]9.2 Proverava da korisnik pripada grupi Administrator ili je Superadmin
  - [x]9.3 Baca PermissionDenied ako nema odgovarajucu ulogu
  - [x]9.4 NE ukljucuje Urednik - samo Administrator i Superadmin mogu publish/withdraw

- [x]Task 10: Azurirati ArticleDetailView context za publish/withdraw akcije (AC: #1, #3, #5, #8)
  - [x]10.1 Dodati `can_publish` context varijablu (Administrator/Superadmin + READY status)
  - [x]10.2 Dodati `can_withdraw` context varijablu (Administrator/Superadmin + PUBLISHED status)
  - [x]10.3 Dodati `is_published` context varijablu (status == PUBLISHED)
  - [x]10.4 Dodati `is_withdrawn` context varijablu (status == WITHDRAWN)
  - [x]10.5 Dodati `has_withdrawal_reason` context varijablu
  - [x]10.6 Dodati `select_related("published_by", "withdrawn_by")` u get_queryset()

- [x]Task 11: Azurirati article_detail.html - publish/withdraw akcije i status alerts (AC: #1-#5)
  - [x]11.1 Dodati "Objavi" dugme u Quick Actions (samo za READY + Admin/Superadmin)
  - [x]11.2 Dodati "Povuci" dugme u Quick Actions (samo za PUBLISHED + Admin/Superadmin)
  - [x]11.3 "Objavi" dugme pokrece HTMX GET na `article-publish-check` endpoint
  - [x]11.4 "Povuci" dugme pokrece HTMX GET na `article-withdraw-check` endpoint
  - [x]11.5 Dodati alert za PUBLISHED status: "Clanak je objavljen."
  - [x]11.6 Dodati alert za WITHDRAWN status sa razlogom povlacenja
  - [x]11.7 Dodati modal containere za publish i withdraw modale
  - [x]11.8 Prosiriti htmx:afterSwap JS listener za nove modale

- [x]Task 12: Kreirati HTMX partial template za publish modal (AC: #2)
  - [x]12.1 Kreirati `templates/articles/partials/_publish_modal.html`
  - [x]12.2 Bootstrap 5 modal sa confirmation sadrzajem
  - [x]12.3 Confirmation tekst + "Objavi" dugme (POST form na `article-publish`)
  - [x]12.4 Cancel dugme za zatvaranje modala

- [x]Task 13: Kreirati HTMX partial template za withdraw modal (AC: #4)
  - [x]13.1 Kreirati `templates/articles/partials/_withdraw_modal.html`
  - [x]13.2 Bootstrap 5 modal sa upozorenjem o implikacijama
  - [x]13.3 Textarea za obavezan razlog povlacenja (required)
  - [x]13.4 Upozorenje: "Povuceni clanak ostaje vidljiv sa oznakom POVUCENO"
  - [x]13.5 "Povuci clanak" dugme (POST form na `article-withdraw`)
  - [x]13.6 Cancel dugme za zatvaranje modala

- [x]Task 14: Kreirati testove (AC: #1-#8)
  - [x]14.1 Service testovi: `publish_article` sa validnim READY clankom
  - [x]14.2 Service testovi: `publish_article` odbija ne-READY clanak (svaki status)
  - [x]14.3 Service testovi: `publish_article` cuva published_by/published_at
  - [x]14.4 Service testovi: `withdraw_article` sa validnim PUBLISHED clankom i razlogom
  - [x]14.5 Service testovi: `withdraw_article` odbija ne-PUBLISHED clanak
  - [x]14.6 Service testovi: `withdraw_article` odbija prazan razlog
  - [x]14.7 Service testovi: `withdraw_article` cuva withdrawal_reason/withdrawn_by/withdrawn_at
  - [x]14.8 View testovi: `article_publish_check` GET za READY clanak (Administrator)
  - [x]14.9 View testovi: `article_publish_check` odbija za Urednik (403)
  - [x]14.10 View testovi: `article_publish_check` odbija za Bibliotekar (403)
  - [x]14.11 View testovi: `article_publish` POST sa uspesnim publish-om
  - [x]14.12 View testovi: `article_publish` POST sa ne-READY clankom
  - [x]14.13 View testovi: `article_withdraw_check` GET za PUBLISHED clanak (Administrator)
  - [x]14.14 View testovi: `article_withdraw_check` odbija za Urednik (403)
  - [x]14.15 View testovi: `article_withdraw` POST sa razlogom
  - [x]14.16 View testovi: `article_withdraw` POST bez razloga (greska)
  - [x]14.17 Permission testovi: publisher scoping za publish/withdraw endpointe
  - [x]14.18 Permission testovi: Urednik ne moze publish/withdraw
  - [x]14.19 Permission testovi: Bibliotekar ne moze publish/withdraw
  - [x]14.20 Permission testovi: Superadmin moze publish/withdraw
  - [x]14.21 Template testovi: dugmad vidljiva samo za odgovarajuci status + Administrator
  - [x]14.22 Integration testovi: kompletni flow READY -> PUBLISHED (publish)
  - [x]14.23 Integration testovi: kompletni flow PUBLISHED -> WITHDRAWN (withdraw)
  - [x]14.24 Integration testovi: DRAFT -> REVIEW -> READY -> PUBLISHED -> WITHDRAWN (full lifecycle)
  - [x]14.25 Koristiti Factory Boy, pytest-django iz postojeceg test setup-a

## Dev Notes

### KRITICNO: Services Layer Pattern (project-context.md)

Sva business logika za status tranzicije ide u `articles/services.py`. VEC postoji `submit_article_for_review()`, `approve_article()`, `return_article_for_revision()` i `InvalidStatusTransition` - ova prica DODAJE nove service funkcije u isti fajl.

```python
# articles/services.py - DODATI uz postojece funkcije

def publish_article(article: Article, user) -> Article:
    """
    Publish article (READY -> PUBLISHED).

    Args:
        article: Article instance to publish
        user: User performing the publication (Administrator/Superadmin)

    Returns:
        Updated Article instance

    Raises:
        InvalidStatusTransition: If article is not in READY status
    """
    if article.status != ArticleStatus.READY:
        raise InvalidStatusTransition(
            "Samo članci spremni za objavu mogu biti objavljeni."
        )

    with transaction.atomic():
        article = Article.objects.select_for_update().get(pk=article.pk)
        if article.status != ArticleStatus.READY:
            raise InvalidStatusTransition(
                "Samo članci spremni za objavu mogu biti objavljeni."
            )
        article.status = ArticleStatus.PUBLISHED
        article.published_by = user
        article.published_at = timezone.now()
        article.save(update_fields=[
            "status", "published_by", "published_at", "updated_at",
        ])

    return article


def withdraw_article(article: Article, user, reason: str) -> Article:
    """
    Withdraw published article (PUBLISHED -> WITHDRAWN).

    Args:
        article: Article instance to withdraw
        user: User performing the withdrawal (Administrator/Superadmin)
        reason: Withdrawal reason (required)

    Returns:
        Updated Article instance

    Raises:
        InvalidStatusTransition: If article is not PUBLISHED or reason is empty
    """
    if article.status != ArticleStatus.PUBLISHED:
        raise InvalidStatusTransition(
            "Samo objavljeni članci mogu biti povučeni."
        )

    if not reason or not reason.strip():
        raise InvalidStatusTransition(
            "Razlog povlačenja je obavezan."
        )

    with transaction.atomic():
        article = Article.objects.select_for_update().get(pk=article.pk)
        if article.status != ArticleStatus.PUBLISHED:
            raise InvalidStatusTransition(
                "Samo objavljeni članci mogu biti povučeni."
            )
        article.status = ArticleStatus.WITHDRAWN
        article.withdrawal_reason = reason.strip()
        article.withdrawn_by = user
        article.withdrawn_at = timezone.now()
        article.save(update_fields=[
            "status", "withdrawal_reason", "withdrawn_by",
            "withdrawn_at", "updated_at",
        ])

    return article
```

### Article Model Migracija

Dodati nova polja u TRACKING sekciju Article modela, NAKON `returned_at` a PRE `created_at`:

```python
# U Article modelu, u === TRACKING === sekciji, NAKON returned_at

published_by = models.ForeignKey(
    "users.User",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="published_articles",
    verbose_name=_("Objavio"),
)
published_at = models.DateTimeField(
    _("Objavljeno"),
    null=True,
    blank=True,
)
withdrawal_reason = models.TextField(
    _("Razlog povlačenja"),
    blank=True,
    help_text=_("Razlog povlačenja objavljenog članka."),
)
withdrawn_by = models.ForeignKey(
    "users.User",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="withdrawn_articles",
    verbose_name=_("Povukao"),
)
withdrawn_at = models.DateTimeField(
    _("Povučeno"),
    null=True,
    blank=True,
)
```

### Admin Permission Helper

```python
# articles/views.py - DODATI pored _check_reviewer_permission()

def _check_admin_permission(user):
    """
    Check if user has Administrator/Superadmin role.

    Raises PermissionDenied if user is not Administrator or Superadmin.
    This is stricter than _check_reviewer_permission - does NOT include Urednik.
    Only Administrator and Superadmin can publish/withdraw articles.
    Call AFTER _check_article_permission() (publisher scoping + admin role check).
    """
    if user.is_superuser:
        return
    group_names = _get_user_group_names(user)
    if group_names & {"Administrator", "Superadmin"}:
        return
    raise PermissionDenied
```

**VAZNO:** Urednik NE moze objaviti ili povuci clanak. Samo Administrator i Superadmin.
Redosled provere u endpointu:
1. `_check_article_permission(user, article)` - publisher scoping
2. `_check_admin_permission(user)` - admin role check

### Publish/Withdraw Endpoints (HTMX FBV)

```python
# articles/views.py - DODATI (Story 3.7)

@login_required
@require_GET
def article_publish_check(request, pk):
    """
    Check/confirm article publishing via HTMX GET.
    Returns modal content for publish confirmation.
    """
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=pk,
    )
    _check_article_permission(request.user, article)
    _check_admin_permission(request.user)

    errors = []
    if article.status != ArticleStatus.READY:
        errors.append("Članak nije u statusu Spremno za objavu.")

    return render(request, "articles/partials/_publish_modal.html", {
        "article": article,
        "errors": errors,
        "is_ready": len(errors) == 0,
    })


@login_required
@require_POST
def article_publish(request, pk):
    """
    Publish article (READY -> PUBLISHED) via POST.
    Delegates to publish_article() service function.
    """
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=pk,
    )
    _check_article_permission(request.user, article)
    _check_admin_permission(request.user)

    try:
        publish_article(article, request.user)
        messages.success(request, "Članak objavljen.")
    except InvalidStatusTransition as e:
        messages.error(request, str(e))

    return HttpResponseRedirect(reverse("articles:detail", kwargs={"pk": pk}))


@login_required
@require_GET
def article_withdraw_check(request, pk):
    """
    Check/prepare withdrawal form via HTMX GET.
    Returns modal content with reason textarea and warnings.
    """
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=pk,
    )
    _check_article_permission(request.user, article)
    _check_admin_permission(request.user)

    errors = []
    if article.status != ArticleStatus.PUBLISHED:
        errors.append("Članak nije u statusu Objavljeno.")

    return render(request, "articles/partials/_withdraw_modal.html", {
        "article": article,
        "errors": errors,
        "is_ready": len(errors) == 0,
    })


@login_required
@require_POST
def article_withdraw(request, pk):
    """
    Withdraw article (PUBLISHED -> WITHDRAWN) via POST.
    Delegates to withdraw_article() service function.
    """
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=pk,
    )
    _check_article_permission(request.user, article)
    _check_admin_permission(request.user)

    reason = request.POST.get("withdrawal_reason", "").strip()

    try:
        withdraw_article(article, request.user, reason)
        messages.success(request, "Članak povučen.")
    except InvalidStatusTransition as e:
        messages.error(request, str(e))

    return HttpResponseRedirect(reverse("articles:detail", kwargs={"pk": pk}))
```

### URL Routes

```python
# articles/urls.py - DODATI u urlpatterns

# Publish & Withdraw HTMX endpoints (Story 3.7)
path(
    "<int:pk>/publish-check/",
    views.article_publish_check,
    name="article-publish-check",
),
path(
    "<int:pk>/publish/",
    views.article_publish,
    name="article-publish",
),
path(
    "<int:pk>/withdraw-check/",
    views.article_withdraw_check,
    name="article-withdraw-check",
),
path(
    "<int:pk>/withdraw/",
    views.article_withdraw,
    name="article-withdraw",
),
```

### Publish Modal Template

```html
<!-- templates/articles/partials/_publish_modal.html -->
<div class="modal-dialog">
    <div class="modal-content">
        <div class="modal-header">
            <h5 class="modal-title">
                {% if is_ready %}
                <i class="bi bi-globe me-2 text-success"></i>Potvrda objavljivanja
                {% else %}
                <i class="bi bi-exclamation-triangle me-2 text-warning"></i>Nije moguće objaviti
                {% endif %}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
            {% if is_ready %}
            <p>Članak <strong>{{ article.title }}</strong> će biti objavljen i postati vidljiv na javnom portalu.</p>
            <p class="text-muted mb-0">
                <i class="bi bi-info-circle me-1"></i>
                Nakon objavljivanja, članak će biti dostupan posetiocima portala.
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
            <form method="post" action="{% url 'articles:article-publish' pk=article.pk %}" style="display:inline;">
                {% csrf_token %}
                <button type="submit" class="btn btn-success">
                    <i class="bi bi-globe me-1"></i>Objavi
                </button>
            </form>
            {% else %}
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Zatvori</button>
            {% endif %}
        </div>
    </div>
</div>
```

### Withdraw Modal Template

```html
<!-- templates/articles/partials/_withdraw_modal.html -->
<div class="modal-dialog">
    <div class="modal-content">
        <div class="modal-header">
            <h5 class="modal-title">
                {% if is_ready %}
                <i class="bi bi-x-circle me-2 text-danger"></i>Povlačenje članka
                {% else %}
                <i class="bi bi-exclamation-triangle me-2 text-warning"></i>Nije moguće povući
                {% endif %}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        {% if is_ready %}
        <form method="post" action="{% url 'articles:article-withdraw' pk=article.pk %}">
            {% csrf_token %}
            <div class="modal-body">
                <div class="alert alert-danger mb-3">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    <strong>Upozorenje:</strong> Povučeni članak ostaje vidljiv na javnom portalu sa oznakom "POVUČENO".
                    Metapodaci ostaju dostupni, ali PDF može biti nedostupan.
                </div>
                <p>Članak <strong>{{ article.title }}</strong> će biti povučen.</p>
                <div class="mb-3">
                    <label for="withdrawal_reason" class="form-label fw-bold">Razlog povlačenja <span class="text-danger">*</span></label>
                    <textarea class="form-control" id="withdrawal_reason" name="withdrawal_reason"
                              rows="4" required
                              placeholder="Navedite razlog povlačenja članka..."></textarea>
                    <div class="form-text">Razlog povlačenja će biti javno prikazan na stranici članka.</div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Otkaži</button>
                <button type="submit" class="btn btn-danger">
                    <i class="bi bi-x-circle me-1"></i>Povuci članak
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

U Quick Actions sekciju dodati publish/withdraw dugmad (NAKON review dugmadi):

```html
<!-- U Quick Actions card, nakon review dugmadi -->
{% if can_publish %}
<button type="button" class="list-group-item list-group-item-action text-success"
        hx-get="{% url 'articles:article-publish-check' pk=article.pk %}"
        hx-target="#publish-modal-container"
        hx-swap="innerHTML">
    <i class="bi bi-globe me-2"></i>Objavi
</button>
{% endif %}
{% if can_withdraw %}
<button type="button" class="list-group-item list-group-item-action text-danger"
        hx-get="{% url 'articles:article-withdraw-check' pk=article.pk %}"
        hx-target="#withdraw-modal-container"
        hx-swap="innerHTML">
    <i class="bi bi-x-circle me-2"></i>Povuci
</button>
{% endif %}
```

Dodati modal containere na dno stranice (pored postojecih):

```html
<!-- Publish Modal Container (Story 3.7) -->
<div class="modal fade" id="publishModal" tabindex="-1">
    <div id="publish-modal-container">
        <!-- HTMX will inject modal content here -->
    </div>
</div>

<!-- Withdraw Modal Container (Story 3.7) -->
<div class="modal fade" id="withdrawModal" tabindex="-1">
    <div id="withdraw-modal-container">
        <!-- HTMX will inject modal content here -->
    </div>
</div>
```

Prosiriti JavaScript htmx:afterSwap listener:

```javascript
// DODATI u postojeci htmx:afterSwap listener
if (event.detail.target.id === 'publish-modal-container') {
    bootstrap.Modal.getOrCreateInstance(document.getElementById('publishModal')).show();
}
if (event.detail.target.id === 'withdraw-modal-container') {
    bootstrap.Modal.getOrCreateInstance(document.getElementById('withdrawModal')).show();
}
```

Dodati PUBLISHED status alert (NAKON is_ready alert-a):

```html
{% if is_published %}
<div class="alert alert-success mb-4">
    <i class="bi bi-globe me-2"></i>
    <strong>Članak je objavljen.</strong>
    {% if article.published_at %}
    <br><small class="text-muted">Objavljeno: {{ article.published_at|date:"d.m.Y. H:i" }}
    {% if article.published_by %} od {{ article.published_by }}{% endif %}</small>
    {% endif %}
</div>
{% endif %}
```

Dodati WITHDRAWN status alert (NAKON published alert-a):

```html
{% if is_withdrawn %}
<div class="alert alert-danger mb-4">
    <i class="bi bi-x-circle me-2"></i>
    <strong>Članak je povučen.</strong>
    {% if article.withdrawal_reason %}
    <p class="mb-0 mt-1"><strong>Razlog:</strong> {{ article.withdrawal_reason }}</p>
    {% endif %}
    {% if article.withdrawn_at %}
    <small class="text-muted">Povučeno: {{ article.withdrawn_at|date:"d.m.Y. H:i" }}
    {% if article.withdrawn_by %} od {{ article.withdrawn_by }}{% endif %}</small>
    {% endif %}
</div>
{% endif %}
```

### ArticleDetailView Context Izmene

```python
# U ArticleDetailView.get_context_data(), DODATI:

# Story 3.7: Publish/Withdraw action context
context["can_publish"] = (
    flags["is_admin"]
) and self.object.status == ArticleStatus.READY

context["can_withdraw"] = (
    flags["is_admin"]
) and self.object.status == ArticleStatus.PUBLISHED

context["is_published"] = self.object.status == ArticleStatus.PUBLISHED
context["is_withdrawn"] = self.object.status == ArticleStatus.WITHDRAWN

context["has_withdrawal_reason"] = bool(
    self.object.withdrawal_reason
    and self.object.status == ArticleStatus.WITHDRAWN
)
```

**NAPOMENA:** `flags["is_admin"]` vec proverava Superadmin, Administrator i is_superuser u PublisherScopedMixin. NE treba dodatna provera. Samo proveravati `flags["is_admin"]` za publish/withdraw akcije jer je to dovoljno.

### select_related Update

U ArticleDetailView.get_queryset() DODATI `"published_by"` i `"withdrawn_by"` u select_related:

```python
def get_queryset(self):
    queryset = super().get_queryset().select_related(
        "issue", "issue__publication", "issue__publication__publisher",
        "created_by", "submitted_by", "reviewed_by", "returned_by",
        "published_by", "withdrawn_by",  # Story 3.7
    )
    return self.get_scoped_queryset(queryset)
```

### Status Tranzicije Kompletne

```
DRAFT -> REVIEW      (Story 3.5: submit_article_for_review)
REVIEW -> READY      (Story 3.6: approve_article)
REVIEW -> DRAFT      (Story 3.6: return_article_for_revision)
READY -> PUBLISHED   (Story 3.7: publish_article)
PUBLISHED -> WITHDRAWN (Story 3.7: withdraw_article)
```

WITHDRAWN je terminal state - nema daljih tranzicija.

### HTMX Modal Pattern (KRITICNO)

ISTI pattern kao Story 3.5 i 3.6:

1. Dugme ima `hx-get` atribut - ucitava sadrzaj modala sa servera
2. HTMX response ide u odgovarajuci modal container
3. JavaScript `htmx:afterSwap` listener otvara Bootstrap modal
4. Confirmation/submit forma unutar modala koristi standardni `<form method="post">` (NE HTMX POST) - jer POST treba da uradi redirect
5. CSRF token: forma unutar modala MORA imati `{% csrf_token %}`
6. Withdraw modal ima `<textarea required>` za obavezan razlog (isti pattern kao return modal)

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/templates/articles/partials/_publish_modal.html        # Publish confirmation modal
doi_portal/doi_portal/templates/articles/partials/_withdraw_modal.html       # Withdraw modal sa textarea
doi_portal/doi_portal/articles/tests/test_publish_withdraw.py                # Publish/withdraw testovi
doi_portal/doi_portal/articles/migrations/0006_*.py                          # Migration za nova polja
```

### Fajlovi za modifikaciju (POSTOJECI)

- `doi_portal/doi_portal/articles/models.py` - Dodati published_by, published_at, withdrawal_reason, withdrawn_by, withdrawn_at polja
- `doi_portal/doi_portal/articles/services.py` - Dodati publish_article(), withdraw_article()
- `doi_portal/doi_portal/articles/views.py` - Dodati 4 nova FBV-a + _check_admin_permission() + context updates
- `doi_portal/doi_portal/articles/urls.py` - Dodati 4 nova URL route-a
- `doi_portal/doi_portal/templates/articles/article_detail.html` - Publish/withdraw dugmad, modali, alerts, JS

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

Svi UI tekstovi MORAJU koristiti ispravne srpske dijakritike:

| Kontekst | ISPRAVNO |
|----------|----------|
| Publish dugme | "Objavi" |
| Withdraw dugme | "Povuci" |
| Cancel dugme | "Otkazi" |
| Close dugme | "Zatvori" |
| Publish modal title | "Potvrda objavljivanja" |
| Withdraw modal title | "Povlacenje clanka" |
| Publish modal body | "Clanak ... ce biti objavljen i postati vidljiv na javnom portalu." |
| Withdraw modal body | "Clanak ... ce biti povucen." |
| Withdraw warning | "Povuceni clanak ostaje vidljiv sa oznakom POVUCENO" |
| Reason label | "Razlog povlacenja" |
| Reason placeholder | "Navedite razlog povlacenja clanka..." |
| Reason help | "Razlog povlacenja ce biti javno prikazan na stranici clanka." |
| Toast publish | "Clanak objavljen." |
| Toast withdraw | "Clanak povucen." |
| Error: not READY | "Samo clanci spremni za objavu mogu biti objavljeni." |
| Error: not PUBLISHED | "Samo objavljeni clanci mogu biti povuceni." |
| Error: no reason | "Razlog povlacenja je obavezan." |
| PUBLISHED alert | "Clanak je objavljen." |
| WITHDRAWN alert | "Clanak je povucen." |
| WITHDRAWN reason | "Razlog: ..." |

**NAPOMENA:** U template HTML fajlovima i Python string literalima koristiti `c` umesto `c` gde je potrebno: `Clanak` -> `Clanak` (vec u ASCII u HTML-u, ali verbose_name i UI tekstovi MORAJU koristiti UTF-8 srpske dijakritike: `c` = `c`, `s` = `s`, `z` = `z`, itd.). Videti primere u Dev Notes code blocks-ovima iznad - svi string literali koriste ispravne karaktere.

### Anti-Patterns (ZABRANJENO)

```python
# POGRESNO - Status tranzicija direktno u view-u
def publish_view(request, pk):
    article.status = ArticleStatus.PUBLISHED
    article.save()  # NE! Koristi services.py

# POGRESNO - Vracati JSON za HTMX response
return JsonResponse({"success": True})  # NE! Vracaj HTML fragment

# POGRESNO - Dozvoliti publish bez READY statusa
if article.status in [ArticleStatus.READY, ArticleStatus.REVIEW]:
    article.status = ArticleStatus.PUBLISHED  # NE! Samo READY -> PUBLISHED

# POGRESNO - Dozvoliti Uredniku da objavi clanak
# Urednik moze samo odobriti (REVIEW -> READY), NE objaviti

# POGRESNO - Dozvoliti Bibliotekaru da objavi ili povuce clanak
# Bibliotekar moze samo submit-ovati, NE publish/withdraw

# POGRESNO - Kreirati novi permission helper za publisher scoping
def _check_publish_publisher(user, article):  # NE! Koristi _check_article_permission

# POGRESNO - Koristiti CBV za publish/withdraw endpoint
class ArticlePublishView(View):  # NE! Koristi FBV za HTMX

# POGRESNO - Dozvoliti withdraw BEZ razloga
if reason:  # razlog je OBAVEZAN, baciti gresku ako prazan

# POGRESNO - Ukloniti withdrawn clanak sa javnog portala
# WITHDRAWN clanci ostaju VIDLJIVI sa oznakom - NE brisati

# POGRESNO - Kreirati novi Django app za workflow
# Sve ide u postojeci articles app

# POGRESNO - Kreirati _check_publisher_permission umesto _check_admin_permission
# Za publish/withdraw koristiti NOVI _check_admin_permission (Administrator + Superadmin ONLY)
# NE koristiti _check_reviewer_permission (ukljucuje Urednik koji NE SME publish/withdraw)
```

### Previous Story Learnings (Story 3.1-3.6)

1. **`_check_article_permission()`** - VEC postoji u views.py. Koristi za publish/withdraw endpoint publisher scoping. (Story 3.2)
2. **`_get_user_group_names(user)`** - VEC postoji, keshira group names. Koristi u `_check_admin_permission()`. (Story 3.6)
3. **HTMX CSRF token** - za HTMX POST iz modala, koristi standardnu Django formu sa `{% csrf_token %}`, NE HTMX POST. (Story 3.3/3.5)
4. **FBV pattern** - Svi HTMX endpoint-i koriste FBV-ove sa `@login_required` i `@require_POST` / `@require_GET`. (Story 3.3)
5. **`select_related` chain** - Uvek ukljuciti `"issue", "issue__publication", "issue__publication__publisher"` za publisher scoping. (Story 3.1)
6. **Django messages** - Koristiti `messages.success()` i `messages.error()` za toast feedback. (Story 3.1)
7. **auditlog** - Article je VEC registrovan. Status promene se automatski beleze. (Story 3.4)
8. **Test pattern** - Factory Boy, pytest-django. (Story 3.4)
9. **services.py** - VEC postoji sa `submit_article_for_review()`, `approve_article()`, `return_article_for_revision()`, `InvalidStatusTransition`. Dodati nove funkcije u ISTI fajl. (Story 3.5/3.6)
10. **`transaction.atomic()` + `select_for_update()`** - Koristiti za status tranzicije (concurrent request zaštita). (Story 3.6)
11. **Modal pattern** - Bootstrap 5 modal + HTMX GET za ucitavanje + htmx:afterSwap JS listener. `bootstrap.Modal.getOrCreateInstance()` za otvaranje. (Story 3.5/3.6)
12. **`flags["is_admin"]`** - VEC proverava Administrator, Superadmin i is_superuser u PublisherScopedMixin._get_user_role_flags(). (Story 3.1)
13. **`can_submit`, `can_review` context** - VEC postoje u ArticleDetailView. Dodati analogni `can_publish`, `can_withdraw`. (Story 3.5/3.6)
14. **`is_in_review`, `is_ready` context** - VEC postoje. Dodati `is_published`, `is_withdrawn` po istom patternu. (Story 3.5/3.6)
15. **`_check_reviewer_permission()`** - Ukljucuje Urednik. Za publish/withdraw kreirati STRIKTINIJI `_check_admin_permission()` koji NE ukljucuje Urednik. (Story 3.6)
16. **Return modal pattern** - Modal sa required textarea za razlog. Koristiti isti pattern za withdraw modal. (Story 3.6)

### Git Commit Pattern

```
story-3-7: feat(articles): implementiraj Article Publishing & Withdrawal sa publish/withdraw akcijama i withdrawal reason tracking (Story 3.7)
```

### NFR Requirements

- **FR30:** Administrator moze objaviti clanak - direktna implementacija
- **FR31:** Administrator moze povuci (withdraw) objavljeni clanak - direktna implementacija
- **FR32:** Sistem prikazuje withdrawn clanke sa oznakom - withdrawal alert u article_detail.html
- **NFR3:** Admin panel stranice < 5 sekundi - modal se ucitava preko HTMX, minimalan payload
- **NFR12:** Audit log - status promena se automatski belezi (django-auditlog)
- UX zahtev: Status badge boje: Published (zelena/bg-success), Withdrawn (crvena/bg-danger)
- UX zahtev: "Confirm modal za destruktivne akcije" - modal pre publish/withdraw

### Dependencies (Python/Django)

Nema novih Python zavisnosti! Sve je vec instalirano:
- Django 5.2+ (form handling, views, messages)
- HTMX 2.0.8 (CDN - vec u admin_base.html) - za ucitavanje modal sadrzaja
- Bootstrap 5 (CSS framework - vec u admin_base.html) - za modal komponentu
- django-auditlog (automatic logging - vec registrovan)
- Factory Boy + pytest-django (vec u test setup-u)

### Project Structure Notes

- Service logika ide u `doi_portal/doi_portal/articles/services.py` (VEC postoji sa Story 3.5/3.6 funkcijama)
- Modal partial-i idu u `doi_portal/doi_portal/templates/articles/partials/` (vec postoje `_approve_modal.html`, `_return_revision_modal.html`)
- Testovi idu u `doi_portal/doi_portal/articles/tests/test_publish_withdraw.py` (NOVI fajl)
- URL routes ostaju u `articles` namespace
- NE kreirati novi Django app
- NE kreirati core/exceptions.py - `InvalidStatusTransition` VEC postoji u articles/services.py

### Test Pattern

```python
# articles/tests/test_publish_withdraw.py - NOVI FAJL

import pytest
from django.urls import reverse

from doi_portal.articles.models import Article, ArticleStatus
from doi_portal.articles.services import (
    InvalidStatusTransition,
    publish_article,
    withdraw_article,
)


@pytest.mark.django_db
class TestPublishArticleService:
    """Tests for publish_article service function."""

    def test_publish_valid_ready_article(self, ready_article, admin_user):
        """Valid READY article transitions to PUBLISHED."""
        result = publish_article(ready_article, admin_user)
        assert result.status == ArticleStatus.PUBLISHED
        assert result.published_by == admin_user
        assert result.published_at is not None

    def test_publish_rejects_non_ready(self, draft_article, admin_user):
        """Non-READY article raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition):
            publish_article(draft_article, admin_user)

    def test_publish_rejects_review_article(self, review_article, admin_user):
        """REVIEW article cannot be published (must be READY)."""
        with pytest.raises(InvalidStatusTransition):
            publish_article(review_article, admin_user)


@pytest.mark.django_db
class TestWithdrawArticleService:
    """Tests for withdraw_article service function."""

    def test_withdraw_valid_published_article(self, published_article, admin_user):
        """Valid PUBLISHED article with reason transitions to WITHDRAWN."""
        result = withdraw_article(published_article, admin_user, "Duplicirani podaci")
        assert result.status == ArticleStatus.WITHDRAWN
        assert result.withdrawal_reason == "Duplicirani podaci"
        assert result.withdrawn_by == admin_user
        assert result.withdrawn_at is not None

    def test_withdraw_rejects_non_published(self, ready_article, admin_user):
        """Non-PUBLISHED article raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition):
            withdraw_article(ready_article, admin_user, "Razlog")

    def test_withdraw_rejects_empty_reason(self, published_article, admin_user):
        """Empty reason raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition, match="Razlog"):
            withdraw_article(published_article, admin_user, "")

    def test_withdraw_rejects_whitespace_reason(self, published_article, admin_user):
        """Whitespace-only reason raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition):
            withdraw_article(published_article, admin_user, "   ")


@pytest.mark.django_db
class TestArticlePublishCheckView:
    """Tests for article_publish_check HTMX GET endpoint."""

    def test_publish_check_valid(self, client, admin_user, ready_article):
        """Publish check for READY article returns is_ready=True."""
        client.force_login(admin_user)
        url = reverse("articles:article-publish-check", kwargs={"pk": ready_article.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "Potvrda objavljivanja" in response.content.decode()

    def test_publish_check_rejects_urednik(self, client, urednik_user, ready_article):
        """Urednik cannot access publish check (403)."""
        client.force_login(urednik_user)
        url = reverse("articles:article-publish-check", kwargs={"pk": ready_article.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_publish_check_rejects_bibliotekar(self, client, bibliotekar_user, ready_article):
        """Bibliotekar cannot access publish check (403)."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:article-publish-check", kwargs={"pk": ready_article.pk})
        response = client.get(url)
        assert response.status_code == 403


@pytest.mark.django_db
class TestArticlePublishView:
    """Tests for article_publish POST endpoint."""

    def test_publish_success(self, client, admin_user, ready_article):
        """Successful publish redirects with success message."""
        client.force_login(admin_user)
        url = reverse("articles:article-publish", kwargs={"pk": ready_article.pk})
        response = client.post(url)
        assert response.status_code == 302
        ready_article.refresh_from_db()
        assert ready_article.status == ArticleStatus.PUBLISHED


@pytest.mark.django_db
class TestArticleWithdrawView:
    """Tests for article_withdraw POST endpoint."""

    def test_withdraw_success(self, client, admin_user, published_article):
        """Successful withdraw with reason redirects."""
        client.force_login(admin_user)
        url = reverse("articles:article-withdraw", kwargs={"pk": published_article.pk})
        response = client.post(url, {"withdrawal_reason": "Duplikat"})
        assert response.status_code == 302
        published_article.refresh_from_db()
        assert published_article.status == ArticleStatus.WITHDRAWN
        assert published_article.withdrawal_reason == "Duplikat"

    def test_withdraw_without_reason_fails(self, client, admin_user, published_article):
        """Withdraw without reason shows error."""
        client.force_login(admin_user)
        url = reverse("articles:article-withdraw", kwargs={"pk": published_article.pk})
        response = client.post(url, {"withdrawal_reason": ""})
        assert response.status_code == 302
        published_article.refresh_from_db()
        assert published_article.status == ArticleStatus.PUBLISHED  # Unchanged
```

**NAPOMENA za fixture-e:** Kreirati `ready_article` i `published_article` pytest fixture-e u conftest.py ili u samom test fajlu koristeci ArticleFactory:

```python
@pytest.fixture
def ready_article(article_factory, urednik_user):
    """Article in READY status (approved by Urednik)."""
    return article_factory(status=ArticleStatus.READY, reviewed_by=urednik_user)

@pytest.fixture
def published_article(article_factory, admin_user):
    """Article in PUBLISHED status."""
    return article_factory(status=ArticleStatus.PUBLISHED, published_by=admin_user)
```

### References

- [Source: epics.md#Story 3.7: Article Publishing & Withdrawal]
- [Source: epics.md#Story 3.6: Editorial Review Process - upstream dependency]
- [Source: epics.md#Story 3.8: Dashboard Statistics & Pending Items - downstream dependency]
- [Source: prd.md#5. Article Management - FR30 (Objavljivanje), FR31 (Povlacenje), FR32 (Withdrawn prikaz)]
- [Source: prd.md#Content Lifecycle - Withdrawn clanaka]
- [Source: architecture.md#API & Communication Patterns - HTMX endpoints]
- [Source: architecture.md#Implementation Patterns - HTMX Patterns]
- [Source: architecture.md#Data Architecture - RBAC Model]
- [Source: project-context.md#Services Layer (Business Logic)]
- [Source: project-context.md#Error Handling - Custom exceptions, InvalidStatusTransition]
- [Source: project-context.md#HTMX Pravila]
- [Source: project-context.md#Naming Konvencije]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri]
- [Source: ux-design-specification.md#Status Badge - Published (zelena), Withdrawn (crvena)]
- [Source: ux-design-specification.md#Decision Patterns - Confirm modal za destruktivne akcije]
- [Source: 3-6-editorial-review-process.md - HTMX modal pattern, services.py, _check_reviewer_permission]
- [Source: articles/services.py - approve_article, return_article_for_revision, InvalidStatusTransition]
- [Source: articles/views.py - _check_article_permission, _check_reviewer_permission, _get_user_group_names, ArticleDetailView context, FBV patterns]
- [Source: articles/models.py - Article model, ArticleStatus, reviewed_by/reviewed_at/returned_by/returned_at]
- [Source: articles/urls.py - Existing URL patterns and namespace]
- [Source: templates/articles/article_detail.html - Quick Actions, modal containers, htmx:afterSwap, status alerts]
- [Source: templates/articles/partials/_approve_modal.html - Modal template pattern reference]
- [Source: templates/articles/partials/_return_revision_modal.html - Modal with textarea pattern reference]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 63 story-specific tests pass (test_publish_withdraw.py) - 61 original + 2 added in review
- Full articles test suite: 423 passed, 0 failed (excluding 11 pre-existing ClamAV test failures from Story 3.3)
- Migration 0006_add_publish_withdraw_fields applied successfully

### Senior Developer Review (AI)

**Reviewer:** Amelia (Dev Agent) - Claude Opus 4.5
**Date:** 2026-02-01
**Outcome:** APPROVED (all issues fixed)

**Issues Found: 6 (2 MEDIUM, 4 LOW) - All Fixed**

1. **[MEDIUM][FIXED] Performance: Extra DB query in `can_review` context** - `ArticleDetailView.get_context_data()` line 415 used `self.request.user.groups.filter(name="Urednik").exists()` generating an extra DB query. Replaced with cached `flags["is_urednik"]` from `_get_user_role_flags()`. [views.py:415]
2. **[MEDIUM][FIXED] Test coverage gap: Missing withdraw_check tests** - `TestArticleWithdrawCheckView` was missing tests for Bibliotekar rejection and login required. Added `test_withdraw_check_rejects_bibliotekar` and `test_withdraw_check_requires_login`. [test_publish_withdraw.py]
3. **[LOW][FIXED] Dead code: Unused `has_withdrawal_reason` context variable** - Set in `get_context_data()` but never referenced in any template. Removed. [views.py:438-441]
4. **[LOW][FIXED] Code quality: Unnecessary parentheses in context assignments** - `can_publish` and `can_withdraw` had misleading parenthetical wrapping. Cleaned up to single-expression format. [views.py:427-433]
5. **[LOW][FIXED] UX: Missing `linebreaksbr` filter for withdrawal_reason** - Multi-line withdrawal reasons rendered as single line in template. Added `|linebreaksbr` filter. [article_detail.html:62]
6. **[LOW][FIXED] JavaScript optimization: Repetitive if-chain in htmx:afterSwap** - Replaced 5 separate `if` statements with data-driven lookup map for maintainability and minor performance gain. [article_detail.html:397-413]

**AC Validation: All 8 Acceptance Criteria IMPLEMENTED**
- AC #1: READY articles marked, "Objavi" action available for READY + Admin
- AC #2: Publish confirmation modal, READY->PUBLISHED transition, published_by/published_at saved, toast
- AC #3: PUBLISHED badge (bg-success), "Povuci" action, warning in modal
- AC #4: Withdraw with required reason, PUBLISHED->WITHDRAWN, all fields saved, toast
- AC #5: WITHDRAWN badge (bg-danger), reason/date visible, no further actions
- AC #6: 403 Forbidden for non-Admin/Superadmin
- AC #7: InvalidStatusTransition for invalid statuses
- AC #8: Urednik/Bibliotekar cannot see publish/withdraw buttons

### Completion Notes List

- Task 1: Added published_by, published_at, withdrawal_reason, withdrawn_by, withdrawn_at to Article model. Migration 0006 created and applied.
- Task 2: Implemented publish_article() service with READY status validation, transaction.atomic + select_for_update.
- Task 3: Implemented withdraw_article() service with PUBLISHED status validation, required reason validation, transaction.atomic + select_for_update.
- Task 4: Created article_publish_check FBV (HTMX GET) returning _publish_modal.html.
- Task 5: Created article_publish FBV (POST) delegating to publish_article() service.
- Task 6: Created article_withdraw_check FBV (HTMX GET) returning _withdraw_modal.html with reason textarea.
- Task 7: Created article_withdraw FBV (POST) delegating to withdraw_article() service.
- Task 8: Added 4 URL routes: publish-check, publish, withdraw-check, withdraw.
- Task 9: Created _check_admin_permission() helper (Administrator/Superadmin only, NOT Urednik).
- Task 10: Updated ArticleDetailView context with can_publish, can_withdraw, is_published, is_withdrawn, has_withdrawal_reason. Added select_related for published_by, withdrawn_by.
- Task 11: Updated article_detail.html with publish/withdraw buttons, PUBLISHED/WITHDRAWN alerts, modal containers, JS htmx:afterSwap handlers.
- Task 12: Created _publish_modal.html (Bootstrap 5 confirmation modal).
- Task 13: Created _withdraw_modal.html (Bootstrap 5 modal with required textarea and warnings).
- Task 14: 61 comprehensive tests covering all AC #1-#8: service tests (8+13), view tests (5+6+3+7), permission tests (8), template/button visibility tests (8), integration tests (3 including full lifecycle DRAFT->REVIEW->READY->PUBLISHED->WITHDRAWN).

### File List

**New files:**
- `doi_portal/doi_portal/articles/migrations/0006_add_publish_withdraw_fields.py` - Migration for new model fields
- `doi_portal/doi_portal/templates/articles/partials/_publish_modal.html` - Publish confirmation modal
- `doi_portal/doi_portal/templates/articles/partials/_withdraw_modal.html` - Withdraw modal with reason textarea
- `doi_portal/doi_portal/articles/tests/test_publish_withdraw.py` - 63 comprehensive tests (61 original + 2 added in review)

**Modified files:**
- `doi_portal/doi_portal/articles/models.py` - Added published_by, published_at, withdrawal_reason, withdrawn_by, withdrawn_at fields
- `doi_portal/doi_portal/articles/services.py` - Added publish_article(), withdraw_article() functions
- `doi_portal/doi_portal/articles/views.py` - Added 4 FBVs + _check_admin_permission() + ArticleDetailView context updates
- `doi_portal/doi_portal/articles/urls.py` - Added 4 URL routes for publish/withdraw endpoints
- `doi_portal/doi_portal/templates/articles/article_detail.html` - Added publish/withdraw buttons, alerts, modal containers, JS
