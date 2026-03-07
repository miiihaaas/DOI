# Sprint Change Proposal — Ispravke Crossref XML i UX poboljšanja

**Datum:** 2026-03-07
**Trigger:** docs/potrebne-ispravke.md
**Scope Classification:** Minor-to-Moderate
**Preporučeni put:** Direct Adjustment (patch stories)

---

## 1. Rezime problema

Tokom implementacije i testiranja Epic-a 5 (Crossref XML Integration, stories 5-1 do 5-6), identifikovana su 4 problema koja utiču na kvalitet generisanog XML-a i korisničko iskustvo:

| # | Problem | Severity | Tip |
|---|---------|----------|-----|
| 1 | Language polje koristi TextInput umesto Select widgeta | Srednji | UX / Data Quality |
| 2 | `<resource>` element u XML-u je kružna referenca (doi.org → doi.org) | **KRITIČAN** | Bug |
| 3 | Nedostaje podrška za eksterni landing page/PDF (sajt izdavača) | Visok | Novi zahtev |
| 4 | Nedostaje dugme za regenerisanje XML-a nakon ispravke podataka | Visok | UX Gap |

---

## 2. Impact analiza

### 2.1 Epic Impact

| Epic | Uticaj | Detalji |
|------|--------|---------|
| Epic 2 (Content Structure) | Retroaktivni fix | Language widget na Publication/Article formama |
| Epic 3 (Article Workflow) | Nova story | Eksterni URL polja na Article modelu |
| Epic 5 (Crossref XML) | Bug fix + dopuna | Resource URL fix, regenerisanje dugme |
| Epic 6 (Compliance) | Bez uticaja | — |

### 2.2 Artifact Impact

**PRD:**
- Ne pominje eksplicitno eksterni landing page — novo zahtev van originalnog scope-a
- Language widget tip nije specificiran — dopuna, ne konflikt
- `<resource>` URL implicitno definisan kroz FR41 (landing page) ali ne eksplicitno u Crossref sekciji

**Architecture:**
- Article data model treba proširiti sa 3 nova polja (use_external_resource, external_landing_url, external_pdf_url)
- XML šablon arhitektura ostaje ista (Jinja2 templates)
- Nova migracija potrebna

**UX Design:**
- Article forma: switch UX za eksterni URL (novo)
- Publication/Article forme: Select widget umesto TextInput (izmena)
- Issue detail page: regenerisanje dugme (dopuna)

### 2.3 Codebase Impact

**Pogođeni fajlovi:**

| Fajl | Linija | Problem |
|------|--------|---------|
| `crossref/templates/crossref/journal_article.xml.j2` | 126 | `<resource>` = doi.org (kružna ref.) |
| `crossref/templates/crossref/conference_paper.xml.j2` | 134 | `<resource>` = doi.org (kružna ref.) |
| `crossref/templates/crossref/book_chapter.xml.j2` | 111 | `<resource>` = doi.org (kružna ref.) |
| `publications/forms.py` | 87-92 | language = TextInput |
| `articles/forms.py` | 97-102 | language = TextInput |
| `templates/issues/issue_detail.html` | 190-251 | Nema regenerisanje dugme |
| `articles/models.py` | — | Nedostaju external URL polja |

---

## 3. Preporučeni pristup: Direct Adjustment

### Rationale

- Sva 4 problema imaju jasna, konkretna rešenja
- Problemi 1, 2, 4 su niske složenosti (Low effort)
- Problem 3 je srednje složenosti ali sa jasnim planom
- Nema potrebe za rollback-om ili MVP review-om
- Ukupan risk: **Low**

### Trade-offs razmatrani

- **Rollback:** Nije potreban — implementirani kod je ispravan, samo treba dopuna
- **MVP Review:** Problem 3 (eksterni URL) se može odložiti za post-MVP ako je scope concern
- **Hybrid:** Izabrano — problemi 1, 2, 4 idu odmah, problem 3 po odluci PO-a

---

## 4. Detaljni Change Proposals

### Story 5-3a: Fix `<resource>` URL u Crossref XML šablonima

**Prioritet:** KRITIČAN — blokira svaki DOI registration
**Effort:** Low
**Epic:** 5 (Crossref XML Integration)

**Opis:** Zameni hardkodirani `doi.org` URL sa stvarnim portal URL-om u sva 3 XML šablona. Dodaj `site_url` varijablu u template context.

**Izmene:**

```
Fajl: crossref/templates/crossref/journal_article.xml.j2
Sekcija: doi_data/resource (linija 126)

STARO:
<resource>https://doi.org/{{ publisher.doi_prefix }}/{{ article.doi_suffix }}</resource>

NOVO:
<resource>{{ site_url }}/articles/{{ article.pk }}/</resource>

Rationale: <resource> je destinacija DOI-a, ne sam DOI link. Trenutno stvara kružnu referencu.
```

```
Fajl: crossref/templates/crossref/conference_paper.xml.j2
Sekcija: doi_data/resource (linija 134)

STARO:
<resource>https://doi.org/{{ publisher.doi_prefix }}/{{ article.doi_suffix }}</resource>

NOVO:
<resource>{{ site_url }}/articles/{{ article.pk }}/</resource>

Rationale: Isti bug kao journal_article šablon.
```

```
Fajl: crossref/templates/crossref/book_chapter.xml.j2
Sekcija: doi_data/resource (linija 111)

STARO:
<resource>https://doi.org/{{ publisher.doi_prefix }}/{{ article.doi_suffix }}</resource>

NOVO:
<resource>{{ site_url }}/articles/{{ article.pk }}/</resource>

Rationale: Isti bug kao journal_article šablon.
```

```
Fajl: crossref/services.py (XML generation service)
Sekcija: template context

STARO:
context ne sadrži site_url

NOVO:
Dodati site_url u template context (iz Django settings ili Sites framework)

Rationale: Šabloni trebaju pristup base URL-u portala.
```

**Acceptance Criteria:**
1. Given XML se generiše za bilo koji tip publikacije, When pregledam `<resource>` element, Then sadrži portal URL (`https://publikacije.doi.rs/articles/{pk}/`), a ne `doi.org` URL
2. Given `site_url` je definisan u settings, When se XML generiše, Then koristi ispravan base URL
3. Given postojeći XML testovi, When pokrenemo test suite, Then svi testovi prolaze sa novim URL formatom

---

### Story 2-4a: Language Select Widget za Publication i Article forme

**Prioritet:** Srednji
**Effort:** Low
**Epic:** 2 (retroaktivna patch story)

**Opis:** Zameni TextInput sa Select widgetom za language polje na obe forme. Dodaj LANGUAGE_CHOICES konstantu sa najčešćim ISO 639-1 jezicima.

**Izmene:**

```
Fajl: Novo — core/constants.py (ili odgovarajuća lokacija)

NOVO:
LANGUAGE_CHOICES = [
    ("sr", "Srpski (sr)"),
    ("en", "Engleski (en)"),
    ("de", "Nemački (de)"),
    ("fr", "Francuski (fr)"),
    ("it", "Italijanski (it)"),
    ("ru", "Ruski (ru)"),
    ("es", "Španski (es)"),
    ("hr", "Hrvatski (hr)"),
    ("bs", "Bosanski (bs)"),
    ("sl", "Slovenački (sl)"),
    ("mk", "Makedonski (mk)"),
    ("bg", "Bugarski (bg)"),
]

Rationale: Centralizovana lista jezika za konzistentnost između formi.
```

```
Fajl: publications/forms.py
Sekcija: Widget za language (linije 87-92)

STARO:
"language": forms.TextInput(attrs={"class": "form-control", "placeholder": "sr"})

NOVO:
"language": forms.Select(choices=LANGUAGE_CHOICES, attrs={"class": "form-select"})

Rationale: Select umesto slobodnog teksta sprečava pogrešan unos.
```

```
Fajl: articles/forms.py
Sekcija: Widget za language (linije 97-102)

STARO:
"language": forms.TextInput(attrs={"class": "form-control", "placeholder": "npr. sr, en"})

NOVO:
"language": forms.Select(choices=LANGUAGE_CHOICES, attrs={"class": "form-select"})

Rationale: Isti razlog. Placeholder "npr. sr, en" je bio konfuzan jer polje prima samo jedan jezik.
```

**Acceptance Criteria:**
1. Given otvorim formu za kreiranje/edit publikacije, When vidim language polje, Then je Select dropdown sa predefinisanim jezicima
2. Given otvorim formu za kreiranje/edit članka, When vidim language polje, Then je Select dropdown sa istom listom jezika
3. Given postojeći podaci sa language="sr", When otvorim edit formu, Then je "Srpski (sr)" selektovan

---

### Story 5-7 (proširenje): Uključiti regenerisanje XML-a u Deposit Workflow Page

**Prioritet:** Visok
**Effort:** Low (dodatak na postojeću backlog story)
**Epic:** 5

**Opis:** U okviru Story 5-7 (Crossref Deposit Workflow Page, trenutno backlog), dodati acceptance criteria za regenerisanje XML-a.

**Izmena u story fajlu (kad se kreira):**

```
Dodatni Acceptance Criteria za Story 5-7:

NOVO:
- Given XML je već generisan za izdanje i prikazuje XSD greške,
  When korisnik ispravi podatke i klikne "Regeneriši XML",
  Then se novi XML generiše sa ispravljenim podacima i XSD status se osvežava

- Given dugme "Regeneriši XML" je prikazano,
  When korisnik klikne na njega,
  Then se prikaže confirmation modal ("Postojeći XML će biti zamenjen")
  i nakon potvrde pokrene se regenerisanje
```

```
Fajl: templates/issues/issue_detail.html
Sekcija: {% if issue.crossref_xml %} blok (nakon linija 212-222)

STARO:
Samo "Pregled XML" i "Preuzmi XML" dugmad

NOVO:
Dodati "Regeneriši XML" dugme sa hx-post, hx-confirm, i osvežavanjem Crossref kartice

Rationale: Korisnik mora moći da regeneriše XML nakon ispravke grešaka.
```

---

### Story 3-1a: Podrška za eksterni landing page i PDF URL (OPCIONO — po odluci PO)

**Prioritet:** Srednji (može biti post-MVP)
**Effort:** Medium
**Epic:** 3 (Article Workflow — retroaktivna patch story)

**Opis:** Dodaj mogućnost da DOI pokazuje na sajt izdavača umesto na portal. Novi model polja, switch UX na formi, uslovna logika u XML šablonima.

**Izmene:**

```
Fajl: articles/models.py

NOVO polja:
use_external_resource = models.BooleanField(
    _("Koristi eksterni URL za DOI"),
    default=False,
    help_text=_("Ako je uključeno, DOI će pokazivati na sajt izdavača umesto na portal."),
)
external_landing_url = models.URLField(
    _("Eksterna landing stranica"),
    blank=True,
    help_text=_("URL stranice članka na sajtu izdavača"),
)
external_pdf_url = models.URLField(
    _("Eksterni PDF URL"),
    blank=True,
    help_text=_("URL PDF fajla na sajtu izdavača (opciono)"),
)
```

```
Fajl: articles/forms.py

NOVO:
- Dodati nova 3 polja u ArticleForm
- Switch (checkbox) za use_external_resource
- HTMX toggle za prikaz/skrivanje external_landing_url i external_pdf_url
- Validacija: ako use_external_resource=True, external_landing_url je obavezan
```

```
Fajl: sva 3 XML šablona — <resource> element

STARO (nakon fix-a iz Story 5-3a):
<resource>{{ site_url }}/articles/{{ article.pk }}/</resource>

NOVO:
{% if article.use_external_resource and article.external_landing_url %}
<resource>{{ article.external_landing_url }}</resource>
{% else %}
<resource>{{ site_url }}/articles/{{ article.pk }}/</resource>
{% endif %}
```

```
Fajl: portal/article_detail.html

NOVO:
Ako article.use_external_resource, prikazati link ka originalnom sajtu izdavača
```

**Acceptance Criteria:**
1. Given otvorim formu za članak, When uključim switch "Članak se nalazi i na sajtu izdavača", Then se prikazuju polja za eksterni URL
2. Given switch je uključen i external_landing_url je popunjen, When se generiše XML, Then `<resource>` sadrži eksterni URL
3. Given switch je isključen, When se generiše XML, Then `<resource>` sadrži portal URL
4. Given switch je uključen ali external_landing_url je prazan, When pokušam da sačuvam, Then dobijem validation error
5. Given članak ima eksterni URL, When posetim landing page na portalu, Then vidim link ka originalnom sajtu izdavača

---

## 5. Implementation Handoff

### Scope Classification: Minor-to-Moderate

| Story | Scope | Handoff |
|-------|-------|---------|
| 5-3a (resource URL fix) | **Minor** | Dev team — direktna implementacija |
| 2-4a (language select) | **Minor** | Dev team — direktna implementacija |
| 5-7 proširenje (regenerisanje) | **Minor** | SM — dodati AC u story pre kreiranja |
| 3-1a (eksterni URL) | **Moderate** | PO odluka (MVP/post-MVP) → Dev team |

### Preporučeni redosled

| Red | Story | Razlog | Zavisnosti |
|-----|-------|--------|------------|
| 1 | **5-3a** | KRITIČAN bug | Nema — može odmah |
| 2 | **2-4a** | Brza ispravka | Nema — može paralelno sa 5-3a |
| 3 | **5-7** (sa regenerisanjem) | Već planirana story | Zavisi od 5-3a (resource URL fix) |
| 4 | **3-1a** | Najveći scope | Zavisi od 5-3a (resource URL logika) |

### Success Criteria

1. Svi DOI-evi generisani kroz portal imaju ispravan `<resource>` URL koji vodi na landing page
2. Language polja koriste Select widget sa predefinisanim ISO 639-1 jezicima
3. Korisnik može regenerisati XML nakon ispravke podataka
4. (Ako odobreno) Korisnik može konfigurisati da DOI pokazuje na sajt izdavača

---

## 6. Odobrenje

- [x] Sprint Change Proposal odobren (2026-03-07)
- [x] Story 3-1a: **MVP** — odobreno za MVP scope
- [x] Patch stories kreirane i dodane u sprint-status.yaml:
  - `5-3a-fix-resource-url.md` (ready-for-dev)
  - `2-4a-language-select-widget.md` (ready-for-dev)
  - `3-1a-external-landing-page-pdf-url.md` (ready-for-dev)
  - Story 5-7 notirana za proširenje sa regenerisanje zahtevom
