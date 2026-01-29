---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
inputDocuments:
  - 'DOI - Portal.md'
documentCounts:
  briefs: 0
  research: 0
  brainstorming: 0
  projectDocs: 1
workflowType: 'prd'
projectType: 'greenfield'
classification:
  projectType: web_app
  domain: scientific
  complexity: medium-high
  projectContext: greenfield
  architecture: MPA
  offline: false
  realtime: false
  seo: false
techStack:
  language: Python 3.13
  framework: Django 5.2+
  taskQueue: Celery
  cache: Redis
  database: MySQL
  containerization: Docker
---

# Product Requirements Document - DOI

**Author:** Mihas
**Date:** 2026-01-24
**Last Updated:** 2026-01-27
**Revision:** 1.2 - Crossref Compliance Update (XML Head, Contributor fields, Affiliations, SiteSettings)

## Executive Summary

**Vizija:** DOI Portal je interni servisni alat koji omogucava izdavacima naucnih publikacija da jednostavno kreiraju landing stranice za clanke potrebne za DOI registraciju, bez tehnickog znanja.

**Diferencirajuci faktor:** Jedinstven fokus na Crossref XML uskladjenost sa automatskom validacijom - admin korisnici mogu samostalno generisati ispravne XML fajlove bez tehnicke podrske.

**Ciljni korisnici:**
- **Primarni:** Bibliotekari, urednici i administratori naucnih institucija
- **Sekundarni:** Istrazivaci i studenti koji pristupaju clancima putem DOI linkova

**Tip projekta:** Greenfield MPA web aplikacija
**Tech stack:** Python 3.13, Django 5.2+, MySQL, Redis, Celery, Docker

## Success Criteria

### User Success

**Za izdavace/administratore (primarni korisnici):**
- Mogu kreirati landing stranice za clanke bez tehnickog znanja
- Landing stranice ispunjavaju Crossref zahteve za DOI registraciju
- Draft/nacrt se automatski cuva - nema gubitka zapocetog rada
- Jasan workflow: unos → pregled → odobrenje → objava

**Za posetioce portala (sekundarni korisnici):**
- Mogu pristupiti metapodacima i preuzeti PDF
- Landing stranica jasno prikazuje sve potrebne informacije o clanku

### Business Success

- Ovo je **interni servisni alat**, ne komercijalni portal
- Uspeh = admin korisnici mogu samostalno raditi bez konfuzije
- 12-mesecni cilj: Stabilan sistem bez problema, bez dilema kod korisnika
- Kljucna metrika: Broj uspesno generisanih DOI landing stranica

### Technical Success

- Crossref XML generisanje radi ispravno za sve tipove publikacija
- GDPR uskladjenost implementirana
- RBAC sa 4 uloge funkcionise bez problema
- Audit log belezi sve akcije
- Sistem stabilan i bez gresaka

### Measurable Outcomes

| Metrika | Cilj |
|---------|------|
| Admin moze kreirati clanak | < 15 min za kompletan unos |
| XML validacija | 100% Crossref-kompatibilan output |
| Draft sacuvanje | Automatski, bez gubitka podataka |
| Sistem uptime | 99%+ |

## Product Scope

### MVP - Minimum Viable Product

**Sve iz specifikacije DOI - Portal.md:**
- Kompletan javni portal (pocetna, publikacije, izdavaci, o portalu, kontakt)
- Landing stranice za clanke
- Admin panel sa sve 4 uloge (Superadmin, Administrator, Urednik, Bibliotekar)
- CRUD za izdavace, publikacije, izdanja, clanke
- Crossref XML generisanje (bez API-ja za auto-deposit)
- GDPR compliance

### Growth Features (Post-MVP)

- HTML editor za unos celog teksta clanka
- Crossref API integracija za automatsko slanje XML-a
- **Funding informacije** - Unos podataka o finansiranju istrazivanja (funder_name, award_number, Open Funder Registry DOI)
- **Citation list** - Strukturirane reference za clanke
- **Crossmark integracija** - Pracenje ispravki i azuriranja clanaka

### Vision (Future)

- Auto-extract metapodataka iz PDF fajlova (AI/ML)
- Automatizacija kompletnog DOI workflow-a

## User Journeys

### Journey 1: Marija - Bibliotekar unosi novi clanak

**Persona:** Marija (35), diplomirala bibliotekarstvo, radi u naucnoj instituciji 8 godina. Osrednje informaticki pismena - koristi Word, Excel, email bez problema, ali se plasi "komplikovanih sistema".

**Motivacija:** Zeli napredovanje u zvanju. Bibliotekarstvo je konzervativna oblast - svaka nova vestina je prednost.

**Narativna putanja:**

*Ponedeljak, 9:15h* - Marija otvara email. Urednik casopisa salje joj PDF novog clanka sa molbom da ga unese u sistem za DOI.

*9:20h* - Loguje se na admin panel. Na dashboard-u vidi svoje prethodne draft-ove i nastavlja gde je stala prosle nedelje sa drugim clankom.

*9:25h* - Kreira novi clanak. Sistem je povezao publikaciju → izdanje automatski. Unosi naslov, autore (drag & drop redosled), ORCID-ove. Sistem validira ORCID format u realnom vremenu.

*9:40h* - Upload-uje PDF. Cuva kao draft. Sistem automatski cuva svaku izmenu.

*9:45h* - Klik na "Spremno za pregled". Clanak odlazi uredniku na proveru.

**Kritican momenat:** Marija mora da izadje na sastanak. Kad se vrati, njen rad je sacuvan - nista nije izgubljeno.

**Frustracija (koju izbegavamo):** Spor sistem, izgubljeni podaci, nejasna veza clanak-izdanje-publikacija.

---

### Journey 2: Dragan - Administrator odobrava i objavljuje

**Persona:** Dragan (42), administrator sistema, tehicki potkovan. Odgovoran za kvalitet podataka i Crossref uskladjenost.

**Narativna putanja:**

*Utorak, 8:00h* - Dragan otvara dashboard. Vidi: "23 clanka ceka odobrenje".

*8:05h* - Otvara prvi clanak. Pregleda:
- Metapodaci kompletni? ✓
- ORCID-ovi validni? ✓
- PDF ucloan? ✓
- Crossref obavezna polja popunjena? ✓

*8:10h* - Klik "Odobri". Clanak dobija status "Ready to publish".

*10:00h* - Zavrsio sa 23 clanka. Ide na "Crossref Deposit" stranicu. Selektuje sve odobrene, klik "Generisi XML".

*10:02h* - Pregleda XML preview. Sistem pokazuje upozorenja ako nesto fali. Sve ok.

*10:05h* - Preuzima XML fajl, upload-uje na Crossref portal (Growth: automatski API).

*10:15h* - Vraca se, oznacava clanke kao "Published". Landing stranice su sada javne.

**Kritican momenat:** XML mora biti 100% validan. Sistem MORA upozoriti pre slanja ako nesto nije u redu.

---

### Journey 3: Ana - Istrazivac trazi clanak

**Persona:** Ana (28), doktorand na PMF-u, istrazuje molekularnu biologiju.

**Narativna putanja:**

*Sreda, 14:00h* - Ana cita naucni rad. U referencama vidi DOI: `10.1234/example.2024.001`

*14:01h* - Klik na DOI link → otvara se landing stranica na portal.doi.rs

*14:02h* - Vidi: naslov, autore, apstrakt, kljucne reci. Brzo skenira - ovo je clanak koji trazi.

*14:03h* - Klik "Preuzmi PDF" → download zapocinje.

**Uspeh:** Ana je za 3 minuta dobila PDF koji joj treba. Nije morala da se registruje, placa, ili trazi po sajtu.

---

### Journey 4: Superadmin - Upravljanje sistemom

**Persona:** IT administrator, tehicki ekspert.

**Kratka putanja:**
- Kreira nove korisnike i dodeljuje uloge
- Pregleda audit log kad nesto "ne stima"
- Konfigurise Crossref kredencijale
- Prati sistemske logove i upozorenja

---

### Journey Requirements Summary

| Journey | Kljucne funkcionalnosti |
|---------|------------------------|
| Bibliotekar | Draft auto-save, ORCID validacija, jasna hijerarhija publikacija, jednostavan UI |
| Administrator | Bulk operacije, XML preview/validacija, dashboard sa pending stavkama, audit trail |
| Posetilac | Brza landing stranica, jasan PDF download, minimalan friction |
| Superadmin | User management, RBAC, audit logs, system config |

## Domain-Specific Requirements

### Crossref Compliance

**Verzija sheme:** Crossref XSD 5.4.0

- Svaki izdavac ima svoj **DOI prefix** (npr. `10.1234`) - mora se cuvati u izdavac CRUD-u
- XML generisanje prema aktuelnoj Crossref XSD shemi (5.4.0)
- Validacija XML-a pre download-a/slanja
- Obavezna Crossref polja moraju biti validirana pre objave

#### XML Head elementi (OBAVEZNO za svaki deposit)

Svaki XML fajl koji se salje Crossref-u MORA sadrzati `<head>` sekciju sa:

| Element | Opis | Izvor podataka |
|---------|------|----------------|
| `doi_batch_id` | Jedinstveni ID batch-a | Auto-generisan (UUID + timestamp) |
| `timestamp` | Vreme generisanja (YYYYMMDDHHmmss) | Auto-generisan |
| `depositor_name` | Naziv organizacije/osobe koja salje | SiteSettings.depositor_name |
| `email_address` | Email za Crossref submission log | SiteSettings.depositor_email |
| `registrant` | Naziv registranta | Publisher.name (iz veze Publication → Publisher) |

#### Podrzani tipovi sadrzaja

| Tip | XML kontejner | Crossref element |
|-----|---------------|------------------|
| Casopis | `<journal>` | `<journal_article>` |
| Zbornik | `<conference>` | `<conference_paper>` |
| Knjiga/Monografija | `<book>` | `<content_item>` |

#### Kontributor zahtevi (OBAVEZNO)

Za svakog autora/kontributora, Crossref zahteva:

| Polje | Obaveznost | Vrednosti |
|-------|------------|-----------|
| `sequence` | **OBAVEZNO** | `first` (prvi autor) ili `additional` (ostali) |
| `contributor_role` | **OBAVEZNO** | `author`, `editor`, `chair`, `translator`, `reviewer` |
| `surname` | **OBAVEZNO** | Prezime |
| `given_name` | Preporuceno | Ime |
| `ORCID` | Preporuceno | Format: `https://orcid.org/0000-0000-0000-0000` |
| `affiliations` | Preporuceno | Institucija, ROR ID, departman |

### GDPR & Privacy

- **Izdavac je odgovoran** za pristanak autora za prikaz podataka
- Portal samo prikazuje podatke koje izdavac dostavi
- Soft delete za sve podatke (mogucnost povratka)
- Audit log sa cuvanjem minimum 1 godina

### Content Lifecycle

- **Withdrawn clanaka:** Landing stranica ostaje javna sa oznakom "WITHDRAWN"
- Metapodaci ostaju vidljivi, PDF moze biti uklonjen
- Crossref mora biti obavesten o withdraw statusu (Growth feature)

### Technical Constraints

| Constraint | Vrednost |
|------------|----------|
| PDF Storage | Cloud (S3 ili slicno) |
| Virus Scan | Da, obavezno za sve upload-e |
| Max File Size | 100 MB |
| Backup | Dnevni, retencija 90+ dana |

### Data Model Update

#### Izdavac (Publisher) - polja

**Osnovna polja (implementirano):**
- `name` - Naziv izdavaca - **OBAVEZNO**
- `slug` - URL-friendly identifikator - auto-generisan
- `description` - Opis izdavaca
- `logo` - Logo (JPG, PNG, SVG, max 2MB)
- `contact_email`, `contact_phone`, `website` - Kontakt informacije
- `doi_prefix` - Crossref DOI prefix (npr. "10.1234") - **OBAVEZNO**, validiran regex `^10\.\d{4,}$`

**Growth polja (opciono, za API):**
- `crossref_username` - Crossref API username
- `crossref_password` - Crossref API password (enkriptovan)

---

#### Podešavanja portala (SiteSettings) - globalna polja

**Singleton model** - samo jedna instanca u bazi:

- `depositor_name` - Naziv organizacije koja šalje XML na Crossref - **OBAVEZNO za XML**
- `depositor_email` - Email za Crossref notifikacije o statusu deposit-a - **OBAVEZNO za XML**

**Napomena:** `registrant` se ne čuva kao posebno polje - dobija se iz `Publisher.name` pri generisanju XML-a.

---

#### Publikacija (Publication) - type-specific polja

**Zajednicka polja (svi tipovi):**
- `title`, `slug`, `description`, `cover_image`
- `publisher` (FK) - Povezana sa izdavacem
- `publication_type` - JOURNAL, CONFERENCE, BOOK, OTHER
- `language` - ISO 639-1 kod (default: 'sr')
- `subject_area`, `access_type` (OPEN, RESTRICTED)

**Casopis (Journal) polja:**
- `issn_print` - ISSN (Print), format ####-####
- `issn_online` - e-ISSN (Electronic)
- `abbreviation` - ISO skracenica casopisa
- `frequency` - Ucestalost izlazenja

**Zbornik (Conference) polja:**
- `conference_name` - Pun naziv konferencije - **OBAVEZNO za tip**
- `conference_acronym` - Skracenica (npr. "ICML2024")
- `conference_location` - Lokacija (npr. "Beograd, Srbija")
- `conference_date` - Datum pocetka konferencije
- `conference_date_end` - Datum zavrsetka konferencije - **NOVO**
- `conference_number` - Redni broj konferencije (npr. 5 za "5th") - **NOVO**
- `series_issn` - ISSN serije (ako je deo serije)

**Knjiga/Monografija (Book) polja:**
- `isbn_print` - ISBN (Print), ISBN-13 format
- `isbn_online` - ISBN (Electronic)
- `edition` - Izdanje (npr. "2nd edition")
- `series_title` - Naziv serije/kolekcije

---

#### Izdanje (Issue) - polja

**Osnovna polja:**
- `publication` (FK) - Povezano sa publikacijom
- `volume` - Volumen
- `issue_number` - Broj izdanja
- `year` - Godina izdanja - **OBAVEZNO**
- `publication_date` - Datum objavljivanja
- `cover_image` - Naslovna slika izdanja
- `status` - DRAFT, SCHEDULED, PUBLISHED, ARCHIVE

**Za Zbornik (proceedings_metadata) - specificna polja:**
- `proceedings_title` - Naslov zbornika (ako razlicit od publication.title)
- `proceedings_publisher_name` - Naziv izdavaca zbornika
- `proceedings_publisher_place` - Mesto izdavanja

---

#### Clanak (Article) - polja

**Osnovna polja:**
- `issue` (FK) - Povezan sa izdanjem
- `title` - Naslov clanka - **OBAVEZNO**
- `subtitle` - Podnaslov
- `abstract` - Apstrakt (plain text ili JATS format)
- `keywords` - Kljucne reci (ArrayField ili JSON)
- `doi_suffix` - Sufiks za DOI (pun DOI = publisher.doi_prefix + "/" + doi_suffix) - **OBAVEZNO**
- `first_page`, `last_page` - Stranice
- `article_number` - Za online-only clanke (umesto stranica)
- `language` - ISO 639-1 kod
- `publication_type` - `full_text`, `abstract_only`, `bibliographic_record` - **OBAVEZNO za Crossref**
- `pdf_file` - PDF fajl (S3 storage)
- `status` - DRAFT, REVIEW, READY, PUBLISHED, WITHDRAWN
- `created_by` (FK) - Ko je kreirao

**License/Access polja:**
- `license_url` - URL licence (npr. CC BY 4.0)
- `license_applies_to` - `vor` (Version of Record), `am` (Accepted Manuscript), `tdm` (Text Mining)
- `free_to_read` - Boolean, da li je Open Access
- `free_to_read_start_date` - Od kada je besplatno dostupan

---

#### Autor/Kontributor (Author) - polja

**Identifikacija:**
- `given_name` - Ime - Preporuceno
- `surname` - Prezime - **OBAVEZNO**
- `suffix` - Sufiks (Jr., III, itd.)
- `email` - Email adresa
- `orcid` - ORCID iD, format `0000-0000-0000-000X`, validiran
- `orcid_authenticated` - Boolean, da li je ORCID autentifikovan

**Crossref obavezna polja:**
- `sequence` - **OBAVEZNO**: `first` (prvi/corresponding) ili `additional` (ostali)
- `contributor_role` - **OBAVEZNO**: `author`, `editor`, `chair`, `translator`, `reviewer`

**Redosled i status:**
- `order` - Redni broj za sortiranje (drag & drop)
- `is_corresponding` - Boolean, da li je corresponding author
- `article` (FK) - Povezan sa clankom

---

#### Afilijacija (Affiliation) - polja

Posebna tabela za institucije autora (M2M sa Author):

- `author` (FK) - Povezana sa autorom
- `institution_name` - Naziv institucije - **OBAVEZNO**
- `institution_ror_id` - ROR ID (https://ror.org/...) - Preporuceno
- `department` - Departman/odeljenje
- `order` - Redosled afilijacija

---

#### Finansiranje (Funding) - Growth Feature

Posebna tabela za informacije o finansiranju istrazivanja:

- `article` (FK) - Povezano sa clankom
- `funder_name` - Naziv finansijera - **OBAVEZNO ako postoji**
- `funder_doi` - DOI iz Open Funder Registry (10.13039/...)
- `funder_ror_id` - ROR ID finansijera
- `award_number` - Broj projekta/granta
- `grant_doi` - Crossref Grant DOI (ako postoji)

## Web App Specific Requirements

### Project-Type Overview

**Tip:** MPA (Multi-Page Application) web portal
**Framework:** Django 5.2+ sa server-side renderingom
**Pristup:** Desktop-first responzivan dizajn

### Browser Support

| Browser | Podrska |
|---------|---------|
| Chrome | Poslednje 2 verzije |
| Firefox | Poslednje 2 verzije |
| Safari | Poslednje 2 verzije |
| Edge | Poslednje 2 verzije |
| IE11 | Ne podrzavamo |

### Responsive Design

- **Prioritet:** Desktop-first
- **Breakpoints:**
  - Desktop: > 1200px
  - Tablet: 768px - 1199px
  - Mobile: < 768px
- **Kriticne stranice za mobile:** Landing stranica clanka, pretraga

### Performance Targets

*Detaljne performance metrike - videti sekciju Non-Functional Requirements.*

### Accessibility

- **Nivo:** Standardna pristupacnost
- Semanticki HTML5 elementi
- Alt tekst za sve slike
- Dovoljan kontrast boja (4.5:1 minimum)
- Keyboard navigation za kljucne akcije
- Aria labels gde je potrebno

### Implementation Considerations

- Django templates sa HTMX za dinamicke delove (opciono)
- Static files: CSS/JS minifikacija, CDN za produkciju
- Image optimization: Thumbnails za naslovne strane, lazy loading
- Caching: Redis za sessions i cache, CDN za staticke resurse

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Pristup:** Problem-Solving MVP
- Resava konkretan problem: kreiranje DOI landing stranica za izdavace
- Sve funkcionalnosti iz specifikacije isporucuju se odjednom

**Tim:** 1 developer (full-stack)

### MVP Feature Set (Phase 1)

**Sve iz DOI - Portal.md specifikacije:**

| Modul | Funkcionalnosti |
|-------|-----------------|
| Javni portal | Pocetna, Publikacije, Izdavaci, O portalu, Kontakt |
| Landing stranice | Clanci sa metapodacima, PDF download |
| Admin - Korisnici | 4 uloge (Superadmin, Admin, Urednik, Bibliotekar) |
| Admin - Sadrzaj | CRUD: Izdavaci, Publikacije, Izdanja, Clanci |
| Admin - Workflow | Draft → Review → Publish |
| Crossref | XML generisanje (bez API-ja) |

### Post-MVP Features

**Phase 2 (Growth):**
- HTML editor za ceo tekst clanka
- Crossref API integracija (auto-deposit)

**Phase 3 (Vision):**
- Auto-extract metapodataka iz PDF fajlova (AI/ML)
- Kompletna automatizacija DOI workflow-a

### Risk Mitigation Strategy

| Rizik | Mitigacija |
|-------|------------|
| 1 developer | Fokus na Django best practices, reusable komponente, dobra dokumentacija |
| Bez Crossref test env | Validacija XML-a lokalno prema XSD shemi; rucno testiranje na Crossref staging pre go-live |
| Kompleksnost RBAC | Django permissions + django-guardian; poceti sa jednostavnim modelom |
| Obim posla | Striktno se drzati specifikacije, bez scope creep-a |

### Preporuke za 1 developera

1. Koristi Django Admin kao osnovu za admin panel
2. Prioritizuj: Clanci → Izdanja → Publikacije → Izdavaci (redom zavisnosti)
3. Unit testovi za Crossref XML generisanje (kriticno)
4. Docker + staging okruzenje od prvog dana

## Functional Requirements

### 1. User Management & Authentication

- **FR1:** ~~UKLONJEN~~ - Javna registracija nije potrebna (interni korisnici, Superadmin kreira naloge - videti FR4)
- **FR2:** Korisnik se moze prijaviti na sistem
- **FR3:** Korisnik moze resetovati zaboravljenu lozinku
- **FR4:** Superadmin moze kreirati nove korisnike
- **FR5:** Superadmin moze dodeliti/promeniti ulogu korisniku (Superadmin, Administrator, Urednik, Bibliotekar)
- **FR6:** Superadmin moze aktivirati/deaktivirati korisnike
- **FR7:** Sistem belezi poslednju aktivnost korisnika

### 2. Publisher Management (Izdavaci)

- **FR8:** Administrator moze kreirati novog izdavaca
- **FR9:** Administrator moze editovati podatke o izdavacu (naziv, logo, opis, kontakt, DOI prefix)
- **FR10:** Administrator moze pregledati listu svih izdavaca
- **FR11:** Sistem cuva DOI prefix za svakog izdavaca
- **FR12:** Posetilac moze videti stranicu izdavaca sa listom njegovih publikacija
- **FR12a:** Superadmin moze podesiti globalne Crossref depositor podatke (depositor_name, depositor_email) u Django Admin - **AZURIRANO**
- **FR12b:** Sistem validira da su globalni depositor podaci popunjeni pre generisanja XML-a - **AZURIRANO**
- **FR12c:** Sistem koristi Publisher.name kao registrant vrednost pri generisanju XML-a - **NOVO**

### 3. Publication Management (Publikacije)

- **FR13:** Administrator moze kreirati novu publikaciju (casopis, zbornik, monografija, ostalo)
- **FR14:** Administrator moze editovati podatke o publikaciji
- **FR15:** Administrator moze povezati publikaciju sa izdavacem
- **FR16:** Sistem podrzava razlicite tipove publikacija sa specificnim poljima
- **FR16a:** Za tip Zbornik, sistem cuva conference_date_end i conference_number - **NOVO**
- **FR17:** Posetilac moze pregledati listu svih publikacija sa filterima

### 4. Issue Management (Izdanja)

- **FR18:** Urednik moze kreirati novo izdanje publikacije
- **FR19:** Urednik moze editovati podatke o izdanju (volume, broj, godina, naslovna slika)
- **FR20:** Urednik moze postaviti status izdanja (draft, scheduled, published, archive)
- **FR21:** Posetilac moze pregledati sva izdanja publikacije

### 5. Article Management (Clanci)

- **FR22:** Bibliotekar moze kreirati novi clanak
- **FR23:** Bibliotekar moze uneti metapodatke clanka (naslov, podnaslov, apstrakt, kljucne reci)
- **FR24:** Bibliotekar moze dodati autore sa reorderingom (ime, afilijacija, ORCID, email)
- **FR24a:** Sistem automatski postavlja sequence polje (first za prvog autora, additional za ostale) - **NOVO**
- **FR24b:** Bibliotekar moze izabrati contributor_role za svakog autora (author, editor, chair, translator, reviewer) - **NOVO**
- **FR24c:** Bibliotekar moze dodati vise afilijacija po autoru sa ROR ID-jem - **NOVO**
- **FR25:** Bibliotekar moze upload-ovati PDF fajl
- **FR26:** Bibliotekar moze sacuvati clanak kao draft
- **FR27:** Sistem automatski cuva izmene (auto-save)
- **FR28:** Sistem validira ORCID format
- **FR28a:** Sistem validira da prvi autor ima sequence='first' pre objave - **NOVO**
- **FR29:** Urednik moze pregledati clanak za odobrenje
- **FR30:** Administrator moze objaviti clanak
- **FR30a:** Bibliotekar moze izabrati publication_type za clanak (full_text, abstract_only, bibliographic_record) - **NOVO**
- **FR30b:** Bibliotekar moze uneti license informacije (license_url, free_to_read) - **NOVO**
- **FR31:** Administrator moze povuci (withdraw) objavljeni clanak
- **FR32:** Sistem prikazuje withdrawn clanke sa oznakom

### 6. Crossref Integration

- **FR33:** Administrator moze generisati Crossref XML za izdanje (svi clanci izdanja u jednom XML fajlu)
- **FR33a:** Sistem automatski generise XML Head sa doi_batch_id, timestamp, depositor i registrant podacima - **NOVO**
- **FR33b:** Sistem korektno generise kontributor elemente sa sequence i contributor_role atributima - **NOVO**
- **FR33c:** Sistem ukljucuje afilijacije sa ROR ID-jem u XML ako su unete - **NOVO**
- **FR34:** Sistem prikazuje preview generisanog XML-a za izdanje
- **FR35:** Sistem validira XML prema Crossref XSD shemi (verzija 5.4.0) - **AZURIRANO**
- **FR36:** Sistem upozorava na greske pre generisanja XML-a
- **FR36a:** Sistem proverava da li su depositor podaci popunjeni za izdavaca pre generisanja - **NOVO**
- **FR36b:** Sistem proverava da li svi clanci imaju barem jednog autora sa sequence='first' - **NOVO**
- **FR37:** Administrator moze preuzeti generisani XML fajl za izdanje

### 7. Public Portal

- **FR38:** Posetilac moze videti pocetnu stranu portala
- **FR39:** Posetilac moze pretrazivati clanke po nazivu, autoru i kljucnim recima
- **FR40:** Posetilac moze filtrirati publikacije po vrsti, oblasti, pristupu, jeziku
- **FR41:** Posetilac moze videti landing stranicu clanka sa svim metapodacima
- **FR42:** Posetilac moze preuzeti PDF clanka
- **FR43:** Posetilac moze videti stranicu "O portalu"
- **FR44:** Posetilac moze poslati poruku preko kontakt forme
- **FR45:** Sistem salje kontakt poruke na definisanu email adresu

### 8. Admin Dashboard & Audit

- **FR46:** Administrator vidi statistiku na dashboard-u (broj publikacija, clanaka, pending zahteva)
- **FR47:** Administrator vidi listu clanaka koji cekaju odobrenje
- **FR48:** Superadmin moze pregledati audit log (ko, sta, kada)
- **FR49:** Sistem belezi sve izmene sadrzaja u audit log
- **FR50:** Superadmin moze obraditi zahtev za brisanje podataka (GDPR)

## Non-Functional Requirements

### Performance

| Zahtev | Kriterijum |
|--------|------------|
| Landing stranica clanka | First Contentful Paint < 3 sekunde |
| Javne stranice portala | Ucitavanje < 3 sekunde |
| Admin panel stranice | Ucitavanje < 5 sekundi |
| PDF download | Direktan link, bez procesiranja |
| Pretraga | Rezultati < 2 sekunde |
| XML generisanje | < 30 sekundi za izdanje sa 50 clanaka |

### Security

| Zahtev | Kriterijum |
|--------|------------|
| HTTPS | Obavezno za sve stranice (TLS 1.2+) |
| Password policy | Min 8 karaktera, kombinacija slova/brojeva |
| Session management | Timeout nakon 30 min neaktivnosti |
| Lozinke | Hashirane (bcrypt/argon2), nikad plain text |
| PDF upload | Virus scan pre prihvatanja |
| Audit log | Sve admin akcije se beleze (ko, sta, kada, IP) |
| GDPR | Soft delete, pravo na brisanje, cuvanje logova 1+ godina |

### Accessibility

| Zahtev | Kriterijum |
|--------|------------|
| HTML | Semanticki HTML5 elementi |
| Slike | Alt tekst za sve slike |
| Kontrast | Minimum 4.5:1 za tekst |
| Keyboard | Navigacija za kljucne akcije |
| Forms | Labels povezani sa input poljima |

### Integration

| Zahtev | Kriterijum |
|--------|------------|
| Crossref XML | Validacija prema aktuelnoj XSD shemi |
| Cloud Storage | S3-compatible API za PDF fajlove |
| Email | SMTP za kontakt formu i notifikacije |

### Reliability

| Zahtev | Kriterijum |
|--------|------------|
| Uptime | 99% dostupnost |
| Backup | Dnevni backup baze i fajlova |
| Data retention | Backup cuvanje 90+ dana |
| Error handling | Graceful degradation, user-friendly error poruke |
