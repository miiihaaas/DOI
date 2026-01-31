# Story 3.2: Author Management with Drag & Drop

Status: done

## Story

As a **Bibliotekar**,
I want **to add and reorder article authors with ORCID validation and Crossref-compliant fields**,
So that **author information is complete, properly ordered and ready for Crossref XML generation**.

## Background

Ovo je druga prica u Epiku 3 (Article Workflow). Author model je kljucan za Crossref XML generisanje - svaki kontributor mora imati `sequence` (first/additional), `contributor_role` (author, editor, chair, translator, reviewer), ime, prezime i opciono ORCID, email i afilijacije. Bibliotekar koristi drag & drop za reordering autora i inline formu za unos podataka.

**FR Pokrivenost:** FR24 (autori sa reorderingom), FR24a (automatski sequence), FR24b (contributor_role izbor), FR24c (afilijacije sa ROR ID-jem), FR28 (ORCID validacija), FR28a (validacija prvog autora pre objave)

**Zavisnosti (sve DONE):**
- Story 3.1: Article Model & Basic Metadata Entry - Article FK za Author model, articles app infrastruktura
- Story 2.8: Row-Level Permissions - publisher-scoped mixins (indirektno preko Article)
- Story 1.7: Admin Dashboard Shell - admin layout, sidebar, breadcrumbs

**Blokira:**
- Story 3.5: Submit Article for Review - validacija "barem jedan autor" pre submit-a
- Story 5.1: Crossref Service Infrastructure - Author/Affiliation data za XML generisanje

## Acceptance Criteria

1. **Given** Author model je kreiran
   **When** se pregleda struktura modela
   **Then** sadrzi polja: `article` (FK), `given_name`, `surname` (obavezno), `suffix`, `email`, `orcid`, `orcid_authenticated` (boolean), `sequence` (TextChoices: FIRST, ADDITIONAL), `contributor_role` (TextChoices: AUTHOR, EDITOR, CHAIR, TRANSLATOR, REVIEWER), `is_corresponding` (boolean), `order` (PositiveIntegerField)
   **And** migracije se uspesno izvrsavaju
   **And** default `contributor_role` je AUTHOR
   **And** default `sequence` je ADDITIONAL

2. **Given** Affiliation model je kreiran
   **When** se pregleda struktura modela
   **Then** sadrzi polja: `author` (FK), `institution_name` (obavezno), `institution_ror_id`, `department`, `order` (PositiveIntegerField)
   **And** Author moze imati vise afilijacija (1:N relacija)

3. **Given** Bibliotekar edituje clanak
   **When** pregleda sekciju "Autori"
   **Then** postojeci autori su prikazani u sortiranom redosledu
   **And** svaki autor prikazuje: ime, prezime, afilijaciju, ORCID (ako postoji), corresponding badge, contributor_role
   **And** Alpine.js upravlja prikazom liste

4. **Given** Bibliotekar klikne "Dodaj autora"
   **When** se pojavi inline forma
   **Then** polja su: given_name, surname, email, orcid, contributor_role (select), is_corresponding (checkbox)
   **And** forma koristi Alpine.js za inline editing
   **And** podaci se cuvaju putem HTMX POST zahteva

5. **Given** Bibliotekar unese ORCID
   **When** ORCID polje izgubi fokus (blur event)
   **Then** ORCID format se validira (####-####-####-####X regex)
   **And** zelena ikonica oznacava validan, crvena nevalidan format
   **And** HTMX poziva validacioni endpoint za real-time feedback

6. **Given** vise autora postoji
   **When** Bibliotekar prevuce autora na novu poziciju (drag & drop)
   **Then** Alpine.js (SortableJS) upravlja drag & drop reorderingom
   **And** `order` polje se automatski azurira
   **And** `sequence` polje se automatski racuna: order=1 dobija FIRST, ostali ADDITIONAL
   **And** promena se cuva putem HTMX POST zahteva

7. **Given** Bibliotekar uklanja autora
   **When** klikne dugme za uklanjanje
   **Then** prikazuje se potvrda
   **And** autor je uklonjen iz clanka
   **And** preostali autori se automatski re-orderuju
   **And** sequence se ponovo racuna

8. **Given** Bibliotekar dodaje afilijaciju autoru
   **When** klikne "Dodaj afilijaciju" na autoru
   **Then** inline forma za afilijaciju se pojavljuje sa: institution_name, institution_ror_id, department
   **And** moze dodati vise afilijacija po autoru

9. **Given** ORCID validacioni endpoint postoji
   **When** se posalje GET zahtev sa ORCID vrednoshcu
   **Then** vraca HTML fragment sa statusom validacije (valid/invalid)
   **And** regex pattern: `^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$`

10. **Given** Author i Affiliation modeli postoje
    **When** se registruju sa auditlog
    **Then** sve CRUD operacije se beleze u audit log

## Tasks / Subtasks

- [x] Task 1: Kreirati Author i Affiliation modele (AC: #1, #2)
  - [x] 1.1 Kreirati `AuthorSequence` TextChoices enum (FIRST="first", ADDITIONAL="additional")
  - [x] 1.2 Kreirati `ContributorRole` TextChoices enum (AUTHOR="author", EDITOR="editor", CHAIR="chair", TRANSLATOR="translator", REVIEWER="reviewer")
  - [x] 1.3 Kreirati `Author` model u `articles/models.py` sa svim poljima prema AC#1
  - [x] 1.4 Dodati `Author.Meta`: ordering=["order"], verbose_name="Autor", verbose_name_plural="Autori"
  - [x] 1.5 Dodati `Author.__str__()` koji vraca "given_name surname" ili samo "surname" ako nema given_name
  - [x] 1.6 Kreirati `Affiliation` model u `articles/models.py` sa svim poljima prema AC#2
  - [x] 1.7 Dodati `Affiliation.Meta`: ordering=["order"], verbose_name="Afilijacija", verbose_name_plural="Afilijacije"
  - [x] 1.8 Registrovati Author i Affiliation sa auditlog u `articles/apps.py` ready() metodi (AC: #10)
  - [x] 1.9 Dodati `author_count` property na Article model: `return self.authors.count()`
  - [x] 1.10 Kreirati i izvrsiti migracije

- [x] Task 2: Implementirati ORCID validator (AC: #5, #9)
  - [x] 2.1 U `articles/validators.py` kreirati `validate_orcid(value)` funkciju
  - [x] 2.2 Regex pattern: `^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$`
  - [x] 2.3 Baciti `ValidationError` sa porukom na srpskom: "Neispravan ORCID format. Očekivani format: 0000-0000-0000-000X"
  - [x] 2.4 Dodati validator na Author.orcid field: `validators=[validate_orcid]`
  - [ ] 2.5 Opciono: implementirati ORCID checksum validaciju (mod-11-2 algoritam) ako ima vremena

- [x] Task 3: Kreirati Author/Affiliation forme (AC: #4, #8)
  - [x] 3.1 Kreirati `AuthorForm(ModelForm)` sa poljima: given_name, surname, suffix, email, orcid, contributor_role, is_corresponding
  - [x] 3.2 Bootstrap 5 widget attrs za sva polja (class="form-control" / "form-select" / "form-check-input")
  - [x] 3.3 Srpski labels sa ispravnim dijakritikama
  - [x] 3.4 Kreirati `AffiliationForm(ModelForm)` sa poljima: institution_name, institution_ror_id, department
  - [x] 3.5 Bootstrap 5 widget attrs za sva polja

- [x] Task 4: Kreirati HTMX views za Author CRUD + ORCID validaciju (AC: #4, #5, #6, #7, #9)
  - [x] 4.1 `author_add(request, article_pk)` - FBV, kreira autora, vraca HTML fragment
  - [x] 4.2 `author_update(request, pk)` - FBV, azurira autora, vraca HTML fragment
  - [x] 4.3 `author_delete(request, pk)` - FBV, brise autora, re-orderuje preostale
  - [x] 4.4 `author_reorder(request, article_pk)` - FBV, prima JSON sa novim redosledom, azurira order i sequence
  - [x] 4.5 `validate_orcid_view(request)` - FBV, GET endpoint, prima ?orcid=..., vraca HTML fragment
  - [x] 4.6 `affiliation_add(request, author_pk)` - FBV, kreira afilijaciju, vraca HTML fragment
  - [x] 4.7 `affiliation_delete(request, pk)` - FBV, brise afilijaciju
  - [x] 4.8 Svi FBV-ovi moraju proveravati `request.headers.get('HX-Request')` i publisher scoping
  - [x] 4.9 Dodati `@require_http_methods(["POST"])` ili `["GET"]` dekoratere

- [x] Task 5: Kreirati URL routes za Author endpoints (AC: #4, #5, #6, #7)
  - [x] 5.1 U `articles/urls.py` dodati HTMX author routes:
    - `<int:article_pk>/authors/add/` (name: author-add)
    - `authors/<int:pk>/update/` (name: author-update)
    - `authors/<int:pk>/delete/` (name: author-delete)
    - `<int:article_pk>/authors/reorder/` (name: author-reorder)
    - `validate-orcid/` (name: validate-orcid)
    - `authors/<int:author_pk>/affiliations/add/` (name: affiliation-add)
    - `affiliations/<int:pk>/delete/` (name: affiliation-delete)

- [x] Task 6: Kreirati template-ove sa Alpine.js i HTMX (AC: #3, #4, #5, #6, #7, #8)
  - [x] 6.1 Kreirati `templates/articles/partials/_author_list.html` - kompletna lista autora sa drag & drop
  - [x] 6.2 Kreirati `templates/articles/partials/_author_item.html` - jedan autor sa edit/delete akcijama
  - [x] 6.3 Kreirati `templates/articles/partials/_author_form.html` - inline forma za dodavanje/editovanje autora
  - [x] 6.4 Kreirati `templates/articles/partials/_orcid_validation.html` - fragment za ORCID validacioni feedback
  - [x] 6.5 Kreirati `templates/articles/partials/_affiliation_item.html` - jedna afilijacija
  - [x] 6.6 Kreirati `templates/articles/partials/_affiliation_form.html` - inline forma za afilijaciju
  - [x] 6.7 Azurirati `templates/articles/article_form.html` - dodati Author sekciju nakon metapodataka (samo za edit, ne za create)
  - [x] 6.8 Azurirati `templates/articles/article_detail.html` - prikazati listu autora

- [x] Task 7: Integrisati SortableJS za drag & drop (AC: #6)
  - [x] 7.1 Dodati SortableJS CDN link u article_form.html (https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js)
  - [x] 7.2 Kreirati Alpine.js `authorList()` komponentu sa drag & drop logikom
  - [x] 7.3 Na `onEnd` event: HTMX POST sa novim redosledom na reorder endpoint
  - [x] 7.4 Automatsko racunanje sequence: order=1 → FIRST, ostali → ADDITIONAL

- [x] Task 8: Kreirati AuthorFactory, AffiliationFactory i testove (AC: #1-#10)
  - [x] 8.1 `AuthorFactory` u `articles/tests/factories.py`
  - [x] 8.2 `AffiliationFactory` u `articles/tests/factories.py`
  - [x] 8.3 Model testovi: kreiranje, validacija, ORCID validator, ordering, cascade delete
  - [x] 8.4 View testovi: author CRUD sa razlicitim ulogama, ORCID validation endpoint
  - [x] 8.5 Reorder testovi: drag & drop order azuriranje, sequence auto-calculation
  - [x] 8.6 Permission testovi: publisher scoping (Bibliotekar moze samo za svoje artikle)
  - [x] 8.7 Affiliation testovi: add/delete afilijacija, multiple afilijacija po autoru

## Dev Notes

### KRITICNO: Pratiti ustanovljene patterns iz Story 3.1 i Epic 2

Author management MORA pratiti IDENTICNE patterns kao Article app:

1. **Model pattern**: Author i Affiliation u `articles/models.py` (NE novi app)
2. **View pattern**: FBV-ovi za HTMX endpoints (ne CBV) - snake_case, `HX-Request` header check
3. **Form pattern**: `AuthorForm(ModelForm)` sa Bootstrap 5 widget attrs
4. **Template pattern**: HTMX partials sa `_` prefix u `articles/partials/` direktorijumu
5. **Test pattern**: Factory Boy, pytest-django
6. **Auditlog**: Registracija u `apps.py` `ready()` metodi

### Author Model - Kompletna polja specifikacija

```python
# articles/models.py - DODATI u postojeci fajl

class AuthorSequence(models.TextChoices):
    """Crossref sequence atribut za kontributore."""
    FIRST = "first", _("Glavni (first)")
    ADDITIONAL = "additional", _("Ostali (additional)")

class ContributorRole(models.TextChoices):
    """Crossref contributor_role atribut."""
    AUTHOR = "author", _("Autor")
    EDITOR = "editor", _("Urednik")
    CHAIR = "chair", _("Predsedavajući")
    TRANSLATOR = "translator", _("Prevodilac")
    REVIEWER = "reviewer", _("Recenzent")

class Author(models.Model):
    """
    Author/Contributor model for articles.

    Stores Crossref-compliant contributor data including
    sequence, contributor_role, and ORCID.
    Part of hierarchy: Article -> Author -> Affiliation.
    """
    article = models.ForeignKey(
        "articles.Article",
        on_delete=models.CASCADE,
        related_name="authors",
        verbose_name=_("Članak"),
    )
    # Identification
    given_name = models.CharField(
        _("Ime"),
        max_length=255,
        blank=True,
    )
    surname = models.CharField(
        _("Prezime"),
        max_length=255,
    )
    suffix = models.CharField(
        _("Sufiks"),
        max_length=50,
        blank=True,
        help_text=_("npr. Jr., III"),
    )
    email = models.EmailField(
        _("Email"),
        blank=True,
    )
    orcid = models.CharField(
        _("ORCID"),
        max_length=19,
        blank=True,
        validators=[validate_orcid],
        help_text=_("Format: 0000-0000-0000-000X"),
    )
    orcid_authenticated = models.BooleanField(
        _("ORCID autentifikovan"),
        default=False,
    )

    # Crossref required
    sequence = models.CharField(
        _("Redosled (Crossref)"),
        max_length=20,
        choices=AuthorSequence.choices,
        default=AuthorSequence.ADDITIONAL,
    )
    contributor_role = models.CharField(
        _("Uloga kontributora"),
        max_length=20,
        choices=ContributorRole.choices,
        default=ContributorRole.AUTHOR,
    )

    # Status
    is_corresponding = models.BooleanField(
        _("Korespondentan autor"),
        default=False,
    )
    order = models.PositiveIntegerField(
        _("Redni broj"),
        default=0,
    )

    class Meta:
        verbose_name = _("Autor")
        verbose_name_plural = _("Autori")
        ordering = ["order"]

    def __str__(self) -> str:
        if self.given_name:
            return f"{self.given_name} {self.surname}"
        return self.surname
```

### Affiliation Model

```python
class Affiliation(models.Model):
    """
    Affiliation model for authors.

    Stores institution data with optional ROR ID for Crossref.
    One author can have multiple affiliations.
    """
    author = models.ForeignKey(
        "articles.Author",
        on_delete=models.CASCADE,
        related_name="affiliations",
        verbose_name=_("Autor"),
    )
    institution_name = models.CharField(
        _("Naziv institucije"),
        max_length=500,
    )
    institution_ror_id = models.URLField(
        _("ROR ID"),
        blank=True,
        help_text=_("https://ror.org/..."),
    )
    department = models.CharField(
        _("Departman"),
        max_length=500,
        blank=True,
    )
    order = models.PositiveIntegerField(
        _("Redni broj"),
        default=0,
    )

    class Meta:
        verbose_name = _("Afilijacija")
        verbose_name_plural = _("Afilijacije")
        ordering = ["order"]

    def __str__(self) -> str:
        if self.department:
            return f"{self.department}, {self.institution_name}"
        return self.institution_name
```

### ORCID Validator

```python
# articles/validators.py
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_orcid(value: str) -> None:
    """
    Validate ORCID format: 0000-0000-0000-000X

    Pattern: 4 groups of 4 digits separated by dashes,
    last character can be digit or uppercase X.
    """
    if not value:
        return  # Empty is OK (field is optional/blank=True)

    pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
    if not re.match(pattern, value):
        raise ValidationError(
            _("Neispravan ORCID format. Očekivani format: 0000-0000-0000-000X"),
            code="invalid_orcid",
        )
```

### HTMX Author Views Pattern

Svi author HTMX endpoints su **Function-Based Views** (FBV) - NE CBV. Ovo je u skladu sa architecture.md pravilima: FBV za HTMX endpoints, snake_case naming.

```python
# articles/views.py - DODATI u postojeci fajl

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required

@login_required
@require_POST
def author_add(request, article_pk):
    """Add author to article via HTMX."""
    article = get_object_or_404(Article, pk=article_pk)
    # Publisher scoping check
    _check_article_permission(request.user, article)

    form = AuthorForm(request.POST)
    if form.is_valid():
        author = form.save(commit=False)
        author.article = article
        # Auto-set order to next available
        max_order = article.authors.aggregate(
            max_order=models.Max("order")
        )["max_order"] or 0
        author.order = max_order + 1
        # Auto-set sequence
        if author.order == 1:
            author.sequence = AuthorSequence.FIRST
        else:
            author.sequence = AuthorSequence.ADDITIONAL
        author.save()

    # Return updated author list fragment
    authors = article.authors.prefetch_related("affiliations").all()
    return render(request, "articles/partials/_author_list.html", {
        "article": article,
        "authors": authors,
    })

@login_required
@require_POST
def author_reorder(request, article_pk):
    """Reorder authors via HTMX (drag & drop)."""
    article = get_object_or_404(Article, pk=article_pk)
    _check_article_permission(request.user, article)

    import json
    order_data = json.loads(request.body)
    # order_data = {"order": [pk1, pk2, pk3, ...]}

    for index, author_pk in enumerate(order_data.get("order", []), start=1):
        Author.objects.filter(pk=author_pk, article=article).update(
            order=index,
            sequence=AuthorSequence.FIRST if index == 1 else AuthorSequence.ADDITIONAL,
        )

    authors = article.authors.prefetch_related("affiliations").all()
    return render(request, "articles/partials/_author_list.html", {
        "article": article,
        "authors": authors,
    })

@login_required
@require_GET
def validate_orcid_view(request):
    """Validate ORCID format via HTMX GET request."""
    orcid = request.GET.get("orcid", "").strip()
    is_valid = False
    if orcid:
        import re
        is_valid = bool(re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$', orcid))

    return render(request, "articles/partials/_orcid_validation.html", {
        "orcid": orcid,
        "is_valid": is_valid,
        "has_value": bool(orcid),
    })
```

### Publisher Scoping Helper za Author FBV-ove

Author nema direktan publisher FK. Scoping ide preko `article.issue.publication.publisher` - CETIRI nivoa relacije:

```python
# articles/views.py - helper funkcija

def _check_article_permission(user, article):
    """
    Check if user has permission to modify authors on this article.

    Raises PermissionDenied if not allowed.
    """
    from django.core.exceptions import PermissionDenied

    if user.is_superuser:
        return
    if user.groups.filter(name__in=["Administrator", "Superadmin"]).exists():
        return
    # Urednik/Bibliotekar - check publisher scoping
    if hasattr(user, "publisher") and user.publisher:
        if article.issue.publication.publisher == user.publisher:
            return
    raise PermissionDenied
```

### Alpine.js Author List Component

```javascript
// U article_form.html - authors sekcija (samo za edit mode)
function authorList() {
    return {
        authors: [],  // Populated from server-rendered data
        showForm: false,

        initSortable() {
            const el = document.getElementById('author-list');
            if (el) {
                new Sortable(el, {
                    handle: '.drag-handle',
                    animation: 150,
                    onEnd: (evt) => {
                        // Collect new order
                        const items = el.querySelectorAll('[data-author-id]');
                        const order = Array.from(items).map(item =>
                            parseInt(item.dataset.authorId)
                        );
                        // HTMX POST to reorder endpoint
                        htmx.ajax('POST', reorderUrl, {
                            target: '#authors-container',
                            swap: 'innerHTML',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrfToken,
                            },
                            body: JSON.stringify({order: order}),
                        });
                    }
                });
            }
        }
    }
}
```

### Template Structure za Author Sekciju

```html
<!-- templates/articles/partials/_author_list.html -->
<div id="authors-container">
    {% for author in authors %}
        {% include "articles/partials/_author_item.html" with author=author %}
    {% empty %}
        <div class="text-muted text-center py-3">
            Nema dodanih autora. Kliknite "Dodaj autora" za početak.
        </div>
    {% endfor %}
</div>
```

```html
<!-- templates/articles/partials/_author_item.html -->
<div class="card mb-2" data-author-id="{{ author.pk }}">
    <div class="card-body py-2 d-flex align-items-center">
        <span class="drag-handle me-2" style="cursor: grab;">
            <i class="bi bi-grip-vertical"></i>
        </span>
        <div class="flex-grow-1">
            <strong>{{ author.surname }}{% if author.given_name %}, {{ author.given_name }}{% endif %}</strong>
            <span class="badge bg-info ms-1">{{ author.get_contributor_role_display }}</span>
            {% if author.is_corresponding %}
                <span class="badge bg-warning ms-1">Korespondentan</span>
            {% endif %}
            {% if author.orcid %}
                <span class="text-success ms-2">
                    <i class="bi bi-check-circle"></i> {{ author.orcid }}
                </span>
            {% endif %}
            {% for aff in author.affiliations.all %}
                <br><small class="text-muted">{{ aff.institution_name }}{% if aff.department %}, {{ aff.department }}{% endif %}</small>
            {% endfor %}
        </div>
        <div class="ms-2">
            <span class="badge bg-{{ author.sequence|yesno:'primary,secondary' }}">
                {{ author.get_sequence_display }}
            </span>
        </div>
        <!-- Edit/Delete buttons -->
    </div>
</div>
```

### ORCID Validation Template

```html
<!-- templates/articles/partials/_orcid_validation.html -->
{% if has_value %}
    {% if is_valid %}
        <span class="text-success">
            <i class="bi bi-check-circle-fill"></i> Validan ORCID
        </span>
    {% else %}
        <span class="text-danger">
            <i class="bi bi-x-circle-fill"></i> Neispravan ORCID format
        </span>
    {% endif %}
{% endif %}
```

### URL Routes za Author Endpoints

```python
# articles/urls.py - DODATI u postojeci urlpatterns

urlpatterns = [
    # ... postojeci article CRUD routes ...

    # Author HTMX endpoints
    path("<int:article_pk>/authors/add/", views.author_add, name="author-add"),
    path("authors/<int:pk>/update/", views.author_update, name="author-update"),
    path("authors/<int:pk>/delete/", views.author_delete, name="author-delete"),
    path("<int:article_pk>/authors/reorder/", views.author_reorder, name="author-reorder"),

    # ORCID validation
    path("validate-orcid/", views.validate_orcid_view, name="validate-orcid"),

    # Affiliation HTMX endpoints
    path("authors/<int:author_pk>/affiliations/add/", views.affiliation_add, name="affiliation-add"),
    path("affiliations/<int:pk>/delete/", views.affiliation_delete, name="affiliation-delete"),
]
```

### Auditlog Registration

```python
# articles/apps.py - AZURIRATI ready() metod
def ready(self):
    from auditlog.registry import auditlog
    from .models import Affiliation, Article, Author
    auditlog.register(Article)
    auditlog.register(Author)
    auditlog.register(Affiliation)
```

### Autori Sekcija u article_form.html - SAMO za Edit Mode

Author sekcija se prikazuje SAMO kad clanak vec postoji (edit mode, ne create mode):

```html
<!-- U article_form.html, POSLE forme za metapodatke, UNUTAR is_edit bloka -->
{% if is_edit %}
<div class="card mt-4">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="card-title mb-0">Autori</h5>
        <button type="button" class="btn btn-sm btn-outline-primary"
                hx-get="{% url 'articles:author-add' article_pk=object.pk %}"
                hx-target="#author-form-container"
                hx-swap="innerHTML">
            <i class="bi bi-plus-lg me-1"></i>Dodaj autora
        </button>
    </div>
    <div class="card-body">
        <div id="author-form-container"></div>
        <div id="authors-container"
             hx-get="{% url 'articles:author-add' article_pk=object.pk %}"
             hx-trigger="load"
             hx-swap="none">
            {% include "articles/partials/_author_list.html" with authors=object.authors.all %}
        </div>
    </div>
</div>
{% endif %}
```

### SortableJS - CDN Dependency

```html
<!-- U article_form.html javascript block -->
{% block javascript %}
{{ block.super }}
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.15.3/dist/cdn.min.js"></script>
{% if is_edit %}
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js"></script>
<script src="https://unpkg.com/htmx.org@2.0.8/dist/htmx.min.js"></script>
{% endif %}
{% endblock %}
```

**VAZNO:** Proveriti da li je HTMX vec ukljucen u `admin_base.html`. Ako jeste, NE dodavati ponovo u article_form.html. Dupli HTMX include moze izazvati probleme.

### Fajlovi za kreiranje (NOVI)

```
templates/articles/partials/
├── _author_list.html          # Kompletna lista autora sa drag & drop
├── _author_item.html          # Jedan autor item
├── _author_form.html          # Inline forma za autora
├── _orcid_validation.html     # ORCID validacioni feedback
├── _affiliation_item.html     # Jedna afilijacija
└── _affiliation_form.html     # Inline forma za afilijaciju
```

### Fajlovi za modifikaciju (POSTOJECI)

- `doi_portal/doi_portal/articles/models.py` - Dodati Author, Affiliation, AuthorSequence, ContributorRole, author_count property
- `doi_portal/doi_portal/articles/validators.py` - Dodati validate_orcid funkciju
- `doi_portal/doi_portal/articles/views.py` - Dodati HTMX FBV-ove za author CRUD + ORCID validaciju
- `doi_portal/doi_portal/articles/forms.py` - Dodati AuthorForm, AffiliationForm
- `doi_portal/doi_portal/articles/urls.py` - Dodati author/affiliation/ORCID routes
- `doi_portal/doi_portal/articles/apps.py` - Registrovati Author i Affiliation sa auditlog
- `doi_portal/doi_portal/templates/articles/article_form.html` - Dodati Author sekciju (edit mode)
- `doi_portal/doi_portal/templates/articles/article_detail.html` - Prikazati listu autora
- `doi_portal/doi_portal/articles/tests/factories.py` - Dodati AuthorFactory, AffiliationFactory

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

Svi UI tekstovi MORAJU koristiti ispravne srpske dijakritike:

| Kontekst | ISPRAVNO |
|----------|----------|
| Model verbose_name | "Autor" / "Autori" |
| Model verbose_name | "Afilijacija" / "Afilijacije" |
| Form labels | "Ime", "Prezime", "Email", "Uloga kontributora" |
| Contributor roles | "Autor", "Urednik", "Predsedavajući", "Prevodilac", "Recenzent" |
| Sequence | "Glavni (first)", "Ostali (additional)" |
| Button text | "Dodaj autora", "Sačuvaj", "Ukloni" |
| Messages | "Autor uspešno dodat.", "Autor uspešno uklonjen." |
| Validation | "Neispravan ORCID format. Očekivani format: 0000-0000-0000-000X" |
| Corresponding | "Korespondentan autor" |
| Section header | "Autori" |
| Affiliation label | "Naziv institucije", "Departman", "ROR ID" |
| Empty state | "Nema dodanih autora. Kliknite \"Dodaj autora\" za početak." |

### Anti-Patterns (ZABRANJENO)

```python
# POGRESNO - Kreirati novi Django app za autore
# doi_portal/authors/  # NE! Author ide u articles app

# POGRESNO - Koristiti CBV za HTMX endpoints
class AuthorAddView(CreateView):  # NE! Koristi FBV

# POGRESNO - Vracati JSON za HTMX response
return JsonResponse({"success": True})  # NE! Vracaj HTML fragment

# POGRESNO - Author bez article FK (M2M)
authors = models.ManyToManyField(Author)  # NE! Koristi ForeignKey

# POGRESNO - Zaboraviti publisher scoping na HTMX endpoints
def author_add(request, article_pk):
    article = Article.objects.get(pk=article_pk)  # NE bez permission check!

# POGRESNO - Hardkodovati sequence umesto auto-racunanja
# Sequence se AUTOMATSKI racuna na osnovu order polja

# POGRESNO - Koristiti inline formset za autore
# Projekat koristi HTMX + Alpine.js inline editing, NE Django formsets

# POGRESNO - Zaboraviti auditlog registraciju za Author/Affiliation
# Oba modela MORAJU biti registrovana u apps.py ready()

# POGRESNO - SortableJS import bez provere HTMX duplicate
# Proveriti da li admin_base.html vec ima HTMX pre dodavanja
```

### Testing Pattern

```python
# articles/tests/factories.py - DODATI

class AuthorFactory(DjangoModelFactory):
    class Meta:
        model = Author

    given_name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    article = factory.SubFactory(ArticleFactory)
    contributor_role = "author"
    sequence = "additional"
    order = factory.Sequence(lambda n: n + 1)


class AffiliationFactory(DjangoModelFactory):
    class Meta:
        model = Affiliation

    institution_name = factory.Faker("company")
    author = factory.SubFactory(AuthorFactory)
    order = factory.Sequence(lambda n: n + 1)
```

### Previous Story Learnings (Story 3.1)

1. **`get_scoped_queryset()` override** - Article koristi `issue__publication__publisher`. Author endpoint-i moraju koristiti `article.issue.publication.publisher` za proveru.
2. **SoftDeleteManager** - Author i Affiliation NEMAJU soft delete (brisanje autora je hard delete jer su child objekti). Cascade delete kad se Article obrise.
3. **Form `user` kwarg** - Author HTMX endpoints NE koriste user kwarg na formi vec direktno proveravaju permission u view-u.
4. **Alpine.js CDN** - Vec ukljucen u article_form.html javascript block. NE duplirati.
5. **Template structure** - Koristiti `admin_base.html` za extend, ali HTMX partials su standalone fragmenti (ne extenduju nista).
6. **auditlog registration** - U `apps.py` `ready()` metodi. DODATI Author i Affiliation pored postojeceg Article registracije.
7. **Test isolation** - UVEK dva publishera za permission testove (isti pattern kao Story 3.1).
8. **701 testova** proslo u Story 3.1 - NE sme se regresirati.

### Git Commit Pattern

```
story-3-2: feat(articles): implementiraj Author Management sa drag & drop i ORCID validacijom (Story 3.2)
```

### NFR Requirements

- **NFR12:** Audit log - Author/Affiliation CRUD se automatski belezi kroz auditlog
- **NFR3:** Admin panel stranice < 5 sekundi - select_related/prefetch_related za Author FK-ove
- **NFR17:** Keyboard navigacija - drag & drop mora podrzavati alternativni keyboard reorder

### Dependencies (Python/Django)

Sve zavisnosti VEC postoje u projektu - NEMA novih pip/uv instalacija za Python.
Frontend dependency (CDN):
- **SortableJS 1.15.6** - CDN link za drag & drop (https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js)
- Alpine.js 3.15.3 - VEC koristen u Story 3.1
- HTMX 2.0.8 - proveriti da li je vec u admin_base.html

### Project Structure Notes

- Author i Affiliation modeli idu u `doi_portal/doi_portal/articles/models.py` (NE novi app)
- HTMX partials idu u `doi_portal/doi_portal/templates/articles/partials/` (sa `_` prefix)
- HTMX FBV endpoints idu u `doi_portal/doi_portal/articles/views.py`
- URL namespace ostaje `articles` (isti app)
- Test files: `articles/tests/` direktorijum pattern
- Slediti `from __future__ import annotations` pattern iz svih modela

### References

- [Source: epics.md#Story 3.2: Author Management with Drag & Drop]
- [Source: prd.md#5. Article Management - FR24, FR24a, FR24b, FR24c, FR28, FR28a]
- [Source: prd.md#Data Model Update - Autor/Kontributor (Author) polja]
- [Source: prd.md#Data Model Update - Afilijacija (Affiliation) polja]
- [Source: prd.md#Crossref Compliance - Kontributor zahtevi]
- [Source: architecture.md#Frontend Architecture - Alpine.js Use Cases]
- [Source: architecture.md#HTMX Patterns]
- [Source: ux-design-specification.md#Component 2: Author List]
- [Source: ux-design-specification.md#Component 6: ORCID Input]
- [Source: project-context.md#HTMX Pravila]
- [Source: project-context.md#Naming Konvencije]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri]
- [Source: crossref_documentation_sumary.md#Zajednicki elementi - kontributori]
- [Source: 3-1-article-model-basic-metadata-entry.md - Article model, views, forms patterns]
- [Source: articles/models.py - Article model, SoftDeleteManager import]
- [Source: articles/validators.py - Placeholder for ORCID validator]
- [Source: articles/views.py - CBV patterns, publisher scoping]
- [Source: articles/forms.py - ArticleForm pattern]
- [Source: articles/urls.py - Existing URL patterns]
- [Source: articles/apps.py - Auditlog registration pattern]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None - clean implementation with zero errors.

### Completion Notes List

- All 8 tasks completed successfully
- 81 new tests written and passing (791 total, 0 failures, 0 regressions)
- Author and Affiliation models created with all Crossref-compliant fields
- ORCID validator with regex pattern and Serbian error messages
- HTMX FBV views for Author CRUD, reorder, ORCID validation
- Publisher scoping enforced via 4-level chain: article.issue.publication.publisher
- SortableJS integrated for drag & drop with Alpine.js authorList() component
- Auditlog registered for Author and Affiliation models
- All templates follow _ prefix convention for HTMX partials
- Bootstrap 5 styling consistent with Story 3.1 patterns
- Serbian diacritics used correctly throughout (č, ć, š, đ, ž)
- Task 2.5 (ORCID checksum mod-11-2) left as optional/not implemented per story spec

### File List

**Modified files:**
- `doi_portal/doi_portal/articles/models.py` - Added Author, Affiliation, AuthorSequence, ContributorRole, author_count property
- `doi_portal/doi_portal/articles/validators.py` - Added validate_orcid function
- `doi_portal/doi_portal/articles/views.py` - Added HTMX FBV views for author CRUD, reorder, ORCID validation
- `doi_portal/doi_portal/articles/forms.py` - Added AuthorForm, AffiliationForm
- `doi_portal/doi_portal/articles/urls.py` - Added author/affiliation/ORCID routes
- `doi_portal/doi_portal/articles/apps.py` - Registered Author and Affiliation with auditlog
- `doi_portal/doi_portal/templates/articles/article_form.html` - Added Author section (edit mode), SortableJS integration
- `doi_portal/doi_portal/templates/articles/article_detail.html` - Added authors display section
- `doi_portal/doi_portal/articles/tests/factories.py` - Added AuthorFactory, AffiliationFactory

**New files:**
- `doi_portal/doi_portal/templates/articles/partials/_author_list.html` - Author list HTMX partial
- `doi_portal/doi_portal/templates/articles/partials/_author_item.html` - Single author item partial
- `doi_portal/doi_portal/templates/articles/partials/_author_form.html` - Author inline form partial
- `doi_portal/doi_portal/templates/articles/partials/_orcid_validation.html` - ORCID validation feedback partial
- `doi_portal/doi_portal/templates/articles/partials/_affiliation_item.html` - Single affiliation partial
- `doi_portal/doi_portal/templates/articles/partials/_affiliation_form.html` - Affiliation inline form partial
- `doi_portal/doi_portal/articles/tests/test_authors.py` - 81 comprehensive tests
- `doi_portal/doi_portal/articles/migrations/0002_author_affiliation.py` - Migration for Author and Affiliation
