---
title: 'Interni podaci izdavača - kontakt osobe, Crossref kredencijali i napomene'
slug: 'publisher-internal-data'
created: '2026-03-15'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Django 5.2', 'Alpine.js 3.15', 'Bootstrap 5.3', 'HTMX 2.0', 'cryptography (Fernet)']
files_to_modify:
  - 'doi_portal/publishers/models.py'
  - 'doi_portal/publishers/fields.py'
  - 'doi_portal/publishers/forms.py'
  - 'doi_portal/publishers/views.py'
  - 'doi_portal/publishers/urls.py'
  - 'doi_portal/publishers/admin.py'
  - 'doi_portal/publishers/apps.py'
  - 'doi_portal/templates/publishers/publisher_form.html'
  - 'doi_portal/templates/publishers/publisher_detail.html'
  - 'doi_portal/templates/publishers/partials/_contact_form.html'
  - 'doi_portal/templates/publishers/partials/_contact_item.html'
  - 'doi_portal/templates/publishers/partials/_contact_list.html'
  - 'doi_portal/templates/publishers/partials/_note_form.html'
  - 'doi_portal/templates/publishers/partials/_note_item.html'
  - 'doi_portal/templates/publishers/partials/_note_list.html'
  - 'doi_portal/publishers/tests/test_models.py'
  - 'doi_portal/publishers/tests/test_forms.py'
  - 'doi_portal/publishers/tests/test_views.py'
code_patterns:
  - 'SoftDeleteMixin za soft delete sa is_deleted/deleted_at/deleted_by'
  - 'HTMX partial pattern: partials/_prefix template + FBV sa @login_required/@require_POST'
  - 'Alpine.js x-data komponente za interaktivnost'
  - 'Bootstrap 5 form-control widgeti sa placeholder-ima'
  - 'Auditlog registracija u apps.py ready()'
  - '_check_permission helper funkcija za HTMX view-ove'
  - 'Individual ModelForm (NE formset) za child modele'
test_patterns:
  - 'pytest sa @pytest.mark.django_db dekoratorom'
  - 'Fixture-based: admin_user, publisher, superadmin_user, urednik_user, bibliotekar_user'
  - 'Test klase po feature-u'
  - 'Permission testovi: 403 za neovlašćene korisnike'
  - 'Form validation testovi: required, format, uniqueness'
  - 'View CRUD testovi: list, create, update, detail, delete'
---

# Tech-Spec: Interni podaci izdavača - kontakt osobe, Crossref kredencijali i napomene

**Created:** 2026-03-15

## Overview

### Problem Statement

Admin korisnici DOI portala nemaju interni pregled kontakt osoba, Crossref kredencijala i napomena za izdavače unutar samog portala - koriste Excel tabelu za evidenciju tih podataka. Potrebno je centralizovati te interne informacije u portal, ali ih ne prikazivati na javnim stranicama.

### Solution

Proširiti Publisher model sa Crossref kredencijalima (username + enkriptovani password) i dodati dva nova child modela: PublisherContact (kontakt osobe) i PublisherNote (napomene/komentari). Svi novi podaci su vidljivi isključivo u dashboard-u za Administrator/Superadmin korisnike. Koristi se HTMX partial pattern sa function-based view-ovima (kao Author/Affiliation u articles app) za child model CRUD.

### Scope

**In Scope:**
- `PublisherContact` child model sa soft delete (ime, prezime, email, telefon, role kao slobodan tekst)
- `crossref_username` i `crossref_password` (enkriptovano u bazi, opciono) na Publisher modelu
- `PublisherNote` child model - comment sekcija na publisher detail stranici (tekst, autor, created_at, updated_at)
- HTMX partial pattern sa FBV za kontakt osobe (add/edit/delete) na publisher form i detail stranicama
- HTMX partial pattern sa FBV za napomene (add/edit/delete) na publisher detail stranici
- Password se NE šalje u HTML - prikazuje se na zahtev preko dedikovanog HTMX endpointa
- Custom `EncryptedCharField` koristeći `cryptography.fernet.Fernet` (bez third-party Django paketa)

**Out of Scope:**
- Promene na public stranicama (`portal/` templates) - NE DIRATI
- Promene na postojećim `contact_email`/`contact_phone`/`website` poljima
- API/serializers za nove podatke
- Promene na RBAC sistemu (postojeći `AdministratorRequiredMixin` je dovoljan)
- Drag-drop reordering za kontakte (može se dodati kasnije)

## Context for Development

### Codebase Patterns

1. **Child Model Pattern (Author → Article):**
   - ForeignKey sa `on_delete=CASCADE`, `related_name`
   - `order` polje (PositiveIntegerField, default=0) za sortiranje
   - SoftDeleteMixin na prvom nivou child-a
   - Individual ModelForm (NE Django formset)
   - HTMX partial template-i u `partials/` poddirektorijumu sa `_` prefiksom

2. **HTMX FBV CRUD Pattern (iz articles app):**
   - Function-based view-ovi sa `@login_required` i `@require_POST`/`@require_GET` dekoratorima
   - Permission check pomoću helper funkcije (npr. `_check_article_permission()`)
   - View vraća renderovan partial, HTMX zamenjuje sadržaj u target `div`-u
   - CSRF token se šalje inline u formama (`{% csrf_token %}`), a za dugmad van formi koristi se wrapper `<form>` element

3. **SoftDeleteMixin (iz `core/mixins.py`):**
   - Polja: `is_deleted` (BooleanField), `deleted_at` (DateTimeField), `deleted_by` (FK → User)
   - Manageri: `objects` (filtrira deleted), `all_objects` (uključuje sve)
   - Metode: `soft_delete(user=None)`, `restore()`

4. **Form Widget Pattern:**
   - Svi inputi koriste `class="form-control"` (Bootstrap 5)
   - Placeholder-i na srpskom jeziku
   - `invalid-feedback d-block` za prikaz grešaka
   - Custom `clean_*()` metode za validaciju

5. **Alpine.js Pattern:**
   - Inline `x-data="functionName()"` u template-ima
   - Direktive: `x-show`, `x-text`, `:class`, `@click`
   - Funkcije definisane u `<script>` tagu unutar template-a

6. **Auditlog Pattern:**
   - Registracija u `apps.py` → `ready()` metodi
   - `from auditlog.registry import auditlog` + `auditlog.register(Model)`

7. **Template Structure:**
   - Dashboard extends `admin_base.html`, koristi Bootstrap 5 cards
   - Portal extends `portal/base.html` - NE DIRATI
   - HTMX partials idu u `templates/{app}/partials/` poddirektorijum sa `_` prefiksom
   - Ikone: Bootstrap Icons sa `bi bi-*` klasama
   - Poruke: Django `messages` framework sa Bootstrap alert klasama

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `publishers/models.py` | Postojeći Publisher model - dodati Crossref polja + nove child modele |
| `publishers/forms.py` | Postojeći PublisherForm - dodati Crossref polja + nove forme |
| `publishers/views.py` | Postojeći CRUD view-ovi - dodati FBV HTMX endpointe |
| `publishers/urls.py` | Postojeće URL rute - dodati nove za HTMX |
| `publishers/admin.py` | Postojeći PublisherAdmin - dodati inline + Crossref fieldset |
| `publishers/apps.py` | App config - dodati auditlog registraciju novih modela |
| `publishers/mixins.py` | AdministratorRequiredMixin - referenca za permission pattern |
| `core/mixins.py` | SoftDeleteMixin/Manager - koristiti za PublisherContact |
| `articles/models.py` | Author/Affiliation child model pattern - referenca |
| `articles/views.py` | FBV HTMX view-ovi (`author_add`, `author_delete`, etc.) - referenca za pattern |
| `templates/publishers/publisher_form.html` | Dashboard forma - dodati Crossref + Contact sekcije |
| `templates/publishers/publisher_detail.html` | Dashboard detail - dodati Contact + Notes sekcije |
| `templates/articles/partials/_author_form.html` | HTMX partial referenca za `partials/` konvenciju |
| `templates/portal/publishers/publisher_detail.html` | Public detail - **NE DIRATI** |
| `templates/portal/publishers/publisher_list.html` | Public list - **NE DIRATI** |

### Technical Decisions

1. **FBV sa dekoratorima za HTMX endpointe** - Projekat koristi function-based view-ove sa `@login_required`/`@require_POST`/`@require_GET` za HTMX CRUD (videti articles app: `author_add`, `author_delete`, `author_update`). Pratimo isti pristup za konzistentnost, ne CBV.

2. **Custom `EncryptedCharField` umesto `django-fernet-fields`** - Paket `django-fernet-fields` je napušten i nekompatibilan sa Django 5.2. Implementiramo custom model field u `publishers/fields.py` koristeći `cryptography.fernet.Fernet` (već prisutan kao transitivna zavisnost). Ovo je 30-40 linija koda i potpuno pod našom kontrolom.

3. **Password se NE šalje u HTML** - Crossref password se nikada ne renderuje u template (ni u formi ni u detail stranici). U detail stranici prikazuje se `••••••••` a pravi password se dohvata na zahtev kroz dedikovani HTMX endpoint (`reveal-password`). U edit formi password polje je prazno - unos novog passworda ga menja, prazno polje ga zadržava.

4. **PublisherNote bez soft delete** - Napomene se hard delete-uju (kao Affiliation model) jer nemaju kritičnu vrednost za audit trail. Autor i timestamp su dovoljni.

5. **PublisherContact sa soft delete** - Kontakt osobe koriste SoftDeleteMixin jer mogu sadržati važne podatke.

6. **HTMX partials u `partials/` poddirektorijumu** - Po konvenciji iz `project-context.md` i articles app, HTMX fragmenti idu u `templates/publishers/partials/` sa `_` prefiksom.

7. **CSRF za delete dugmad** - Delete dugmad su umotana u `<form>` element sa `{% csrf_token %}` da bi HTMX POST imao CSRF token. Ne oslanjamo se na globalni `htmx:configRequest` handler.

8. **`is_edited` flag na PublisherNote** - Umesto poređenja `updated_at != created_at` (koje je uvek true zbog `auto_now`), koristimo eksplicitni `is_edited` BooleanField koji se setuje na True pri update-u.

9. **Svi admini mogu moderisati napomene** - Svaka osoba sa Administrator/Superadmin rolom može editovati ili brisati napomene drugih admina. Ovo je svesna dizajn odluka jer je portal interni alat sa malim brojem admin korisnika.

## Implementation Plan

### Tasks

- [ ] **Task 1: Kreirati custom `EncryptedCharField`**
  - File: `doi_portal/publishers/fields.py` (novi fajl)
  - Action: Kreirati custom Django model field koji koristi `cryptography.fernet.Fernet` za dvosmerno enkriptovanje:
    ```python
    """Custom encrypted field using Fernet symmetric encryption."""
    from __future__ import annotations

    import base64
    import hashlib

    from cryptography.fernet import Fernet
    from django.conf import settings
    from django.db import models


    def _get_fernet():
        """Get Fernet instance using FERNET_KEY or derived from SECRET_KEY."""
        key = getattr(settings, "FERNET_KEY", None)
        if not key:
            # Derive a valid Fernet key from SECRET_KEY
            digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
            key = base64.urlsafe_b64encode(digest)
        elif isinstance(key, str):
            key = key.encode()
        return Fernet(key)


    class EncryptedCharField(models.CharField):
        """CharField that encrypts value at rest using Fernet."""

        def get_prep_value(self, value):
            """Encrypt before saving to database."""
            if value is None or value == "":
                return value
            f = _get_fernet()
            return f.encrypt(value.encode()).decode()

        def from_db_value(self, value, expression, connection):
            """Decrypt when reading from database."""
            if value is None or value == "":
                return value
            try:
                f = _get_fernet()
                return f.decrypt(value.encode()).decode()
            except Exception:
                return value  # Return raw if decryption fails

        def get_internal_type(self):
            return "TextField"  # Encrypted values are longer than originals
    ```
  - Notes: Koristi `cryptography` koji je već prisutan kao transitivna zavisnost. `get_internal_type` vraća "TextField" jer enkriptovani string je duži od originala. Fallback na `SECRET_KEY` ako `FERNET_KEY` nije setovan.

- [ ] **Task 2: Kreirati `PublisherContact` model**
  - File: `doi_portal/publishers/models.py`
  - Action: Dodati novi model `PublisherContact(SoftDeleteMixin, models.Model)`:
    ```python
    class PublisherContact(SoftDeleteMixin, models.Model):
        """Internal contact person for a publisher."""

        publisher = models.ForeignKey(
            Publisher,
            on_delete=models.CASCADE,
            related_name="contacts",
        )
        first_name = models.CharField(_("Ime"), max_length=100)
        last_name = models.CharField(_("Prezime"), max_length=100)
        email = models.EmailField(_("Email"), blank=True)
        phone = models.CharField(_("Telefon"), max_length=50, blank=True)
        role = models.CharField(
            _("Funkcija"),
            max_length=100,
            blank=True,
            help_text=_("npr. direktor, urednik, kontakt za Crossref"),
        )
        order = models.PositiveIntegerField(_("Redosled"), default=0)
        created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
        updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)

        objects = SoftDeleteManager()
        all_objects = models.Manager()

        class Meta:
            verbose_name = _("Kontakt osoba")
            verbose_name_plural = _("Kontakt osobe")
            ordering = ["order", "last_name"]

        def __str__(self):
            return f"{self.first_name} {self.last_name}"
    ```

- [ ] **Task 3: Kreirati `PublisherNote` model**
  - File: `doi_portal/publishers/models.py`
  - Action: Dodati novi model `PublisherNote(models.Model)` (BEZ soft delete):
    ```python
    class PublisherNote(models.Model):
        """Internal note/comment for a publisher. Comment thread style."""

        publisher = models.ForeignKey(
            Publisher,
            on_delete=models.CASCADE,
            related_name="notes",
        )
        text = models.TextField(_("Tekst napomene"))
        author = models.ForeignKey(
            "users.User",
            on_delete=models.SET_NULL,
            null=True,
            related_name="publisher_notes",
            verbose_name=_("Autor"),
        )
        is_edited = models.BooleanField(_("Izmenjeno"), default=False)
        created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
        updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)

        class Meta:
            verbose_name = _("Napomena")
            verbose_name_plural = _("Napomene")
            ordering = ["-created_at"]

        def __str__(self):
            return f"Napomena za {self.publisher.name} ({self.created_at:%d.%m.%Y})"
    ```
  - Notes: `is_edited` flag se eksplicitno setuje na `True` u view-u pri update-u. Ne koristimo `updated_at` za detekciju jer `auto_now=True` ga uvek menja.

- [ ] **Task 4: Dodati Crossref polja na Publisher model**
  - File: `doi_portal/publishers/models.py`
  - Action: Dodati dva nova polja na Publisher klasu, posle `website` polja:
    ```python
    from doi_portal.publishers.fields import EncryptedCharField

    # Crossref credentials (internal only)
    crossref_username = models.CharField(
        _("Crossref korisničko ime"),
        max_length=100,
        blank=True,
        help_text=_("Korisničko ime za Crossref API"),
    )
    crossref_password = EncryptedCharField(
        _("Crossref lozinka"),
        max_length=255,
        blank=True,
        help_text=_("Lozinka za Crossref API (enkriptovana u bazi)"),
    )
    ```
  - Action: Ažurirati `__all__` listu da uključi `"PublisherContact"` i `"PublisherNote"`

- [ ] **Task 5: Kreirati i pokrenuti migraciju**
  - Action: `python manage.py makemigrations publishers`
  - Action: `python manage.py migrate`

- [ ] **Task 6: Kreirati `PublisherContactForm` i `PublisherNoteForm`**
  - File: `doi_portal/publishers/forms.py`
  - Action: Dodati dve nove forme:
    ```python
    from .models import Publisher, PublisherContact, PublisherNote, validate_doi_prefix

    class PublisherContactForm(forms.ModelForm):
        """Form for adding/editing internal contact persons."""

        class Meta:
            model = PublisherContact
            fields = ["first_name", "last_name", "email", "phone", "role"]
            widgets = {
                "first_name": forms.TextInput(attrs={
                    "class": "form-control",
                    "placeholder": "Ime",
                }),
                "last_name": forms.TextInput(attrs={
                    "class": "form-control",
                    "placeholder": "Prezime",
                }),
                "email": forms.EmailInput(attrs={
                    "class": "form-control",
                    "placeholder": "email@primer.rs",
                }),
                "phone": forms.TextInput(attrs={
                    "class": "form-control",
                    "placeholder": "+381 11 123 4567",
                }),
                "role": forms.TextInput(attrs={
                    "class": "form-control",
                    "placeholder": "npr. direktor, urednik, kontakt za Crossref",
                }),
            }

    class PublisherNoteForm(forms.ModelForm):
        """Form for adding/editing publisher notes."""

        class Meta:
            model = PublisherNote
            fields = ["text"]
            widgets = {
                "text": forms.Textarea(attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Unesite napomenu...",
                }),
            }
    ```
  - Action: Dodati `crossref_username` u PublisherForm `fields` listu i dodati widget:
    ```python
    "crossref_username": forms.TextInput(attrs={
        "class": "form-control",
        "placeholder": "Crossref korisničko ime",
    }),
    ```
  - Action: Dodati zasebno `crossref_password` polje u PublisherForm kao `CharField` (NE iz modela):
    ```python
    crossref_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Unesite novu lozinku (ostavite prazno za bez promene)",
            "autocomplete": "new-password",
        }),
        label=_("Crossref lozinka"),
    )
    ```
  - Action: Dodati custom `save()` metodu na PublisherForm da handluje password:
    ```python
    def save(self, commit=True):
        publisher = super().save(commit=False)
        password = self.cleaned_data.get("crossref_password")
        if password:
            publisher.crossref_password = password
        if commit:
            publisher.save()
        return publisher
    ```
  - Notes: Password polje je uvek prazno u formi. Ako korisnik unese novu lozinku, ona se sačuva. Ako ostavi prazno, postojeća lozinka se ne menja. Ovo sprečava slanje dekriptovanog passworda u HTML.

- [ ] **Task 7: Kreirati `_check_publisher_permission` helper funkciju**
  - File: `doi_portal/publishers/views.py`
  - Action: Dodati helper funkciju za permission check u HTMX view-ovima (po uzoru na `_check_article_permission` iz articles app):
    ```python
    from django.core.exceptions import PermissionDenied

    def _check_publisher_admin(user):
        """Check if user is Administrator or Superadmin. Raises PermissionDenied."""
        if user.is_superuser:
            return
        group_names = set(user.groups.values_list("name", flat=True))
        if "Administrator" in group_names or "Superadmin" in group_names:
            return
        raise PermissionDenied
    ```

- [ ] **Task 8: Dodati FBV HTMX view-ove za PublisherContact**
  - File: `doi_portal/publishers/views.py`
  - Action: Dodati function-based view-ove (po uzoru na articles app `author_add`/`author_delete`/`author_update`):
    ```python
    from django.contrib.auth.decorators import login_required
    from django.shortcuts import get_object_or_404, render
    from django.views.decorators.http import require_GET, require_POST

    @login_required
    @require_GET
    def contact_list(request, publisher_pk):
        """HTMX partial: lista kontakata za izdavača."""
        _check_publisher_admin(request.user)
        publisher = get_object_or_404(Publisher, pk=publisher_pk)
        contacts = publisher.contacts.all()
        return render(request, "publishers/partials/_contact_list.html", {
            "publisher": publisher,
            "contacts": contacts,
        })

    @login_required
    @require_GET
    def contact_add_form(request, publisher_pk):
        """HTMX partial: prazna forma za dodavanje kontakta."""
        _check_publisher_admin(request.user)
        publisher = get_object_or_404(Publisher, pk=publisher_pk)
        form = PublisherContactForm()
        return render(request, "publishers/partials/_contact_form.html", {
            "publisher": publisher,
            "form": form,
        })

    @login_required
    @require_POST
    def contact_add(request, publisher_pk):
        """HTMX partial: dodaj kontakt osobu."""
        _check_publisher_admin(request.user)
        publisher = get_object_or_404(Publisher, pk=publisher_pk)
        form = PublisherContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.publisher = publisher
            contact.save()
            contacts = publisher.contacts.all()
            return render(request, "publishers/partials/_contact_list.html", {
                "publisher": publisher,
                "contacts": contacts,
            })
        return render(request, "publishers/partials/_contact_form.html", {
            "publisher": publisher,
            "form": form,
        })

    @login_required
    @require_GET
    def contact_edit_form(request, pk):
        """HTMX partial: forma za editovanje kontakta."""
        _check_publisher_admin(request.user)
        contact = get_object_or_404(PublisherContact, pk=pk)
        form = PublisherContactForm(instance=contact)
        return render(request, "publishers/partials/_contact_form.html", {
            "publisher": contact.publisher,
            "form": form,
            "contact": contact,
        })

    @login_required
    @require_POST
    def contact_update(request, pk):
        """HTMX partial: ažuriraj kontakt osobu."""
        _check_publisher_admin(request.user)
        contact = get_object_or_404(PublisherContact, pk=pk)
        form = PublisherContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            contacts = contact.publisher.contacts.all()
            return render(request, "publishers/partials/_contact_list.html", {
                "publisher": contact.publisher,
                "contacts": contacts,
            })
        return render(request, "publishers/partials/_contact_form.html", {
            "publisher": contact.publisher,
            "form": form,
            "contact": contact,
        })

    @login_required
    @require_POST
    def contact_delete(request, pk):
        """HTMX partial: soft delete kontakta."""
        _check_publisher_admin(request.user)
        contact = get_object_or_404(PublisherContact, pk=pk)
        publisher = contact.publisher
        contact.soft_delete(user=request.user)
        contacts = publisher.contacts.all()
        return render(request, "publishers/partials/_contact_list.html", {
            "publisher": publisher,
            "contacts": contacts,
        })
    ```

- [ ] **Task 9: Dodati FBV HTMX view-ove za PublisherNote**
  - File: `doi_portal/publishers/views.py`
  - Action: Dodati function-based view-ove za napomene:
    ```python
    @login_required
    @require_GET
    def note_list(request, publisher_pk):
        """HTMX partial: lista napomena za izdavača."""
        _check_publisher_admin(request.user)
        publisher = get_object_or_404(Publisher, pk=publisher_pk)
        notes = publisher.notes.select_related("author").all()
        note_form = PublisherNoteForm()
        return render(request, "publishers/partials/_note_list.html", {
            "publisher": publisher,
            "notes": notes,
            "note_form": note_form,
        })

    @login_required
    @require_POST
    def note_add(request, publisher_pk):
        """HTMX partial: dodaj napomenu."""
        _check_publisher_admin(request.user)
        publisher = get_object_or_404(Publisher, pk=publisher_pk)
        form = PublisherNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.publisher = publisher
            note.author = request.user
            note.save()
            notes = publisher.notes.select_related("author").all()
            note_form = PublisherNoteForm()
            return render(request, "publishers/partials/_note_list.html", {
                "publisher": publisher,
                "notes": notes,
                "note_form": note_form,
            })
        # On error, re-render list with the invalid form
        notes = publisher.notes.select_related("author").all()
        return render(request, "publishers/partials/_note_list.html", {
            "publisher": publisher,
            "notes": notes,
            "note_form": form,
        })

    @login_required
    @require_GET
    def note_edit_form(request, pk):
        """HTMX partial: forma za editovanje napomene."""
        _check_publisher_admin(request.user)
        note = get_object_or_404(PublisherNote, pk=pk)
        form = PublisherNoteForm(instance=note)
        return render(request, "publishers/partials/_note_form.html", {
            "publisher": note.publisher,
            "form": form,
            "note": note,
        })

    @login_required
    @require_POST
    def note_update(request, pk):
        """HTMX partial: ažuriraj napomenu."""
        _check_publisher_admin(request.user)
        note = get_object_or_404(PublisherNote, pk=pk)
        form = PublisherNoteForm(request.POST, instance=note)
        if form.is_valid():
            note = form.save(commit=False)
            note.is_edited = True
            note.save()
            notes = note.publisher.notes.select_related("author").all()
            note_form = PublisherNoteForm()
            return render(request, "publishers/partials/_note_list.html", {
                "publisher": note.publisher,
                "notes": notes,
                "note_form": note_form,
            })
        return render(request, "publishers/partials/_note_form.html", {
            "publisher": note.publisher,
            "form": form,
            "note": note,
        })

    @login_required
    @require_POST
    def note_delete(request, pk):
        """HTMX partial: hard delete napomene."""
        _check_publisher_admin(request.user)
        note = get_object_or_404(PublisherNote, pk=pk)
        publisher = note.publisher
        note.delete()  # Hard delete
        notes = publisher.notes.select_related("author").all()
        note_form = PublisherNoteForm()
        return render(request, "publishers/partials/_note_list.html", {
            "publisher": publisher,
            "notes": notes,
            "note_form": note_form,
        })
    ```
  - Notes: Svaki view koji vraća `_note_list.html` prosleđuje `note_form` u kontekstu jer lista uvek sadrži formu za dodavanje.

- [ ] **Task 10: Dodati HTMX endpoint za reveal Crossref passworda**
  - File: `doi_portal/publishers/views.py`
  - Action: Dodati FBV za prikaz passworda na zahtev:
    ```python
    from django.http import HttpResponse

    @login_required
    @require_POST
    def reveal_crossref_password(request, pk):
        """HTMX partial: prikaži dekriptovani crossref password."""
        _check_publisher_admin(request.user)
        publisher = get_object_or_404(Publisher, pk=pk)
        if publisher.crossref_password:
            return HttpResponse(
                f'<code>{publisher.crossref_password}</code>'
                f' <button class="btn btn-sm btn-outline-secondary ms-2" '
                f'hx-get="{{% url "publishers:detail" pk={pk} %}}" '
                f'hx-target="closest .card-body" hx-swap="innerHTML">'
                f'<i class="bi bi-eye-slash"></i> Sakrij</button>'
            )
        return HttpResponse('<span class="text-muted">Nije unet</span>')
    ```
  - Notes: Password se šalje samo na eksplicitni POST zahtev. "Sakrij" dugme reload-uje celu sekciju. Alternativno, koristiti mali template partial umesto inline HTML-a u view-u.
  - **BOLJA ALTERNATIVA** - Kreirati partial `publishers/partials/_crossref_password_revealed.html`:
    ```html
    <code>{{ password }}</code>
    <form method="post" class="d-inline"
          hx-post="{% url 'publishers:hide-crossref-password' pk=publisher.pk %}"
          hx-target="#crossref-password-cell"
          hx-swap="innerHTML">
        {% csrf_token %}
        <button type="submit" class="btn btn-sm btn-outline-secondary ms-2">
            <i class="bi bi-eye-slash"></i> Sakrij
        </button>
    </form>
    ```
  - I ažurirati view:
    ```python
    @login_required
    @require_POST
    def reveal_crossref_password(request, pk):
        """HTMX: prikaži dekriptovani crossref password."""
        _check_publisher_admin(request.user)
        publisher = get_object_or_404(Publisher, pk=pk)
        return render(request, "publishers/partials/_crossref_password_revealed.html", {
            "publisher": publisher,
            "password": publisher.crossref_password or "",
        })

    @login_required
    @require_POST
    def hide_crossref_password(request, pk):
        """HTMX: sakrij crossref password (vrati masked view)."""
        _check_publisher_admin(request.user)
        publisher = get_object_or_404(Publisher, pk=pk)
        return render(request, "publishers/partials/_crossref_password_masked.html", {
            "publisher": publisher,
        })
    ```
  - I kreirati `publishers/partials/_crossref_password_masked.html`:
    ```html
    <code>••••••••</code>
    <form method="post" class="d-inline"
          hx-post="{% url 'publishers:reveal-crossref-password' pk=publisher.pk %}"
          hx-target="#crossref-password-cell"
          hx-swap="innerHTML">
        {% csrf_token %}
        <button type="submit" class="btn btn-sm btn-outline-secondary ms-2">
            <i class="bi bi-eye"></i> Prikaži
        </button>
    </form>
    ```

- [ ] **Task 11: Dodati URL rute za HTMX endpointe**
  - File: `doi_portal/publishers/urls.py`
  - Action: Dodati nove URL pattern-e:
    ```python
    urlpatterns = [
        # Postojeći
        path("", views.PublisherListView.as_view(), name="list"),
        path("create/", views.PublisherCreateView.as_view(), name="create"),
        path("<int:pk>/", views.PublisherDetailView.as_view(), name="detail"),
        path("<int:pk>/edit/", views.PublisherUpdateView.as_view(), name="update"),
        path("<int:pk>/delete/", views.PublisherDeleteView.as_view(), name="delete"),

        # Crossref password reveal (HTMX)
        path("<int:pk>/reveal-password/", views.reveal_crossref_password, name="reveal-crossref-password"),
        path("<int:pk>/hide-password/", views.hide_crossref_password, name="hide-crossref-password"),

        # Kontakt osobe (HTMX)
        path("<int:publisher_pk>/contacts/", views.contact_list, name="contact-list"),
        path("<int:publisher_pk>/contacts/add-form/", views.contact_add_form, name="contact-add-form"),
        path("<int:publisher_pk>/contacts/add/", views.contact_add, name="contact-add"),
        path("contacts/<int:pk>/edit-form/", views.contact_edit_form, name="contact-edit-form"),
        path("contacts/<int:pk>/update/", views.contact_update, name="contact-update"),
        path("contacts/<int:pk>/delete/", views.contact_delete, name="contact-delete"),

        # Napomene (HTMX)
        path("<int:publisher_pk>/notes/", views.note_list, name="note-list"),
        path("<int:publisher_pk>/notes/add/", views.note_add, name="note-add"),
        path("notes/<int:pk>/edit-form/", views.note_edit_form, name="note-edit-form"),
        path("notes/<int:pk>/update/", views.note_update, name="note-update"),
        path("notes/<int:pk>/delete/", views.note_delete, name="note-delete"),
    ]
    ```

- [ ] **Task 12: Ažurirati `PublisherDetailView` da prosledi kontakte i napomene u kontekst**
  - File: `doi_portal/publishers/views.py`
  - Action: Ažurirati `get_context_data()`:
    ```python
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [...]  # postojeće
        context["contacts"] = self.object.contacts.all()
        context["notes"] = self.object.notes.select_related("author").all()
        context["note_form"] = PublisherNoteForm()
        return context
    ```

- [ ] **Task 13: Kreirati `templates/publishers/partials/` direktorijum i HTMX partial `_contact_item.html`**
  - File: `doi_portal/templates/publishers/partials/_contact_item.html`
  - Action: Kreirati partial za prikaz jednog kontakta:
    ```html
    <div class="card mb-2" id="contact-{{ contact.pk }}">
        <div class="card-body py-2 d-flex align-items-center">
            <div class="flex-grow-1">
                <strong>{{ contact.first_name }} {{ contact.last_name }}</strong>
                {% if contact.role %}
                <span class="text-muted ms-2">- {{ contact.role }}</span>
                {% endif %}
                <div class="small text-muted">
                    {% if contact.email %}
                    <i class="bi bi-envelope me-1"></i>{{ contact.email }}
                    {% endif %}
                    {% if contact.phone %}
                    <i class="bi bi-telephone ms-2 me-1"></i>{{ contact.phone }}
                    {% endif %}
                </div>
            </div>
            <div class="ms-2 d-flex gap-1">
                <button type="button" class="btn btn-sm btn-outline-primary"
                        hx-get="{% url 'publishers:contact-edit-form' pk=contact.pk %}"
                        hx-target="#contact-form-container"
                        hx-swap="innerHTML">
                    <i class="bi bi-pencil"></i>
                </button>
                <form method="post" class="d-inline"
                      hx-post="{% url 'publishers:contact-delete' pk=contact.pk %}"
                      hx-target="#contacts-section"
                      hx-swap="innerHTML"
                      hx-confirm="Obrisati kontakt osobu?">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-sm btn-outline-danger">
                        <i class="bi bi-trash"></i>
                    </button>
                </form>
            </div>
        </div>
    </div>
    ```
  - Notes: Delete dugme je umotano u `<form>` sa `{% csrf_token %}` da bi HTMX POST imao CSRF token (F6 fix).

- [ ] **Task 14: Kreirati HTMX partial `_contact_form.html`**
  - File: `doi_portal/templates/publishers/partials/_contact_form.html`
  - Action: Kreirati partial formu za add/edit kontakta:
    ```html
    <div class="card mb-3 border-primary">
        <div class="card-body">
            <h6 class="card-title">{% if contact %}Izmeni kontakt{% else %}Novi kontakt{% endif %}</h6>
            <form method="post"
                  {% if contact %}
                    hx-post="{% url 'publishers:contact-update' pk=contact.pk %}"
                  {% else %}
                    hx-post="{% url 'publishers:contact-add' publisher_pk=publisher.pk %}"
                  {% endif %}
                  hx-target="#contacts-section"
                  hx-swap="innerHTML">
                {% csrf_token %}
                <div class="row">
                    <div class="col-md-4 mb-2">
                        <label class="form-label">Ime <span class="text-danger">*</span></label>
                        {{ form.first_name }}
                        {% if form.first_name.errors %}
                        <div class="invalid-feedback d-block">{{ form.first_name.errors.0 }}</div>
                        {% endif %}
                    </div>
                    <div class="col-md-4 mb-2">
                        <label class="form-label">Prezime <span class="text-danger">*</span></label>
                        {{ form.last_name }}
                        {% if form.last_name.errors %}
                        <div class="invalid-feedback d-block">{{ form.last_name.errors.0 }}</div>
                        {% endif %}
                    </div>
                    <div class="col-md-4 mb-2">
                        <label class="form-label">Funkcija</label>
                        {{ form.role }}
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6 mb-2">
                        <label class="form-label">Email</label>
                        {{ form.email }}
                        {% if form.email.errors %}
                        <div class="invalid-feedback d-block">{{ form.email.errors.0 }}</div>
                        {% endif %}
                    </div>
                    <div class="col-md-6 mb-2">
                        <label class="form-label">Telefon</label>
                        {{ form.phone }}
                    </div>
                </div>
                <div class="d-flex gap-2 mt-2">
                    <button type="submit" class="btn btn-sm btn-primary">
                        <i class="bi bi-check-lg me-1"></i>Sačuvaj
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary"
                            hx-get="{% url 'publishers:contact-list' publisher_pk=publisher.pk %}"
                            hx-target="#contacts-section"
                            hx-swap="innerHTML">
                        Otkaži
                    </button>
                </div>
            </form>
        </div>
    </div>
    ```

- [ ] **Task 15: Kreirati HTMX partial `_contact_list.html`**
  - File: `doi_portal/templates/publishers/partials/_contact_list.html`
  - Action: Kreirati wrapper partial:
    ```html
    <div id="contact-form-container"></div>
    {% for contact in contacts %}
        {% include "publishers/partials/_contact_item.html" with contact=contact %}
    {% empty %}
        <p class="text-muted">Nema unetih kontakt osoba.</p>
    {% endfor %}
    <button type="button" class="btn btn-sm btn-outline-primary mt-2"
            hx-get="{% url 'publishers:contact-add-form' publisher_pk=publisher.pk %}"
            hx-target="#contact-form-container"
            hx-swap="innerHTML">
        <i class="bi bi-plus-lg me-1"></i>Dodaj kontakt osobu
    </button>
    ```

- [ ] **Task 16: Kreirati HTMX partial `_note_item.html`**
  - File: `doi_portal/templates/publishers/partials/_note_item.html`
  - Action: Kreirati partial za prikaz jedne napomene:
    ```html
    <div class="card mb-2" id="note-{{ note.pk }}">
        <div class="card-body py-2">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <strong>{{ note.author.get_full_name|default:note.author.username }}</strong>
                    <span class="text-muted small ms-2">
                        {{ note.created_at|date:"d.m.Y. H:i" }}
                        {% if note.is_edited %}
                        <em>(izmenjeno {{ note.updated_at|date:"d.m.Y. H:i" }})</em>
                        {% endif %}
                    </span>
                </div>
                <div class="d-flex gap-1">
                    <button type="button" class="btn btn-sm btn-outline-primary"
                            hx-get="{% url 'publishers:note-edit-form' pk=note.pk %}"
                            hx-target="#note-{{ note.pk }}"
                            hx-swap="outerHTML">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <form method="post" class="d-inline"
                          hx-post="{% url 'publishers:note-delete' pk=note.pk %}"
                          hx-target="#notes-section"
                          hx-swap="innerHTML"
                          hx-confirm="Obrisati napomenu?">
                        {% csrf_token %}
                        <button type="submit" class="btn btn-sm btn-outline-danger">
                            <i class="bi bi-trash"></i>
                        </button>
                    </form>
                </div>
            </div>
            <p class="mb-0 mt-1">{{ note.text|linebreaksbr }}</p>
        </div>
    </div>
    ```
  - Notes: Koristi `note.is_edited` umesto poređenja datuma (F5 fix). Delete dugme umotano u `<form>` sa CSRF tokenom (F6 fix).

- [ ] **Task 17: Kreirati HTMX partial `_note_form.html`**
  - File: `doi_portal/templates/publishers/partials/_note_form.html`
  - Action: Kreirati partial za edit napomene (inline zamena):
    ```html
    <div class="card mb-2 border-primary" id="note-{{ note.pk }}">
        <div class="card-body py-2">
            <form method="post"
                  hx-post="{% url 'publishers:note-update' pk=note.pk %}"
                  hx-target="#notes-section"
                  hx-swap="innerHTML">
                {% csrf_token %}
                <div class="mb-2">
                    {{ form.text }}
                    {% if form.text.errors %}
                    <div class="invalid-feedback d-block">{{ form.text.errors.0 }}</div>
                    {% endif %}
                </div>
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-sm btn-primary">
                        <i class="bi bi-check-lg me-1"></i>Sačuvaj
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary"
                            hx-get="{% url 'publishers:note-list' publisher_pk=publisher.pk %}"
                            hx-target="#notes-section"
                            hx-swap="innerHTML">
                        Otkaži
                    </button>
                </div>
            </form>
        </div>
    </div>
    ```

- [ ] **Task 18: Kreirati HTMX partial `_note_list.html`**
  - File: `doi_portal/templates/publishers/partials/_note_list.html`
  - Action: Kreirati wrapper sa uvek-vidljivom formom za dodavanje:
    ```html
    <form method="post"
          hx-post="{% url 'publishers:note-add' publisher_pk=publisher.pk %}"
          hx-target="#notes-section"
          hx-swap="innerHTML"
          class="mb-3">
        {% csrf_token %}
        <div class="mb-2">
            {{ note_form.text }}
        </div>
        <button type="submit" class="btn btn-sm btn-primary">
            <i class="bi bi-plus-lg me-1"></i>Dodaj napomenu
        </button>
    </form>

    {% for note in notes %}
        {% include "publishers/partials/_note_item.html" with note=note %}
    {% empty %}
        <p class="text-muted">Nema napomena za ovog izdavača.</p>
    {% endfor %}
    ```
  - Notes: `note_form` se prosleđuje iz svakog view-a koji renderuje ovaj template (F4 fix). Nema `{% load publishers_tags %}` (F3 fix).

- [ ] **Task 19: Kreirati password partial template-e**
  - File: `doi_portal/templates/publishers/partials/_crossref_password_masked.html`
  - Action:
    ```html
    <code>••••••••</code>
    <form method="post" class="d-inline"
          hx-post="{% url 'publishers:reveal-crossref-password' pk=publisher.pk %}"
          hx-target="#crossref-password-cell"
          hx-swap="innerHTML">
        {% csrf_token %}
        <button type="submit" class="btn btn-sm btn-outline-secondary ms-2">
            <i class="bi bi-eye"></i> Prikaži
        </button>
    </form>
    ```
  - File: `doi_portal/templates/publishers/partials/_crossref_password_revealed.html`
  - Action:
    ```html
    <code>{{ password }}</code>
    <form method="post" class="d-inline"
          hx-post="{% url 'publishers:hide-crossref-password' pk=publisher.pk %}"
          hx-target="#crossref-password-cell"
          hx-swap="innerHTML">
        {% csrf_token %}
        <button type="submit" class="btn btn-sm btn-outline-secondary ms-2">
            <i class="bi bi-eye-slash"></i> Sakrij
        </button>
    </form>
    ```

- [ ] **Task 20: Ažurirati `publisher_form.html` - dodati Crossref sekciju i kontakte**
  - File: `doi_portal/templates/publishers/publisher_form.html`
  - Action: Posle sekcije "Kontakt informacije" (posle `</div>` za website, pre `<div class="d-flex justify-content-between mt-4">`), dodati:
    ```html
    <hr>
    <h6 class="mb-3">Crossref kredencijali</h6>
    <div class="row">
        <div class="col-md-6 mb-3">
            <label for="id_crossref_username" class="form-label">Korisničko ime</label>
            {{ form.crossref_username }}
            {% if form.crossref_username.errors %}
            <div class="invalid-feedback d-block">{{ form.crossref_username.errors.0 }}</div>
            {% endif %}
        </div>
        <div class="col-md-6 mb-3">
            <label for="id_crossref_password" class="form-label">Lozinka</label>
            {{ form.crossref_password }}
            <div class="form-text">Ostavite prazno ako ne želite da menjate lozinku.</div>
            {% if form.crossref_password.errors %}
            <div class="invalid-feedback d-block">{{ form.crossref_password.errors.0 }}</div>
            {% endif %}
        </div>
    </div>

    {% if form.instance.pk %}
    <hr>
    <h6 class="mb-3">Kontakt osobe (interne)</h6>
    <div id="contacts-section"
         hx-get="{% url 'publishers:contact-list' publisher_pk=form.instance.pk %}"
         hx-trigger="load"
         hx-swap="innerHTML">
        <div class="text-center py-3">
            <div class="spinner-border spinner-border-sm" role="status"></div>
        </div>
    </div>
    {% endif %}
    ```
  - Notes: Password polje je uvek prazno (ne šalje se dekriptovani password u HTML - F7 fix). Kontakti samo pri edit-u (ne pri kreiranju jer nema PK).

- [ ] **Task 21: Ažurirati `publisher_detail.html` - dodati Crossref, kontakte i napomene**
  - File: `doi_portal/templates/publishers/publisher_detail.html`
  - Action: Posle kartice "Kontakt informacije" a pre kartice "Sistemske informacije", dodati:
    ```html
    {% if publisher.crossref_username or publisher.crossref_password %}
    <div class="card mb-4">
        <div class="card-header">
            <h5 class="card-title mb-0">Crossref kredencijali</h5>
        </div>
        <div class="card-body">
            <dl class="row mb-0">
                {% if publisher.crossref_username %}
                <dt class="col-sm-4">Korisničko ime</dt>
                <dd class="col-sm-8"><code>{{ publisher.crossref_username }}</code></dd>
                {% endif %}

                {% if publisher.crossref_password %}
                <dt class="col-sm-4">Lozinka</dt>
                <dd class="col-sm-8" id="crossref-password-cell">
                    {% include "publishers/partials/_crossref_password_masked.html" %}
                </dd>
                {% endif %}
            </dl>
        </div>
    </div>
    {% endif %}

    <div class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="card-title mb-0">Kontakt osobe (interne)</h5>
        </div>
        <div class="card-body">
            <div id="contacts-section"
                 hx-get="{% url 'publishers:contact-list' publisher_pk=publisher.pk %}"
                 hx-trigger="load"
                 hx-swap="innerHTML">
                <div class="text-center py-3">
                    <div class="spinner-border spinner-border-sm" role="status"></div>
                </div>
            </div>
        </div>
    </div>

    <div class="card mb-4">
        <div class="card-header">
            <h5 class="card-title mb-0">Napomene</h5>
        </div>
        <div class="card-body">
            <div id="notes-section"
                 hx-get="{% url 'publishers:note-list' publisher_pk=publisher.pk %}"
                 hx-trigger="load"
                 hx-swap="innerHTML">
                <div class="text-center py-3">
                    <div class="spinner-border spinner-border-sm" role="status"></div>
                </div>
            </div>
        </div>
    </div>
    ```
  - Notes: Password se NE šalje u HTML (F8 fix). Koristi se `_crossref_password_masked.html` partial sa HTMX reveal endpoint-om.

- [ ] **Task 22: Ažurirati Django admin**
  - File: `doi_portal/publishers/admin.py`
  - Action: Dodati `TabularInline` za PublisherContact i PublisherNote, ažurirati fieldsets:
    ```python
    from .models import Publisher, PublisherContact, PublisherNote

    class PublisherContactInline(admin.TabularInline):
        model = PublisherContact
        extra = 0
        fields = ["first_name", "last_name", "email", "phone", "role", "order"]

    class PublisherNoteInline(admin.TabularInline):
        model = PublisherNote
        extra = 0
        fields = ["text", "author", "created_at"]
        readonly_fields = ["author", "created_at"]

    @admin.register(Publisher)
    class PublisherAdmin(admin.ModelAdmin):
        # ... postojeće ...
        inlines = [PublisherContactInline, PublisherNoteInline]
        fieldsets = [
            # ... postojeće Basic Info, Kontakt, DOI fieldsets ...
            ("Crossref", {
                "fields": ["crossref_username", "crossref_password"],
                "classes": ["collapse"]
            }),
            # ... Status, Datumi ...
        ]
    ```

- [ ] **Task 23: Registrovati nove modele sa auditlog-om**
  - File: `doi_portal/publishers/apps.py`
  - Action: Ažurirati `ready()`:
    ```python
    def ready(self):
        try:
            from auditlog.registry import auditlog
            from .models import Publisher, PublisherContact, PublisherNote
            auditlog.register(Publisher)
            auditlog.register(PublisherContact)
            auditlog.register(PublisherNote)
        except ImportError:
            pass
    ```

- [ ] **Task 24: Napisati testove za modele**
  - File: `doi_portal/publishers/tests/test_models.py`
  - Action: Dodati test klase:
    - `TestPublisherContact`: kreiranje, soft delete, restore, ordering, `__str__`
    - `TestPublisherNote`: kreiranje, hard delete, ordering `-created_at`, `__str__`, author SET_NULL, `is_edited` default False
    - `TestPublisherCrossrefFields`: kreiranje sa crossref_username/password, blank dozvoljeno
    - `TestEncryptedCharField`: vrednost u bazi != plain text, dekriptovanje vraća original, prazan string se ne enkriptuje

- [ ] **Task 25: Napisati testove za forme**
  - File: `doi_portal/publishers/tests/test_forms.py`
  - Action: Dodati test klase:
    - `TestPublisherContactForm`: validacija required (first_name, last_name), email format, widget klase
    - `TestPublisherNoteForm`: validacija required (text), widget klase
    - `TestPublisherFormCrossref`: crossref polja u formi, password polje prazno, save() logika (prazan password ne menja postojeći)

- [ ] **Task 26: Napisati testove za view-ove**
  - File: `doi_portal/publishers/tests/test_views.py`
  - Action: Dodati test klase:
    - `TestContactViews`: FBV CRUD operacije, permission check (403 za neadmin), HTMX partial response
    - `TestNoteViews`: FBV CRUD, author automatski setovan, `is_edited` True na update, permission check
    - `TestRevealPasswordView`: reveal/hide endpoint, permission check, response sadrži password
    - Koristiti fixture-e: `admin_user`, `publisher`, `superadmin_user`

### Acceptance Criteria

- [ ] AC 1: Given admin korisnik je na publisher edit stranici, when vidi formu, then postoji sekcija "Crossref kredencijali" sa poljima za username i password, i password polje je uvek prazno (ne prikazuje dekriptovanu vrednost).

- [ ] AC 2: Given admin korisnik je na publisher edit stranici, when unese crossref kredencijale i sačuva, then username i password su sačuvani u bazi (password enkriptovano). When ponovo otvori formu, username je popunjen ali password polje je prazno sa placeholder tekstom "Ostavite prazno ako ne želite da menjate lozinku".

- [ ] AC 3: Given admin korisnik je na publisher edit stranici, when ostavi password polje prazno i sačuva, then postojeći password se NE menja.

- [ ] AC 4: Given admin korisnik je na publisher edit stranici, when klikne "Dodaj kontakt osobu", then se prikaže HTMX forma za unos kontakt osobe (ime*, prezime*, email, telefon, funkcija) bez refresha stranice.

- [ ] AC 5: Given admin korisnik je popunio kontakt formu, when klikne "Sačuvaj", then kontakt osoba se sačuva i prikaže u listi kontakata bez refresha.

- [ ] AC 6: Given admin korisnik vidi kontakt osobu u listi, when klikne Edit, then se prikaže forma sa popunjenim podacima. When klikne Delete i potvrdi, then kontakt osoba se soft-delete-uje i nestaje iz liste bez refresha.

- [ ] AC 7: Given admin korisnik je na publisher detail stranici, when vidi sekciju "Napomene", then postoji tekst polje za unos nove napomene i dugme "Dodaj napomenu".

- [ ] AC 8: Given admin korisnik je uneo tekst napomene, when klikne "Dodaj napomenu", then napomena se sačuva sa autorom (trenutno ulogovan korisnik) i datumom, i prikaže u listi bez refresha.

- [ ] AC 9: Given napomena postoji u listi, when je korisnik pregleda, then vidi ime autora, datum kreiranja, i tekst. Ako je napomena editovana, prikazuje se "(izmenjeno DD.MM.YYYY. HH:MM)" tekst.

- [ ] AC 10: Given admin korisnik vidi napomenu, when klikne Edit, then može izmeniti tekst i sačuvati (napomena se označi kao editovana). When klikne Delete i potvrdi, then se napomena trajno briše.

- [ ] AC 11: Given korisnik pristupa public stranici izdavača (`/publishers/<slug>/`), when pregleda stranicu, then NE VIDI Crossref kredencijale, interne kontakt osobe, niti napomene. Postojeći public kontakt podaci (email, telefon, website) se i dalje prikazuju.

- [ ] AC 12: Given neautorizovan korisnik (Urednik, Bibliotekar, anoniman), when pokuša pristupiti HTMX endpointima za kontakte/napomene/reveal-password, then dobija 403 Forbidden.

- [ ] AC 13: Given crossref_password je sačuvan u bazi, when se direktno pogleda u bazi, then vrednost je enkriptovana (nije plain text).

- [ ] AC 14: Given admin korisnik je na publisher detail stranici, when vidi Crossref lozinku, then je prikazana kao `••••••••`. When klikne "Prikaži", then HTMX POST dohvati i prikaže dekriptovanu lozinku. When klikne "Sakrij", then se vrati na masked prikaz.

## Additional Context

### Dependencies

- **Nema novih third-party dependency-ja** - Koristimo `cryptography` biblioteku koja je već prisutna kao transitivna zavisnost (`argon2-cffi` → `cryptography`). Custom `EncryptedCharField` je ~30 linija koda u `publishers/fields.py`.

### Testing Strategy

**Unit testovi (pytest):**
- Model testovi: kreiranje, validacija, soft/hard delete, ordering, `__str__`, `is_edited` flag
- Field testovi: EncryptedCharField enkriptovanje/dekriptovanje, prazan string, None handling
- Form testovi: required polja, widget klase, password save logika (prazan ne menja postojeći)
- View testovi: FBV CRUD operacije, HTMX partial rendering, permission check (403), reveal/hide password

**Manual testing:**
1. Kreirati izdavača, dodati Crossref kredencijale - proveriti da password polje ostaje prazno
2. Editovati izdavača, ostaviti password prazno - proveriti da se postojeći ne menja
3. Na detail stranici kliknuti "Prikaži" za password - proveriti HTMX reveal
4. Dodati 3 kontakt osobe - proveriti HTMX add/edit/delete bez refresha
5. Dodati 3 napomene sa različitim korisnicima - proveriti comment thread prikaz i `is_edited` flag
6. Editovati napomenu - proveriti da se prikaže "(izmenjeno...)" tekst
7. Otvoriti public stranicu izdavača - proveriti da nema internih podataka
8. Proveriti bazu direktno da je crossref_password enkriptovan
9. Pokušati pristup HTMX endpointima sa Urednik korisnikom - proveriti 403

### Notes

- **Buduće proširenje:** Crossref kredencijali se mogu koristiti u Crossref API integraciji za automatsku DOI registraciju. Password se dekriptuje automatski pri čitanju sa custom `EncryptedCharField`.

- **Buduće proširenje:** Kontakt osobe mogu dobiti drag-drop reordering (SortableJS + HTMX) jer `order` polje već postoji na modelu.

- **Dizajn odluka:** Svi admini (Administrator/Superadmin) mogu moderisati napomene svih korisnika. Ovo je svesna odluka jer je portal interni alat sa malim brojem admin korisnika i moderisanje je poželjno.

- **VAŽNO:** Portal/public templates (`templates/portal/`) se NE DIRAJU. Svi novi podaci su isključivo u dashboard templates (`templates/publishers/`).
