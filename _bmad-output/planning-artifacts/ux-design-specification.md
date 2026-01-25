---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-03-core-experience
  - step-04-emotional-response
  - step-05-inspiration
  - step-06-design-system
  - step-07-defining-experience
  - step-08-visual-foundation
  - step-09-design-directions
  - step-10-user-journeys
  - step-11-component-strategy
  - step-12-ux-patterns
  - step-13-responsive-accessibility
  - step-14-complete
inputDocuments:
  - prd.md
  - DOI - Portal.md
documentCounts:
  prd: 1
  briefs: 0
  projectDocs: 1
---

# UX Design Specification - DOI

**Author:** Mihas
**Date:** 2026-01-24

---

## Executive Summary

### Project Vision

DOI Portal je interni servisni alat koji omogucava izdavacima naucnih publikacija da jednostavno kreiraju landing stranice za clanke potrebne za DOI registraciju, bez tehnickog znanja. Jedinstveni fokus na Crossref XML uskladjenost sa automatskom validacijom omogucava admin korisnicima da samostalno generisu ispravne XML fajlove bez tehnicke podrske.

**Kljucni princip:** Jedan clanak = jedna stranica = jedan DOI.

### Target Users

**Primarni korisnici (Admin Panel):**

| Persona | Profil | Kljucna potreba |
|---------|--------|-----------------|
| **Marija (Bibliotekar)** | 35g, diplomirala bibliotekarstvo, osrednje IT pismena, plasi se "komplikovanih sistema" | Jednostavan unos bez konfuzije, auto-save, jasna hijerarhija |
| **Dragan (Administrator)** | 42g, tehnicki potkovan, odgovoran za kvalitet podataka i Crossref uskladjenost | Bulk operacije, XML preview/validacija, dashboard sa pending stavkama |
| **Urednik** | Pregledava i odobrava sadrzaj pre objave | Brz pregled, jasne akcije approve/reject, efikasan workflow |
| **Superadmin** | IT administrator, tehnicki ekspert | User management, RBAC, audit logs, sistemska podesavanja |

**Sekundarni korisnici (Javni Portal):**

| Persona | Profil | Kljucna potreba |
|---------|--------|-----------------|
| **Ana (Istrazivac)** | 28g, doktorand, trazi clanke preko DOI linkova | Brz pristup PDF-u, bez registracije, minimalna frikcija |

### Key Design Challenges

1. **Hijerarhija sadrzaja** - Veza Izdavac → Publikacija → Izdanje → Clanak mora biti kristalno jasna za korisnike koji se plase "komplikovanih sistema"

2. **Crossref kompleksnost** - XML validacija i generisanje moraju biti transparentni za administratora, ali "nevidljivi" za bibliotekara

3. **Dual-interface dizajn** - Javni portal (minimalisticki, brz, fokusiran na sadrzaj) vs Admin panel (funkcionalan, detaljan, workflow-orijentisan) - potpuno razliciti UX obrasci

4. **Status workflow clarity** - Draft → Review → Ready to Publish → Published → Withdrawn - korisnik mora uvek znati gde je i sta je sledeci korak

### Design Opportunities

1. **Progressive disclosure u adminu** - Bibliotekar vidi samo ono sto mu treba, administrator moze "otvoriti" napredne opcije - smanjuje kognitivno opterecenje

2. **Landing stranica kao showcase** - Posetilac dolazi sa DOI linka i za 3 sekunde ima sve sto mu treba (metapodaci, apstrakt, PDF download) - to je nas "wow" momenat

3. **Auto-save kao osigurac poverenja** - "Nikad ne gubim rad" eliminise anksioznost kod korisnika koji se plase tehnoloskih sistema

4. **Vizuelna hijerarhija kroz ikonice** - Svaka vrsta publikacije (casopis, zbornik, monografija) ima svoju ikonicu - instant prepoznavanje bez citanja

## Core User Experience

### Defining Experience

**Admin Panel - Bibliotekar Marija:**
> *"Unosim clanak i znam da nista nece nestati"*

Najcesca akcija: **Kreiranje clanka sa metapodacima** - unos naslova, autora, ORCID-ova, apstrakta, upload PDF-a, cuvanje kao draft.

**Javni Portal - Istrazivac Ana:**
> *"Klik na DOI → vidim clanak → preuzmem PDF"*

Najcesca akcija: **Preuzimanje PDF-a** - dolazi sa DOI linka, 3 sekunde do "download started".

### Platform Strategy

| Aspekt | Odluka | Razlog |
|--------|--------|--------|
| **Tip** | MPA (Multi-Page Application) | Django server-side rendering, SEO za landing stranice |
| **Pristup** | Desktop-first responsive | Admin radi na desktopu, posetilac moze biti na mobile |
| **Offline** | Nije potrebno | Uvek online, nema offline use case |
| **Touch vs Mouse** | Primarno mouse/keyboard | Admin panel je radna povrsina, ne touch interface |

### Effortless Interactions

1. **Auto-save bez razmisljanja** - Korisnik nikad ne klikce "Save", sistem pamti sve automatski
2. **ORCID validacija u realnom vremenu** - Unese format, odmah vidi da li je validan
3. **Hijerarhija se sama "resi"** - Kad kreira clanak, sistem vec zna publikaciju i izdanje
4. **PDF download bez prepreka** - Posetilac klikne jednom, preuzimanje krece odmah

### Critical Success Moments

| Momenat | Korisnik | "Wow" osecaj |
|---------|----------|--------------|
| **Draft sacuvan** | Bibliotekar | "Moram da izadjem na sastanak... kad se vratim, sve je tu!" |
| **XML validacija prosla** | Administrator | "Sve zeleno, mogu da saljem Crossref-u" |
| **PDF preuzet** | Posetilac | "3 sekunde i imam sta mi treba" |
| **Clanak objavljen** | Administrator | "Landing stranica je live, DOI radi" |

### Experience Principles

1. **"Nikad ne gubim rad"** - Auto-save je default, ne feature
2. **"Vidim gde sam"** - Status workflow-a uvek vidljiv (Draft → Review → Published)
3. **"Sistem me vodi"** - Jasni next steps, validacije pre nego sto pogresim
4. **"Brzo do cilja"** - Minimalna frikcija, maksimalna efikasnost

## Desired Emotional Response

### Primary Emotional Goals

**Bibliotekar (Marija):**
> *"Osecam se sigurno i kompetentno"*

- **Sigurnost** - "Nista ne mogu da pokvarim, sistem me cuva"
- **Kompetentnost** - "Znam sta radim, cak i kad je sistem nov"
- **Mir** - "Nema panike, sve se automatski cuva"

**Administrator (Dragan):**
> *"Osecam se u kontroli i efikasno"*

- **Kontrola** - "Vidim sve sto se desava, nista me ne iznenaduje"
- **Efikasnost** - "Bulk operacije, brz pregled, nema gubljenja vremena"
- **Poverenje** - "XML je validan, Crossref nece odbiti"

**Posetilac (Ana):**
> *"Osecam se kao da sam dobila tacno ono sto mi treba"*

- **Zadovoljstvo** - "Brzo sam nasla clanak"
- **Olaksanje** - "Nije bilo prepreka, registracija, cekanja"

### Emotional Journey Mapping

| Faza | Admin korisnik | Portal posetilac |
|------|----------------|------------------|
| **Prvo otvaranje** | "Izgleda jednostavno, mogu ovo" | "Cista stranica, vidim PDF odmah" |
| **Tokom rada** | "Auto-save... super, ne brinem" | "Metapodaci su pregledni" |
| **Zavrsetak** | "Gotovo! Clanak je spreman za pregled" | "PDF preuzet, mogu da nastavim" |
| **Kad nesto podje naopako** | "Upozorenje je jasno, znam sta da popravim" | "Ako nema PDF, bar vidim apstrakt" |
| **Povratak** | "Dashboard mi pokazuje gde sam stala" | "DOI link uvek radi" |

### Micro-Emotions

| Pozitivno (gradimo) | Negativno (izbegavamo) |
|---------------------|------------------------|
| **Poverenje** - "Sistem radi kako ocekujem" | **Skepticizam** - "Da li je ovo stvarno sacuvano?" |
| **Jasnost** - "Znam sta je sledeci korak" | **Konfuzija** - "Gde je sada taj clanak?" |
| **Osecaj napretka** - "Vidim koliko sam uradila" | **Frustracija** - "Opet moram da klikcem?" |
| **Profesionalnost** - "Ovo izgleda ozbiljno" | **Sumnja** - "Da li ce Crossref prihvatiti?" |

### Design Implications

| Zeljena emocija | UX pristup |
|-----------------|------------|
| **Sigurnost** | Auto-save indikator, undo opcije, confirm dialogs za destruktivne akcije |
| **Kompetentnost** | Progresivno otkrivanje, inline pomoc, tooltips |
| **Kontrola** | Dashboard sa statusima, filtri, bulk akcije, audit trail |
| **Efikasnost** | Keyboard shortcuts, quick actions, minimalni broj klikova |
| **Zadovoljstvo** | Brzo ucitavanje (<3s), cist dizajn, PDF download bez prepreka |

### Emotional Design Principles

1. **"Sistem te cuva"** - Uvek auto-save, uvek mogucnost povratka, nikad gubitak podataka
2. **"Jasno je sta se desava"** - Status uvek vidljiv, akcije imaju feedback, greske su razumljive
3. **"Ti si u kontroli"** - Korisnik odlucuje tempo, sistem predlaze ali ne forsira
4. **"Profesionalno i pouzdano"** - Dizajn koji uliva poverenje, naucni kontekst

## UX Pattern Analysis & Inspiration

### Inspiring Products Analysis

**1. MDPI (mdpi.com)** - Naucni izdavac sa modernim portalom

| Aspekt | Sta rade dobro | Prenosivo na DOI Portal |
|--------|----------------|-------------------------|
| **Navigacija** | Jasna hijerarhija: Journal → Volume → Issue → Article | Da - isti model publikacija |
| **Filter sistem** | Multiselect filteri u zaglavlju, brza pretraga | Da - za stranu Publikacije |
| **Article landing** | Sve na jednoj strani: metapodaci, apstrakt, PDF | Da - nasa landing stranica |
| **Vizuelni identitet** | Cist, profesionalan, naucni kontekst | Da - isti ton |

*Kljucna lekcija: Informaciona arhitektura je odlicna - korisnik nikad nije izgubljen.*

**2. Frontiers (frontierspartnerships.org)** - Premium naucni izdavac

| Aspekt | Sta rade dobro | Prenosivo na DOI Portal |
|--------|----------------|-------------------------|
| **Article layout** | Sajdbar sa metapodacima, glavni sadrzaj centralno | Da - tacno ovaj layout |
| **Floating actions** | PDF download, share, DOI link uvek vidljivi | Da - floating bar |
| **Vizuelna hijerarhija** | Clanci u grid karticama 3x | Da - za prikaz clanaka |
| **Responsivnost** | Odlicna mobile verzija | Da - za posetioce |

*Kljucna lekcija: Floating action bar je sjajan za brz pristup PDF-u bez skrolovanja.*

**3. doi.rs (postojeci sajt)** - Vizuelni identitet koji treba pratiti

| Aspekt | Sta preuzimamo |
|--------|----------------|
| **Boje** | Primarna paleta sa doi.rs |
| **Tipografija** | Konzistentnost sa glavnim sajtom |
| **Header/Footer** | Isti obrazac - top header sa kontaktom, sticky meni |
| **Ton** | Profesionalan, pouzdan, srpski kontekst |

### Transferable UX Patterns

**Navigation Patterns:**
- Breadcrumbs na svakoj strani (MDPI) → Olaksava orijentaciju
- Sticky meni (doi.rs) → Uvek dostupna navigacija
- Sidebar za filtere (MDPI) → Efikasno filtriranje publikacija

**Interaction Patterns:**
- Floating action bar (Frontiers) → PDF/Share/DOI uvek vidljivi
- Infinite scroll (MDPI) → Za liste publikacija/clanaka
- Card grid 3 kolone (Frontiers) → Za prikaz clanaka u izdanju

**Visual Patterns:**
- Ikonice za tip publikacije (MDPI) → Instant prepoznavanje
- Status badges → Draft/Published/Withdrawn jasno oznaceni
- Sajdbar layout za article (Frontiers) → Metapodaci levo, sadrzaj desno

### Anti-Patterns to Avoid

| Anti-pattern | Zasto izbegavamo | Alternativa |
|--------------|------------------|-------------|
| **Pretrpane forme** | Korisnik se plasi kompleksnosti | Progressive disclosure |
| **Skriveni status** | Korisnik ne zna gde je clanak u workflow-u | Uvek vidljiv status badge |
| **PDF iza registracije** | Posetilac zeli brz download | Direktan link, bez prepreka |
| **Nejasne greske** | "Error occurred" ne pomaze | Konkretna poruka + sta da uradi |
| **Auto-refresh bez upozorenja** | Gubi se kontekst | Notifikacija pre refresh-a |

### Design Inspiration Strategy

**Adopt (Preuzimamo direktno):**
- Floating action bar za PDF/Share/DOI (Frontiers)
- Card grid 3 kolone za clanke (Frontiers)
- Breadcrumbs na svakoj strani (MDPI)
- Multiselect filter sistem (MDPI)

**Adapt (Prilagodjujemo):**
- Sajdbar layout - pojednostavljen za nase potrebe
- Infinite scroll - sa lazy loading optimizacijom
- Status badges - prilagodjen nas workflow

**Avoid (Izbegavamo):**
- Kompleksne forme bez progressive disclosure
- Skrivene akcije iza dropdown menija
- Tehnicke poruke o greskama

## Design System Foundation

### Design System Choice

**Izabrano: Bootstrap 5 za ceo projekat**

| Komponenta | Resenje |
|------------|---------|
| **Javni portal** | Bootstrap 5 + custom tema (doi.rs boje) |
| **Admin panel** | Custom Django views + Bootstrap 5 (NE Django Admin) |
| **Forme** | django-crispy-forms + crispy-bootstrap5 |
| **Dashboard** | Bootstrap cards, Chart.js za statistike |
| **Tabele** | DataTables.js ili bootstrap-table |
| **Ikonice** | Bootstrap Icons ili Heroicons |

### Rationale for Selection

1. **Jedan design system** - konzistentnost izmedju javnog portala i admin panela, manje koda za odrzavanje
2. **Potpuna kontrola nad admin UX-om** - custom admin panel omogucava dizajn workflow-a tacno po user journey-ima
3. **Poznat alat** - Bootstrap je vec poznat, nema krive ucenja
4. **Vizuelna fleksibilnost** - lako prilagoditi doi.rs brendingu bez ogranicenja Django Admin-a
5. **Lep admin panel** - moze se dizajnirati kao moderna SaaS aplikacija, ne kao genericki admin

### Implementation Approach

```
Javni Portal:
├── templates/public/
│   ├── base.html
│   ├── home.html
│   ├── publications/
│   ├── article-landing.html
│   └── components/
└── static/
    ├── css/portal.css (doi.rs tema)
    └── js/portal.js

Admin Panel (Custom Bootstrap):
├── views/
│   ├── dashboard.py
│   ├── articles.py
│   ├── publications.py
│   └── users.py
├── templates/admin_custom/
│   ├── base.html (sidebar, header)
│   ├── dashboard.html
│   ├── articles/ (list, form, detail)
│   └── components/
└── static/
    ├── css/admin.css
    └── js/admin.js
```

### Customization Strategy

**Bootstrap Custom Theme (doi.rs brending):**
- Primary color: doi.rs primarna boja
- Secondary color: doi.rs sekundarna boja
- Font family: konzistentno sa doi.rs
- Border radius, shadows: po doi.rs dizajn sistemu

**Admin Panel Features:**
- Sidebar navigacija (collapsible)
- Dashboard sa statistikama i pending stavkama
- CRUD sa DataTables (sortiranje, filtriranje, pretraga)
- Multi-step forme za kompleksne unose
- Inline editing za autore (drag & drop reordering)
- Status workflow buttons sa vizuelnim feedback-om

**Trade-offs:**
- Vise custom koda za CRUD operacije (ali Django CBV to olaksava)
- Potpuna kontrola nad UX-om za bibliotekarev journey

## Defining Experience

### Primary Defining Experiences

**1. Admin Panel - Bibliotekarev momenat:**
> *"Unesem clanak i znam da je siguran"*

Korisnik kreira novi clanak, unosi metapodatke, dodaje autore, upload-uje PDF - i nikada se ne brine da li je sacuvano. Sistem je uvek korak ispred.

**Zasto ovo definise iskustvo:**
- Eliminise strah od gubitka rada
- Gradi poverenje u sistem
- Omogucava fokus na sadrzaj, ne na tehnologiju

**2. Javni Portal - Posetiocev momenat:**
> *"Klik na DOI → Vidim clanak → Preuzmem PDF"*

Posetilac dolazi sa DOI linka iz naucnog rada. Za 3 sekunde ima sve sto mu treba - naslov, autore, apstrakt, PDF dugme. Bez registracije, bez cekanja, bez frikcije.

**Zasto ovo definise iskustvo:**
- DOI landing stranica je "lice" portala
- Svaki DOI link vodi ovde - to je prvi kontakt
- Brz PDF download = zadovoljan korisnik

### User Mental Model

| Korisnik | Mentalni model | Ocekivanje |
|----------|----------------|------------|
| **Bibliotekar** | "Ovo je kao Word sa automatskim cuvanjem" | Pisi, sistem pamti, nema "Save" dugmeta |
| **Administrator** | "Ovo je kao Trello za clanke" | Vidim status, pomeram kroz faze, bulk akcije |
| **Posetilac** | "Ovo je kao Wikipedia za naucne clanke" | Otvori, procitaj, preuzmi - bez prepreka |

### Success Criteria

**Za bibliotekarev unos clanka:**

| Kriterijum | Mera uspeha |
|------------|-------------|
| Auto-save feedback | "Sacuvano pre X sekundi" uvek vidljivo |
| Draft recovery | Ako zatvori browser, sve je tu kad se vrati |
| Validacija u realnom vremenu | ORCID format proveren odmah |
| Jasna hijerarhija | Publikacija → Izdanje → Clanak jasno prikazani |

**Za posetiocev pristup clanku:**

| Kriterijum | Mera uspeha |
|------------|-------------|
| Time to PDF | < 3 klikova od DOI linka do PDF preuzimanja |
| First Contentful Paint | < 3 sekunde |
| Vidljivost akcija | PDF dugme iznad fold-a, uvek vidljivo |
| Mobile friendly | Radi na telefonu bez zumiranja |

### Novel vs. Established Patterns

| Pattern | Tip | Implementacija |
|---------|-----|----------------|
| **Auto-save** | Established (Google Docs) | "Sacuvano" badge |
| **Status workflow** | Established (Trello) | Draft → Review → Published |
| **Floating action bar** | Established (Frontiers) | PDF/Share/DOI uvek vidljivi |
| **ORCID inline validation** | Niche established | Zelena/crvena ikonica |
| **Drag & drop autori** | Established | Reordering liste |

**Zakljucak:** Koristimo dokazane obrasce koje korisnici vec razumeju - nema potrebe za novel patterns.

### Experience Mechanics - Unos clanka

```
1. INICIJACIJA
   └── Klik "Novi clanak" → Forma se otvara
   └── Publikacija i Izdanje vec preselektovani (ako dolazi iz izdanja)

2. INTERAKCIJA
   └── Unosi polja jedno po jedno
   └── Auto-save na svakom blur/pause (debounced 2s)
   └── ORCID validacija: unese → ikonica se menja (⏳→✓/✗)
   └── Autori: klik "Dodaj autora" → nova kartica → drag za reorder

3. FEEDBACK
   └── "Sacuvano" badge u header-u (uvek vidljiv)
   └── Validacione poruke ispod polja (inline, ne modal)
   └── Progress indicator: "Metapodaci ✓ | Autori ✓ | PDF ○"

4. ZAVRSETAK
   └── Klik "Spremno za pregled" → Status se menja
   └── Toast notifikacija: "Clanak poslat uredniku na pregled"
   └── Redirect na listu clanaka sa highlight-om novog
```

## Visual Design Foundation

### Color System

**Napomena:** Paleta ce biti prilagodjena doi.rs brendingu kada brand guidelines budu dostupni.

**Predlozena paleta:**

| Tip | Namena | Vrednost |
|-----|--------|----------|
| **Primary** | Glavni akcent, CTA dugmad, linkovi | #1a365d (tamno plava) |
| **Secondary** | Sekundarni elementi, hover states | #3182ce (svetlija plava) |
| **Success** | Validacija OK, objavljeno | #38a169 (zelena) |
| **Warning** | Upozorenja, draft status | #dd6b20 (narandzasta) |
| **Danger** | Greske, brisanje | #e53e3e (crvena) |
| **Neutral** | Tekst, pozadine, borderi | Siva skala |

**Semantic Color Mapping:**
```css
--color-text-primary: #1a202c;
--color-text-secondary: #4a5568;
--color-bg-primary: #ffffff;
--color-bg-secondary: #f7fafc;
--color-border: #e2e8f0;
--color-status-draft: #dd6b20;
--color-status-review: #3182ce;
--color-status-published: #38a169;
--color-status-withdrawn: #e53e3e;
```

### Typography System

| Element | Velicina | Tezina |
|---------|----------|--------|
| **H1** | 2.25rem (36px) | 700 (Bold) |
| **H2** | 1.875rem (30px) | 600 (Semibold) |
| **H3** | 1.5rem (24px) | 600 |
| **H4** | 1.25rem (20px) | 600 |
| **Body** | 1rem (16px) | 400 (Regular) |
| **Small** | 0.875rem (14px) | 400 |
| **Caption** | 0.75rem (12px) | 400 |

**Font Stack:**
```css
--font-family-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                    "Helvetica Neue", Arial, sans-serif;
```

**Ton:** Profesionalan, citak, pristupacno za naucni sadrzaj.

### Spacing & Layout Foundation

**Base Unit:** 8px (Bootstrap default)

| Token | Vrednost | Upotreba |
|-------|----------|----------|
| `xs` | 4px | Mikro razmaci |
| `sm` | 8px | Unutrasnji padding malih elemenata |
| `md` | 16px | Standardni padding |
| `lg` | 24px | Razmak izmedju sekcija |
| `xl` | 32px | Veci razmaci |
| `2xl` | 48px | Razmak izmedju velikih blokova |

**Grid System:**
- 12-column Bootstrap grid
- Container max-width: 1200px (desktop)
- Gutters: 24px

**Layout Principles:**
1. **Javni portal:** Prostran, "airy" - vise whitespace-a, fokus na citljivost
2. **Admin panel:** Efikasniji, denser - vise informacija na ekranu, ali ne pretrpan
3. **Mobile:** Touch-friendly targets (min 44px), veci razmaci

### Accessibility Considerations

| Zahtev | Standard | Implementacija |
|--------|----------|----------------|
| **Contrast ratio** | WCAG AA (4.5:1 tekst) | Sve boje proverene |
| **Focus states** | Vidljiv focus ring | `:focus-visible` stilovi |
| **Touch targets** | Min 44x44px | Dugmad i linkovi |
| **Font size** | Min 16px body | Sprecava zoom na iOS |
| **Color blindness** | Ne oslanjati se samo na boju | Ikonice + tekst za status |

## Design Direction Decision

### Design Directions Explored

**Direction 1: "Clean Academic"** - Prostran, whitespace-orijentisan, jasna hijerarhija. Inspiracija: Frontiers + MDPI. Idealno za javni portal.

**Direction 2: "Compact Efficient"** - Denser layout, vise informacija na ekranu, collapsible sidebar, DataTables. Idealno za admin panel.

### Chosen Direction: Hybrid Approach

| Deo sistema | Stil | Razlog |
|-------------|------|--------|
| **Javni portal** | Clean Academic | Posetilac treba brz pristup, profesionalan izgled |
| **Admin panel** | Compact Efficient | Admin radi sa puno podataka, efikasnost je prioritet |
| **Landing stranica clanka** | Clean Academic | "Lice" portala, mora izgledati premium |
| **Dashboard** | Hybrid | Cards za statistike, tabele za liste |

### Key Layout Patterns

**Javni Portal Layout:**
- Sticky header sa navigacijom
- Hero sekcija sa pretragom
- 3-column card grid za publikacije/clanke
- Sidebar za filtere na listing stranicama
- Footer sa linkovima i kontaktom

**Admin Panel Layout:**
- Collapsible sidebar navigacija (levo)
- Breadcrumbs + user menu (gore)
- Content area sa cards/tables
- Sticky action bar za forme

**Article Landing Layout (Frontiers stil):**
- Breadcrumbs za hijerarhiju
- 2-column: glavni sadrzaj (2/3) + sidebar (1/3)
- Sidebar: publikacija info, izdavac, metrika
- Floating action bar: PDF, Share, DOI (fixed)

### Design Rationale

1. **Poznati obrasci** - Korisnici naucnih portala vec znaju Frontiers/MDPI pattern
2. **Dual-mode dizajn** - Razlicite potrebe za posetioce vs admin korisnike
3. **Bootstrap komponente** - Vecina elemenata vec postoji u Bootstrap 5
4. **doi.rs brending** - Boje i tipografija uskladjeni sa glavnim sajtom

## User Journey Flows

### Journey 1: Bibliotekar unosi novi clanak

**Tok:** Login → Dashboard → Novi clanak → Metapodaci → Autori → Apstrakt → PDF → Preview → Spremno za pregled

**Kriticne tacke:**
- Auto-save na svakom koraku
- ORCID validacija u realnom vremenu (zelena/crvena ikonica)
- Drag & drop za redosled autora
- Preview landing stranice pre slanja
- Toast notifikacija: "Poslato uredniku na pregled"

### Journey 2: Administrator odobrava i objavljuje

**Tok:** Dashboard (pending stavke) → Pregled clanka → Odobri/Vrati → Crossref Deposit → Generisi XML → Validacija → Download → Objavi

**Kriticne tacke:**
- Bulk operacije za vise clanaka
- XML validacija pre generisanja
- Jasna upozorenja o nedostajucim Crossref poljima
- Status workflow uvek vidljiv

### Journey 3: Posetilac pristupa clanku

**Tok:** DOI link → Landing stranica (<3s) → Vidi metapodatke → Preuzmi PDF / Citiraj / Deli

**Kriticne tacke:**
- First Contentful Paint < 3 sekunde
- PDF dugme uvek vidljivo (floating bar)
- Zero friction - bez registracije
- Citiranje u APA/MLA/BibTeX formatima

### Journey 4: Superadmin upravlja korisnicima

**Tok:** Dashboard → Korisnici → Dodaj/Edit/Deaktiviraj → Audit log

**Kriticne tacke:**
- Confirm modal za destruktivne akcije
- Email notifikacija novom korisniku
- Audit log za sve akcije

### Journey Patterns

**Navigation Patterns:**
- Breadcrumbs na svakoj strani
- Collapsible sidebar meni
- Quick actions na Dashboard-u

**Decision Patterns:**
- Confirm modal za destruktivne akcije
- Inline validacija pre submit-a
- Preview pre konacne akcije

**Feedback Patterns:**
- Auto-save indicator: "Sacuvano pre X sekundi"
- Toast notifikacije za uspesne akcije
- Inline error messages ispod polja
- Status badges na listama (Draft, Review, Published)

**Error Recovery Patterns:**
- Jasne poruke sta nije u redu
- Link za povratak na problematicno mesto
- Undo opcija gde je moguce

## Component Strategy

### Design System Components (Bootstrap 5)

| Kategorija | Komponente | Status |
|------------|------------|--------|
| **Layout** | Grid, Container, Row, Col | Koristi direktno |
| **Navigation** | Navbar, Breadcrumb, Nav, Tab | Koristi direktno |
| **Forms** | Input, Select, Checkbox, Validation | Koristi + extend |
| **Buttons** | Button, Button Group, Dropdown | Koristi direktno |
| **Cards** | Card, Card Group | Koristi + extend |
| **Tables** | Table + DataTables.js | Koristi + plugin |
| **Feedback** | Alert, Toast, Modal, Progress | Koristi direktno |
| **Indicators** | Badge, Spinner | Koristi + extend |

### Custom Components (Required for MVP)

**1. Article Card**
- Kartica za prikaz clanka sa ikonom tipa, naslovom, autorima, apstraktom
- Variants: Compact (liste), Full (grid)
- States: Default, Hover, Draft (grayed)

**2. Author List**
- Drag & drop reordering
- ORCID validacija u realnom vremenu
- Corresponding author checkbox
- Add/Remove funkcionalnost

**3. Status Badge**
- Draft (narandzasta), Review (plava), Published (zelena), Withdrawn (crvena)
- Ikonica + tekst (accessibility)

**4. Floating Action Bar**
- PDF download, Share, DOI link
- Fixed position (right na desktop, bottom na mobile)

**5. Auto-save Indicator**
- States: Saved, Saving, Error
- "Sacuvano pre X sekundi" format
- Uvek vidljiv u header-u forme

**6. ORCID Input**
- Auto-formatiranje (####-####-####-####)
- Real-time validacija
- Link ikonica za ORCID profil

**7. Filter Sidebar**
- Multiselect filtri za publikacije
- Collapsible sekcije
- Clear all funkcionalnost

**8. Citation Modal**
- APA, MLA, Chicago, BibTeX, RIS formati
- Copy to clipboard funkcionalnost

**9. XML Preview**
- Code block sa syntax highlighting
- Validacija status (OK/Errors)
- Download button

**10. Publication Hierarchy**
- Breadcrumb-style navigacija
- Izdavac → Publikacija → Izdanje → Clanak

### Component Implementation Strategy

**Pristup:**
- Extend Bootstrap komponente gde je moguce
- Custom CSS sa BEM metodologijom
- Vanilla JS ili Alpine.js za interaktivnost
- Django template components za reusability

**File Structure:**
```
static/css/components/ - Custom component styles
static/js/components/ - Component JavaScript
templates/components/ - Django template partials
```

### Implementation Roadmap

**SVE komponente su obavezne za MVP release:**

| Komponenta | Prioritet | Potrebno za |
|------------|-----------|-------------|
| Article Card | Kriticno | Prikaz clanaka |
| Status Badge | Kriticno | Workflow vidljivost |
| ORCID Input | Kriticno | Unos autora |
| Auto-save Indicator | Kriticno | Poverenje korisnika |
| Author List | Kriticno | Unos/reorder autora |
| Floating Action Bar | Kriticno | PDF download |
| Filter Sidebar | Kriticno | Pretraga publikacija |
| Citation Modal | Obavezno | Citiranje clanaka |
| XML Preview | Obavezno | Crossref validacija |
| Publication Hierarchy | Obavezno | Navigacija sadrzaja |

**Napomena:** Nema faziranja - sve komponente se implementiraju tokom izgradnje aplikacije.

## UX Consistency Patterns

### Button Hierarchy

| Tip | Izgled | Kada koristiti |
|-----|--------|----------------|
| **Primary** | Solid, primary color | Glavna akcija (1 po ekranu) |
| **Secondary** | Outline, primary color | Sekundarne akcije, cancel |
| **Tertiary** | Text only | Manje vazne akcije |
| **Danger** | Solid red | Destruktivne akcije |
| **Disabled** | Grayed out | Nedostupna akcija |

**Pravila:** Samo 1 primary po ekranu. Primary desno, Secondary levo. Danger uvek sa confirm.

### Feedback Patterns

| Tip | Boja | Kada |
|-----|------|------|
| **Success** | Zelena | Akcija uspesna |
| **Error** | Crvena | Akcija neuspesna |
| **Warning** | Narandzasta | Upozorenje |
| **Info** | Plava | Informacija |

**Toast:** Top-right (desktop), 5s auto-dismiss osim Error.
**Inline:** Poruke ispod polja sa odgovarajucom bojom bordure.

### Form Patterns

- Labels iznad polja
- Required oznaceno sa *
- Real-time validacija na blur
- Submit disabled dok nije validno
- Auto-save: debounced 2s, indicator uvek vidljiv
- Multi-step: progress indicator, save na svakom koraku

### Navigation Patterns

**Breadcrumbs:** Uvek prisutni, max 5 nivoa, poslednji bold.
**Sidebar (Admin):** Collapsible, sticky, ikonice + tekst.
**Header (Portal):** Sticky, hamburger na mobile.
**Pagination:** < 50 stavki pagination, > 50 infinite scroll.

### Modal Patterns

- Close: X + Escape + overlay click
- Focus trap
- Max width: 600px (mali), 900px (veliki)
- Confirm modal za sve destruktivne akcije

### Empty States

- Centrirana poruka sa ikonom
- Glavna poruka bold, sekundarna siva
- CTA dugme ako ima smisla
- Primeri: "Nema clanaka" + [Kreiraj prvi], "Nema rezultata" + [Ocisti filtere]

### Loading States

| Kontekst | Indikator |
|----------|-----------|
| Stranica | Skeleton loader |
| Akcija | Spinner u dugmetu |
| Upload | Progress bar |
| Infinite scroll | Spinner na dnu |

### Search & Filter Patterns

- Search: debounced 300ms, min 3 char, clear dugme
- Filteri: multiselect, collapsible, "Ocisti sve"
- Aktivni filteri kao tagovi iznad rezultata
- URL parametri za shareable filtere

## Responsive Design & Accessibility

### Responsive Strategy

**Pristup:** Desktop-first responsive design

| Platforma | Prioritet | Razlog |
|-----------|-----------|--------|
| **Desktop** | Primarno | Admin korisnici rade na desktopu 95%+ vremena |
| **Tablet** | Sekundarno | Posetilac moze pristupati sa tableta |
| **Mobile** | Tercijarno | Posetilac moze pristupati sa telefona |

**Admin Panel:** Optimizovan iskljucivo za desktop (min 1024px). Mobile/tablet nije kriticno za admin workflow.

**Javni Portal:** Fully responsive - posetilac moze doci sa bilo kog uredjaja.

### Breakpoint Strategy

Bootstrap 5 default breakpoints:

| Breakpoint | Velicina | Upotreba |
|------------|----------|----------|
| `xs` | <576px | Mobile portrait |
| `sm` | ≥576px | Mobile landscape |
| `md` | ≥768px | Tablet |
| `lg` | ≥992px | Desktop |
| `xl` | ≥1200px | Large desktop |
| `xxl` | ≥1400px | Extra large desktop |

### Layout Adaptations

**Javni Portal:**

| Element | Desktop | Tablet | Mobile |
|---------|---------|--------|--------|
| **Navigation** | Horizontal menu | Horizontal menu | Hamburger |
| **Article cards** | 3 kolone | 2 kolone | 1 kolona |
| **Article landing** | 2 kolone (content + sidebar) | 1 kolona, sidebar ispod | 1 kolona |
| **Floating action bar** | Fixed right | Fixed right | Fixed bottom |
| **Filter sidebar** | Sticky left | Collapsible overlay | Collapsible overlay |

**Admin Panel:**

| Element | Desktop (≥992px) | Manje od 992px |
|---------|------------------|----------------|
| **Sidebar** | Expanded, collapsible | Ne prikazuje se / overlay |
| **Tables** | Full width, all columns | Horizontal scroll |
| **Forms** | Multi-column layout | Single column |
| **Dashboard cards** | 4 kolone | Stack vertically |

### Accessibility Strategy

**Standard:** WCAG 2.1 Level AA compliance

| Kategorija | Zahtev | Implementacija |
|------------|--------|----------------|
| **Perceivable** | Contrast 4.5:1 (tekst), 3:1 (large) | Testirani color combinations |
| **Operable** | Keyboard navigation | Tab order, focus states, skip links |
| **Understandable** | Clear labels, error messages | Descriptive labels, inline validation |
| **Robust** | Semantic HTML | Proper heading hierarchy, ARIA landmarks |

**Specificni zahtevi:**

| Element | A11y Feature |
|---------|--------------|
| **Forms** | Labels linked to inputs, error descriptions, required indicators |
| **Buttons** | Descriptive text (ne samo ikonice), focus visible |
| **Images** | Alt text za sve slike, decorative marked as aria-hidden |
| **Color** | Ne oslanja se samo na boju - ikonice + tekst za status |
| **Focus** | Visible focus ring (:focus-visible) |
| **Motion** | Respect prefers-reduced-motion |
| **Screen readers** | ARIA live regions za dinamicke promene |

### Testing Strategy

**Accessibility Testing:**

| Alat | Namena |
|------|--------|
| **axe DevTools** | Automated accessibility testing |
| **WAVE** | Visual accessibility checker |
| **Lighthouse** | Performance + accessibility audit |
| **Manual keyboard** | Tab navigation testing |
| **Screen reader** | NVDA/VoiceOver testing |

**Responsive Testing:**

| Metod | Upotreba |
|-------|----------|
| **Browser DevTools** | Device emulation |
| **Real devices** | Final validation |
| **BrowserStack** | Cross-browser testing |

### Implementation Guidelines

**CSS Organization:**

```scss
// Mobile-first za portal, desktop-first za admin
// Portal: base styles mobile, @media for larger
// Admin: base styles desktop, @media for smaller

// Portal example
.article-card {
  // Mobile base
  @media (min-width: 768px) { /* Tablet */ }
  @media (min-width: 992px) { /* Desktop */ }
}

// Admin example
.admin-sidebar {
  // Desktop base
  @media (max-width: 991px) { /* Hide/overlay */ }
}
```

**Focus Management:**

```css
/* Visible focus for keyboard users */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Remove for mouse users */
:focus:not(:focus-visible) {
  outline: none;
}
```

**Skip Links:**

```html
<a href="#main-content" class="skip-link">
  Preskoci na glavni sadrzaj
</a>
```

---

## Appendix: Implementation Notes

### Key Technical Decisions

| Odluka | Razlog |
|--------|--------|
| Bootstrap 5 | Poznat alat, brza implementacija, responsive out-of-box |
| Custom admin panel | Potpuna kontrola nad UX, bez ogranicenja Django Admin-a |
| Desktop-first admin | Admin korisnici rade iskljucivo na desktopu |
| Mobile-first portal | Posetilac moze doci sa bilo kog uredjaja |
| WCAG AA | Standardni nivo pristupacnosti za javne servise |

### Dependencies

| Paket | Verzija | Namena |
|-------|---------|--------|
| Bootstrap | 5.3+ | CSS framework |
| django-crispy-forms | latest | Form rendering |
| crispy-bootstrap5 | latest | Bootstrap 5 form templates |
| DataTables.js | latest | Interactive tables |
| Chart.js | latest | Dashboard charts |
| Bootstrap Icons | latest | Ikonice |

### File Structure Reference

```
static/
├── css/
│   ├── portal.css          # Javni portal tema
│   ├── admin.css           # Admin panel tema
│   └── components/         # Custom komponente
├── js/
│   ├── portal.js           # Portal JavaScript
│   ├── admin.js            # Admin JavaScript
│   └── components/         # Component scripts
└── img/
    └── icons/              # Custom ikonice

templates/
├── public/                 # Javni portal
│   ├── base.html
│   ├── home.html
│   ├── publications/
│   └── article-landing.html
├── admin_custom/           # Custom admin panel
│   ├── base.html
│   ├── dashboard.html
│   └── articles/
└── components/             # Reusable partials
```

---

*Dokument generisan: 2026-01-25*
*UX Design Workflow Complete*
