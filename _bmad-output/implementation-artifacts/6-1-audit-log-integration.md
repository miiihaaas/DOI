# Story 6.1: Audit Log Integration

Status: done

## Story

As a **system**,
I want **to automatically log all content changes**,
So that **there is a complete audit trail for compliance**.

## Acceptance Criteria

1. **AC1: django-auditlog konfiguracija** - `auditlog` je u INSTALLED_APPS i `AuditlogMiddleware` je konfigurisan u MIDDLEWARE za automatsko hvatanje actor (user) i remote_addr informacija.

2. **AC2: Registracija svih modela** - Sledeci modeli su registrovani sa auditlog: Publisher, Publication, Issue, Article, Author, Affiliation, User, CrossrefExport. Registracija je verifikovana testovima.

3. **AC3: CREATE logovanje** - Kada se kreira instanca registrovanog modela, kreira se LogEntry sa action=CREATE, actor (user), timestamp, model, object_id, i changes (JSON).

4. **AC4: UPDATE logovanje** - Kada se azurira instanca registrovanog modela, kreira se LogEntry sa action=UPDATE, a changes polje prikazuje stare i nove vrednosti za izmenjena polja.

5. **AC5: DELETE logovanje** - Kada se brise instanca registrovanog modela, kreira se LogEntry sa action=DELETE, a object representation je sacuvan u logu.

6. **AC6: Sistemske akcije (bez korisnika)** - Kada akciju izvrsava sistem (Celery task, management command) bez user konteksta, actor je null, ali IP adresa se beleži ako je dostupna.

7. **AC7: Retencija logova** - Audit logovi se cuvaju minimum 1 godinu (365 dana). Stariji logovi se mogu arhivirati ali ne brisati. Celery task za arhiviranje je implementiran.

## Tasks / Subtasks

- [x] Task 1: Dodaj AuditlogMiddleware u MIDDLEWARE (AC: #1)
  - [x] 1.1 Dodaj `"auditlog.middleware.AuditlogMiddleware"` u MIDDLEWARE listu u `config/settings/base.py` - POSLE `AuthenticationMiddleware`
  - [x] 1.2 Pokreni migracije: `python manage.py migrate auditlog` (ako vec nije migrirano)
  - [x] 1.3 Napisi test da verifikuje da je middleware aktivan

- [x] Task 2: Registruj User model sa auditlog (AC: #2)
  - [x] 2.1 U `users/apps.py` dodaj `ready()` metod koji registruje User model sa auditlog
  - [x] 2.2 Prati isti pattern kao `articles/apps.py` (koristi `try/except ImportError` guard) - referenciraj i `publishers/apps.py`, `issues/apps.py` za dodatne primere
  - [x] 2.3 Napisi test `test_user_registered_with_auditlog` u `users/tests/`

- [x] Task 3: Verifikuj postojecu registraciju modela (AC: #2)
  - [x] 3.1 Verifikuj da su Publisher, Publication, Issue, Article, Author, Affiliation, CrossrefExport vec registrovani (vec jesu - samo dodaj testove ako nedostaju)
  - [x] 3.2 Napisi objedinjeni test koji proverava SVE registrovane modele odjednom

- [x] Task 4: Testovi za CREATE logovanje (AC: #3)
  - [x] 4.1 Napisi test za User create log entry
  - [x] 4.2 Verifikuj da LogEntry sadrzi: actor, timestamp, content_type, object_id, changes
  - [x] 4.3 Verifikuj da je remote_addr popunjen kada postoji request kontekst (middleware)

- [x] Task 5: Testovi za UPDATE logovanje (AC: #4)
  - [x] 5.1 Napisi test za User update log entry
  - [x] 5.2 Verifikuj da changes JSON sadrzi old i new vrednosti za izmenjena polja

- [x] Task 6: Testovi za DELETE logovanje (AC: #5)
  - [x] 6.1 Napisi test za delete log entry (bilo koji model)
  - [x] 6.2 Verifikuj da je object_repr sacuvan nakon brisanja

- [x] Task 7: Testovi za sistemske akcije bez korisnika (AC: #6)
  - [x] 7.1 Napisi test koji kreira/menja model bez request konteksta (simulira Celery task)
  - [x] 7.2 Verifikuj da actor je None/null
  - [x] 7.3 Verifikuj da se LogEntry ipak kreira

- [x] Task 8: Implementiraj Celery task za arhiviranje starih logova (AC: #7)
  - [x] 8.1 Kreiraj `core/tasks.py` sa `audit_log_archive_task`
  - [x] 8.2 Task arhivira LogEntry starije od 365 dana u JSON fajl (S3 storage u produkciji)
  - [x] 8.2a Verifikuj da je S3 storage konfigurisan (`django-storages` + AWS credentials). Za dev environment koristi lokalni file storage fallback (`MEDIA_ROOT/audit-archives/`) ako S3 nije dostupan
  - [x] 8.3 NE brise originale - samo markira kao arhivirane (dodaj custom field ili koristi timestamp filter)
  - [x] 8.4 Napisi test za archive task
  - [x] 8.5 Registruj task u Celery beat schedule za mesecno izvrsavanje

## Dev Notes

### Kriticno: Sta je VEC implementirano

`django-auditlog` je **vec instaliran i konfigurisan** u projektu. Sledece je vec na mestu:

**INSTALLED_APPS:** `auditlog` je u `THIRD_PARTY_APPS` u `config/settings/base.py` (linija 84)

**Vec registrovani modeli (NE DIRATI - vec rade):**
- `Publisher` - registrovan u `publishers/apps.py:ready()` (linija 20-24)
- `Publication` - registrovan u `publications/apps.py:ready()` (linija 15-21)
- `Issue` - registrovan u `issues/apps.py:ready()` (linija 15-21)
- `Article`, `Author`, `Affiliation` - registrovani u `articles/apps.py:ready()` (linija 17-25)
- `CrossrefExport` - registrovan direktno u `crossref/models.py` (linija 64)

**NIJE implementirano (ovo je scope ove story):**
1. `AuditlogMiddleware` - NIJE u MIDDLEWARE listi (kritično za actor/IP tracking)
2. `User` model - NIJE registrovan sa auditlog
3. Retencija/arhiviranje logova - ne postoji
4. Objedinjeni testovi za kompletnu registraciju

### AuditlogMiddleware pozicija

MORA biti POSLE `AuthenticationMiddleware` da bi imao pristup `request.user`:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "doi_portal.core.middleware.LastActivityMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "auditlog.middleware.AuditlogMiddleware",  # DODAJ OVDE - posle auth
]
```

### User model registracija - pattern

Prati isti pattern kao ostale apps. U `users/apps.py`:

```python
def ready(self):
    """Register User model with auditlog for audit trail."""
    try:
        from auditlog.registry import auditlog
        from .models import User
        auditlog.register(User)
    except ImportError:
        pass
```

**VAZNO:** Proveri da `users/apps.py` vec ima `ready()` metod (mozda za signals). Ako ima, dodaj auditlog registraciju u postojeci `ready()`, NE kreiraj novi.

### Celery task za arhiviranje

Koristi `core/tasks.py` (core app je za shared funkcionalnosti). Pattern:

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def audit_log_archive_task(self, days_threshold=365):
    """Arhiviraj audit log entries starije od threshold dana."""
    from auditlog.models import LogEntry
    from django.utils import timezone

    cutoff_date = timezone.now() - timezone.timedelta(days=days_threshold)
    old_entries = LogEntry.objects.filter(timestamp__lt=cutoff_date)
    # Serializuj u JSON i uploaduj na S3
    # NE BRISATI originale u ovoj fazi
```

### Testovi - organizacija

- Middleware test: `core/tests/test_middleware.py` (dodaj u postojeci fajl ako postoji)
- User auditlog test: `users/tests/test_auditlog.py`
- Objedinjeni test svih modela: `core/tests/test_auditlog_registration.py`
- Archive task test: `core/tests/test_tasks.py`

### Biblioteke i verzije

| Biblioteka | Verzija | Napomena |
|------------|---------|----------|
| django-auditlog | 3.0.0 (project-context) / 3.4.1 (architecture) | Vec instaliran - koristi verziju iz `pyproject.toml` |
| Celery | latest | Vec konfigurisan u projektu |
| django-storages | - | Za S3 upload arhiviranih logova |

**VAZNO:** NE dodaj nove dependencies. Sve potrebno je vec instalirano.

### Project Structure Notes

- `doi_portal/config/settings/base.py` - MIDDLEWARE lista (linija 149-161)
- `doi_portal/doi_portal/users/apps.py` - dodaj auditlog registraciju
- `doi_portal/doi_portal/core/tasks.py` - kreiraj ako ne postoji (za archive task)
- Svi testovi prate `pytest-django` sa `Factory Boy` pattern
- Test fajlovi koriste `test_` prefix

### Anti-patterns (ZABRANJENO)

- NE menjaj postojecu registraciju u `publishers/apps.py`, `articles/apps.py`, itd.
- NE koristi `auditlog.register()` na module nivou (osim za CrossrefExport koji vec tako radi) - koristiti `apps.py:ready()` pattern
- NE dodaj requirements u `requirements/*.txt` - projekat koristi `uv` i `pyproject.toml`
- NE brisati stare log entries u archive tasku - samo exportuj
- NE returnaj JSON iz HTMX endpointa

### References

- [Source: docs/project-context.md#Audit-Logging] - django-auditlog registracija pattern
- [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture] - django-auditlog 3.4.1 izbor
- [Source: _bmad-output/planning-artifacts/epics.md#Story-6.1] - Acceptance criteria sa BDD formatom
- [Source: config/settings/base.py#L84] - auditlog u INSTALLED_APPS
- [Source: config/settings/base.py#L149-161] - MIDDLEWARE lista bez AuditlogMiddleware
- [Source: publishers/apps.py] - Pattern za auditlog registraciju u ready()
- [Source: articles/apps.py] - Pattern za vise modela u jednom ready()

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- auditlog API uses `contains()` not `is_registered()` in installed version
- `object_id` field is int type, not str - tests adjusted accordingly

### Completion Notes List

- AC1: AuditlogMiddleware added to MIDDLEWARE after AuthenticationMiddleware. 3 tests verify configuration.
- AC2: User model registered via `users/apps.py:ready()`. All 8 models verified with parametrized tests + unified check.
- AC3: CREATE logging verified - LogEntry created with timestamp, content_type, object_id, changes.
- AC4: UPDATE logging verified - changes_dict contains old/new values for modified fields.
- AC5: DELETE logging verified - object_repr preserved after deletion.
- AC6: System actions without user context - actor is None, LogEntry still created.
- AC7: Archive task implemented in `core/tasks.py` with local file fallback. Does NOT delete originals. Registered in CELERY_BEAT_SCHEDULE for monthly execution. 6 tests cover task functionality.
- Full test suite: 1680 passed, 3 skipped, 0 failed.

### File List

- `doi_portal/config/settings/base.py` - MODIFIED: Added AuditlogMiddleware to MIDDLEWARE, added CELERY_BEAT_SCHEDULE
- `doi_portal/doi_portal/users/apps.py` - MODIFIED: Added auditlog.register(User) in ready()
- `doi_portal/doi_portal/core/tasks.py` - CREATED: audit_log_archive_task Celery task
- `doi_portal/doi_portal/core/tests/test_middleware.py` - CREATED: 3 middleware config tests
- `doi_portal/doi_portal/core/tests/test_auditlog_registration.py` - CREATED: 9 model registration tests
- `doi_portal/doi_portal/users/tests/test_auditlog.py` - CREATED: 9 CRUD + system action tests
- `doi_portal/doi_portal/core/tests/test_tasks.py` - CREATED: 6 archive task tests
