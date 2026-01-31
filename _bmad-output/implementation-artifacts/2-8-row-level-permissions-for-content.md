# Story 2.8: Row-Level Permissions for Content

Status: done

## Story

As a **system**,
I want **to enforce row-level permissions based on publisher assignment across all content hierarchy views**,
So that **Urednici and Bibliotekari can only manage content from their assigned publishers, while Administrators retain full access**.

## Background

Epik 2 implementirao je kompletnu hijerarhiju sadrzaja: Publisher (Story 2.1) -> Publication (Story 2.3/2.4) -> Issue (Story 2.6). Row-level permissions vec postoje parcijalno - `PublisherScopedMixin` i `PublisherScopedEditMixin` u `publishers/mixins.py` koriste se u Publication views (Story 2.4) i Issue views (Story 2.6). Takodje, `PublisherPermissionMixin` postoji u `core/permissions.py`. Guardian permissions se dodeljuju pri kreiranju/azuriranju korisnika (Story 1.6 - `users/services.py`).

Ova prica KONSOLIDUJE i PROSIRUJE postojece permission mehanizme da obezbedi:
1. Sistematsko testiranje svih permission granica (URL direct access, queryset filtering)
2. Guardian ObjectPermission integraciju sa User publisher assignment signalima
3. Automatsku sinhronizaciju guardian permissions pri promeni publisher-a
4. Centralni permission servis u `core/permissions.py` za buducu upotrebu u Epic 3 (Articles)
5. End-to-end testiranje svih admin views sa razlicitim ulogama

**FR Pokrivenost:**
- FR8-FR12 (Publisher access rules - vec implementirano, ovde se testira)
- FR13-FR17 (Publication row-level filtering - vec implementirano u Story 2.4)
- FR18-FR21 (Issue row-level filtering - vec implementirano u Story 2.6)

**Napomena:** Ova prica ne kreira nove modele. Fokus je na konsolidaciji, prosirenju i robusnom testiranju permission sistema pre prelaska na Epic 3 (Article Workflow) koji ce intenzivno zavisiti od ovih mehanizama.

## Acceptance Criteria

1. **Given** korisnik sa ulogom Urednik ili Bibliotekar
   **When** mu se dodeli Publisher putem User modela (user.publisher FK)
   **Then** django-guardian object permission se automatski dodeljuje
   **And** `assign_publisher_permissions()` se poziva sa ispravnim permissijama

2. **Given** Urednik sa publisher dodelom
   **When** upituje (query) publikacije
   **Then** queryset je filtriran da prikazuje SAMO publikacije tog izdavaca
   **And** filter se primenjuje na nivou view/mixin-a (`get_scoped_queryset()`)

3. **Given** Urednik pokusava da pristupi publikaciji drugog izdavaca
   **When** koristi direktan URL (npr. `/publications/{slug}/edit/`)
   **Then** vraca se 403 Forbidden ili 404 Not Found (zavisno od view implementacije)
   **And** pristup je blokiran na nivou `test_func()` u mixin-u (403) ili `get_scoped_queryset()` filtriranja (404)
   **Note:** Postojece UpdateView/DetailView koriste `get_scoped_queryset()` koji filtrira queryset, pa ce Django vratiti 404 umesto 403 za objekte van scope-a. Ovo je prihvatljiv security pattern jer ne otkriva postojanje resursa.

4. **Given** korisnik sa ulogom Administrator
   **When** pristupa bilo kom sadrzaju
   **Then** NEMA row-level filtriranja (pun pristup svim izdavacima)

5. **Given** promeni se publisher dodela korisnika (user.publisher)
   **When** se sacuva promena
   **Then** django-guardian permissions se azuriraju u skladu sa promenom
   **And** stare permissions se uklanjaju, nove se dodeljuju
   **And** promena se belezi u audit log-u

6. **Given** Urednik sa publisher dodelom
   **When** upituje izdanja (issues)
   **Then** queryset je filtriran preko `publication__publisher` relacije
   **And** vide se SAMO izdanja publikacija tog izdavaca

7. **Given** Bibliotekar sa publisher dodelom
   **When** pokusava da edituje publikaciju ili izdanje
   **Then** vraca se 403 Forbidden
   **And** `PublisherScopedEditMixin` blokira pristup

8. **Given** korisnik bez publisher dodele (Urednik bez publisher FK)
   **When** pokusava da pristupi sadrzaju
   **Then** vraca se 403 Forbidden
   **And** queryset vraca prazan set

## Tasks / Subtasks

- [x] Task 1: Prosiriti `core/permissions.py` sa centralizovanim permission helperima (AC: #1, #4, #5)
  - [x] 1.1 Dodati `get_user_publishers()` helper koji vraca Publisher queryset za korisnika (za buducu upotrebu sa M2M)
  - [x] 1.2 Dodati `has_publisher_access(user, publisher)` helper za proveru pristupa korisnika izdavacu
  - [x] 1.3 Dodati `sync_guardian_permissions(user, old_publisher, new_publisher)` servis za sinhronizaciju
  - [x] 1.4 Refaktorisati `PublisherPermissionMixin` da koristi nove helpere (backward compatible)

- [x] Task 2: Dodati signal-based permission sync u postojeci `users/signals.py` (AC: #1, #5)
  - [x] 2.1 Dodati `pre_save` i `post_save` signal handlere na User model u **postojeci** `users/signals.py` (fajl vec postoji sa password signalima iz Story 1.5)
  - [x] 2.2 Signal handler treba da detektuje promenu publisher-a koristeci `pre_save` za staru vrednost (`_old_publisher` pattern)
  - [x] 2.3 **NIJE POTREBNO** registrovati signal u `users/apps.py` - `ready()` metoda VEC importuje `doi_portal.users.signals` (potvrdjeno u kodu)
  - [x] 2.4 Obezbediti da postojeci `UserUpdateForm.save()` i signal ne dupliraju permission assignment (guardian `assign_perm` je vec idempotantan)

- [x] Task 3: Verifikovati i ucvrstiti Publisher admin views permissions (AC: #3, #4)
  - [x] 3.1 Verifikovati da `PublisherListView` koristi `AdministratorRequiredMixin` (vec implementirano - samo test)
  - [x] 3.2 Verifikovati da Publisher CRUD ostaje Admin-only (Urednik/Bibliotekar NE smeju pristupiti)
  - [x] 3.3 Napisati end-to-end testove za svaku ulogu na svaki Publisher view endpoint

- [x] Task 4: Verifikovati i ucvrstiti Publication admin views permissions (AC: #2, #3, #4, #7)
  - [x] 4.1 Verifikovati `PublicationListView` sa `PublisherScopedMixin` (vec implementirano - test)
  - [x] 4.2 Verifikovati `PublicationUpdateView` sa `PublisherScopedEditMixin` (vec - test)
  - [x] 4.3 Verifikovati `PublicationCreateView` sa `AdministratorRequiredMixin` (vec - test)
  - [x] 4.4 Verifikovati `PublicationDeleteView` sa `AdministratorRequiredMixin` (vec - test)
  - [x] 4.5 Test: Urednik vidi SAMO svoje publikacije u listi
  - [x] 4.6 Test: Urednik NE moze da pristupi publikaciji drugog izdavaca putem direktnog URL-a
  - [x] 4.7 Test: Bibliotekar NE moze da edituje (403 na update view)
  - [x] 4.8 Test: Administrator vidi SVE publikacije

- [x] Task 5: Verifikovati i ucvrstiti Issue admin views permissions (AC: #6, #3, #7)
  - [x] 5.1 Verifikovati `IssueListView` sa `PublisherScopedMixin` i custom `get_scoped_queryset()` (vec - test)
  - [x] 5.2 Verifikovati `IssueCreateView` - Urednik moze kreirati SAMO za svoje publikacije
  - [x] 5.3 Verifikovati `IssueUpdateView` - Urednik moze editovati SAMO svoje izdanja
  - [x] 5.4 Verifikovati `IssueDeleteView` sa `AdministratorRequiredMixin` (vec - test)
  - [x] 5.5 Test: Urednik vidi SAMO izdanja svojih publikacija
  - [x] 5.6 Test: Urednik NE moze pristupiti izdanju drugog izdavaca
  - [x] 5.7 Test: Bibliotekar NE moze kreirati/editovati izdanja (403)
  - [x] 5.8 Test: Administrator vidi SVA izdanja

- [x] Task 6: Napisati end-to-end permission integration testove (AC: #1-#8)
  - [x] 6.1 Test klasa: `TestRowLevelPermissionsPublications` - svi AC scenariji za publications
  - [x] 6.2 Test klasa: `TestRowLevelPermissionsIssues` - svi AC scenariji za issues
  - [x] 6.3 Test klasa: `TestGuardianPermissionSync` - signal/service permission sync
  - [x] 6.4 Test klasa: `TestPublisherAssignmentChange` - promena publisher-a azurira permissions
  - [x] 6.5 Test: Korisnik bez publisher dodele dobija prazan queryset
  - [x] 6.6 Test: Korisnik bez uloge (ni u jednoj grupi) dobija 403
  - [x] 6.7 Test: Superuser (is_superuser=True) ima pun pristup bez obzira na grupe

- [x] Task 7: Azurirati sprint-status.yaml (AC: N/A)
  - [x] 7.1 Promeniti status `2-8-row-level-permissions-for-content` na `review`

## Dev Notes

### CRITICAL: Ovo je KONSOLIDACIONA prica - NE KREIRAJ nove modele

Veci deo permission mehanizma VEC POSTOJI i radi. Ova prica:
1. **PROSIRUJE** `core/permissions.py` sa korisnim helperima
2. **DODAJE** signal-based automatsku sinhronizaciju guardian permissions
3. **PIŠE** robusne end-to-end testove za SVE permission granice
4. **PRIPREMA** permission infrastrukturu za Epic 3 (Articles)

### Postojeci permission mehanizmi (NE ponavljaj ih)

**`publishers/mixins.py`** (vec postoji, koristi se):
- `PublisherScopedMixin` - Filtrira queryset po publisher za Urednik/Bibliotekar
- `PublisherScopedEditMixin` - Blokira edit za Bibliotekar, dozvoljava Uredniku
- `AdministratorRequiredMixin` - Samo Admin/Superadmin

**`core/permissions.py`** (vec postoji):
- `PublisherPermissionMixin` - Starija verzija, koristi `UserPassesTestMixin`
- `role_required` decorator - Za FBV, provera grupnog clanstva

**`users/services.py`** (vec postoji):
- `assign_publisher_permissions(user, publisher)` - Dodeljuje guardian `view_publisher`, `change_publisher`
- `remove_publisher_permissions(user, publisher)` - Uklanja guardian permissions

**`users/forms.py`** (vec postoji):
- `UserCreateForm.save()` - Poziva `assign_publisher_permissions` pri kreiranju korisnika
- `UserUpdateForm.save()` - Detektuje promenu publisher-a i azurira permissions

### Fajlovi za modifikaciju

- `doi_portal/doi_portal/core/permissions.py` - Dodati `get_user_publishers()`, `has_publisher_access()`, `sync_guardian_permissions()`
- `doi_portal/doi_portal/users/signals.py` - Dodati `pre_save`/`post_save` signal handlere za publisher permission sync (fajl VEC POSTOJI sa password signalima)
- `doi_portal/doi_portal/users/apps.py` - **NEMA PROMENA** (`ready()` vec importuje signals modul)
- `doi_portal/doi_portal/core/tests/test_permissions.py` - Prosiriti sa novim testovima

### Novi fajlovi za kreiranje

- `doi_portal/doi_portal/core/tests/test_row_level_permissions.py` - End-to-end integration testovi

### Permission Model Design

```
User (users/models.py)
  |-- publisher (FK -> Publisher)  # Already exists
  |-- groups (M2M -> Group)        # Django auth - Already exists

Publisher (publishers/models.py)
  |-- Guardian ObjectPermissions: view_publisher, change_publisher

Permission Flow:
  1. Superadmin kreira korisnika sa publisher FK + role Group
  2. UserCreateForm.save() -> assign_publisher_permissions()
  3. Signal post_save na User -> sync_guardian_permissions() (NOVO - dodaje se u postojeci users/signals.py)
  4. View mixin (PublisherScopedMixin) -> test_func() + get_scoped_queryset()
  5. Queryset filter: publication.publisher == user.publisher (ili publication__publisher za Issue)
  NAPOMENA: apps.py VEC importuje signals modul - NEMA dodatne konfiguracije
```

### Guardian Permission Pattern

```python
# Dodeljene permissions (vec implementirano u users/services.py):
assign_perm("publishers.view_publisher", user, publisher)
assign_perm("publishers.change_publisher", user, publisher)

# View koriscenje (vec implementirano u publishers/mixins.py):
# PublisherScopedMixin NE koristi guardian za queryset filtering!
# Koristi user.publisher FK direktno:
queryset.filter(publisher=user.publisher)  # Za Publication
queryset.filter(publication__publisher=user.publisher)  # Za Issue

# Guardian se koristi samo za object-level permission check (buduci use case)
# Trenutno, FK-based filtering je primarni mehanizam
```

### Signal Handler Design (PROSIRENJE - Task 2)

```python
# users/signals.py (VEC POSTOJI - dodati nove signale uz postojece password signale)
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from doi_portal.users.models import User

@receiver(pre_save, sender=User)
def capture_old_publisher(sender, instance, **kwargs):
    """Capture old publisher before save for permission sync."""
    if instance.pk:
        try:
            old_user = User.objects.get(pk=instance.pk)
            instance._old_publisher = old_user.publisher
        except User.DoesNotExist:
            instance._old_publisher = None
    else:
        instance._old_publisher = None

@receiver(post_save, sender=User)
def sync_publisher_permissions(sender, instance, created, **kwargs):
    """Auto-sync guardian permissions when publisher changes."""
    old_publisher = getattr(instance, '_old_publisher', None)
    new_publisher = instance.publisher

    if old_publisher != new_publisher:
        if old_publisher:
            remove_publisher_permissions(instance, old_publisher)
        if new_publisher:
            assign_publisher_permissions(instance, new_publisher)
```

**VAZNO:** Signal handler mora biti idempotantan - `UserUpdateForm.save()` VEC radi permission sync. Signal sluzi kao safety net za direktne ORM promene (npr. admin shell, bulk update).

### Centralni Permission Helpers (NOVO - Task 1)

```python
# core/permissions.py - DODATI

def get_user_publishers(user):
    """
    Return publishers accessible to user.

    Superuser/Admin/Superadmin: all publishers
    Urednik/Bibliotekar: only assigned publisher
    Future: support M2M for multiple publishers
    """
    if user.is_superuser:
        return Publisher.objects.all()
    if user.groups.filter(name__in=["Superadmin", "Administrator"]).exists():
        return Publisher.objects.all()
    if user.publisher:
        return Publisher.objects.filter(pk=user.publisher_id)
    return Publisher.objects.none()

def has_publisher_access(user, publisher):
    """Check if user has access to specific publisher."""
    if user.is_superuser:
        return True
    if user.groups.filter(name__in=["Superadmin", "Administrator"]).exists():
        return True
    return user.publisher_id == publisher.pk if user.publisher else False
```

### Issue Queryset Scoping Pattern (vec implementirano)

Issue nema direktan publisher FK. Scoping ide preko `publication__publisher`:

```python
# issues/views.py - VEC POSTOJI u svim Issue views:
def get_scoped_queryset(self, queryset):
    flags = self._get_user_role_flags()
    if flags["is_admin"]:
        return queryset
    if flags["has_publisher"]:
        return queryset.filter(
            publication__publisher=self.request.user.publisher
        )
    return queryset.none()
```

### IssueForm Publication Scoping (vec implementirano)

```python
# issues/forms.py - VEC POSTOJI (pojednostavljen prikaz):
class IssueForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            if user.is_superuser or user.groups.filter(
                name__in=["Administrator", "Superadmin"]
            ).exists():
                queryset = Publication.objects.select_related("publisher")
            elif hasattr(user, "publisher") and user.publisher:
                queryset = Publication.objects.filter(
                    publisher=user.publisher
                ).select_related("publisher")
            else:
                queryset = Publication.objects.none()
            self.fields["publication"].queryset = queryset
```

### Testing Strategy

Koristiti `pytest-django` sa factory pattern-ima. Sve factory klase vec postoje:
- `UserFactory` - `users/tests/factories.py`
- `PublisherFactory` - `publications/tests/factories.py` (takodje re-exportovan iz `issues/tests/factories.py`)
- `PublicationFactory` - `publications/tests/factories.py`
- `IssueFactory` - `issues/tests/factories.py`

```python
# core/tests/test_row_level_permissions.py

@pytest.fixture
def two_publishers(db):
    """Kreirati dva izdavaca za testiranje izolacije."""
    pub_a = PublisherFactory(name="Publisher A", doi_prefix="10.1111")
    pub_b = PublisherFactory(name="Publisher B", doi_prefix="10.2222")
    return pub_a, pub_b

@pytest.fixture
def urednik_a(two_publishers):
    """Urednik dodeljen Publisher A."""
    user = UserFactory()
    user.publisher = two_publishers[0]
    user.save()
    Group.objects.get(name="Urednik").user_set.add(user)
    return user

@pytest.fixture
def publication_a(two_publishers):
    """Publikacija Publisher A."""
    return PublicationFactory(publisher=two_publishers[0])

@pytest.fixture
def publication_b(two_publishers):
    """Publikacija Publisher B."""
    return PublicationFactory(publisher=two_publishers[1])
```

**Test scenariji:**
1. Urednik A vidi publication_a, NE vidi publication_b
2. Urednik A pristupi publication_b direktno -> 404 (queryset scoping) ili 403
3. Urednik A vidi issue od publication_a, NE vidi issue od publication_b
4. Administrator vidi SVE (publication_a + publication_b)
5. Bibliotekar NE moze editovati -> 403
6. Korisnik bez publisher-a -> prazan queryset / 403
7. Promena publisher-a -> permissions se azuriraju

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

Svi UI tekstovi i poruke MORAJU koristiti ispravne srpske dijakritike: `c` -> `č`, `c` -> `ć`, `s` -> `š`, `dj` -> `đ`, `z` -> `ž`.

| Kontekst | ISPRAVNO |
|----------|----------|
| Permission denied poruka | "Nemate dozvolu za pristup ovoj stranici." |
| Publisher label | "Izdavač" |
| Publication label | "Publikacija" |
| Urednik role | "Urednik" |
| Bibliotekar role | "Bibliotekar" |

### Anti-Patterns to Avoid

```python
# POGRESNO - Kreirati novi permission mixin umesto prosirenja postojeceg
class MyNewPermissionMixin:  # NE! Koristi PublisherScopedMixin

# POGRESNO - Hardkodovati publisher ID u queryset
queryset.filter(publisher_id=1)  # NE! Koristi user.publisher

# POGRESNO - Zaboraviti publication__publisher za Issue
queryset.filter(publisher=user.publisher)  # NE za Issue model!
queryset.filter(publication__publisher=user.publisher)  # ISPRAVNO za Issue

# POGRESNO - Duplo dodeljvanje permissions (form + signal)
# Signal MORA biti idempotantan - koristiti assign_perm (guardian vec handluje duplikate)

# POGRESNO - Testirati permissions samo sa jednim izdavacem
# OBAVEZNO koristiti DVA izdavaca za proveru izolacije

# POGRESNO - Ne testirati direct URL access
# OBAVEZNO testirati i queryset filtering I direct URL (403)
```

### Git Commit Pattern

```
story-2-8: feat(permissions): konsoliduj row-level permissions sa guardian sync i end-to-end testovima (Story 2.8)
```

### Dependencies

**Zavisi od:**
- Story 1.2 (Custom User Model & RBAC Setup) - DONE
- Story 1.6 (User Management by Superadmin - guardian integration) - DONE
- Story 2.1 (Publisher Model) - DONE
- Story 2.4 (Publication Admin List - PublisherScopedMixin) - DONE
- Story 2.6 (Issue Model & Admin CRUD - issue permissions) - DONE

**Blokira:**
- Story 3.1 (Article Model) - ce koristiti iste permission mehanizme
- Story 3.5 (Submit Article for Review) - workflow permissions
- Story 3.6 (Editorial Review Process) - Urednik-scoped review

### Previous Story Learnings (Story 2.6, 2.7)

1. **`get_scoped_queryset()` override za Issue** - Issue nema direktan publisher FK, mora se filtrirati preko `publication__publisher`. Ovaj pattern je ustanovljen u Story 2.6 i ponovljen u svim Issue views.
2. **Role flags caching** - `_get_user_role_flags()` u `PublisherScopedMixin` kesira role flags na view instanci da izbegne ponavljane DB upite. Ovo je dobar pattern - prosiriti ga.
3. **SoftDeleteManager** - Automatski iskljucuje `is_deleted=True` zapise, ne treba eksplicitan filter.
4. **Test factories** - Koristiti `UserFactory`, `PublicationFactory`, `IssueFactory` za konzistentne testove.
5. **HTMX** nije relevantan za ovu pricu (permissions, ne UI).
6. **Guardian je instaliran** ali se trenutno koristi minimalno - samo `view_publisher` i `change_publisher` na Publisher objektu.
7. **`PublisherScopedMixin`** radi filtriranje po `user.publisher` FK, NE po guardian permissions. Guardian sluzi kao dodatni sloj sigurnosti.

### NFR Requirements Addressed

- **NFR7:** HTTPS + proper session management (vec implementirano)
- **NFR12:** Audit log - SVE admin akcije se beleze (django-auditlog vec registrovan za Publisher, Publication, Issue)
- **NFR13:** GDPR - Row-level access osigurava da korisnici ne vide podatke kojima nemaju pristup

### Project Structure Notes

- Svi permission mixini: `doi_portal/doi_portal/publishers/mixins.py` (PublisherScopedMixin, AdministratorRequiredMixin)
- Centralni permission helpers: `doi_portal/doi_portal/core/permissions.py`
- Guardian permission services: `doi_portal/doi_portal/users/services.py`
- User model sa publisher FK: `doi_portal/doi_portal/users/models.py`
- Publication views (vec koriste mixins): `doi_portal/doi_portal/publications/views.py`
- Issue views (vec koriste mixins): `doi_portal/doi_portal/issues/views.py`
- Postojeci permission testovi: `doi_portal/doi_portal/core/tests/test_permissions.py`

### References

- [Source: epics.md#Story 2.8: Row-Level Permissions for Content]
- [Source: prd.md#RBAC Implementation - Django Groups + django-guardian 3.2.0]
- [Source: architecture.md#Data Architecture - RBAC Model, Row-Level Permissions]
- [Source: architecture.md#Cross-Cutting Concerns - Authorization]
- [Source: project-context.md#RBAC Model (django-guardian)]
- [Source: project-context.md#Services Layer (Business Logic)]
- [Source: core/permissions.py - PublisherPermissionMixin, role_required]
- [Source: publishers/mixins.py - PublisherScopedMixin, PublisherScopedEditMixin, AdministratorRequiredMixin]
- [Source: users/services.py - assign_publisher_permissions, remove_publisher_permissions]
- [Source: users/forms.py - UserCreateForm.save(), UserUpdateForm.save() - permission sync]
- [Source: publications/views.py - PublicationListView uses PublisherScopedMixin]
- [Source: issues/views.py - IssueListView custom get_scoped_queryset]
- [Source: 2-4-publication-admin-list-edit.md - PublisherScopedMixin introduction]
- [Source: 2-6-issue-model-admin-crud.md - Issue scoping via publication__publisher]

## Manuelno Testiranje

### Uputstvo za manuelno testiranje price (Manual Testing Guide)

**Preduslovi:**
1. Pokrenuti lokalno okruzenje: `docker-compose -f docker-compose.local.yml up`
2. Kreirati test korisnike putem Django shell ili Superadmin UI:
   - **Superadmin** korisnik (u Superadmin grupi)
   - **Administrator** korisnik (u Administrator grupi)
   - **Urednik A** - dodeljen Publisher A
   - **Urednik B** - dodeljen Publisher B
   - **Bibliotekar A** - dodeljen Publisher A
   - **Korisnik bez publisher-a** - Urednik bez publisher FK
3. Kreirati dva izdavaca: **Publisher A** (DOI: 10.1111) i **Publisher B** (DOI: 10.2222)
4. Kreirati po jednu publikaciju za svakog izdavaca
5. Kreirati po jedno izdanje za svaku publikaciju

---

### Test 1: Urednik vidi samo svoje publikacije (AC: #2)

1. Prijaviti se kao **Urednik A**
2. Navigirati na **Publikacije** u admin panelu
3. **Ocekivano:** Vidljive SAMO publikacije od Publisher A
4. Publikacije od Publisher B NE smeju biti vidljive u listi

### Test 2: Urednik ne moze pristupiti tudjoj publikaciji (AC: #3)

1. Prijaviti se kao **Urednik A**
2. Otvoriti browser dev tools -> Console
3. Rucno uneti URL publikacije od Publisher B: `/publications/{slug-publisher-b-pub}/`
4. **Ocekivano:** 404 Not Found ili 403 Forbidden stranica (queryset scoping vraca 404 jer objekat nije u filtriranom queryset-u)

### Test 3: Administrator vidi sve (AC: #4)

1. Prijaviti se kao **Administrator**
2. Navigirati na **Publikacije**
3. **Ocekivano:** Vidljive SVE publikacije (i Publisher A i Publisher B)
4. Navigirati na **Izdanja**
5. **Ocekivano:** Vidljiva SVA izdanja svih publikacija

### Test 4: Urednik vidi samo svoja izdanja (AC: #6)

1. Prijaviti se kao **Urednik A**
2. Navigirati na **Izdanja**
3. **Ocekivano:** Vidljiva SAMO izdanja publikacija od Publisher A
4. Izdanja publikacija od Publisher B NE smeju biti vidljiva

### Test 5: Bibliotekar ne moze editovati (AC: #7)

1. Prijaviti se kao **Bibliotekar A**
2. Navigirati na **Publikacije**
3. **Ocekivano:** Publikacije Publisher A su vidljive (read-only)
4. Pokusati pristupiti edit URL-u: `/publications/{slug}/edit/`
5. **Ocekivano:** 403 Forbidden

### Test 6: Korisnik bez publisher-a nema pristup sadrzaju (AC: #8)

1. Prijaviti se kao **Korisnik bez publisher-a**
2. Navigirati na **Publikacije**
3. **Ocekivano:** Prazna lista (nema pristupa nijednom sadrzaju) ili 403

### Test 7: Promena publisher dodele azurira pristup (AC: #5)

1. Prijaviti se kao **Superadmin**
2. Ici na **Upravljanje korisnicima**
3. Otvoriti **Urednik A**
4. Promeniti publisher sa **Publisher A** na **Publisher B**
5. Sacuvati
6. Odjaviti se, prijaviti kao **Urednik A**
7. Navigirati na **Publikacije**
8. **Ocekivano:** Sada su vidljive SAMO publikacije od Publisher B (ne od Publisher A)

### Test 8: Superuser ima pun pristup (dopunski test)

1. Prijaviti se koristenjem Django superuser naloga (`createsuperuser`)
2. Navigirati na **Publikacije** i **Izdanja**
3. **Ocekivano:** Sav sadrzaj je vidljiv bez ogranicenja

---

**Napomena:** Svi testovi se mogu automatizovati u `test_row_level_permissions.py` sa pytest-django. Manuelno testiranje je korisno za vizuelnu potvrdu UX-a permission denied poruka.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 614 project tests pass (0 failures, 3 skipped)
- 90 new tests written for Story 2.8 (29 in test_permissions.py + 61 in test_row_level_permissions.py)

### Completion Notes List

1. Task 1: Added `get_user_publishers()`, `has_publisher_access()`, `sync_guardian_permissions()` to `core/permissions.py`. Refactored `PublisherPermissionMixin` to use `get_user_publishers()` for centralized publisher resolution while maintaining backward compatibility.
2. Task 2: Added `pre_save` and `post_save` signal handlers to existing `users/signals.py` using `@receiver` decorator with string sender reference (`"users.User"`). Signal detects publisher changes via `_old_publisher` pattern and delegates to `sync_guardian_permissions()`. Idempotent with existing `UserUpdateForm.save()` logic.
3. Task 3: Wrote 13 tests verifying all Publisher views are Admin-only (Urednik/Bibliotekar get 403, Administrator/Superuser get 200, unauthenticated get 302).
4. Task 4: Wrote 15 tests verifying Publication views: Urednik sees only own publisher, direct URL to other publisher returns 404, Bibliotekar cannot edit (403), Administrator sees all.
5. Task 5: Wrote 14 tests verifying Issue views: queryset filtering via `publication__publisher`, Urednik create/edit own only, Bibliotekar cannot create/edit, Admin full access.
6. Task 6: Wrote 19 integration tests covering guardian sync, publisher assignment changes updating queryset access, no-publisher users getting 403/empty, superuser full access.
7. No new models created (consolidation story as specified).
8. No changes needed to `users/apps.py` - `ready()` already imports signals module.

### File List

**Modified:**
- `doi_portal/doi_portal/core/permissions.py` - Added `get_user_publishers()`, `has_publisher_access()`, `sync_guardian_permissions()`, refactored `PublisherPermissionMixin`
- `doi_portal/doi_portal/users/signals.py` - Added `capture_old_publisher` (pre_save) and `sync_publisher_permissions` (post_save) signal handlers
- `doi_portal/doi_portal/core/tests/test_permissions.py` - Added 20 new tests for permission helpers and signal sync

**Created:**
- `doi_portal/doi_portal/core/tests/test_row_level_permissions.py` - 61 E2E integration tests for all content hierarchy views
