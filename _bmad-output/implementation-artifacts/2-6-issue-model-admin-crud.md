# Story 2.6: Issue Model & Admin CRUD

Status: done

## Story

As an **Urednik (Editor)**,
I want **to create and manage issues for publications**,
So that **articles can be organized into volumes and issues for Crossref DOI registration**.

## Background

Story 2.3 implementirala je Publication model sa type-specific poljima. Story 2.4 dodala je admin list sa sortiranjem i row-level permissions. Story 2.5 dodala je javnu listu publikacija. Ova prica kreira `issues` Django app sa Issue modelom i kompletnim admin CRUD-om. Issue je sledeci nivo u hijerarhiji: Publisher > Publication > Issue > Article (Epic 3).

**FR Pokrivenost:**
- FR18: Urednik moze kreirati novo izdanje publikacije
- FR19: Urednik moze editovati podatke o izdanju (volume, broj, godina, naslovna slika)
- FR20: Urednik moze postaviti status izdanja (draft, scheduled, published, archive)

**Napomena:** FR21 (javni pregled izdanja) je pokrivena Story 2.7.

## Acceptance Criteria

1. **Given** Issue model je kreiran
   **When** pregledam strukturu modela
   **Then** model sadrzi polja: `publication` (FK), `volume` (CharField), `issue_number` (CharField), `year` (PositiveIntegerField, obavezno), `title` (optional CharField), `cover_image` (ImageField), `publication_date` (DateField), `status` (enum: DRAFT, SCHEDULED, PUBLISHED, ARCHIVE), `created_at`, `updated_at`
   **And** status podrazumevano ima vrednost DRAFT
   **And** soft delete polja su ukljucena (`is_deleted`, `deleted_at`, `deleted_by`)
   **And** `related_name="issues"` na Publication FK (za `publication.issues.count()`)
   **And** unique constraint za kombinaciju (`publication`, `volume`, `issue_number`) sprecava duplikate
   **And** migracije se uspesno primenjuju

2. **Given** Publication model ima `issue_count` property
   **When** Issue model sa `related_name="issues"` postoji
   **Then** `publication.issue_count` vraca tacan broj izdanja (umesto hardkodovanog 0)
   **And** Publication admin list prikazuje tacan issue count u koloni (Story 2.4 placeholder popunjen)

3. **Given** ulogovani Urednik
   **When** navigira na Issues za svoju dodeljenu publikaciju
   **Then** lista izdanja se prikazuje sa kolonama: volume, issue_number, year, status badge, article count (placeholder 0 do Epic 3), cover thumbnail
   **And** lista podrzava sortiranje po volume, year, status
   **And** lista podrzava filtriranje po status

4. **Given** Urednik klikne "Novo izdanje"
   **When** forma se prikaze
   **Then** polje za publikaciju je ograniceno na publikacije iz dodeljenog izdavaca
   **And** polja za volume, issue_number, year, title, cover_image, publication_date, status su prikazana
   **And** status podrazumevano ima vrednost DRAFT
   **And** Conference-specific polja (proceedings_title, proceedings_publisher_name, proceedings_publisher_place) su prikazana SAMO kada je tip publikacije CONFERENCE

5. **Given** validni podaci o izdanju su uneti
   **When** forma se obradi
   **Then** izdanje je kreirano sa DRAFT statusom
   **And** toast notifikacija potvrdjuje uspesno kreiranje
   **And** korisnik je preusmeren na issue list za tu publikaciju

6. **Given** Urednik menja status izdanja
   **When** status se promeni na PUBLISHED
   **Then** status se azurira
   **And** promena se belezi u audit log

7. **Given** Urednik bez publisher dodele
   **When** pokusa da kreira izdanje za nedodeljenu publikaciju
   **Then** akcija je odbijena sa 403 Forbidden

8. **Given** Administrator
   **When** pristupa Issues
   **Then** vidi sva izdanja svih publikacija (bez publisher scoping-a)
   **And** moze kreirati, editovati i brisati (soft delete) izdanja

## Tasks / Subtasks

- [x]Task 1: Kreirati `issues` Django app i registrovati ga (AC: #1)
  - [x]1.1 Kreirati app: `doi_portal/doi_portal/issues/` sa `__init__.py`, `apps.py`, `models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py` i `tests/` direktorijum
  - [x]1.2 Registrovati `"doi_portal.issues"` u `LOCAL_APPS` u `config/settings/base.py`
  - [x]1.3 `apps.py`: `IssuesConfig` sa `name = "doi_portal.issues"`, `verbose_name = "Izdanja"`

- [x]Task 2: Implementirati Issue model (AC: #1)
  - [x]2.1 Kreirati `IssueStatus(models.TextChoices)`: DRAFT="DRAFT" "Nacrt", SCHEDULED="SCHEDULED" "Zakazano", PUBLISHED="PUBLISHED" "Objavljeno", ARCHIVE="ARCHIVE" "Arhivirano"
  - [x]2.2 Kreirati `Issue(models.Model)` sa svim poljima iz AC #1
  - [x]2.3 FK na Publication: `publication = models.ForeignKey(Publication, on_delete=models.PROTECT, related_name="issues")` - PROTECT jer brisanje publikacije sa izdanjima treba spreciti
  - [x]2.4 `volume` = CharField(max_length=20, blank=True) - string jer moze biti "Special", "Supplement" itd.
  - [x]2.5 `issue_number` = CharField(max_length=20, blank=True) - string iz istog razloga
  - [x]2.6 `year` = PositiveIntegerField() - OBAVEZNO
  - [x]2.7 `title` = CharField(max_length=500, blank=True) - opcioni naslov izdanja
  - [x]2.8 `cover_image` = ImageField(upload_to="issues/covers/", blank=True, null=True)
  - [x]2.9 `publication_date` = DateField(blank=True, null=True) - datum objave
  - [x]2.10 `status` = CharField(choices=IssueStatus.choices, default=IssueStatus.DRAFT)
  - [x]2.11 Dodati Conference proceedings polja (iz PRD Data Model Update):
    - `proceedings_title` = CharField(max_length=500, blank=True) - Naslov zbornika (ako razlicit od publication.title)
    - `proceedings_publisher_name` = CharField(max_length=255, blank=True) - Naziv izdavaca zbornika
    - `proceedings_publisher_place` = CharField(max_length=255, blank=True) - Mesto izdavanja
  - [x]2.12 Soft delete polja: `is_deleted`, `deleted_at`, `deleted_by` (isti pattern kao Publisher/Publication)
  - [x]2.13 SoftDeleteManager (importovati iz `publishers.models`) kao `objects`, `all_objects = models.Manager()`
  - [x]2.14 Meta: `verbose_name = "Izdanje"`, `verbose_name_plural = "Izdanja"`, `ordering = ["-year", "-volume", "-issue_number"]`, `unique_together = [["publication", "volume", "issue_number"]]` ili `constraints` sa UniqueConstraint (iskljuciti soft-deleted)
  - [x]2.15 `__str__`: `f"{self.publication.title} - Vol. {self.volume}, No. {self.issue_number} ({self.year})"`
  - [x]2.16 `save()`: auto-generisati slug ili ostati bez slug-a (Issue nema slug jer se identifikuje po PK/ID)
  - [x]2.17 `soft_delete(user)` i `restore()` metode (isti pattern kao Publisher/Publication)
  - [x]2.18 `article_count` property (return 0 za sada, Story 3.1 ce popuniti)
  - [x]2.19 `status_badge_class` property za CSS klase: DRAFT="bg-secondary", SCHEDULED="bg-info", PUBLISHED="bg-success", ARCHIVE="bg-warning"
  - [x]2.20 Kreirati i primeniti migraciju

- [x]Task 3: Registrovati Issue model za auditlog (AC: #6)
  - [x]3.1 U `issues/apps.py` dodati `ready()` metodu ili u `issues/__init__.py` registrovati `auditlog.register(Issue)` (slediti pattern iz publishers/publications apps)
  - [x]3.2 Verifikovati da CRUD operacije generisu LogEntry zapise

- [x]Task 4: Implementirati IssueForm (AC: #4, #5)
  - [x]4.1 Kreirati `IssueForm(forms.ModelForm)` u `issues/forms.py`
  - [x]4.2 Fields: publication, volume, issue_number, year, title, cover_image, publication_date, status, proceedings_title, proceedings_publisher_name, proceedings_publisher_place
  - [x]4.3 Widget za `publication_date`: `forms.DateInput(attrs={"type": "date"})` (HTML5 date picker)
  - [x]4.4 Widget za `cover_image`: `forms.ClearableFileInput(attrs={"accept": "image/*"})`
  - [x]4.5 Sve labele na srpskom sa dijakritikama (koristiti `gettext_lazy`)
  - [x]4.6 Custom `clean()`: validirati unique_together - prikazati korisniku razumljivu poruku ako kombinacija vec postoji
  - [x]4.7 `__init__()`: Prilagoditi publication queryset na osnovu korisnika (prosleden kao kwarg):
    - Administrator/Superadmin: sve publikacije
    - Urednik: samo publikacije svog izdavaca
    - Bibliotekar: samo publikacije svog izdavaca

- [x]Task 5: Implementirati Issue admin views (AC: #2, #3, #4, #5, #6, #7, #8)
  - [x]5.1 Kreirati `IssueListView(PublisherScopedMixin, ListView)` u `issues/views.py`
    - Template: `issues/issue_list.html`
    - `paginate_by = 20`
    - `get_queryset()`: filtriraj po publication_id (GET param), status (GET param), sortiranje po volume/year/status
    - Scope po publisher-u (PublisherScopedMixin) - Urednik/Bibliotekar vide samo svoje
    - `get_scoped_queryset()`: NAPOMENA - Issue nema direktan `publisher` FK. Scope se radi preko `publication__publisher`: `queryset.filter(publication__publisher=self.request.user.publisher)` - OVERAJDUJ `get_scoped_queryset()` da radi preko Publication FK
    - `get_context_data()`: breadcrumbs, publication info (ako je filtrirano), status choices, role flags
  - [x]5.2 Kreirati `IssueCreateView(PublisherScopedEditMixin, CreateView)` - Urednik+ moze kreirati
    - Prosle diti `user` kroz `get_form_kwargs()` za publication queryset filtering
    - `form_valid()`: success message, redirect na list
    - Ako je `publication_id` prosledjen u URL query, pre-selektovati publication u formi
    - NAPOMENA za `get_scoped_queryset()`: Issue se scope-uje preko `publication__publisher` - videti Task 5.1
  - [x]5.3 Kreirati `IssueUpdateView(PublisherScopedEditMixin, UpdateView)` - Urednik+ moze editovati
    - Scope queryset da Urednik moze editovati samo issues svoje publikacije
    - `get_scoped_queryset()` override da filtrira preko `publication__publisher`
  - [x]5.4 Kreirati `IssueDetailView(PublisherScopedMixin, DetailView)` - Bibliotekar moze videti
    - Prikazuje sve podatke o izdanju
    - Placeholder za article list (Story 3.1)
    - `get_scoped_queryset()` override da filtrira preko `publication__publisher`
  - [x]5.5 Kreirati `IssueDeleteView(AdministratorRequiredMixin, DeleteView)` - samo Admin+ moze brisati
    - Soft delete umesto stvarnog brisanja
    - Warning ako issue ima article-e (placeholder, vracati 0 za sada)

- [x]Task 6: Kreirati Issue URL konfiguraciju (AC: #3)
  - [x]6.1 Kreirati `issues/urls.py` sa `app_name = "issues"`:
    - `path("", IssueListView.as_view(), name="list")`
    - `path("create/", IssueCreateView.as_view(), name="create")`
    - `path("<int:pk>/", IssueDetailView.as_view(), name="detail")`
    - `path("<int:pk>/edit/", IssueUpdateView.as_view(), name="update")`
    - `path("<int:pk>/delete/", IssueDeleteView.as_view(), name="delete")`
  - [x]6.2 Registrovati u `config/urls.py`:
    `path("dashboard/issues/", include("doi_portal.issues.urls", namespace="issues")),`

- [x]Task 7: Kreirati Issue admin templates (AC: #3, #4, #5)
  - [x]7.1 Kreirati `templates/issues/issue_list.html` - extends `admin_base.html`
    - Tabela sa kolonama: Volume, Broj, Godina, Naslov, Status (badge), Artikli (count), Cover (thumbnail), Akcije
    - Filter po statusu (dropdown ili checkboxes)
    - Filter po publikaciji (dropdown)
    - Sortiranje po klikabilnim zaglavljima kolona (slediti publication_list.html pattern iz Story 2.4)
    - "Novo izdanje" dugme (vidljivo samo za Urednik+)
    - Breadcrumbs: Kontrolna tabla > Izdanja
    - Ako se filtrira po publikaciji: Kontrolna tabla > Publikacije > {Publication Title} > Izdanja
  - [x]7.2 Kreirati `templates/issues/issue_form.html` - extends `admin_base.html`
    - Form layout slican `publication_form.html` patternu
    - Publication select ogranicen na user-scoped publications
    - Conference-specific proceedings polja prikazana/skrivena sa Alpine.js ili staticki (samo kad je tip CONFERENCE)
    - Date picker za `publication_date`
    - Cover image upload sa preview-om
    - Breadcrumbs: Kontrolna tabla > Izdanja > Novo izdanje (ili Izmeni izdanje)
  - [x]7.3 Kreirati `templates/issues/issue_detail.html` - extends `admin_base.html`
    - Svi podaci o izdanju
    - Status badge
    - Cover image (ako postoji)
    - Sekcija za articles (placeholder: "Clanci ce biti dostupni nakon implementacije Story 3.1")
    - Dugmad: Izmeni, Nazad (Obrisi samo za Admina)
    - Breadcrumbs: Kontrolna tabla > Izdanja > {Issue title/number}
  - [x]7.4 Kreirati `templates/issues/issue_confirm_delete.html` - extends `admin_base.html`
    - Upozorenje o brisanju sa article count
    - Breadcrumbs

- [x]Task 8: Azurirati sidebar navigaciju (AC: #3)
  - [x]8.1 Azurirati `admin_base.html` sidebar - dodati "Izdanja" link ispod "Publikacije"
    - URL: `{% url 'issues:list' %}`
    - Ikona: `bi-journals` ili `bi-collection`
    - Vidljivost: svi autentifikovani korisnici (Urednik, Bibliotekar, Administrator, Superadmin)
    - Active class detekcija za `/dashboard/issues/` path

- [x]Task 9: Azurirati Publication admin views da linkuju na Issues (AC: #2)
  - [x]9.1 U `publications/publication_detail.html` dodati sekciju za izdanja sa linkom na issue list filtrirano po toj publikaciji: `{% url 'issues:list' %}?publication={{ publication.pk }}`
  - [x]9.2 U `publications/publication_list.html` issue_count kolona sada prikazuje tacan broj (zahvaljujuci `related_name="issues"` i Count annotation u view-u) - verifikovati da `_HAS_ISSUES_RELATION` check u `PublicationListView` sada detektuje relation i koristi `Count("issues")`
  - [x]9.3 NAPOMENA: `_HAS_ISSUES_RELATION` u `publications/views.py` se proverava pri ucitavanju modula. Nakon sto Issue model postoji sa `related_name="issues"`, ova promenljiva ce automatski biti `True` - NEMA potrebe za promenom koda, samo verifikovati

- [x]Task 10: Azurirati public portal publication detail (AC: indirektno)
  - [x]10.1 U `portal/publications/publication_detail.html` - zameniti placeholder "Izdanja ce biti dostupna uskoro." sa listom objavljenih izdanja (samo PUBLISHED status)
  - [x]10.2 U `portal/views.py` - `PublicationPublicDetailView.get_context_data()`: dodati `context["issues"] = self.object.issues.filter(status="PUBLISHED").order_by("-year", "-volume", "-issue_number")`

- [x]Task 11: Napisati testove (AC: #1-#8)
  - [x]11.1 Test Issue model kreiranje sa svim poljima
  - [x]11.2 Test unique constraint za (publication, volume, issue_number)
  - [x]11.3 Test soft delete i restore
  - [x]11.4 Test IssueStatus choices
  - [x]11.5 Test article_count property (vraca 0)
  - [x]11.6 Test status_badge_class property
  - [x]11.7 Test IssueForm validacija (valid i invalid data)
  - [x]11.8 Test IssueForm publication queryset scoping za Urednik
  - [x]11.9 Test IssueListView - prikazuje issues, filtrirane po publisher scope
  - [x]11.10 Test IssueListView - filter po statusu
  - [x]11.11 Test IssueListView - filter po publikaciji
  - [x]11.12 Test IssueCreateView - Urednik moze kreirati za svoju publikaciju
  - [x]11.13 Test IssueCreateView - Urednik ne moze kreirati za tudju publikaciju (403)
  - [x]11.14 Test IssueCreateView - Administrator moze kreirati za bilo koju publikaciju
  - [x]11.15 Test IssueUpdateView - Urednik moze editovati svoje
  - [x]11.16 Test IssueUpdateView - Bibliotekar ne moze editovati (403)
  - [x]11.17 Test IssueDeleteView - samo Administrator moze brisati
  - [x]11.18 Test IssueDeleteView - soft delete se izvrsava (ne hard delete)
  - [x]11.19 Test auditlog registracija (LogEntry kreiran)
  - [x]11.20 Test Publication.issue_count sada vraca tacan broj
  - [x]11.21 Test Publication admin list issue_count kolona
  - [x]11.22 Test breadcrumbs na svim stranicama
  - [x]11.23 Test proceedings polja vidljiva samo za CONFERENCE publikacije

## Dev Notes

### KRITICNO: Ovo je prvi novi Django app od Story 1.x

Ovo je prvi put da se kreira potpuno nov Django app (issues) od pocetka. Slediti tacno isti pattern kao `publishers/` i `publications/` apps.

### Postojeci fajlovi koje TREBA modifikovati

- `doi_portal/config/settings/base.py` - Dodati `"doi_portal.issues"` u LOCAL_APPS
- `doi_portal/config/urls.py` - Dodati issues URL include
- `doi_portal/doi_portal/templates/admin_base.html` - Dodati "Izdanja" link u sidebar
- `doi_portal/doi_portal/templates/publications/publication_detail.html` - Dodati sekciju za izdanja
- `doi_portal/doi_portal/templates/portal/publications/publication_detail.html` - Zameniti placeholder sa realnom listom izdanja
- `doi_portal/doi_portal/portal/views.py` - Dodati issues queryset u PublicationPublicDetailView

### Novi fajlovi za kreiranje

```
doi_portal/doi_portal/issues/
    __init__.py
    admin.py
    apps.py
    forms.py
    models.py
    urls.py
    views.py
    tests/
        __init__.py
        test_models.py
        test_views.py
        test_forms.py
        factories.py

doi_portal/doi_portal/templates/issues/
    issue_list.html
    issue_form.html
    issue_detail.html
    issue_confirm_delete.html
```

### Row-Level Permissions - KRITICAN DETALJ

Issue model nema direktan FK na Publisher. Scoping se radi PREKO Publication FK:

```python
# POGRESNO - Issue nema publisher FK
queryset.filter(publisher=self.request.user.publisher)

# ISPRAVNO - Scope preko Publication FK
queryset.filter(publication__publisher=self.request.user.publisher)
```

**Implementacija:** Override `get_scoped_queryset()` u svim Issue views da koristi `publication__publisher` umesto `publisher`:

```python
class IssueListView(PublisherScopedMixin, ListView):
    model = Issue

    def get_scoped_queryset(self, queryset):
        """Override to scope via publication__publisher (Issue nema direktan publisher FK)."""
        flags = self._get_user_role_flags()
        if flags["is_admin"]:
            return queryset
        if flags["has_publisher"]:
            return queryset.filter(publication__publisher=self.request.user.publisher)
        return queryset.none()

    def get_queryset(self):
        queryset = super().get_queryset().select_related("publication", "publication__publisher")
        queryset = self.get_scoped_queryset(queryset)
        # ... filteri i sortiranje ...
        return queryset
```

### IssueForm - Publication Queryset Scoping

Forma mora ograniciti `publication` dropdown na osnovu korisnikove uloge:

```python
class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = [
            "publication", "volume", "issue_number", "year", "title",
            "cover_image", "publication_date", "status",
            "proceedings_title", "proceedings_publisher_name",
            "proceedings_publisher_place",
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            if user.is_superuser or user.groups.filter(name__in=["Administrator", "Superadmin"]).exists():
                self.fields["publication"].queryset = Publication.objects.select_related("publisher")
            elif hasattr(user, "publisher") and user.publisher:
                self.fields["publication"].queryset = Publication.objects.filter(
                    publisher=user.publisher
                ).select_related("publisher")
            else:
                self.fields["publication"].queryset = Publication.objects.none()
```

View prosleuje `user` u formu:

```python
def get_form_kwargs(self):
    kwargs = super().get_form_kwargs()
    kwargs["user"] = self.request.user
    return kwargs
```

### Publication issue_count - Automatski popunjeno

`Publication.issue_count` property VEC postoji u models.py i koristi `self.issues.count()`. Jednom kad Issue model sa `related_name="issues"` postoji, ovo ce automatski raditi.

`PublicationListView` u `publications/views.py` ima `_HAS_ISSUES_RELATION` check koji ce automatski detektovati relation pri ucitavanju modula. Posle kreiranja Issue modela i restartovanja servera, kolona issue_count u publication listi ce automatski prikazivati tacne brojeve - NEMA potrebe za promenom koda.

### Proceedings polja - Prikazivanje zavisno od tipa publikacije

Conference proceedings polja (`proceedings_title`, `proceedings_publisher_name`, `proceedings_publisher_place`) su relevantna samo kada je tip publikacije CONFERENCE. U template-u koristiti:

```html
{% if issue.publication.publication_type == "CONFERENCE" %}
<h6 class="text-muted mb-3 border-bottom pb-2">Podaci o zborniku</h6>
<div class="row">
    <div class="col-md-12 mb-3">
        <label for="id_proceedings_title" class="form-label">Naslov zbornika</label>
        {{ form.proceedings_title }}
    </div>
    <!-- ... ostala polja ... -->
</div>
{% endif %}
```

Alternativno, koristiti Alpine.js za dinamicko prikazivanje na create formi (proveriti `publication` select option data attribute za tip).

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

Svi UI tekstovi MORAJU koristiti ispravne srpske dijakritike: `c`, `c`, `s`, `d`, `z`

| Kontekst | ISPRAVNO |
|----------|----------|
| Naslov stranice | "Izdanja" |
| Breadcrumb | "Kontrolna tabla" |
| Novo izdanje dugme | "Novo izdanje" |
| Status DRAFT | "Nacrt" |
| Status SCHEDULED | "Zakazano" |
| Status PUBLISHED | "Objavljeno" |
| Status ARCHIVE | "Arhivirano" |
| Volume label | "Volumen" |
| Issue number label | "Broj izdanja" |
| Year label | "Godina" |
| Cover image label | "Naslovna slika" |
| Publication date label | "Datum objave" |
| Proceedings title | "Naslov zbornika" |
| Success message kreiranje | "Izdanje uspesno kreirano." |
| Success message azuriranje | "Izdanje uspesno azurirano." |
| Success message brisanje | "Izdanje uspesno obrisano." |
| Delete warning | "Da li ste sigurni da zelite da obrisete ovo izdanje?" |
| Placeholder articles | "Clanci ce biti dostupni nakon implementacije." |
| Empty state | "Nema izdanja za prikaz." |

**NAPOMENA:** Tabela iznad koristi ASCII karaktere za citljivost tabele. U kodu koristiti PRAVE dijakritike: `c` -> `c`, `c` -> `c`, `s` -> `s`, `z` -> `z`, `d` -> `d`. Na primer: "Izdanje uspesno kreirano." treba biti "Izdanje uspesno kreirano." sa pravim dijakritikama gde je potrebno: "Izdanje uspešno kreirano."

### URL Pattern za Issue List sa Publication filterom

Kada korisnik klikne na "Issues" iz Publication detail-a, URL treba da bude:
`/dashboard/issues/?publication=5` - lista izdanja filtrirana po Publication ID

U view-u:
```python
publication_id = self.request.GET.get("publication")
if publication_id:
    queryset = queryset.filter(publication_id=publication_id)
```

### Breadcrumbs Pattern

Ako je lista filtriirana po publikaciji:
```python
context["breadcrumbs"] = [
    {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
    {"label": "Publikacije", "url": reverse_lazy("publications:list")},
    {"label": publication.title, "url": reverse("publications:detail", kwargs={"slug": publication.slug})},
    {"label": "Izdanja", "url": None},
]
```

Inace:
```python
context["breadcrumbs"] = [
    {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
    {"label": "Izdanja", "url": None},
]
```

### SoftDeleteManager Import

`SoftDeleteManager` je definisan u `doi_portal/publishers/models.py`. Importovati ga:

```python
from doi_portal.publishers.models import SoftDeleteManager
```

Isto kao Publication model radi.

### Audit Log Registracija Pattern

Slediti pattern iz publications app-a:

```python
# issues/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IssuesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "doi_portal.issues"
    verbose_name = _("Izdanja")

    def ready(self):
        from auditlog.registry import auditlog
        from .models import Issue
        auditlog.register(Issue)
```

### config/urls.py Entry

Dodati ispod `publications` routes:

```python
# Story 2.6: Issue admin routes (under dashboard)
path("dashboard/issues/", include("doi_portal.issues.urls", namespace="issues")),
```

### Testing Strategy

Koristiti `pytest-django` sa Factory Boy. Kreirati `IssueFactory`:

```python
# issues/tests/factories.py
import factory
from factory.django import DjangoModelFactory
from doi_portal.issues.models import Issue, IssueStatus
from doi_portal.publications.tests.factories import PublicationFactory


class IssueFactory(DjangoModelFactory):
    class Meta:
        model = Issue

    publication = factory.SubFactory(PublicationFactory)
    volume = factory.Sequence(lambda n: str(n + 1))
    issue_number = factory.Sequence(lambda n: str(n + 1))
    year = 2026
    status = IssueStatus.DRAFT
```

Koristiti `pytest.fixture` za user-e sa razlicitim rolama (vec postoje u prethodnim testovima - videti conftest.py ili test_views.py u publishers/publications apps).

### Anti-Patterns to Avoid

```python
# POGRESNO - Direktan publisher scope na Issue
queryset.filter(publisher=user.publisher)

# ISPRAVNO - Scope preko Publication
queryset.filter(publication__publisher=user.publisher)

# POGRESNO - Hard delete
issue.delete()

# ISPRAVNO - Soft delete
issue.soft_delete(user=request.user)

# POGRESNO - Plural model name
class Issues(models.Model):

# ISPRAVNO - Singular
class Issue(models.Model):

# POGRESNO - JSON response za admin view
return JsonResponse({"issues": [...]})

# ISPRAVNO - HTML response
return render(request, "issues/issue_list.html", context)

# POGRESNO - Kreirati issue bez publisher scope validacije
# Urednik moze kreirati issue samo za publikacije svog izdavaca

# POGRESNO - Status tranzicija bez audit log-a
issue.status = "PUBLISHED"
issue.save()

# ISPRAVNO - Django auditlog automatski belezi save() promene
# Nema potrebe za dodatnim kodom, samo registrovati model sa auditlog
```

### Git Commit Pattern

```
story-2-6: feat(issues): implementiraj Issue Model & Admin CRUD sa row-level permissions (Story 2.6)
```

### Dependencies

**Zavisi od:**
- Story 2.1 (Publisher Model) - DONE
- Story 2.3 (Publication Model) - DONE
- Story 2.4 (Publication Admin - mixins, list patterns) - DONE
- Story 2.5 (Public Publication List - portal patterns) - DONE

**Blokira:**
- Story 2.7 (Public Issue List & Detail) - potreban je Issue model
- Story 2.8 (Row-Level Permissions for Content) - issue permissions pattern
- Story 3.1 (Article Model) - article FK na Issue

### Previous Story Learnings (Story 2.4, 2.5)

1. **PublisherScopedMixin** - vec postoji u `publishers/mixins.py`, koristi `publisher` FK. Za Issue OVERRIDE `get_scoped_queryset()` da koristi `publication__publisher`
2. **SoftDeleteManager** - importovati iz `publishers/models.py` (ne kreirati ponovo)
3. **Admin template** = `admin_base.html` - sidebar, breadcrumbs, toast notifikacije
4. **Breadcrumbs format**: `[{"label": "...", "url": "..."}, {"label": "...", "url": None}]`
5. **Form pattern**: Custom `__init__()` za queryset scoping, proslediti `user` iz view `get_form_kwargs()`
6. **Publication list issue_count**: `_HAS_ISSUES_RELATION` automatski detektuje relation - ne treba menjati kod
7. **Srpski dijakritici**: OBAVEZNO koristiti `c`, `c`, `s`, `d`, `z` - videti tabelu iznad
8. **HTMX** je vec ukljucen u `base.html` (dodato u Story 2.5) - ne dodavati ponovo
9. **Test patterns**: videti `publications/tests/` i `portal/tests/` za pytest fixture i factory primere
10. **Audit log**: django-auditlog automatski belezi save() promene - registrovati model u apps.py ready()

### Project Structure Notes

- Issue admin views: `doi_portal/doi_portal/issues/views.py`
- Issue model: `doi_portal/doi_portal/issues/models.py`
- Issue forms: `doi_portal/doi_portal/issues/forms.py`
- Issue URLs: `doi_portal/doi_portal/issues/urls.py`
- Issue admin templates: `doi_portal/doi_portal/templates/issues/`
- Issue tests: `doi_portal/doi_portal/issues/tests/`
- Config URLs: `doi_portal/config/urls.py`
- Settings: `doi_portal/config/settings/base.py`
- Sidebar: `doi_portal/doi_portal/templates/admin_base.html`
- Public portal views: `doi_portal/doi_portal/portal/views.py`
- Public portal publication detail: `doi_portal/doi_portal/templates/portal/publications/publication_detail.html`

### NFR Requirements Addressed

- **NFR3:** Admin panel stranice < 5 sekundi - `select_related("publication", "publication__publisher")` za optimizaciju
- **NFR12:** Audit log - django-auditlog registracija za Issue model
- **NFR14:** Semanticki HTML5 elementi u template-ovima
- **NFR15:** Alt tekst za cover images
- **NFR17:** Keyboard navigacija za forme i kontrole

### References

- [Source: epics.md#Story 2.6: Issue Model & Admin CRUD]
- [Source: prd.md#FR18 - Urednik moze kreirati novo izdanje publikacije]
- [Source: prd.md#FR19 - Urednik moze editovati podatke o izdanju]
- [Source: prd.md#FR20 - Urednik moze postaviti status izdanja]
- [Source: prd.md#Izdanje (Issue) - polja - Data Model Update]
- [Source: architecture.md#Data Architecture - django-auditlog]
- [Source: architecture.md#Structure Patterns - Django App Organization]
- [Source: architecture.md#Implementation Patterns - Naming Patterns]
- [Source: project-context.md#Django Apps Struktura - issues/]
- [Source: project-context.md#RBAC Model (django-guardian)]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri]
- [Source: 2-4-publication-admin-list-edit.md - PublisherScopedMixin pattern]
- [Source: 2-5-public-publication-list-with-filters.md - Portal public view patterns]
- [Source: publishers/mixins.py - PublisherScopedMixin, PublisherScopedEditMixin]
- [Source: publications/models.py - Publication model, SoftDeleteManager import]
- [Source: publications/views.py - _HAS_ISSUES_RELATION pattern]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 71 issue-specific tests pass (test_models.py, test_forms.py, test_views.py)
- Full test suite: 505 passed, 3 skipped, 0 failed
- Migration 0001_initial created for issues app
- publications migration 0003 auto-generated (field alterations from previous story)

### Completion Notes List

- Issue model implemented with all fields per AC #1
- UniqueConstraint excludes soft-deleted records (condition=Q(is_deleted=False))
- Publication.issue_count now returns real count via related_name="issues"
- _HAS_ISSUES_RELATION in publications/views.py auto-detects Issue relation at module load
- IssueForm scopes publication queryset based on user role
- All views override get_scoped_queryset() to use publication__publisher
- Sidebar menu updated: issues url_name set, publications url_name fixed, Bibliotekar added to both
- Public portal publication detail now shows real published issues
- Portal test updated to match new "Nema objavljenih izdanja." text

### File List

**New files:**
- `doi_portal/doi_portal/issues/__init__.py`
- `doi_portal/doi_portal/issues/admin.py`
- `doi_portal/doi_portal/issues/apps.py`
- `doi_portal/doi_portal/issues/forms.py`
- `doi_portal/doi_portal/issues/models.py`
- `doi_portal/doi_portal/issues/urls.py`
- `doi_portal/doi_portal/issues/views.py`
- `doi_portal/doi_portal/issues/tests/__init__.py`
- `doi_portal/doi_portal/issues/tests/factories.py`
- `doi_portal/doi_portal/issues/tests/test_models.py`
- `doi_portal/doi_portal/issues/tests/test_forms.py`
- `doi_portal/doi_portal/issues/tests/test_views.py`
- `doi_portal/doi_portal/issues/migrations/0001_initial.py`
- `doi_portal/doi_portal/templates/issues/issue_list.html`
- `doi_portal/doi_portal/templates/issues/issue_form.html`
- `doi_portal/doi_portal/templates/issues/issue_detail.html`
- `doi_portal/doi_portal/templates/issues/issue_confirm_delete.html`

**Modified files:**
- `doi_portal/config/settings/base.py` - Added "doi_portal.issues" to LOCAL_APPS
- `doi_portal/config/urls.py` - Added issues URL include
- `doi_portal/doi_portal/core/menu.py` - Activated issues and publications menu items
- `doi_portal/doi_portal/templates/publications/publication_detail.html` - Added issues section
- `doi_portal/doi_portal/templates/portal/publications/publication_detail.html` - Real issues list
- `doi_portal/doi_portal/portal/views.py` - Real published issues queryset
- `doi_portal/doi_portal/portal/tests/test_views.py` - Updated placeholder test
- `doi_portal/doi_portal/publications/migrations/0003_alter_publication_conference_date_end_and_more.py` - Auto-generated
