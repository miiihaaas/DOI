---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - prd.md
  - architecture.md
  - ux-design-specification.md
totalEpics: 6
totalStories: 46
totalFRsCovered: 50
validationStatus: PASSED
validatedAt: 2026-01-25
prdRevision: "1.1"
prdRevisionNotes: "Added Story 2.3a for Crossref compliance fields"
---

# DOI - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for DOI, decomposing the requirements from the PRD, UX Design, and Architecture documents into implementable stories.

## Requirements Inventory

### Functional Requirements

**1. User Management & Authentication (FR1-FR7)**
- FR1: Korisnik se moze registrovati sa email-om i lozinkom
- FR2: Korisnik se moze prijaviti na sistem
- FR3: Korisnik moze resetovati zaboravljenu lozinku
- FR4: Superadmin moze kreirati nove korisnike
- FR5: Superadmin moze dodeliti/promeniti ulogu korisniku (Superadmin, Administrator, Urednik, Bibliotekar)
- FR6: Superadmin moze aktivirati/deaktivirati korisnike
- FR7: Sistem belezi poslednju aktivnost korisnika

**2. Publisher Management - Izdavaci (FR8-FR12)**
- FR8: Administrator moze kreirati novog izdavaca
- FR9: Administrator moze editovati podatke o izdavacu (naziv, logo, opis, kontakt, DOI prefix)
- FR10: Administrator moze pregledati listu svih izdavaca
- FR11: Sistem cuva DOI prefix za svakog izdavaca
- FR12: Posetilac moze videti stranicu izdavaca sa listom njegovih publikacija

**3. Publication Management - Publikacije (FR13-FR17)**
- FR13: Administrator moze kreirati novu publikaciju (casopis, zbornik, monografija, ostalo)
- FR14: Administrator moze editovati podatke o publikaciji
- FR15: Administrator moze povezati publikaciju sa izdavacem
- FR16: Sistem podrzava razlicite tipove publikacija sa specificnim poljima
- FR17: Posetilac moze pregledati listu svih publikacija sa filterima

**4. Issue Management - Izdanja (FR18-FR21)**
- FR18: Urednik moze kreirati novo izdanje publikacije
- FR19: Urednik moze editovati podatke o izdanju (volume, broj, godina, naslovna slika)
- FR20: Urednik moze postaviti status izdanja (draft, scheduled, published, archive)
- FR21: Posetilac moze pregledati sva izdanja publikacije

**5. Article Management - Clanci (FR22-FR32)**
- FR22: Bibliotekar moze kreirati novi clanak
- FR23: Bibliotekar moze uneti metapodatke clanka (naslov, podnaslov, apstrakt, kljucne reci)
- FR24: Bibliotekar moze dodati autore sa reorderingom (ime, afilijacija, ORCID, email)
- FR25: Bibliotekar moze upload-ovati PDF fajl
- FR26: Bibliotekar moze sacuvati clanak kao draft
- FR27: Sistem automatski cuva izmene (auto-save)
- FR28: Sistem validira ORCID format
- FR29: Urednik moze pregledati clanak za odobrenje
- FR30: Administrator moze objaviti clanak
- FR31: Administrator moze povuci (withdraw) objavljeni clanak
- FR32: Sistem prikazuje withdrawn clanke sa oznakom

**6. Crossref Integration (FR33-FR37)**
- FR33: Administrator moze generisati Crossref XML za izdanje (svi clanci izdanja u jednom XML fajlu)
- FR34: Sistem prikazuje preview generisanog XML-a za izdanje
- FR35: Sistem validira XML prema Crossref XSD shemi
- FR36: Sistem upozorava na greske pre generisanja XML-a
- FR37: Administrator moze preuzeti generisani XML fajl za izdanje

**7. Public Portal (FR38-FR45)**
- FR38: Posetilac moze videti pocetnu stranu portala
- FR39: Posetilac moze pretrazivati clanke po nazivu, autoru i kljucnim recima
- FR40: Posetilac moze filtrirati publikacije po vrsti, oblasti, pristupu, jeziku
- FR41: Posetilac moze videti landing stranicu clanka sa svim metapodacima
- FR42: Posetilac moze preuzeti PDF clanka
- FR43: Posetilac moze videti stranicu "O portalu"
- FR44: Posetilac moze poslati poruku preko kontakt forme
- FR45: Sistem salje kontakt poruke na definisanu email adresu

**8. Admin Dashboard & Audit (FR46-FR50)**
- FR46: Administrator vidi statistiku na dashboard-u (broj publikacija, clanaka, pending zahteva)
- FR47: Administrator vidi listu clanaka koji cekaju odobrenje
- FR48: Superadmin moze pregledati audit log (ko, sta, kada)
- FR49: Sistem belezi sve izmene sadrzaja u audit log
- FR50: Superadmin moze obraditi zahtev za brisanje podataka (GDPR)

### NonFunctional Requirements

**Performance**
- NFR1: Landing stranica clanka - First Contentful Paint < 3 sekunde
- NFR2: Javne stranice portala - Ucitavanje < 3 sekunde
- NFR3: Admin panel stranice - Ucitavanje < 5 sekundi
- NFR4: PDF download - Direktan link, bez procesiranja
- NFR5: Pretraga - Rezultati < 2 sekunde
- NFR6: XML generisanje - < 30 sekundi za izdanje sa 50 clanaka

**Security**
- NFR7: HTTPS obavezno za sve stranice (TLS 1.2+)
- NFR8: Password policy - Min 8 karaktera, kombinacija slova/brojeva
- NFR9: Session management - Timeout nakon 30 min neaktivnosti
- NFR10: Lozinke hashirane (bcrypt/argon2), nikad plain text
- NFR11: PDF upload - Virus scan pre prihvatanja
- NFR12: Audit log - Sve admin akcije se beleze (ko, sta, kada, IP)
- NFR13: GDPR - Soft delete, pravo na brisanje, cuvanje logova 1+ godina

**Accessibility**
- NFR14: Semanticki HTML5 elementi
- NFR15: Alt tekst za sve slike
- NFR16: Kontrast minimum 4.5:1 za tekst
- NFR17: Keyboard navigacija za kljucne akcije
- NFR18: Labels povezani sa input poljima

**Integration**
- NFR19: Crossref XML validacija prema aktuelnoj XSD shemi
- NFR20: Cloud Storage - S3-compatible API za PDF fajlove
- NFR21: Email - SMTP za kontakt formu i notifikacije

**Reliability**
- NFR22: Uptime 99% dostupnost
- NFR23: Dnevni backup baze i fajlova
- NFR24: Backup cuvanje 90+ dana
- NFR25: Graceful degradation, user-friendly error poruke

### Additional Requirements

**Iz Architecture dokumenta:**
- **STARTER TEMPLATE:** Cookiecutter Django 2026.4.3 - OBAVEZNO za inicijalizaciju projekta (Epic 1 Story 1)
- PostgreSQL 16+ umesto MySQL (bolja Django podrska, aktivno odrzavano)
- RBAC implementacija: Django Groups + django-guardian 3.2.0 za row-level permissions
- Audit logging: django-auditlog 3.4.1 za automatski CRUD logging
- Frontend interaktivnost: HTMX 2.0.8 + Alpine.js 3.15.3
- Authentication: django-allauth (Cookiecutter default)
- Password hashing: argon2 (Cookiecutter default)
- File storage: AWS S3 za PDF fajlove
- Virus scanning: ClamAV (self-hosted), Celery task
- XML generation: lxml + Jinja2 templates
- XSD validation: lxml.etree.XMLSchema
- Containerization: Docker + docker-compose
- Reverse proxy: Traefik (Cookiecutter default)
- CI/CD: GitHub Actions (Cookiecutter default)
- Monitoring: Sentry
- Logging: structlog

**Iz UX Design dokumenta:**
- Custom Bootstrap 5 admin panel (NE Django Admin) - potpuna kontrola nad UX
- 10 custom UI komponenti: Article Card, Author List (drag & drop), Status Badge, Floating Action Bar, Auto-save Indicator, ORCID Input, Filter Sidebar, Citation Modal, XML Preview, Publication Hierarchy
- Desktop-first za admin panel, mobile-first za javni portal
- WCAG 2.1 Level AA compliance
- Auto-save na svakom blur/pause (debounced 2s)
- Toast notifikacije (top-right, 5s auto-dismiss)
- Breadcrumbs na svakoj strani
- Collapsible sidebar navigacija za admin

**Iz Crossref dokumentacije (Schema 5.4.0):**
- Tri razlicita XML formata po tipu publikacije:
  - **Casopis (Journal):** `<journal>` container, `<journal_article>` elementi, ISSN obavezan
  - **Zbornik (Conference):** `<conference>` container, `<event_metadata>` za dogadjaj, `<conference_paper>` elementi
  - **Monografija (Book):** `<book>` container, ISBN/NOISBN obavezan, `<content_item>` za poglavlja
- Razlicita obavezna polja po tipu publikacije
- Validacija prema odgovarajucoj Crossref XSD semi za svaki tip

### FR Coverage Map

| FR | Epic | Opis |
|----|------|------|
| FR1 | ~~UKLONJEN~~ | ~~Registracija korisnika~~ - interni korisnici |
| FR2 | Epic 1 | Prijava na sistem |
| FR3 | Epic 1 | Reset lozinke |
| FR4 | Epic 1 | Kreiranje novih korisnika |
| FR5 | Epic 1 | Dodela uloga korisnicima |
| FR6 | Epic 1 | Aktivacija/deaktivacija korisnika |
| FR7 | Epic 1 | Belezenje poslednje aktivnosti |
| FR8 | Epic 2 | Kreiranje izdavaca |
| FR9 | Epic 2 | Editovanje izdavaca |
| FR10 | Epic 2 | Lista izdavaca |
| FR11 | Epic 2 | DOI prefix za izdavaca |
| FR12 | Epic 2 | Javna stranica izdavaca |
| FR13 | Epic 2 | Kreiranje publikacije |
| FR14 | Epic 2 | Editovanje publikacije |
| FR15 | Epic 2 | Povezivanje publikacije sa izdavacem |
| FR16 | Epic 2 | Tipovi publikacija sa specificnim poljima |
| FR17 | Epic 2 | Lista publikacija sa filterima |
| FR18 | Epic 2 | Kreiranje izdanja |
| FR19 | Epic 2 | Editovanje izdanja |
| FR20 | Epic 2 | Status izdanja |
| FR21 | Epic 2 | Lista izdanja publikacije |
| FR22 | Epic 3 | Kreiranje clanka |
| FR23 | Epic 3 | Metapodaci clanka |
| FR24 | Epic 3 | Autori sa reorderingom |
| FR25 | Epic 3 | Upload PDF fajla |
| FR26 | Epic 3 | Cuvanje kao draft |
| FR27 | Epic 3 | Auto-save |
| FR28 | Epic 3 | ORCID validacija |
| FR29 | Epic 3 | Pregled za odobrenje |
| FR30 | Epic 3 | Objavljivanje clanka |
| FR31 | Epic 3 | Povlacenje clanka |
| FR32 | Epic 3 | Prikaz withdrawn clanaka |
| FR33 | Epic 5 | Generisanje Crossref XML po tipu publikacije |
| FR34 | Epic 5 | Preview XML-a |
| FR35 | Epic 5 | Validacija prema Crossref XSD po tipu |
| FR36 | Epic 5 | Upozorenja pre generisanja |
| FR37 | Epic 5 | Preuzimanje XML fajla |
| FR38 | Epic 4 | Pocetna strana portala |
| FR39 | Epic 4 | Pretraga clanaka |
| FR40 | Epic 4 | Filtriranje publikacija |
| FR41 | Epic 4 | Landing stranica clanka |
| FR42 | Epic 4 | Preuzimanje PDF-a |
| FR43 | Epic 4 | Stranica O portalu |
| FR44 | Epic 4 | Kontakt forma |
| FR45 | Epic 4 | Slanje kontakt poruka |
| FR46 | Epic 3 | Dashboard statistika |
| FR47 | Epic 3 | Pending lista clanaka |
| FR48 | Epic 6 | Audit log pregled |
| FR49 | Epic 6 | Belezenje izmena u audit log |
| FR50 | Epic 6 | GDPR zahtevi za brisanje |

## Epic List

### Epic 1: Project Foundation & Authentication
**Cilj:** Clanovi tima mogu pristupiti sistemu sa svojim dodeljenim ulogama

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7

---

### Epic 2: Content Structure Management
**Cilj:** Administratori mogu postaviti kompletnu hijerarhiju sadrzaja (Izdavac → Publikacija → Izdanje)

**FRs covered:** FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19, FR20, FR21

---

### Epic 3: Article Workflow
**Cilj:** Tim moze kreirati, pregledati i objaviti clanke kroz kompletan workflow

**FRs covered:** FR22, FR23, FR24, FR25, FR26, FR27, FR28, FR29, FR30, FR31, FR32, FR46, FR47

---

### Epic 4: Public Portal Experience
**Cilj:** Posetioci mogu otkriti sadrzaj i pristupiti clancima preko DOI linkova

**FRs covered:** FR38, FR39, FR40, FR41, FR42, FR43, FR44, FR45

---

### Epic 5: Crossref XML Integration
**Cilj:** Administratori mogu generisati validan Crossref XML za DOI registraciju, sa podrskom za sve tipove publikacija (casopis, zbornik, monografija) i njihove specificne XML strukture prema Crossref semi 5.4.0

**FRs covered:** FR33, FR34, FR35, FR36, FR37

---

### Epic 6: Compliance & Monitoring
**Cilj:** Superadmin moze osigurati uskladjenost sistema i pratiti sve aktivnosti

**FRs covered:** FR48, FR49, FR50

---

## Epic 1: Project Foundation & Authentication

**Cilj:** Clanovi tima mogu pristupiti sistemu sa svojim dodeljenim ulogama

Ovaj epik postavlja temelj celog sistema koristeci Cookiecutter Django starter i implementira kompletan sistem autentifikacije sa RBAC-om za 4 uloge (Superadmin, Administrator, Urednik, Bibliotekar). Nakon zavrsetka, svi clanovi tima mogu se prijaviti i videti osnovni dashboard prilagodjen njihovoj ulozi.

### Story 1.1: Project Initialization with Cookiecutter Django

As a **developer**,
I want **to initialize the project using Cookiecutter Django starter template**,
So that **I have a production-ready foundation with Docker, PostgreSQL, Celery, and Redis configured**.

**Acceptance Criteria:**

**Given** the developer has Python and cookiecutter installed
**When** running `cookiecutter gh:cookiecutter/cookiecutter-django` with project name "doi_portal"
**Then** a complete Django project structure is created
**And** Docker and docker-compose files are configured for local development
**And** PostgreSQL 16+ is configured as the database
**And** Redis is configured for caching and Celery broker
**And** Celery worker configuration is in place
**And** GitHub Actions CI/CD pipeline is configured
**And** `docker-compose up` successfully starts all services
**And** Django development server is accessible at localhost:8000

---

### Story 1.2: Custom User Model & RBAC Setup

As a **system administrator**,
I want **a custom user model with role-based access control**,
So that **users can be assigned to one of four roles with appropriate permissions**.

**Acceptance Criteria:**

**Given** the project is initialized
**When** the User model is created
**Then** User model extends AbstractUser with additional fields (publisher FK, last_activity)
**And** four Django Groups are created: Superadmin, Administrator, Urednik, Bibliotekar
**And** django-guardian is installed and configured for object-level permissions
**And** each Group has appropriate base permissions defined
**And** User model includes is_active field for activation/deactivation
**And** migrations run successfully
**And** a superuser can be created via `createsuperuser` command

---

### Story 1.3: User Login & Logout

As a **team member**,
I want **to log in and out of the system securely**,
So that **I can access the admin panel according to my role**.

**Acceptance Criteria:**

**Given** a registered user with valid credentials
**When** the user navigates to the login page
**Then** a Bootstrap 5 styled login form is displayed
**And** the user can enter email and password

**Given** valid credentials are submitted
**When** the login form is processed
**Then** the user is authenticated and redirected to dashboard
**And** a session is created with 30-minute inactivity timeout
**And** last_activity timestamp is updated

**Given** an authenticated user
**When** the user clicks logout
**Then** the session is terminated
**And** the user is redirected to login page

**Given** invalid credentials are submitted
**When** the login form is processed
**Then** an error message is displayed
**And** the user remains on the login page

---

### Story 1.4: User Registration - ~~UKLONJENA~~

> **NAPOMENA:** Ova priča je uklonjena. Portal je interni alat - javna registracija nije potrebna.
> Superadmin kreira korisničke naloge ručno (videti Story 1.6: User Management by Superadmin).

---

### Story 1.5: Password Reset

As a **user who forgot their password**,
I want **to reset my password via email**,
So that **I can regain access to my account**.

**Acceptance Criteria:**

**Given** a registered user
**When** clicking "Forgot Password" on login page
**Then** a password reset form is displayed requesting email

**Given** valid email is submitted
**When** the form is processed
**Then** a password reset email is sent with secure token
**And** user sees confirmation message (regardless of email existence for security)

**Given** user clicks the reset link in email
**When** the link is valid and not expired
**Then** a new password form is displayed

**Given** new password meets policy requirements
**When** the password reset form is submitted
**Then** password is updated with argon2 hashing
**And** user is redirected to login page with success message
**And** all existing sessions are invalidated

---

### Story 1.6: User Management by Superadmin

As a **Superadmin**,
I want **to create, edit, and manage user accounts**,
So that **I can control who has access to the system and with what permissions**.

**Acceptance Criteria:**

**Given** a logged-in Superadmin
**When** navigating to User Management
**Then** a list of all users is displayed with status, role, and last activity

**Given** Superadmin clicks "Add User"
**When** the user creation form is displayed
**Then** fields include: email, first name, last name, role selection, publisher assignment (optional)
**And** Superadmin can set initial password or trigger email invitation

**Given** valid user data is submitted
**When** the form is processed
**Then** new user is created with selected role (Group assignment)
**And** if publisher is assigned, django-guardian object permission is set

**Given** Superadmin edits an existing user
**When** changing the user's role
**Then** Group membership is updated accordingly
**And** change is logged in audit trail

**Given** Superadmin deactivates a user
**When** setting is_active=False
**Then** user can no longer log in
**And** existing sessions are terminated
**And** user appears as "Inactive" in user list

**Given** a non-Superadmin user
**When** attempting to access User Management
**Then** access is denied with 403 Forbidden

---

### Story 1.7: Admin Dashboard Shell

As a **logged-in team member**,
I want **to see a dashboard appropriate for my role**,
So that **I can quickly access my most relevant tasks**.

**Acceptance Criteria:**

**Given** a logged-in user
**When** accessing the dashboard
**Then** a Bootstrap 5 admin layout is displayed with:
  - Collapsible sidebar navigation
  - Header with user info and logout
  - Breadcrumbs
  - Main content area

**Given** user has role Bibliotekar
**When** viewing the dashboard
**Then** sidebar shows only relevant menu items (Articles, My Drafts)

**Given** user has role Administrator
**When** viewing the dashboard
**Then** sidebar shows full content management menu

**Given** user has role Superadmin
**When** viewing the dashboard
**Then** sidebar includes User Management and System Settings

**Given** any user action in admin panel
**When** the action is completed
**Then** last_activity timestamp is updated on User model

**Given** session timeout (30 min inactivity)
**When** user attempts any action
**Then** user is redirected to login with session expired message

---

## Epic 2: Content Structure Management

**Cilj:** Administratori mogu postaviti kompletnu hijerarhiju sadrzaja (Izdavac → Publikacija → Izdanje)

Ovaj epik omogucava administratorima da kreiraju i upravljaju strukturom sadrzaja. Svaki tip publikacije (casopis, zbornik, monografija) ima specificna polja prema Crossref zahtevima. Javne stranice omogucavaju posetiocima pregled liste izdavaca, publikacija i izdanja.

### Story 2.1: Publisher Model & Admin CRUD

As an **Administrator**,
I want **to create and manage publishers with their DOI prefixes**,
So that **publications can be organized under their respective publishers**.

**Acceptance Criteria:**

**Given** the Publisher model is created
**When** reviewing the model structure
**Then** it includes fields: name, slug, logo (ImageField), description, contact_email, contact_phone, website, doi_prefix (required, unique), created_at, updated_at
**And** doi_prefix validates format (e.g., "10.1234")
**And** migrations run successfully

**Given** a logged-in Administrator
**When** navigating to Publishers in admin panel
**Then** a list of all publishers is displayed with name, DOI prefix, publication count

**Given** Administrator clicks "Add Publisher"
**When** the form is displayed
**Then** all required fields are shown with proper validation
**And** logo upload accepts common image formats (jpg, png, svg)

**Given** valid publisher data is submitted
**When** the form is processed
**Then** publisher is created successfully
**And** slug is auto-generated from name
**And** toast notification confirms success

**Given** Administrator edits an existing publisher
**When** changes are saved
**Then** publisher data is updated
**And** change is recorded in audit log

**Given** Administrator attempts to delete a publisher with publications
**When** delete is requested
**Then** soft delete is performed (is_deleted=True)
**And** warning is shown about associated publications

---

### Story 2.2: Public Publisher Page

As a **visitor**,
I want **to view a publisher's page with their publications**,
So that **I can browse content from a specific publisher**.

**Acceptance Criteria:**

**Given** a published publisher exists
**When** visitor navigates to /publishers/{slug}/
**Then** publisher details are displayed (name, logo, description, contact info)
**And** list of publications by this publisher is shown
**And** page uses public portal Bootstrap 5 template

**Given** visitor is on publishers listing page
**When** viewing /publishers/
**Then** all active publishers are listed with logos and names
**And** each publisher links to their detail page

**Given** publisher has no published publications
**When** viewing publisher page
**Then** appropriate message is shown ("No publications yet")

**Given** a deleted or inactive publisher
**When** visitor attempts to access the page
**Then** 404 Not Found is returned

---

### Story 2.3: Publication Model with Type-Specific Fields

As an **Administrator**,
I want **to create publications with type-specific metadata fields**,
So that **each publication type (journal, conference, book) has appropriate Crossref-required fields**.

**Acceptance Criteria:**

**Given** the Publication model is created
**When** reviewing the model structure
**Then** it includes common fields: title, slug, publisher (FK), description, cover_image, language, subject_area, access_type, created_at, updated_at
**And** type field is enum: JOURNAL, CONFERENCE, BOOK, OTHER

**Given** publication type is JOURNAL
**When** viewing/editing the publication
**Then** additional fields are available: issn_print, issn_online, abbreviation, frequency

**Given** publication type is CONFERENCE
**When** viewing/editing the publication
**Then** additional fields are available: conference_name, conference_acronym, conference_location, conference_date, series_issn

**Given** publication type is BOOK
**When** viewing/editing the publication
**Then** additional fields are available: isbn_print, isbn_online, edition, series_title

**Given** Administrator creates a new publication
**When** selecting publication type
**Then** form dynamically shows/hides type-specific fields
**And** HTMX is used for dynamic form updates

**Given** valid publication data is submitted
**When** the form is processed
**Then** publication is created with publisher association
**And** type-specific fields are validated (e.g., ISSN format)
**And** django-guardian assigns object permissions if needed

---

### Story 2.3a: Crossref Depositor Fields Migration (PATCH STORY)

> **NAPOMENA:** Ova priča je patch story dodata nakon PRD revizije 1.1 za Crossref compliance.
> Dodaje nedostajuća obavezna polja za Crossref XML generisanje.

As an **Administrator**,
I want **Publisher and Publication models to have Crossref-compliant depositor and conference fields**,
So that **XML generation in Epic 5 can produce valid Crossref deposits with proper head metadata**.

**Acceptance Criteria:**

**Given** the Publisher model exists
**When** reviewing the model fields
**Then** it includes new Crossref depositor fields:
  - `depositor_name` (CharField, max_length=255, blank=True)
  - `depositor_email` (EmailField, blank=True)
  - `registrant` (CharField, max_length=255, blank=True)

**Given** the Publication model exists (CONFERENCE type)
**When** reviewing the model fields
**Then** it includes new conference fields:
  - `conference_date_end` (DateField, null=True, blank=True)
  - `conference_number` (PositiveIntegerField, null=True, blank=True)

**Given** the Django migrations are created
**When** migrations are applied to the database
**Then** migrations complete successfully without data loss

**Given** the Publisher admin form
**When** editing a publisher
**Then** depositor fields appear in a new "Crossref Depositor" fieldset

**Given** the Publication admin form for CONFERENCE type
**When** editing a conference publication
**Then** new fields appear in the conference fieldset alongside existing fields

**Given** the existing test suite
**When** running all tests
**Then** all existing tests pass without modification

---

### Story 2.4: Publication Admin List & Edit

As an **Administrator**,
I want **to manage all publications from the admin panel**,
So that **I can edit and organize publication metadata**.

**Acceptance Criteria:**

**Given** a logged-in Administrator
**When** navigating to Publications
**Then** a list of all publications is displayed
**And** list shows: title, type (with icon), publisher, issue count, status
**And** list supports sorting and filtering by type, publisher

**Given** Administrator clicks on a publication
**When** the detail view opens
**Then** all publication fields are displayed
**And** type-specific fields are shown based on publication type

**Given** Administrator edits publication
**When** changes are saved
**Then** publication is updated
**And** audit log records the change

**Given** Urednik with publisher assignment
**When** viewing publications list
**Then** only publications from assigned publisher are shown
**And** row-level permission is enforced via django-guardian

---

### Story 2.5: Public Publication List with Filters

As a **visitor**,
I want **to browse and filter all publications**,
So that **I can find publications relevant to my interests**.

**Acceptance Criteria:**

**Given** visitor navigates to /publications/
**When** the page loads
**Then** all published publications are listed in card grid (3 columns desktop)
**And** each card shows: cover image, title, type icon, publisher name

**Given** filter sidebar is displayed
**When** visitor selects filters
**Then** publications can be filtered by: type, subject area, access type, language
**And** filters use multiselect checkboxes
**And** HTMX updates results without full page reload

**Given** visitor enters search term
**When** searching in the search box
**Then** publications are filtered by title match
**And** search is debounced (300ms)

**Given** many publications exist
**When** scrolling the list
**Then** pagination is displayed (or infinite scroll for >50 items)

**Given** visitor clicks on a publication card
**When** navigating to detail
**Then** publication detail page is shown with list of issues

---

### Story 2.6: Issue Model & Admin CRUD

As an **Urednik (Editor)**,
I want **to create and manage issues for publications**,
So that **articles can be organized into volumes and issues**.

**Acceptance Criteria:**

**Given** the Issue model is created
**When** reviewing the model structure
**Then** it includes fields: publication (FK), volume, issue_number, year, title (optional), cover_image, publication_date, status, created_at, updated_at
**And** status is enum: DRAFT, SCHEDULED, PUBLISHED, ARCHIVE

**Given** a logged-in Urednik
**When** navigating to Issues for their assigned publication
**Then** a list of issues is displayed with volume, number, year, status, article count

**Given** Urednik clicks "Add Issue"
**When** the form is displayed
**Then** publication is pre-selected based on context
**And** fields for volume, issue_number, year, cover_image are shown
**And** status defaults to DRAFT

**Given** valid issue data is submitted
**When** the form is processed
**Then** issue is created with DRAFT status
**And** toast notification confirms success

**Given** Urednik changes issue status
**When** status is changed to PUBLISHED
**Then** all articles in the issue with "ready" status become visible on public portal

**Given** Urednik without publisher assignment
**When** attempting to create issue for unassigned publication
**Then** action is denied with 403 Forbidden

---

### Story 2.7: Public Issue List & Detail

As a **visitor**,
I want **to browse issues of a publication**,
So that **I can find articles from a specific volume or issue**.

**Acceptance Criteria:**

**Given** visitor views a publication detail page
**When** the page loads
**Then** published issues are listed chronologically (newest first)
**And** each issue shows: volume, number, year, cover thumbnail, article count

**Given** visitor clicks on an issue
**When** navigating to /publications/{pub-slug}/issues/{issue-id}/
**Then** issue detail page shows all published articles in the issue
**And** articles are displayed as cards with title, authors, first page

**Given** issue has status DRAFT
**When** visitor attempts to access
**Then** 404 Not Found is returned (draft issues not public)

**Given** publication hierarchy breadcrumbs
**When** viewing any level (publication, issue)
**Then** breadcrumbs show: Home > Publications > {Publication} > {Issue}

---

### Story 2.8: Row-Level Permissions for Content

As a **system**,
I want **to enforce row-level permissions based on publisher assignment**,
So that **Urednici and Bibliotekari can only manage content from their assigned publishers**.

**Acceptance Criteria:**

**Given** a user with role Urednik or Bibliotekar
**When** assigned to a Publisher via User model
**Then** django-guardian object permission is automatically assigned

**Given** Urednik with publisher assignment
**When** querying publications
**Then** queryset is filtered to only show publications from assigned publisher(s)
**And** filter is applied at the view/mixin level

**Given** Urednik attempts to access publication from different publisher
**When** direct URL is used
**Then** 403 Forbidden is returned

**Given** Administrator role
**When** accessing any content
**Then** no row-level filtering is applied (full access)

**Given** user's publisher assignment is changed
**When** change is saved
**Then** django-guardian permissions are updated accordingly

---

## Epic 3: Article Workflow

**Cilj:** Tim moze kreirati, pregledati i objaviti clanke kroz kompletan workflow

Ovaj epik implementira srz sistema - unos i upravljanje clancima sa kompletnim workflow-om. Bibliotekar unosi clanke sa auto-save funkcijom, ORCID validacijom i drag & drop reorderingom autora. Urednik pregledava i odobrava, administrator objavljuje. Dashboard prikazuje pending stavke.

### Story 3.1: Article Model & Basic Metadata Entry

As a **Bibliotekar**,
I want **to create a new article with basic metadata**,
So that **I can start entering article information for DOI registration**.

**Acceptance Criteria:**

**Given** the Article model is created
**When** reviewing the model structure
**Then** it includes fields: issue (FK), title, subtitle, abstract, keywords (ArrayField or JSON), doi_suffix, first_page, last_page, language, license, status, created_by (FK User), created_at, updated_at
**And** status is enum: DRAFT, REVIEW, READY, PUBLISHED, WITHDRAWN

**Given** a logged-in Bibliotekar
**When** navigating to an issue and clicking "Add Article"
**Then** article creation form is displayed
**And** issue is pre-selected from context
**And** publication hierarchy is shown in breadcrumbs

**Given** Bibliotekar enters article metadata
**When** filling in title, subtitle, abstract, keywords
**Then** form uses Bootstrap 5 styling
**And** abstract field is a textarea with character count
**And** keywords field allows multiple entries (tag input)

**Given** valid article data is submitted
**When** the form is processed
**Then** article is created with status DRAFT
**And** created_by is set to current user
**And** toast notification confirms creation
**And** user is redirected to article edit page for further details

---

### Story 3.2: Author Management with Drag & Drop

As a **Bibliotekar**,
I want **to add and reorder article authors with ORCID validation**,
So that **author information is complete and properly ordered for Crossref**.

**Acceptance Criteria:**

**Given** Article has an Author model/relationship
**When** reviewing the structure
**Then** Author includes: given_name, family_name, affiliation, orcid (optional), email (optional), is_corresponding (boolean), order (integer)
**And** Author is related to Article via ForeignKey or through model

**Given** Bibliotekar is editing an article
**When** viewing the Authors section
**Then** existing authors are listed in order
**And** each author shows: name, affiliation, ORCID (if set), corresponding badge

**Given** Bibliotekar clicks "Add Author"
**When** author form appears
**Then** fields are shown: given_name, family_name, affiliation, orcid, email, is_corresponding checkbox
**And** form uses Alpine.js for inline editing

**Given** Bibliotekar enters an ORCID
**When** ORCID field loses focus
**Then** ORCID format is validated (####-####-####-####X)
**And** validation indicator shows check (green) or X (red)
**And** HTMX calls validation endpoint for real-time feedback

**Given** multiple authors exist
**When** Bibliotekar drags an author to new position
**Then** Alpine.js handles drag & drop reordering
**And** order field is updated automatically
**And** change is saved via HTMX

**Given** Bibliotekar removes an author
**When** clicking remove button
**Then** confirmation is requested
**And** author is removed from article
**And** remaining authors are re-ordered

---

### Story 3.3: PDF Upload with Virus Scanning

As a **Bibliotekar**,
I want **to upload a PDF file for the article**,
So that **visitors can download the full-text article**.

**Acceptance Criteria:**

**Given** Bibliotekar is editing an article
**When** viewing the PDF upload section
**Then** current PDF status is shown (none, uploading, scanning, clean, infected)
**And** upload button/dropzone is displayed

**Given** Bibliotekar selects a PDF file
**When** file is under 100MB and is a valid PDF
**Then** upload progress bar is shown
**And** file is uploaded to temporary storage

**Given** PDF upload completes
**When** file is in temporary storage
**Then** Celery task is triggered for ClamAV virus scan
**And** UI shows "Scanning for viruses..." indicator

**Given** virus scan completes successfully (clean)
**When** no threats are detected
**Then** file is moved to S3 permanent storage
**And** Article.pdf_file field is updated
**And** UI shows "PDF uploaded successfully" with file info

**Given** virus scan detects threat
**When** file is infected
**Then** file is deleted from temporary storage
**And** user is notified: "File rejected: security threat detected"
**And** incident is logged

**Given** Bibliotekar wants to replace PDF
**When** uploading new file
**Then** old file is marked for deletion after new scan passes
**And** article maintains continuous PDF availability during replacement

---

### Story 3.4: Auto-Save Functionality

As a **Bibliotekar**,
I want **my changes to be automatically saved**,
So that **I never lose my work even if I forget to click save**.

**Acceptance Criteria:**

**Given** Bibliotekar is editing an article
**When** any field value changes
**Then** auto-save is triggered after 2 second debounce
**And** HTMX sends partial form data to auto-save endpoint

**Given** auto-save is in progress
**When** request is sent
**Then** save indicator shows "Saving..." with spinner

**Given** auto-save completes successfully
**When** server responds with success
**Then** indicator shows "Saved X seconds ago"
**And** timestamp updates every minute

**Given** auto-save fails
**When** server returns error
**Then** indicator shows "Save failed - retrying..."
**And** retry is attempted after 5 seconds
**And** after 3 failures, user is alerted

**Given** Bibliotekar leaves the page with unsaved changes
**When** navigating away
**Then** browser shows confirmation dialog (if changes pending)

**Given** Bibliotekar returns to a draft article
**When** opening the edit page
**Then** all previously saved data is loaded
**And** last saved timestamp is displayed

---

### Story 3.5: Submit Article for Review

As a **Bibliotekar**,
I want **to submit my completed article for editorial review**,
So that **an Urednik can verify the content before publication**.

**Acceptance Criteria:**

**Given** Bibliotekar has completed article entry
**When** viewing article in DRAFT status
**Then** "Submit for Review" button is displayed

**Given** article has required fields filled
**When** Bibliotekar clicks "Submit for Review"
**Then** validation checks: title, abstract, at least one author, PDF uploaded
**And** if validation fails, missing fields are highlighted

**Given** validation passes
**When** submit is confirmed
**Then** article status changes to REVIEW
**And** toast notification: "Article submitted for review"
**And** Bibliotekar can no longer edit (read-only view)

**Given** article is in REVIEW status
**When** Bibliotekar views the article
**Then** status badge shows "In Review"
**And** message indicates "Waiting for editorial approval"

---

### Story 3.6: Editorial Review Process

As an **Urednik (Editor)**,
I want **to review submitted articles and approve or return them**,
So that **only quality content is published**.

**Acceptance Criteria:**

**Given** a logged-in Urednik
**When** viewing dashboard or articles list
**Then** articles with status REVIEW are highlighted/filtered
**And** count of pending reviews is shown

**Given** Urednik opens an article in REVIEW status
**When** viewing article details
**Then** all metadata, authors, and PDF are displayed
**And** review action buttons are shown: "Approve" and "Return for Revision"

**Given** Urednik clicks "Approve"
**When** confirmation is given
**Then** article status changes to READY
**And** toast notification: "Article approved"
**And** Bibliotekar can see updated status

**Given** Urednik clicks "Return for Revision"
**When** providing feedback comment
**Then** article status changes back to DRAFT
**And** revision comment is stored and visible to Bibliotekar
**And** Bibliotekar can edit and resubmit

**Given** article is in READY status
**When** Urednik views the article
**Then** status badge shows "Ready to Publish"
**And** no further editorial actions available (Admin takes over)

---

### Story 3.7: Article Publishing & Withdrawal

As an **Administrator**,
I want **to publish and withdraw articles**,
So that **content lifecycle is properly managed**.

**Acceptance Criteria:**

**Given** a logged-in Administrator
**When** viewing articles with status READY
**Then** "Publish" action is available

**Given** Administrator clicks "Publish" on READY article
**When** action is confirmed
**Then** article status changes to PUBLISHED
**And** article becomes visible on public portal
**And** publication timestamp is recorded
**And** toast notification: "Article published"

**Given** article is PUBLISHED
**When** Administrator views the article
**Then** "Withdraw" action is available
**And** warning indicates withdrawal implications

**Given** Administrator clicks "Withdraw"
**When** providing withdrawal reason
**Then** article status changes to WITHDRAWN
**And** withdrawal reason and date are stored
**And** article remains visible on public portal with "WITHDRAWN" badge
**And** PDF may be removed or retained (configurable)

**Given** visitor views a withdrawn article
**When** accessing the landing page
**Then** "WITHDRAWN" banner is prominently displayed
**And** withdrawal date and reason are shown
**And** metadata remains visible

---

### Story 3.8: Dashboard Statistics & Pending Items

As an **Administrator**,
I want **to see dashboard statistics and pending items**,
So that **I can monitor system activity and act on pending tasks**.

**Acceptance Criteria:**

**Given** a logged-in Administrator
**When** viewing the dashboard
**Then** statistics cards show:
  - Total publications count
  - Total articles count
  - Articles pending review count
  - Articles ready to publish count

**Given** dashboard displays pending review section
**When** articles are in REVIEW status
**Then** list shows recent pending articles (max 10)
**And** each item shows: title, publication, submitted date, submitter
**And** click navigates to article review page

**Given** dashboard displays ready to publish section
**When** articles are in READY status
**Then** list shows articles awaiting publication
**And** quick "Publish" action is available inline

**Given** user has role Urednik
**When** viewing dashboard
**Then** only pending reviews for their assigned publishers are shown
**And** statistics are scoped to their publishers

**Given** user has role Bibliotekar
**When** viewing dashboard
**Then** "My Drafts" section shows their draft articles
**And** statistics show only their own article counts

---

## Epic 4: Public Portal Experience

**Cilj:** Posetioci mogu otkriti sadrzaj i pristupiti clancima preko DOI linkova

Ovaj epik kreira javno lice portala. Landing stranica clanka je definisuce iskustvo - posetilac dolazi sa DOI linka i za 3 sekunde ima pristup metapodacima i PDF-u. Portal ukljucuje pretragu, filtere, citiranje u vise formata i kontakt formu.

### Story 4.1: Portal Home Page

As a **visitor**,
I want **to see an attractive home page with portal overview**,
So that **I can understand what the portal offers and start browsing**.

**Acceptance Criteria:**

**Given** visitor navigates to the portal root URL
**When** the home page loads
**Then** page loads within 3 seconds (FCP target)
**And** Bootstrap 5 public template is used with doi.rs branding

**Given** home page content is displayed
**When** viewing the page
**Then** hero section shows portal name and search bar
**And** featured/recent publications section is displayed
**And** statistics are shown (total publications, articles, publishers)
**And** quick links to major sections are visible

**Given** visitor uses the hero search bar
**When** entering a search term
**Then** user is redirected to search results page

**Given** visitor is on mobile device
**When** viewing the home page
**Then** responsive layout adapts properly
**And** navigation collapses to hamburger menu
**And** touch targets are at least 44px

---

### Story 4.2: Article Search Functionality

As a **visitor**,
I want **to search for articles by title, author, or keywords**,
So that **I can find specific content I'm looking for**.

**Acceptance Criteria:**

**Given** visitor navigates to search or uses search bar
**When** entering a search query
**Then** search accepts minimum 3 characters
**And** search is debounced (300ms delay)

**Given** search query is submitted
**When** results are processed
**Then** articles are searched by: title, author names, keywords, abstract
**And** results load within 2 seconds (NFR5)

**Given** search results are displayed
**When** viewing the results page
**Then** results show as article cards with: title, authors, publication, year
**And** search term is highlighted in results
**And** result count is displayed

**Given** no results are found
**When** viewing empty results
**Then** helpful message is shown: "No articles found for '{query}'"
**And** suggestions are offered (check spelling, try different keywords)

**Given** many results exist
**When** scrolling through results
**Then** pagination is displayed (20 results per page)
**And** current page and total pages are shown

**Given** visitor clicks on a search result
**When** navigating to article
**Then** article landing page is opened

---

### Story 4.3: Advanced Filtering for Articles

As a **visitor**,
I want **to filter articles by various criteria**,
So that **I can narrow down results to exactly what I need**.

**Acceptance Criteria:**

**Given** visitor is on search results or article listing page
**When** viewing the filter sidebar
**Then** filters are displayed in collapsible sections:
  - Publication type (journal, conference, book)
  - Subject area
  - Language
  - Access type (open, restricted)
  - Year range

**Given** visitor selects filter options
**When** applying filters
**Then** HTMX updates results without full page reload
**And** selected filters appear as tags above results
**And** URL parameters are updated for shareable links

**Given** multiple filters are selected
**When** viewing results
**Then** filters are combined with AND logic
**And** result count updates to reflect filtered set

**Given** visitor clicks "Clear all filters"
**When** action is performed
**Then** all filters are reset
**And** full result set is displayed

**Given** visitor is on mobile
**When** viewing filters
**Then** filter sidebar is collapsible overlay
**And** "Apply Filters" button closes overlay and shows results

---

### Story 4.4: Article Landing Page (Defining Experience)

As a **visitor arriving via DOI link**,
I want **to see article details and access the PDF immediately**,
So that **I get what I need within 3 seconds**.

**Acceptance Criteria:**

**Given** visitor navigates to article landing page via DOI or direct link
**When** the page loads
**Then** First Contentful Paint is under 3 seconds
**And** page uses Clean Academic design style

**Given** article landing page is displayed
**When** viewing the layout
**Then** two-column layout on desktop: main content (2/3) + sidebar (1/3)
**And** breadcrumbs show: Home > Publications > {Publication} > {Issue} > {Article}

**Given** main content area is displayed
**When** viewing article details
**Then** title and subtitle are prominently displayed (H1)
**And** authors are listed with affiliations and ORCID links
**And** abstract is displayed in full
**And** keywords are shown as tags
**And** article metadata: DOI, pages, language, license

**Given** sidebar is displayed
**When** viewing sidebar content
**Then** publication info card shows: cover, title, volume/issue
**And** publisher info with logo
**And** article metrics (if available)

**Given** article is WITHDRAWN
**When** viewing the page
**Then** prominent "WITHDRAWN" banner is displayed at top
**And** withdrawal date and reason are shown
**And** metadata remains visible

---

### Story 4.5: Floating Action Bar

As a **visitor**,
I want **quick access to PDF, citation, and sharing options**,
So that **I can take action without scrolling**.

**Acceptance Criteria:**

**Given** visitor is on article landing page
**When** viewing the page
**Then** floating action bar is displayed
**And** on desktop: fixed position on right side
**And** on mobile: fixed position at bottom

**Given** floating action bar contains
**When** viewing available actions
**Then** PDF download button is prominent (primary style)
**And** Cite button opens citation modal
**And** Share button shows share options
**And** Copy DOI button copies DOI to clipboard

**Given** article has no PDF (withdrawn or not uploaded)
**When** viewing PDF button
**Then** button is disabled with tooltip explanation

**Given** visitor clicks Share
**When** share options appear
**Then** options include: Copy link, Email, Twitter/X, LinkedIn
**And** native share sheet is used on mobile (if available)

**Given** visitor scrolls the page
**When** floating bar position changes
**Then** bar remains visible and accessible
**And** does not obstruct content

---

### Story 4.6: PDF Download

As a **visitor**,
I want **to download the article PDF with one click**,
So that **I can read the full article offline**.

**Acceptance Criteria:**

**Given** visitor clicks PDF download button
**When** PDF is available
**Then** download starts immediately (no intermediate page)
**And** file is served from S3 with signed URL
**And** filename is descriptive: "{doi-suffix}_{title-slug}.pdf"

**Given** PDF download is initiated
**When** file is large
**Then** browser shows download progress
**And** no server-side processing delays the download

**Given** article is open access
**When** downloading PDF
**Then** no login or registration is required

**Given** article is withdrawn but PDF retained
**When** attempting download
**Then** PDF may be available or restricted based on configuration
**And** appropriate message is shown if restricted

**Given** visitor is on mobile
**When** downloading PDF
**Then** PDF opens in browser or downloads based on device settings
**And** experience is seamless

---

### Story 4.7: Citation Modal

As a **visitor**,
I want **to get properly formatted citations in multiple styles**,
So that **I can cite the article in my research**.

**Acceptance Criteria:**

**Given** visitor clicks "Cite" button
**When** citation modal opens
**Then** Bootstrap 5 modal is displayed
**And** article title is shown as modal header

**Given** citation modal is open
**When** viewing available formats
**Then** tabs or buttons show: APA, MLA, Chicago, BibTeX, RIS
**And** default format is APA

**Given** visitor selects a citation format
**When** format is applied
**Then** properly formatted citation is displayed
**And** citation includes: authors, title, publication, year, volume, issue, pages, DOI

**Given** citation is displayed
**When** visitor clicks "Copy to Clipboard"
**Then** citation text is copied
**And** toast notification confirms: "Citation copied!"

**Given** BibTeX or RIS format is selected
**When** viewing the citation
**Then** code-formatted text is displayed
**And** "Download" option is available for .bib or .ris file

**Given** visitor closes modal
**When** clicking X or outside modal
**Then** modal closes smoothly
**And** page state is preserved

---

### Story 4.8: About Page

As a **visitor**,
I want **to learn about the portal and its purpose**,
So that **I understand the context and credibility of the content**.

**Acceptance Criteria:**

**Given** visitor navigates to /about/
**When** the page loads
**Then** About page is displayed with portal information

**Given** About page content is shown
**When** viewing the page
**Then** portal mission/purpose is explained
**And** organization information is provided
**And** contact information is visible
**And** links to policies (if any) are available

**Given** About page uses public template
**When** viewing the layout
**Then** consistent navigation and footer are present
**And** breadcrumbs show: Home > About

---

### Story 4.9: Contact Form

As a **visitor**,
I want **to send a message to the portal administrators**,
So that **I can ask questions or report issues**.

**Acceptance Criteria:**

**Given** visitor navigates to /contact/
**When** the page loads
**Then** contact form is displayed
**And** form includes: name, email, subject, message fields
**And** all fields are required

**Given** visitor fills out the contact form
**When** submitting valid data
**Then** form is validated (email format, required fields)
**And** CAPTCHA or honeypot prevents spam (simple implementation)

**Given** form submission is successful
**When** message is processed
**Then** email is sent to configured admin address via SMTP
**And** email includes all form data and sender info
**And** success message is shown: "Thank you! We'll respond soon."

**Given** form submission fails
**When** validation errors occur
**Then** inline error messages are shown
**And** form data is preserved

**Given** email sending fails
**When** SMTP error occurs
**Then** user-friendly error is shown
**And** error is logged for admin review

---

## Epic 5: Crossref XML Integration

**Cilj:** Administratori mogu generisati validan Crossref XML za DOI registraciju, sa podrskom za sve tipove publikacija (casopis, zbornik, monografija) i njihove specificne XML strukture prema Crossref semi 5.4.0

Ovaj epik implementira kljucni diferencirajuci faktor portala - automatsko generisanje validnog Crossref XML-a. Sistem podrzava tri razlicite XML strukture prema tipu publikacije, validira prema odgovarajucoj XSD semi i upozorava na nedostajuca obavezna polja pre generisanja.

### Story 5.1: Crossref Service Infrastructure

As a **developer**,
I want **a Crossref service layer with XML templates for each publication type**,
So that **XML generation is properly structured and maintainable**.

**Acceptance Criteria:**

**Given** crossref Django app is created
**When** reviewing the structure
**Then** app contains: services.py, validators.py, tasks.py, templates/ directory

**Given** Jinja2 templates are created
**When** reviewing template files
**Then** three templates exist:
  - `crossref/templates/crossref/journal_article.xml.j2`
  - `crossref/templates/crossref/conference_paper.xml.j2`
  - `crossref/templates/crossref/book_chapter.xml.j2`

**Given** journal_article.xml.j2 template
**When** reviewing structure
**Then** template follows Crossref schema with `<journal>` container
**And** includes `<journal_metadata>`, `<journal_issue>`, `<journal_article>` elements
**And** ISSN is properly placed

**Given** conference_paper.xml.j2 template
**When** reviewing structure
**Then** template follows Crossref schema with `<conference>` container
**And** includes `<event_metadata>`, `<proceedings_metadata>`, `<conference_paper>` elements

**Given** book_chapter.xml.j2 template
**When** reviewing structure
**Then** template follows Crossref schema with `<book>` container
**And** includes `<book_metadata>`, `<content_item>` elements
**And** ISBN/NOISBN is properly handled

**Given** CrossrefService class exists
**When** reviewing the interface
**Then** methods include: generate_xml(issue), validate_xml(xml_string), get_required_fields(publication_type)

---

### Story 5.2: Pre-Generation Validation & Warnings

As an **Administrator**,
I want **to see warnings about missing or invalid data before generating XML**,
So that **I can fix issues before attempting Crossref submission**.

**Acceptance Criteria:**

**Given** Administrator navigates to Crossref section for an issue
**When** viewing the issue's Crossref status
**Then** pre-validation is automatically run
**And** results are displayed in a validation panel

**Given** pre-validation runs for a journal issue
**When** checking required fields
**Then** system validates:
  - Publication has ISSN (print or online)
  - All articles have: title, at least one author, DOI suffix
  - All authors have: given_name, family_name
  - Publication date is set

**Given** pre-validation runs for a conference proceedings
**When** checking required fields
**Then** additional validation for:
  - Conference name is set
  - Conference date/location present
  - Proceedings title exists

**Given** pre-validation runs for a book/monograph
**When** checking required fields
**Then** additional validation for:
  - ISBN is set OR NOISBN reason provided
  - Book title exists

**Given** validation issues are found
**When** displaying results
**Then** issues are categorized: Errors (blocking) vs Warnings (non-blocking)
**And** each issue links to the affected article/field for quick fixing
**And** error count is prominently displayed

**Given** no validation issues exist
**When** viewing validation panel
**Then** green checkmark and "Ready for XML generation" message is shown

---

### Story 5.3: XML Generation for All Publication Types

As an **Administrator**,
I want **to generate Crossref XML for any type of publication issue**,
So that **I can register DOIs with Crossref**.

**Acceptance Criteria:**

**Given** Administrator is on issue Crossref page with no blocking errors
**When** clicking "Generate XML"
**Then** appropriate template is selected based on publication type

**Given** publication type is JOURNAL
**When** XML is generated
**Then** `<journal>` structure is used
**And** `<journal_metadata>` contains publication title, ISSN
**And** `<journal_issue>` contains volume, issue, publication_date
**And** each article is wrapped in `<journal_article>`

**Given** publication type is CONFERENCE
**When** XML is generated
**Then** `<conference>` structure is used
**And** `<event_metadata>` contains conference name, dates, location
**And** `<proceedings_metadata>` contains proceedings title
**And** each article is wrapped in `<conference_paper>`

**Given** publication type is BOOK
**When** XML is generated
**Then** `<book>` structure is used
**And** `<book_metadata>` contains title, ISBN
**And** each article/chapter is wrapped in `<content_item>`

**Given** issue has many articles (>20)
**When** generating XML
**Then** Celery task handles generation asynchronously
**And** progress indicator is shown
**And** user is notified when complete

**Given** XML generation completes
**When** viewing results
**Then** success message is displayed
**And** XML is stored for preview and download
**And** generation timestamp is recorded

---

### Story 5.4: XSD Validation

As an **Administrator**,
I want **generated XML to be validated against Crossref XSD schema**,
So that **I'm confident the XML will be accepted by Crossref**.

**Acceptance Criteria:**

**Given** XML has been generated
**When** validation runs automatically
**Then** lxml.etree.XMLSchema is used for validation
**And** Crossref schema 5.4.0 XSD files are used

**Given** XML passes XSD validation
**When** viewing validation results
**Then** green checkmark and "XML is valid" message is shown
**And** validation timestamp is displayed

**Given** XML fails XSD validation
**When** viewing validation results
**Then** specific XSD errors are displayed
**And** errors indicate line numbers and elements
**And** "Invalid XML - cannot be submitted to Crossref" warning is shown

**Given** XSD schema files
**When** system initializes
**Then** schema files are bundled with the application
**And** schema version is documented (5.4.0)

**Given** validation takes time for large files
**When** validation is in progress
**Then** spinner indicates "Validating against Crossref schema..."

---

### Story 5.5: XML Preview with Syntax Highlighting

As an **Administrator**,
I want **to preview the generated XML with syntax highlighting**,
So that **I can review the content before downloading**.

**Acceptance Criteria:**

**Given** XML has been generated
**When** clicking "Preview XML"
**Then** modal or panel opens with XML content displayed

**Given** XML preview is displayed
**When** viewing the content
**Then** XML is syntax highlighted (tags, attributes, values in different colors)
**And** line numbers are shown
**And** content is scrollable for large files

**Given** XML preview is shown
**When** reviewing content
**Then** key sections are collapsible/expandable
**And** search within preview is available (Ctrl+F)

**Given** preview modal/panel
**When** viewing actions
**Then** "Copy to Clipboard" button is available
**And** "Download XML" button is available
**And** "Close" button returns to Crossref page

**Given** XML is invalid
**When** previewing
**Then** validation errors are highlighted in context
**And** error lines are marked with red indicator

---

### Story 5.6: XML Download

As an **Administrator**,
I want **to download the generated XML file**,
So that **I can upload it to Crossref manually**.

**Acceptance Criteria:**

**Given** valid XML has been generated
**When** clicking "Download XML"
**Then** XML file is downloaded
**And** filename format: `{publication-slug}_{volume}_{issue}_{timestamp}.xml`

**Given** XML download is initiated
**When** file is generated
**Then** proper XML declaration is included
**And** UTF-8 encoding is used
**And** file is well-formed

**Given** Administrator downloads XML
**When** file is saved
**Then** file can be directly uploaded to Crossref admin portal
**And** no modifications are needed

**Given** download is requested for invalid XML
**When** validation has failed
**Then** warning dialog appears: "XML has validation errors. Download anyway?"
**And** user can choose to proceed or cancel

**Given** issue has been previously exported
**When** viewing Crossref page
**Then** export history is shown with timestamps
**And** previous exports can be re-downloaded

---

### Story 5.7: Crossref Deposit Workflow Page

As an **Administrator**,
I want **a dedicated Crossref Deposit page to manage the entire process**,
So that **I have a clear workflow for DOI registration**.

**Acceptance Criteria:**

**Given** Administrator navigates to an issue
**When** clicking "Crossref Deposit" tab/button
**Then** dedicated Crossref workflow page is displayed

**Given** Crossref Deposit page is displayed
**When** viewing the layout
**Then** workflow steps are clearly shown:
  1. Pre-validation status
  2. Generate XML button
  3. XSD Validation status
  4. Preview XML
  5. Download XML

**Given** workflow page shows current status
**When** each step is checked
**Then** completed steps show green checkmarks
**And** current step is highlighted
**And** blocked steps are grayed out

**Given** all steps are complete
**When** viewing final status
**Then** "Ready for Crossref Submission" message is shown
**And** link to Crossref admin portal is provided
**And** instructions for manual upload are displayed

**Given** Administrator completes external upload
**When** returning to the page
**Then** "Mark as Deposited" button is available
**And** clicking marks the issue as deposited with timestamp
**And** deposited status is shown on issue list

---

## Epic 6: Compliance & Monitoring

**Cilj:** Superadmin moze osigurati uskladjenost sistema i pratiti sve aktivnosti

Ovaj epik zavrsava sistem sa kompletnim audit logom i GDPR uskladjenoscu. Superadmin moze pregledati sve akcije (ko, sta, kada, IP), obraditi zahteve za brisanje podataka i pratiti sistemske statistike.

### Story 6.1: Audit Log Integration

As a **system**,
I want **to automatically log all content changes**,
So that **there is a complete audit trail for compliance**.

**Acceptance Criteria:**

**Given** django-auditlog is installed
**When** configuring the package
**Then** auditlog is added to INSTALLED_APPS
**And** AuditlogMiddleware is configured

**Given** models need audit logging
**When** registering models with auditlog
**Then** following models are registered: Publisher, Publication, Issue, Article, Author, User

**Given** a registered model instance is created
**When** the create operation completes
**Then** LogEntry is created with action=CREATE
**And** LogEntry contains: actor (user), timestamp, model, object_id, changes (JSON)

**Given** a registered model instance is updated
**When** the update operation completes
**Then** LogEntry is created with action=UPDATE
**And** changes field shows old and new values for modified fields

**Given** a registered model instance is deleted
**When** the delete operation completes
**Then** LogEntry is created with action=DELETE
**And** object representation is preserved in log

**Given** action is performed by anonymous user (system)
**When** no user context exists
**Then** actor is recorded as "System" or null
**And** IP address is still recorded if available

**Given** audit logs exist
**When** checking retention
**Then** logs are retained for minimum 1 year (365 days)
**And** older logs may be archived but not deleted

---

### Story 6.2: Audit Log Viewer

As a **Superadmin**,
I want **to view and search the audit log**,
So that **I can investigate changes and track user activity**.

**Acceptance Criteria:**

**Given** a logged-in Superadmin
**When** navigating to System > Audit Log
**Then** audit log viewer page is displayed
**And** recent log entries are shown in reverse chronological order

**Given** audit log list is displayed
**When** viewing each entry
**Then** entry shows: timestamp, actor (user), action, model, object representation
**And** entries are paginated (50 per page)

**Given** filter options are available
**When** using filters
**Then** logs can be filtered by:
  - Date range (from/to)
  - User (actor)
  - Action type (create/update/delete)
  - Model type (Publisher, Article, etc.)
  - Object ID

**Given** Superadmin clicks on a log entry
**When** detail view opens
**Then** full change details are shown
**And** for updates: old values vs new values are displayed side by side
**And** JSON changes are formatted for readability

**Given** Superadmin searches audit log
**When** entering search term
**Then** logs are searched by object representation and actor name

**Given** non-Superadmin user
**When** attempting to access Audit Log
**Then** access is denied with 403 Forbidden

---

### Story 6.3: Soft Delete Implementation

As a **system**,
I want **to implement soft delete for all content**,
So that **data can be recovered and GDPR deletion can be reversible during grace period**.

**Acceptance Criteria:**

**Given** models need soft delete
**When** implementing soft delete mixin
**Then** SoftDeleteMixin adds: is_deleted (boolean), deleted_at (datetime), deleted_by (FK User)

**Given** SoftDeleteMixin is applied
**When** reviewing affected models
**Then** Publisher, Publication, Issue, Article, Author models have soft delete

**Given** delete() is called on a soft-delete model
**When** default delete is invoked
**Then** is_deleted is set to True
**And** deleted_at is set to current timestamp
**And** deleted_by is set to current user
**And** record is NOT removed from database

**Given** model manager is configured
**When** querying models
**Then** default queryset excludes soft-deleted records
**And** .all_with_deleted() returns all records
**And** .deleted_only() returns only deleted records

**Given** Superadmin views deleted items
**When** navigating to "Deleted Items" section
**Then** list of soft-deleted records is shown
**And** option to restore or permanently delete exists

**Given** soft-deleted item is restored
**When** restore action is performed
**Then** is_deleted is set to False
**And** deleted_at and deleted_by are cleared
**And** item appears in normal queries again

---

### Story 6.4: GDPR Data Request Handling

As a **Superadmin**,
I want **to process GDPR data deletion requests**,
So that **the portal complies with privacy regulations**.

**Acceptance Criteria:**

**Given** Superadmin navigates to System > GDPR Requests
**When** the page loads
**Then** list of data requests is shown (if any)
**And** "New Request" button is available

**Given** Superadmin creates new GDPR request
**When** entering request details
**Then** form includes: requester email, request type (access/deletion), notes, received date

**Given** GDPR deletion request is created
**When** request is saved
**Then** request status is set to PENDING
**And** related data is identified (user account, authored articles)

**Given** Superadmin reviews deletion request
**When** viewing request details
**Then** affected data is listed:
  - User account (if exists)
  - Articles where person is author
  - Audit log entries involving the user

**Given** Superadmin processes deletion
**When** approving the request
**Then** user account is anonymized (email replaced with hash, name cleared)
**And** author entries are anonymized or marked
**And** audit log entries are retained but actor anonymized
**And** request status changes to COMPLETED
**And** completion timestamp is recorded

**Given** deletion has grace period
**When** processing request
**Then** data is first soft-deleted
**And** permanent deletion occurs after 30-day grace period
**And** requester can cancel during grace period

**Given** GDPR request is completed
**When** generating confirmation
**Then** confirmation report is available for download
**And** report documents what data was affected

---

### Story 6.5: System Monitoring with Sentry

As a **system administrator**,
I want **error tracking and performance monitoring**,
So that **issues are detected and resolved quickly**.

**Acceptance Criteria:**

**Given** Sentry SDK is installed
**When** configuring Sentry
**Then** SENTRY_DSN is configured via environment variable
**And** Sentry is initialized in Django settings

**Given** unhandled exception occurs
**When** error is raised
**Then** error is automatically sent to Sentry
**And** error includes: stack trace, request data, user context

**Given** error is sent to Sentry
**When** viewing in Sentry dashboard
**Then** error shows: environment (local/staging/production), release version
**And** errors are grouped by type

**Given** performance monitoring is enabled
**When** requests are processed
**Then** transaction traces are sent to Sentry
**And** slow queries and requests are identified

**Given** sensitive data protection
**When** errors are captured
**Then** passwords are scrubbed
**And** personally identifiable information is masked
**And** request body with sensitive fields is filtered

**Given** Celery tasks are running
**When** task errors occur
**Then** errors are captured with task context
**And** task name and arguments are included

---

### Story 6.6: System Health Dashboard

As a **Superadmin**,
I want **to see system health and statistics at a glance**,
So that **I can monitor the overall system status**.

**Acceptance Criteria:**

**Given** Superadmin navigates to System > Health
**When** the page loads
**Then** system health dashboard is displayed

**Given** health dashboard is displayed
**When** viewing statistics
**Then** following metrics are shown:
  - Total users (active/inactive)
  - Total content (publishers, publications, issues, articles)
  - Articles by status (draft, review, ready, published, withdrawn)
  - Recent audit log activity (24h)

**Given** health dashboard shows system status
**When** checking integrations
**Then** status indicators show:
  - Database connection: OK/Error
  - Redis connection: OK/Error
  - Celery workers: Running/Stopped
  - S3 storage: Accessible/Error

**Given** health check fails
**When** a component is unavailable
**Then** red indicator is shown with error details
**And** recommendation for resolution is provided

**Given** dashboard data
**When** refreshing the page
**Then** data is current (cached for max 1 minute)
**And** last update timestamp is shown

---

## Summary

| Epic | Name | Stories | FRs Covered |
|------|------|---------|-------------|
| 1 | Project Foundation & Authentication | 7 | FR1-FR7 |
| 2 | Content Structure Management | 9* | FR8-FR21 |
| 3 | Article Workflow | 8 | FR22-FR32, FR46-FR47 |
| 4 | Public Portal Experience | 9 | FR38-FR45 |
| 5 | Crossref XML Integration | 7 | FR33-FR37 |
| 6 | Compliance & Monitoring | 6 | FR48-FR50 |
| **TOTAL** | | **46 stories** | **50 FRs** |

*\* Epic 2 includes Story 2.3a (patch story added after PRD revision 1.1 for Crossref compliance)*

---

*Document generated: 2026-01-25*
*Updated: 2026-01-27 (PRD revision 1.1 - Story 2.3a added)*
*Epics and Stories Workflow Complete*
