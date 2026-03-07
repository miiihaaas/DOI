# Potrebne ispravke - DOI Portal

## 1. Višejezičnost publikacija i članaka

### Problem

Na stranici za kreiranje/edit publikacije (npr. `/dashboard/publications/zbornik-radova-narodnog-muzeja/edit/`), polje **jezik** (`language`) je trenutno `CharField(max_length=10)` koje prima samo jedan ISO 639-1 kod (npr. `sr`). Korisnici žele mogućnost da publikacija bude označena na više jezika.

### Analiza Crossref XML specifikacije

Prema Crossref dokumentaciji i XSD shemi 5.4.0:

1. **`language` atribut na metadata elementima** (`journal_metadata`, `book_metadata`, `proceedings_metadata`) prima **samo jedan** ISO 639 kod. Ne podržava listu jezika.

2. **Višejezičnost se u Crossref-u rešava na druge načine:**
   - **Naslovi:** Primarni naslov ide u `<title>`, a prevod u `<original_language_title language="xx">` element
   - **Apstrakti:** Mogu se uključiti na više jezika unutar jednog zapisa
   - **Članci/radovi:** Svaki članak ima svoj `language` atribut — tako zbornik na srpskom može imati članke na engleskom

3. **Za prevode kao zasebne publikacije:** Crossref preporučuje registraciju zasebnih DOI-jeva povezanih sa `hasTranslation` relationship metadata-om.

### Trenutno stanje u kodu

| Fajl | Polje | Tip | Opis |
|------|-------|-----|------|
| `publications/models.py:90` | `Publication.language` | `CharField(max_length=10)` | Jedan jezik, default `sr` |
| `articles/models.py:148` | `Article.language` | `CharField(max_length=10)` | Jedan jezik, default `sr` |
| `publications/forms.py:87` | Widget | `TextInput` | Placeholder: `sr` |
| `articles/forms.py:97` | Widget | `TextInput` | Placeholder: `npr. sr, en` |
| XML šabloni | `language="{{ publication.language }}"` | Atribut | Koristi se u `journal_metadata`, `book_metadata`, `proceedings_metadata` |

### Predloženo rešenje

#### A) Publikacija — primarni jezik ostaje jedan (Crossref zahtev)

Crossref `language` atribut na metadata elementu prima samo jedan kod, tako da `Publication.language` **treba da ostane jedan jezik** — to je primarni jezik publikacije.

**Izmene:**
- Zameniti `TextInput` sa `Select` widget-om koji nudi ISO 639-1 jezike (najčešće: sr, en, de, fr, it, ru, es, hr, bs, sl, mk, bg)
- Dodati help text: _"Primarni jezik publikacije. Članci/radovi mogu biti na različitim jezicima."_

#### B) Članci/radovi — jezik po članku (već postoji)

`Article.language` već postoji i podržava različit jezik po članku. To je ispravan pristup jer u Crossref XML-u svaki `<journal_article>`, `<conference_paper>` ili `<content_item>` može imati svoj jezik.

**Izmene:**
- Zameniti `TextInput` sa `Select` widget-om (ista lista jezika)
- Osigurati da se `article.language` koristi u XML šablonima na nivou članka (ako se već ne koristi)

#### C) Višejezični naslovi (opciono, budući razvoj)

Za publikacije koje imaju naslov na više jezika, dodati podršku za `original_language_title`:

**Model izmene:**
```python
# articles/models.py
original_language_title = models.CharField(
    _("Naslov na originalnom jeziku"),
    max_length=500,
    blank=True,
    help_text=_("Ako se naslov razlikuje od primarnog jezika publikacije"),
)
original_language_code = models.CharField(
    _("Jezik originalnog naslova"),
    max_length=10,
    blank=True,
)
```

**XML šablon izmena:**
```xml
<titles>
  <title>{{ article.title }}</title>
  {% if article.original_language_title %}
  <original_language_title language="{{ article.original_language_code }}">
    {{ article.original_language_title }}
  </original_language_title>
  {% endif %}
</titles>
```

### Plan implementacije

| Korak | Opis | Prioritet | Složenost |
|-------|------|-----------|-----------|
| 1.1 | Kreirati konstantu `LANGUAGE_CHOICES` sa listom ISO 639-1 jezika | Visok | Niska |
| 1.2 | Zameniti `TextInput` sa `Select` widget-om za `Publication.language` | Visok | Niska |
| 1.3 | Zameniti `TextInput` sa `Select` widget-om za `Article.language` | Visok | Niska |
| 1.4 | Dodati help text na `Publication.language` koji objašnjava da članci mogu imati različite jezike | Visok | Niska |
| 1.5 | Proveriti da XML šabloni koriste `article.language` na nivou članka/rada | Visok | Srednja |
| 1.6 | (Opciono) Dodati `original_language_title` i `original_language_code` polja na `Article` model | Nizak | Srednja |
| 1.7 | (Opciono) Ažurirati XML šablone za `original_language_title` podršku | Nizak | Srednja |

### Napomena

Crossref **ne podržava** navođenje više jezika na jednom metadata elementu. Rešenje za višejezični zbornik je:
- Publikacija ima **primarni jezik** (npr. `sr`)
- Svaki članak/rad ima **svoj jezik** (npr. jedan članak `sr`, drugi `en`)
- Opcionalno: članak može imati **naslov na drugom jeziku** kroz `original_language_title`

---

## 2. BUG: `<resource>` element u XML-u je kružna referenca

### Problem

XML šabloni za sve tipove publikacija generišu **pogrešan** `<resource>` URL u `<doi_data>` elementu:

```xml
<!-- TRENUTNO STANJE (POGREŠNO) -->
<doi_data>
  <doi>10.65845/pomology.2022.56.213_214.2</doi>
  <resource>https://doi.org/10.65845/pomology.2022.56.213_214.2</resource>
</doi_data>
```

`<resource>` element u Crossref XML-u definiše **destinaciju** — URL na koji Crossref redirectuje korisnika kada klikne na DOI link. Trenutno `<resource>` pokazuje na sam `doi.org` URL, što stvara **kružnu referencu**:

```
Čitalac klikne DOI: doi.org/10.65845/...
        ↓
Crossref gleda <resource> da vidi gde da redirectuje
        ↓
<resource> = doi.org/10.65845/...  ← ISTI URL!
        ↓
🔄 Kružna referenca (DOI pokazuje na samog sebe)
```

### Pogođeni fajlovi

| Fajl | Linija | Trenutna vrednost |
|------|--------|-------------------|
| `crossref/templates/crossref/journal_article.xml.j2` | 126 | `https://doi.org/{{ publisher.doi_prefix }}/{{ article.doi_suffix }}` |
| `crossref/templates/crossref/conference_paper.xml.j2` | 134 | `https://doi.org/{{ publisher.doi_prefix }}/{{ article.doi_suffix }}` |
| `crossref/templates/crossref/book_chapter.xml.j2` | 111 | `https://doi.org/{{ publisher.doi_prefix }}/{{ article.doi_suffix }}` |

### Kako treba da funkcioniše

`<resource>` treba da sadrži stvarni URL landing stranice članka — mesto gde čitalac može da pročita metapodatke i pristupi PDF-u.

**Primer sa konkretnim člankom:**
```
DOI:     10.65845/pomology.2022.56.213_214.2
Časopis: Voćarstvo (Journal of Pomology)
Naslov:  Dugotrajno čuvanje germplazme voćaka...
```

**Scenario A — Landing page na portalu (doi.rs):**
```xml
<doi_data>
  <doi>10.65845/pomology.2022.56.213_214.2</doi>
  <resource>https://publikacije.doi.rs/articles/123/</resource>
</doi_data>
```
Čitalac klikne DOI → Crossref redirectuje na portal → vidi landing stranicu sa metapodacima i PDF-om.

**Scenario B — Landing page na sajtu izdavača:**
```xml
<doi_data>
  <doi>10.65845/pomology.2022.56.213_214.2</doi>
  <resource>https://www.casopisnvd.rs/clanak/pomology-2022-56-213-214-2</resource>
</doi_data>
```
Čitalac klikne DOI → Crossref redirectuje na sajt izdavača → izdavač prikazuje članak.

### Predloženo rešenje

Ova ispravka je **preduslov** za tačku 3 (eksterni landing page), ali se mora rešiti i sama za sebe.

**Korak 2.1:** Generisati ispravan portal URL za `<resource>`:
```xml
<resource>https://publikacije.doi.rs/articles/{{ article.pk }}/</resource>
```
Ovo zahteva prosleđivanje `site_url` varijable u XML šablon kontekst.

**Korak 2.2:** Kad se implementira podrška za eksterni URL (tačka 3), logika postaje:
```xml
<resource>
  {% if article.use_external_resource and article.external_landing_url %}
    {{ article.external_landing_url }}
  {% else %}
    {{ site_url }}/articles/{{ article.pk }}/
  {% endif %}
</resource>
```

### Prioritet: KRITIČAN

Ovo je bug koji utiče na **svaki registrovani DOI**. Dok se ne popravi, nijedan DOI registrovan preko portala neće ispravno redirectovati čitaoce na landing stranicu.

---

## 3. Podrška za eksterni landing page i PDF (sajt izdavača)

### Problem

Neki izdavači imaju sopstveni sajt gde objavljuju članke (npr. `casopisnvd.rs`). Trenutno portal podržava samo scenario gde se landing stranica i PDF nalaze na portalu (`publikacije.doi.rs`). Potrebno je omogućiti da DOI pokazuje na sajt izdavača umesto na portal.

### Predloženo rešenje

Dodati **switch dugme** na formi za kreiranje/izmenu članka koje otvara polja za unos eksternog URL-a. Članak se i dalje kompletno popunjava na portalu (metapodaci, PDF), ali `<resource>` u Crossref XML-u može da pokazuje na sajt izdavača.

### Nova polja na Article modelu

```python
# articles/models.py
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

### UX na formi (switch dugme)

```
┌─────────────────────────────────────────────────────┐
│  PDF fajl:  [Izaberite fajl]                        │
│                                                     │
│  ☐ Članak se nalazi i na sajtu izdavača             │
│                                                     │
│  ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐  │
│  │ (skriveno dok se ne uključi switch)           │  │
│  │                                               │  │
│  │ Landing stranica izdavača:                    │  │
│  │ [https://www.casopisnvd.rs/clanak/...]        │  │
│  │                                               │  │
│  │ PDF na sajtu izdavača (opciono):              │  │
│  │ [https://www.casopisnvd.rs/pdf-dow/...]       │  │
│  │                                               │  │
│  │ ⓘ DOI broj će pokazivati na sajt izdavača.   │  │
│  │   Podaci na portalu služe kao backup.         │  │
│  └─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘  │
└─────────────────────────────────────────────────────┘
```

### Ponašanje sistema

| Scenario | `<resource>` u XML | Landing na portalu | PDF download na portalu |
|----------|--------------------|--------------------|-------------------------|
| Switch ISKLJUČEN | Portal URL (`publikacije.doi.rs/articles/X/`) | Prikazuje lokalne podatke | Servira lokalni PDF |
| Switch UKLJUČEN | Eksterni URL (`casopisnvd.rs/clanak/...`) | Prikazuje lokalne podatke + link ka originalu | Servira lokalni PDF + link ka eksternom PDF-u |

### Prednosti pristupa

1. **Backup podataka** — PDF i metapodaci su uvek na portalu, čak i ako izdavač ugasi sajt
2. **Fleksibilnost** — Služi obe kategorije izdavača (sa i bez sopstvenog sajta)
3. **Crossref kompatibilnost** — `<resource>` prima bilo koji validan URL
4. **Jednostavan UX** — Switch dugme ne komplikuje formu za izdavače koji nemaju sajt

### Rizici i napomene

1. **Sinhronizacija** — Nema garancije da su podaci na portalu i sajtu izdavača identični. Izdavač može promeniti PDF na svom sajtu. Ovo nije kritično jer portal služi kao arhivska kopija.
2. **Validacija URL-a** — Eksterni URL može postati nedostupan (404). Razmotriti periodičnu proveru dostupnosti (budući razvoj).
3. **Validacija forme** — Ako je switch uključen, `external_landing_url` mora biti obavezno polje.

### Plan implementacije

| Korak | Opis | Prioritet | Složenost |
|-------|------|-----------|-----------|
| 3.1 | Dodati `use_external_resource`, `external_landing_url`, `external_pdf_url` polja na `Article` model | Visok | Niska |
| 3.2 | Kreirati migraciju | Visok | Niska |
| 3.3 | Dodati polja na `ArticleForm` sa switch UX-om (HTMX toggle za prikaz/skrivanje) | Visok | Srednja |
| 3.4 | Dodati validaciju: ako je switch uključen, `external_landing_url` je obavezan | Visok | Niska |
| 3.5 | Ažurirati XML šablone da koriste eksterni URL kad je switch uključen | Visok | Niska |
| 3.6 | Ažurirati landing page template da prikaže link ka originalnom sajtu izdavača | Srednji | Niska |
| 3.7 | Ažurirati PDF download da ponudi i link ka eksternom PDF-u | Nizak | Niska |

---

## 4. Nedostaje dugme za regenerisanje XML-a nakon ispravke podataka

### Problem

Na stranici izdanja (`/dashboard/issues/2/`), jednom kad se Crossref XML generiše, dugme "Generiši XML" nestaje i korisnik **nema mogućnost da ponovo generiše XML** nakon što ispravi podatke.

### Trenutno ponašanje u template-u

U `templates/issues/issue_detail.html` (linije 196-249), logika je:

```
{% if issue.crossref_xml %}
    → Prikazuje: badge "Generisan", datum, XSD status
    → Dugmad: "Pregled XML" i "Preuzmi XML"
    → NEMA dugmeta za regenerisanje ❌
{% else %}
    → Prikazuje: "XML nije generisan"
    → Validacioni panel (HTMX auto-load)
    → Dugme: "Generiši XML"
{% endif %}
```

### Scenario problema

1. Korisnik generiše XML za izdanje
2. XSD validacija javlja 1 grešku (npr. nedostaje ISSN)
3. Korisnik ode na publikaciju i doda ISSN
4. Korisnik se vrati na stranicu izdanja
5. Vidi: "XSD validacija: 1 greške" — ali **nema dugme** da regeneriše XML sa ispravljenim podacima

### Predloženo rešenje

Dodati dugme **"Regeneriši XML"** u sekciju koja se prikazuje kad XML već postoji. Dugme treba da:
- Bude vidljivo uvek kad XML postoji (ispod dugmadi "Pregled" i "Preuzmi")
- Pokrene istu `GenerateXMLView` (POST na `crossref:issue-generate`)
- Nakon uspešnog regenerisanja, osveži Crossref XML karticu sa novim statusom

### Izmena u template-u

```html
<!-- U sekciji {% if issue.crossref_xml %}, nakon postojećih dugmadi -->
<hr class="my-3">
<button type="button"
        class="btn btn-outline-warning w-100"
        hx-post="{% url 'crossref:issue-generate' issue.pk %}"
        hx-target="#generation-result"
        hx-swap="innerHTML"
        hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'
        hx-confirm="Da li ste sigurni? Postojeći XML će biti zamenjen novim.">
    <i class="bi bi-arrow-clockwise me-1"></i>Regeneriši XML
</button>
<div id="generation-result" class="mt-2"></div>
```

### Dodatno razmotriti

- Da li `GenerateXMLView` treba da osveži celu Crossref karticu nakon regenerisanja (HTMX `hx-swap="outerHTML"` na kartici) umesto samo `#generation-result` diva
- Da li prikazati i validacioni panel pre regenerisanja (kao što se prikazuje pre prvog generisanja)

### Plan implementacije

| Korak | Opis | Prioritet | Složenost |
|-------|------|-----------|-----------|
| 4.1 | Dodati dugme "Regeneriši XML" u `issue_detail.html` kad XML postoji | Visok | Niska |
| 4.2 | Osigurati da `GenerateXMLView` ispravno zamenjuje postojeći XML u bazi | Visok | Niska (proveriti da već radi) |
| 4.3 | Nakon regenerisanja, osvežiti Crossref karticu sa novim XSD statusom | Visok | Srednja |
| 4.4 | (Opciono) Dodati validacioni panel i u sekciju gde XML već postoji | Nizak | Niska |
