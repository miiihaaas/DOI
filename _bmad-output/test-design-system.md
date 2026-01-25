# System-Level Test Design - DOI Portal

**Datum:** 2026-01-25
**Autor:** Mihas (TEA - Murat)
**Status:** Draft
**Faza:** Phase 3 - Solutioning (Pre-Implementation Readiness)

---

## Testability Assessment

### Controllability: PASS

**Ocena:** Sistem omogucava kontrolu stanja za testiranje.

| Aspekt | Status | Detalji |
|--------|--------|---------|
| API Seeding | ✅ | Django ORM omogucava direktno kreiranje test podataka |
| Database Reset | ✅ | PostgreSQL transakcije, pytest-django fixture rollback |
| External Dependencies | ✅ | S3 mockable (localstack), ClamAV mockable, Redis testcontainers |
| Dependency Injection | ✅ | Django settings per environment, easy to swap |
| Error Triggering | ✅ | Celery tasks mogu se testirati sinhrono, mock responses |

**Detalji:**
- Cookiecutter Django dolazi sa pytest-django koji automatski rollback-uje transakcije
- `django-guardian` permissions mogu se direktno setovati u test setup-u
- Celery tasks mogu se testirati sa `CELERY_TASK_ALWAYS_EAGER=True`
- S3 storage mockable sa `moto` ili `localstack`
- ClamAV moze se mockati za unit/integration testove

### Observability: PASS

**Ocena:** Sistem pruza dovoljnu vidljivost za validaciju.

| Aspekt | Status | Detalji |
|--------|--------|---------|
| Logging | ✅ | structlog (Cookiecutter default) - strukturirani logovi |
| Audit Trail | ✅ | django-auditlog 3.4.1 - automatski CRUD logging |
| Error Tracking | ✅ | Sentry integracija (Cookiecutter default) |
| Metrics | ⚠️ | Nije eksplicitno definisano - preporuka: dodati Prometheus |
| Health Checks | ⚠️ | Potrebno implementirati `/api/health` endpoint |

**Preporuke:**
- Dodati health check endpoint za DB, Redis, Celery worker status
- Razmotriti Prometheus metriku za performance monitoring

### Reliability: PASS

**Ocena:** Arhitektura podrzava pouzdano testiranje.

| Aspekt | Status | Detalji |
|--------|--------|---------|
| Test Isolation | ✅ | Transakcijski rollback, unique test data (faker) |
| Parallel Safety | ✅ | Django test database per worker |
| Deterministic Results | ✅ | Nema race conditions u sync flow-u |
| Reproducibility | ✅ | Docker environment, seeded factories |
| Loose Coupling | ✅ | Django apps su dobro izolovani, jasne granice |

**Detalji:**
- Cookiecutter Django ima konfigurisan pytest sa `--reuse-db` opcijom
- Factory Boy pattern za test data generaciju
- Docker Compose omogucava reproducibilno okruzenje

---

## Architecturally Significant Requirements (ASRs)

### Visoko-rizicni NFR zahtevi

| ASR ID | Kategorija | Opis | Probability | Impact | Score | Test Approach |
|--------|------------|------|-------------|--------|-------|---------------|
| ASR-001 | PERF | FCP < 3 sekunde za landing stranicu | 2 | 3 | 6 | Lighthouse CI, k6 load test |
| ASR-002 | PERF | Pretraga < 2 sekunde | 2 | 2 | 4 | k6 API load test |
| ASR-003 | PERF | XML generisanje < 30s za 50 clanaka | 2 | 3 | 6 | Unit benchmark test |
| ASR-004 | SEC | RBAC row-level permissions | 3 | 3 | 9 | E2E auth tests, unit permission tests |
| ASR-005 | SEC | Virus scan za sve PDF upload-e | 2 | 3 | 6 | Integration test sa mock ClamAV |
| ASR-006 | SEC | Password hashing (argon2) | 1 | 3 | 3 | Unit test |
| ASR-007 | DATA | Audit log svih CRUD operacija | 2 | 2 | 4 | Integration test |
| ASR-008 | DATA | Soft delete za GDPR compliance | 2 | 3 | 6 | Unit + E2E test |
| ASR-009 | TECH | Crossref XSD validacija | 3 | 3 | 9 | Unit test sa XSD schema |
| ASR-010 | TECH | HTMX partial responses | 2 | 2 | 4 | E2E test |

### Kriticni rizici (Score = 9)

**ASR-004: RBAC Row-Level Permissions**
- **Rizik:** Urednik vidi/modifikuje podatke drugog izdavaca
- **Mitigacija:** Comprehensive permission tests, negative tests za unauthorized access
- **Test Level:** Unit (permission logic) + E2E (user journey)

**ASR-009: Crossref XSD Validation**
- **Rizik:** Generisani XML nije validan za Crossref, DOI registracija failuje
- **Mitigacija:** Unit tests za svaki tip publikacije (journal, conference, book)
- **Test Level:** Unit (schema validation) + Integration (full generation flow)

---

## Test Levels Strategy

### Preporuceni Split

| Test Level | Procenat | Rationale |
|------------|----------|-----------|
| **Unit** | 60% | Django business logic, validators, services |
| **Integration** | 25% | API endpoints, database operations, Celery tasks |
| **E2E** | 15% | Critical user journeys, HTMX interactions |

### Obrazlozenje

**Django MPA aplikacija** favorizuje unit i integration testove:
- Business logic u `services.py`, `validators.py` → Unit tests
- Django views sa ORM → Integration tests (pytest-django)
- HTMX partial responses → Integration tests (Django test client)
- Critical user journeys (bibliotekar unos, admin publish) → E2E (Playwright)

### Test Environment Needs

| Environment | Purpose | Tools |
|-------------|---------|-------|
| **Local** | Development, unit tests | pytest, Docker Compose |
| **CI** | All tests, coverage | GitHub Actions, pytest-cov |
| **Staging** | E2E tests, manual QA | Docker, Playwright |
| **Production-like** | Performance tests | k6, isolated staging |

---

## NFR Testing Approach

### Security

| Zahtev | Pristup | Alati |
|--------|---------|-------|
| HTTPS TLS 1.2+ | Traefik config validation | Manual check |
| Password hashing | Unit test argon2 | pytest |
| RBAC 4 uloge | E2E permission tests | Playwright |
| Row-level permissions | Unit + E2E tests | pytest, Playwright |
| Virus scan PDF | Integration test | Mock ClamAV |
| CSRF protection | E2E form tests | Playwright |
| XSS prevention | E2E input tests | Playwright |
| SQL injection | ORM by design, audit | Code review |

**Kritican test:** Unauthorized access test za svaku ulogu i resurs.

### Performance

| Zahtev | Pristup | Alati | Threshold |
|--------|---------|-------|-----------|
| FCP < 3s | Lighthouse CI | Lighthouse | FCP < 3000ms |
| Pretraga < 2s | k6 load test | k6 | p95 < 2000ms |
| XML gen < 30s | Benchmark test | pytest-benchmark | 50 articles < 30s |
| Admin < 5s | Lighthouse CI | Lighthouse | LCP < 5000ms |

**Performance Test Levels:**
- **Smoke:** 10 VU, 30s - basic sanity
- **Load:** 50 VU, 5min - expected traffic
- **Stress:** 100 VU, 5min - peak traffic

### Reliability

| Zahtev | Pristup | Alati |
|--------|---------|-------|
| 99% uptime | Infrastructure monitoring | Sentry, health checks |
| Error handling | E2E error scenarios | Playwright |
| Celery task failures | Integration tests | pytest, mock |
| Database connection | Health check endpoint | Django management command |
| Redis connection | Health check endpoint | Django management command |

### Maintainability

| Zahtev | Pristup | Alati | Target |
|--------|---------|-------|--------|
| Test coverage | pytest-cov | CI job | >= 80% |
| Code duplication | Linting | flake8, ruff | < 5% |
| Vulnerabilities | Dependency scan | safety, pip-audit | 0 critical/high |
| Documentation | Docstrings | pydocstyle | Critical modules |

---

## Test Environment Requirements

### Local Development

```yaml
services:
  postgres:
    image: postgres:16
    ports: ["5432:5432"]
  redis:
    image: redis:latest
    ports: ["6379:6379"]
  celery:
    command: celery -A config worker -l INFO
  mailpit:
    image: axllent/mailpit
    ports: ["8025:8025"]
```

### CI Pipeline (GitHub Actions)

```yaml
jobs:
  test:
    services:
      postgres:
        image: postgres:16
      redis:
        image: redis:latest
    steps:
      - run: pytest --cov=doi_portal --cov-report=xml
      - run: coverage report --fail-under=80
```

### Staging (E2E Tests)

- Full Docker Compose stack
- Playwright containers
- Isolated test database
- Mock S3 (localstack) or real S3 bucket
- Mock ClamAV for speed

---

## Testability Concerns

### Potencijalni Problemi

| Concern | Severity | Mitigacija |
|---------|----------|------------|
| ClamAV dependency | Medium | Mockable, async task |
| S3 external dependency | Medium | Localstack for tests |
| HTMX dynamic content | Low | Django test client + Playwright |
| Alpine.js state | Low | Playwright E2E only where needed |
| Email sending | Low | Mailpit for local, mock for CI |

### Preporuke za Testabilnost

1. **Kreirati `/api/health` endpoint** - validacija DB, Redis, Celery statusa
2. **Dodati Prometheus metriku** - optional, ali korisno za production monitoring
3. **Factory Boy factories** - standardizovani test data za sve modele
4. **Fixture per app** - `conftest.py` u svakom Django app-u
5. **HTMX test helpers** - custom fixtures za HTMX request simulation

---

## Recommendations for Sprint 0

### Test Framework Setup (`*framework` workflow)

1. **pytest-django konfiguracija**
   - `pytest.ini` sa `DJANGO_SETTINGS_MODULE=config.settings.test`
   - `conftest.py` sa fixture-ima za User, Publisher, Publication, Issue, Article
   - Factory Boy integracija

2. **Coverage setup**
   - `pytest-cov` sa 80% minimum threshold
   - Coverage report u CI

3. **Playwright setup**
   - `playwright.config.ts` sa base URL
   - Auth fixtures za svaku ulogu (Superadmin, Admin, Urednik, Bibliotekar)
   - Storage state reuse za brzinu

### CI Pipeline Setup (`*ci` workflow)

1. **GitHub Actions workflow**
   - Unit tests + coverage
   - Integration tests (sa PostgreSQL, Redis services)
   - E2E tests (Playwright)
   - Lint + security checks

2. **Quality Gates**
   - Coverage >= 80%
   - 0 critical vulnerabilities
   - All E2E smoke tests pass

### Initial Test Coverage Priorities

| Priority | Scope | Tests |
|----------|-------|-------|
| P0 | RBAC permissions | 15 unit + 10 E2E |
| P0 | Crossref XML validation | 20 unit |
| P0 | User authentication | 10 E2E |
| P1 | CRUD operations | 30 integration |
| P1 | HTMX endpoints | 20 integration |
| P2 | Audit logging | 10 integration |
| P2 | File upload | 5 integration |

---

## Quality Gate Criteria (Pre-Implementation)

### Testability Gate

- [x] Controllability: PASS - API seeding, DB reset, mockable dependencies
- [x] Observability: PASS (with recommendations) - Logging, audit, error tracking
- [x] Reliability: PASS - Isolation, parallelization, reproducibility

### ASR Gate

- [ ] Critical ASRs (Score=9) have mitigation plans documented
- [ ] High-priority ASRs (Score>=6) have test approaches defined
- [ ] Test levels strategy aligned with architecture

### Recommendation

**Overall Status:** PASS with CONCERNS

**Concerns:**
1. Health check endpoint not yet implemented - add to Epic 1
2. Prometheus metrics optional but recommended for production
3. Critical RBAC tests must be prioritized in Sprint 1

**Rationale:** Arhitektura je testabilna. Cookiecutter Django pruza solidnu osnovu sa pytest-django, Docker, i CI/CD. Kriticni rizici (RBAC, Crossref XSD) imaju jasne mitigacije kroz test strategiju.

---

## Follow-on Workflows

- **`*framework`** - Initialize test framework (pytest-django, Playwright, factories)
- **`*ci`** - Setup CI/CD quality pipeline
- **`*atdd`** - Generate failing tests for P0 scenarios (RBAC, Crossref)

---

**Generated by:** BMad TEA Agent - Test Architect Module
**Workflow:** `_bmad/bmm/testarch/test-design` (System-Level Mode)
**Version:** 4.0 (BMad v6)
