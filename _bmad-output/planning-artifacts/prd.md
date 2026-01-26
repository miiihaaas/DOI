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

- Svaki izdavac ima svoj **DOI prefix** (npr. `10.1234`) - mora se cuvati u izdavac CRUD-u
- XML generisanje prema aktuelnoj Crossref XSD shemi
- Validacija XML-a pre download-a/slanja
- Obavezna Crossref polja moraju biti validirana pre objave

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

**Izdavac (Publisher) - dodatna polja:**
- `doi_prefix` - Crossref DOI prefix (npr. "10.1234") - **OBAVEZNO**
- `crossref_username` - (opciono, za Growth API)
- `crossref_password` - (opciono, za Growth API)

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

### 3. Publication Management (Publikacije)

- **FR13:** Administrator moze kreirati novu publikaciju (casopis, zbornik, monografija, ostalo)
- **FR14:** Administrator moze editovati podatke o publikaciji
- **FR15:** Administrator moze povezati publikaciju sa izdavacem
- **FR16:** Sistem podrzava razlicite tipove publikacija sa specificnim poljima
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
- **FR25:** Bibliotekar moze upload-ovati PDF fajl
- **FR26:** Bibliotekar moze sacuvati clanak kao draft
- **FR27:** Sistem automatski cuva izmene (auto-save)
- **FR28:** Sistem validira ORCID format
- **FR29:** Urednik moze pregledati clanak za odobrenje
- **FR30:** Administrator moze objaviti clanak
- **FR31:** Administrator moze povuci (withdraw) objavljeni clanak
- **FR32:** Sistem prikazuje withdrawn clanke sa oznakom

### 6. Crossref Integration

- **FR33:** Administrator moze generisati Crossref XML za izdanje (svi clanci izdanja u jednom XML fajlu)
- **FR34:** Sistem prikazuje preview generisanog XML-a za izdanje
- **FR35:** Sistem validira XML prema Crossref XSD shemi
- **FR36:** Sistem upozorava na greske pre generisanja XML-a
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
