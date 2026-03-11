# Prompt za Tech Spec: Markup podrška, Funding info, Afilijacija proširenje, Keyword reordering

**Datum:** 2026-03-11

---

## Kontekst projekta

Django portal za upravljanje DOI metapodacima i generisanje Crossref XML-a. Tech stack: Python 3.13, Django 5.2+, PostgreSQL, HTMX 2.0.8, Alpine.js 3.15.3, Bootstrap 5.3+, Jinja2 za XML template-e. UI je na srpskom (sr-Latn). Dependency manager: `uv` sa `pyproject.toml`.

Projekat koristi auto-save pattern (HTMX `hx-trigger="change delay:2s"`), SortableJS za drag-and-drop (već uključen za autore), Alpine.js komponente za interaktivne forme, i services layer za business logiku.

---

## Stavka 1: Markup podrška za tekstualna polja (Face Markup)

### Problem

Korisnički uneta tekstualna polja (naslov, podnaslov, apstrakt) se prikazuju na landing stranici i u Crossref XML-u kao plain text. Potrebna je podrška za inline formatiranje: italic (npr. nazivi vrsta _Escherichia coli_), bold, subscript (H~2~O), superscript (x^2^), i ćirilični navodnici „primer".

### Crossref standard

Crossref šema 5.4.0 podržava **face markup** u sledećim XML elementima:
- `<title>`, `<subtitle>`, `<original_language_title>` — tagovi: `<i>`, `<b>`, `<sub>`, `<sup>`
- U `<jats:abstract><jats:p>` — JATS standard podržava inline markup
- Face markup u imenima autora **NIJE dozvoljen**

### Markup sintaksa za korisnički unos

Korisnici unose lightweight markup u tekstualna polja:

| Unos | Značenje | HTML (landing stranica) | Crossref XML |
|------|----------|------------------------|--------------|
| `_tekst_` | Italic | `<em>tekst</em>` | `<i>tekst</i>` |
| `**tekst**` | Bold | `<strong>tekst</strong>` | `<b>tekst</b>` |
| `~tekst~` | Subscript | `<sub>tekst</sub>` | `<sub>tekst</sub>` |
| `^tekst^` | Superscript | `<sup>tekst</sup>` | `<sup>tekst</sup>` |
| `„tekst"` | Ćirilični navodnici | `„tekst"` (bez konverzije, Unicode) | `„tekst"` (Unicode) |

### Polja koja podržavaju markup

- `title` (Article model)
- `subtitle` (Article model)
- `original_language_title` (Article model)
- `original_language_subtitle` (Article model)
- `abstract` (Article model)

**Keywords NE podržavaju markup.**

### Implementacija: Markup parser

Kreirati utility modul (npr. `core/markup.py` ili `articles/markup.py`) sa funkcijama:

1. `markup_to_html(text: str) -> str` — konvertuje lightweight markup u HTML za prikaz na landing stranici. Mora escapovati HTML pre konverzije (sprečiti XSS). Redosled parsiranja: escape HTML → bold (`**...**`) → italic (`_..._`) → superscript (`^...^`) → subscript (`~...~`). Navodnici „..." ostaju kao Unicode.

2. `markup_to_crossref_xml(text: str) -> str` — konvertuje lightweight markup u Crossref face markup tagove (`<i>`, `<b>`, `<sub>`, `<sup>`). Mora escapovati XML entitete pre konverzije. Navodnici ostaju kao Unicode.

3. `strip_markup(text: str) -> str` — uklanja markup sintaksu i vraća čist tekst (za meta description, search indexing, itd.)

**Regex pattern primeri:**
- Italic: `_([^_]+)_` (pazi da ne hvata `__` ili `_` u sredini reči — koristi word boundary ili negative lookbehind/lookahead)
- Bold: `\*\*([^*]+)\*\*`
- Superscript: `\^([^^]+)\^`
- Subscript: `~([^~]+)~`

**Važna napomena:** Markup parser mora biti robustan — ne sme da padne na edge case-ovima (neupareni delimiteri, prazni stringovi, nested markup). Neupareni delimiteri treba da ostanu kao literal tekst.

### Implementacija: Landing stranica

Ažurirati `templates/portal/article_detail.html`:
- Polja title, subtitle, abstract renderovati sa `markup_to_html` (custom template filter ili poziv u view context-u)
- Koristiti `|safe` filter SAMO nakon markup_to_html konverzije (jer ona radi HTML escape pre konverzije)
- Search card partial (`_article_search_card.html`) — koristiti `strip_markup` za čist tekst u search rezultatima, ili `markup_to_html` za formatirani prikaz

### Implementacija: Crossref XML

Ažurirati Crossref service (`crossref/services.py`) metodu `_build_context`:
- Title, subtitle, original_language_title, original_language_subtitle, abstract — konvertovati sa `markup_to_crossref_xml` pre prosleđivanja u template context
- Ažurirati Jinja2 template-e da NE escapuju ova polja (jer markup_to_crossref_xml već upravlja XML escape-om)

### Implementacija: Help sekcija na admin stranicama

Na stranicama za uređivanje članaka (`articles/article_form.html`) dodati sekciju/karticu pomoći za formatiranje koja sadrži:

1. **Tabelu sintakse** sa primerima — šta korisnik unosi i kako to izgleda na landing stranici (live rendered primer)
2. **Sekciju sa specijalnim karakterima za kopiranje** — korisnik može kliknuti/kopirati specifične karaktere direktno iz help sekcije i zalepiti ih u polja. Karakteri za kopiranje:
   - `„` i `"` — ćirilični navodnici (otvoreni i zatvoreni)
   - `_` — delimiter za italic
   - `**` — delimiter za bold
   - `~` — delimiter za subscript
   - `^` — delimiter za superscript
3. **Interaktivni primer** — tekstualno polje gde korisnik može da unese tekst sa markup-om i odmah vidi kako će izgledati (mini preview)

Help sekcija treba da bude collapsible (Bootstrap accordion ili collapse), podrazumevano zatvorena, sa jasnim naslovom kao „Pomoć za formatiranje teksta".

Implementirati copy-to-clipboard funkcionalnost za specijalne karaktere (koristi `navigator.clipboard.writeText()` ili fallback sa `document.execCommand('copy')`). Svaki karakter treba da ima mali dugme za kopiranje pored sebe. Nakon uspešnog kopiranja — kratki vizuelni feedback (tooltip „Kopirano!" ili promena ikonice).

### Primer kompletnog unosa sa svim markup-ovima

**Unos:**
```
Analiza _Staphylococcus aureus_ u **urbanim** sredinama: H~2~O i CO~2~ koncentracija na x^2^ + y^2^ sa „posebnim" osvrtom
```

**Landing stranica (HTML):**
```
Analiza <em>Staphylococcus aureus</em> u <strong>urbanim</strong> sredinama: H<sub>2</sub>O i CO<sub>2</sub> koncentracija na x<sup>2</sup> + y<sup>2</sup> sa „posebnim" osvrtom
```

**Crossref XML:**
```xml
Analiza <i>Staphylococcus aureus</i> u <b>urbanim</b> sredinama: H<sub>2</sub>O i CO<sub>2</sub> koncentracija na x<sup>2</sup> + y<sup>2</sup> sa „posebnim" osvrtom
```

---

## Stavka 2: Proširenje afilijacija — mesto, država i ROR autocomplete

### Problem

Afilijacija autora trenutno sadrži `institution_name`, `institution_ror_id` i `department`. Potrebno je dodati mesto (grad) i državu, i implementirati autocomplete pretragu institucija preko ROR API-ja.

### Trenutni model (Affiliation)

```python
class Affiliation(models.Model):
    author = models.ForeignKey(Author, related_name="affiliations", on_delete=models.CASCADE)
    institution_name = models.CharField(max_length=500)
    institution_ror_id = models.URLField(blank=True)
    department = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
```

### Nova polja

Dodati u Affiliation model:
- `city` — CharField(max_length=255, blank=True) — Grad institucije
- `country` — CharField(max_length=255, blank=True) — Država institucije

Ova polja se NE šalju u Crossref XML (Crossref nema location polja u `<institution>` elementu). Koriste se samo za prikaz na landing stranici.

### ROR API Autocomplete

**ROR API endpoint:** `https://api.ror.org/v2/organizations?query={search_term}`

ROR API je **besplatan**, otvoren, ne zahteva API ključ ni autentifikaciju.

**Response struktura (relevantna polja):**
```json
{
  "items": [
    {
      "id": "https://ror.org/01bj3aw27",
      "names": [
        {"value": "University of Belgrade", "types": ["ror_display"]},
        {"value": "Универзитет у Београду", "types": ["label"], "lang": "sr"}
      ],
      "locations": [
        {
          "geonames_details": {
            "name": "Belgrade",
            "country_name": "Serbia",
            "country_code": "RS"
          }
        }
      ],
      "status": "active"
    }
  ]
}
```

### Implementacija: Backend endpoint

Kreirati Django view (FBV, HTMX endpoint) u `articles/` app-u:
- URL: `articles/api/ror-search/` (ili sličan)
- Parametar: `?q=search_term`
- Proxira zahtev ka ROR API-ju (server-side, da se izbegne CORS)
- Vraća HTML partial sa listom rezultata (za HTMX dropdown) ili JSON (za Alpine.js)
- Cachirati rezultate (Django cache, kratki TTL npr. 1h) da se smanji broj zahteva ka ROR-u

### Implementacija: Frontend autocomplete

Na formi za afilijaciju (inline formset unutar article_form.html):
- Input za `institution_name` dobija autocomplete ponašanje
- Korisnik kuca → debounced zahtev (300ms) ka backend endpoint-u → prikaže se dropdown lista rezultata
- Kada korisnik izabere instituciju iz dropdown-a:
  - `institution_name` ← ime institucije (ror_display name)
  - `institution_ror_id` ← ROR URL
  - `city` ← `locations[0].geonames_details.name`
  - `country` ← `locations[0].geonames_details.country_name`
- Korisnik MOŽE i ručno uneti sve (bez ROR-a) — sva polja opciona osim `institution_name`
- Korisnik MOŽE izmeniti auto-popunjena polja nakon izbora

Implementirati sa Alpine.js komponentom (konzistentno sa ostatkom projekta).

### Implementacija: Landing stranica

Ažurirati prikaz afilijacija u `article_detail.html`:

Trenutno:
```
{{ affiliation.institution_name }}{% if affiliation.department %}, {{ affiliation.department }}{% endif %}
```

Novo:
```
{{ affiliation.institution_name }}{% if affiliation.department %}, {{ affiliation.department }}{% endif %}{% if affiliation.city %}, {{ affiliation.city }}{% endif %}{% if affiliation.country %}, {{ affiliation.country }}{% endif %}
```

Primer prikaza: *Tehnološko-metalurški fakultet, Katedra za hemiju, Beograd, Srbija*

### Crossref XML

Bez promena u XML template-u — `city` i `country` se ne šalju. Crossref `<institution>` element podržava samo: `<institution_name>`, `<institution_id>`, `<institution_department>`.

---

## Stavka 3: Funding info (Podaci o projektima/finansiranju)

### Problem

Članci često nastaju u okviru naučnih projekata. Potrebno je omogućiti unos podataka o finansijeru i broju projekta, prikaz na landing stranici, i slanje u Crossref XML (FundRef standard).

### Crossref standard (FundRef)

Crossref podržava funding info kroz `fr:program` namespace:

```xml
<fr:program name="fundref" xmlns:fr="http://www.crossref.org/fundref.xsd">
  <fr:assertion name="fundgroup">
    <fr:assertion name="funder_name">Ministarstvo nauke, tehnološkog razvoja i inovacija
      <fr:assertion name="funder_identifier">https://doi.org/10.13039/501100004564</fr:assertion>
    </fr:assertion>
    <fr:assertion name="award_number">OI-172015</fr:assertion>
  </fr:assertion>
</fr:program>
```

Funding info je **opciona** u Crossref-u. Pozicionira se unutar `<journal_article>` elementa, nakon `<ai:program>` (AccessIndicators) a pre `<doi_data>`.

### Novi model: ArticleFunding

```python
class ArticleFunding(models.Model):
    article = models.ForeignKey(Article, related_name="fundings", on_delete=models.CASCADE)
    funder_name = models.CharField(max_length=500)  # Obavezno - naziv finansijera
    funder_doi = models.URLField(blank=True)  # Open Funder Registry DOI (npr. https://doi.org/10.13039/501100004564)
    funder_ror_id = models.URLField(blank=True)  # ROR ID finansijera (alternativa DOI-u)
    award_number = models.CharField(max_length=255, blank=True)  # Broj projekta/granta
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
```

Jedan članak može imati **više** funding zapisa (više projekata/finansijera).

### Open Funder Registry Autocomplete

**Open Funder Registry** je besplatan, otvoren registar finansijera istraživanja, koji održava Crossref. Može se pretraživati putem Crossref REST API-ja.

**API endpoint:** `https://api.crossref.org/funders?query={search_term}`

**Response struktura:**
```json
{
  "message": {
    "items": [
      {
        "id": "501100004564",
        "name": "Ministarstvo Prosvete, Nauke i Tehnološkog Razvoja",
        "alt-names": ["Ministry of Education, Science and Technological Development"],
        "location": "Serbia",
        "uri": "https://doi.org/10.13039/501100004564"
      }
    ]
  }
}
```

### Implementacija: Backend endpoint

Kreirati Django view u `articles/` app-u:
- URL: `articles/api/funder-search/`
- Parametar: `?q=search_term`
- Proxira zahtev ka Crossref Funders API-ju
- Cachirati rezultate (Django cache, TTL 1h)
- Vraća HTML partial ili JSON za Alpine.js dropdown

### Implementacija: Frontend forma

Na stranici za uređivanje članaka (`article_form.html`):
- Sekcija „Finansiranje" (Funding) — dodati kao novu sekciju, posle autora ili posle metapodataka
- Inline formset (kao za autore/afilijacije) sa:
  - `funder_name` — input sa autocomplete (Open Funder Registry)
  - `funder_doi` — auto-popunjava se pri izboru iz autocomplete-a
  - `award_number` — slobodan tekst unos
- Dodaj/obriši dugmad za više funding zapisa
- Drag-and-drop reordering (SortableJS)
- Kada korisnik izabere finansijera iz autocomplete dropdown-a:
  - `funder_name` ← naziv
  - `funder_doi` ← URI iz registra
- Korisnik MOŽE i ručno uneti (bez autocomplete-a)

### Implementacija: Landing stranica

Dodati novu sekciju u `article_detail.html`, nakon Keywords sekcije:

```html
{% if article.fundings.exists %}
<section class="article-funding mb-4" aria-labelledby="funding-heading">
  <h2 id="funding-heading" class="h5 mb-3">Finansiranje</h2>
  {% for funding in article.fundings.all %}
  <div class="mb-1">
    <span class="fw-semibold">{{ funding.funder_name }}</span>
    {% if funding.award_number %}
    <span class="text-muted">— Projekat br. {{ funding.award_number }}</span>
    {% endif %}
  </div>
  {% endfor %}
</section>
{% endif %}
```

### Implementacija: Crossref XML

1. Dodati `xmlns:fr="http://www.crossref.org/fundref.xsd"` namespace u root `<doi_batch>` element sva tri XML template-a (journal_article.xml.j2, conference_paper.xml.j2, book_chapter.xml.j2).

2. Dodati funding blok unutar `<journal_article>` (i odgovarajućih elemenata u drugim template-ima), nakon `<ai:program>` a pre `<doi_data>`:

```xml
{% if article.fundings %}
<fr:program name="fundref">
  {% for funding in article.fundings %}
  <fr:assertion name="fundgroup">
    {% if funding.funder_ror_id %}
    <fr:assertion name="ror">{{ funding.funder_ror_id }}</fr:assertion>
    {% endif %}
    {% if funding.funder_name %}
    <fr:assertion name="funder_name">{{ funding.funder_name }}
      {% if funding.funder_doi %}
      <fr:assertion name="funder_identifier">{{ funding.funder_doi }}</fr:assertion>
      {% endif %}
    </fr:assertion>
    {% endif %}
    {% if funding.award_number %}
    <fr:assertion name="award_number">{{ funding.award_number }}</fr:assertion>
    {% endif %}
  </fr:assertion>
  {% endfor %}
</fr:program>
{% endif %}
```

3. Ažurirati `_build_context` u `crossref/services.py` da uključi funding podatke u article context.

---

## Stavka 4: Keyword reordering (Promena redosleda ključnih reči)

### Problem

Ključne reči se čuvaju kao JSON lista u `Article.keywords` polju. Redosled je bitan jer se tako prikazuju na landing stranici i u metapodacima. Trenutno nema mogućnosti za promenu redosleda — jedini način je brisanje i ponovo dodavanje.

### Trenutna implementacija

- Model: `keywords = models.JSONField(default=list, blank=True)`
- Template: Alpine.js `keywordsInput()` komponenta sa add/remove funkcionalnostima
- SortableJS je **već uključen** na stranici (koristi se za reordering autora)
- Keywords se prikazuju kao Bootstrap badge-evi u flex kontejneru

### Implementacija

Proširiti postojeću Alpine.js `keywordsInput()` komponentu u `article_form.html`:

1. **Dodati drag-and-drop** na keywords kontejner koristeći SortableJS (isti pristup kao za autore):
   - Inicijalizovati `Sortable.create()` na keywords wrapper elementu
   - `onEnd` callback — ažurirati redosled u Alpine.js `keywords` nizu
   - Vizuelni indikator — cursor grab na badge-ovima, highlight pri drag-u

2. **HTML izmene:**
   - Wrapper div za keywords badge-ove treba da ima `x-ref="keywordsList"` za SortableJS inicijalizaciju
   - Svaki badge treba da ima `data-index` atribut
   - Dodati drag handle ikonicu (npr. `bi-grip-vertical`) na svaki badge

3. **Ponašanje:**
   - Drag-and-drop menja redosled u `keywords` nizu
   - Nakon promene redosleda — triggerovati auto-save (dispatch change event na hidden input, isto kao pri add/remove)
   - Funkcioniše zajedno sa postojećim add/remove

---

## Stavka 5: Floating "Sačuvaj izmene" dugme

### Problem

Na stranici za uređivanje članaka (`articles/article_form.html`) dugme "Sačuvaj izmene" se nalazi na samom dnu forme, unutar normalnog document flow-a. Forma je dugačka (osnovne informacije, autori, afilijacije, ključne reči, itd.), pa korisnik mora da skroluje do dna da bi pronašao dugme. Ovo dovodi do zabune — nije jasno uočljivo, posebno kad korisnik radi izmene na vrhu ili sredini forme.

### Trenutna implementacija

```html
<div class="d-flex justify-content-between mt-4">
    <a href="{% url 'articles:list' %}" class="btn btn-outline-secondary">
        <i class="bi bi-arrow-left me-1"></i>Nazad
    </a>
    <button type="submit" class="btn btn-primary" hx-disinherit="*">
        <i class="bi bi-check-lg me-1"></i>{{ submit_text }}
    </button>
</div>
```

### Implementacija

Pretvoriti oba dugmeta (Nazad i Sačuvaj) u jedan floating "bubble" kontejner fiksiran u donjem desnom uglu ekrana:

1. **Kontejner:** `position: fixed; bottom: 1.5rem; right: 1.5rem; z-index: 1040;` — jedan zaobljeni kontejner (pill/bubble oblik) sa senkom (`box-shadow`) koji sadrži oba dugmeta spojena zajedno
2. **Struktura:** Bootstrap `btn-group` ili custom flex kontejner sa dva dela:
   - **Levi deo:** "Nazad" dugme — `btn-outline-secondary` ili svetlija boja (npr. siva)
   - **Desni deo:** "Sačuvaj izmene" dugme — `btn-primary` ili `btn-success` (istaknuta boja)
3. **Stilizacija:** Oba dugmeta su spojena bez razmaka, zajednički zaobljeni uglovi (levo dugme ima zaobljenje levo, desno dugme zaobljenje desno), veći font (`btn-lg`), izražena senka za floating efekat
4. **Responsive:** Na mobilnim uređajima bubble može biti širi ili centriran na dnu ekrana
5. **Ukloniti** postojeći `<div class="d-flex justify-content-between mt-4">` blok sa dna forme jer se oba dugmeta sele u floating bubble

**Napomena:** Forma već ima auto-save (HTMX `change delay:2s`), ali eksplicitno submit dugme je i dalje potrebno za finalno čuvanje i validaciju. Floating pozicija čini oba dugmeta uvek dostupnim bez skrolovanja.

---

## Fajlovi za izmenu (svi putevi relativni od `doi_portal/doi_portal/`)

| Fajl | Stavka | Izmena |
|------|--------|--------|
| `articles/models.py` | 2, 3 | Novi model ArticleFunding, nova polja city/country u Affiliation |
| `articles/forms.py` | 2, 3 | AffiliationForm proširenje, novi ArticleFundingForm, formset |
| `articles/views.py` | 2, 3 | ROR search endpoint, Funder search endpoint, funding CRUD |
| `articles/urls.py` | 2, 3 | Novi URL-ovi za API endpoint-e |
| `articles/admin.py` | 3 | Registracija ArticleFunding modela |
| `core/markup.py` (NOV) | 1 | Markup parser utility (markup_to_html, markup_to_crossref_xml, strip_markup) |
| `core/templatetags/markup_tags.py` (NOV) | 1 | Template filteri: `render_markup`, `strip_markup` |
| `templates/articles/article_form.html` | 1, 3, 4, 5 | Help sekcija za markup, Funding sekcija, Keyword drag-and-drop, Floating submit |
| `templates/portal/article_detail.html` | 1, 2, 3 | Markup rendering, afilijacija mesto/država, funding sekcija |
| `templates/portal/partials/_article_search_card.html` | 1 | Strip markup u search rezultatima |
| `crossref/services.py` | 1, 3 | markup_to_crossref_xml u build_context, funding data u context |
| `crossref/templates/crossref/journal_article.xml.j2` | 1, 3 | Face markup u title/abstract, fr:program funding blok, namespace |
| `crossref/templates/crossref/conference_paper.xml.j2` | 1, 3 | Isto kao gore |
| `crossref/templates/crossref/book_chapter.xml.j2` | 1, 3 | Isto kao gore |

---

## Acceptance Criteria

### Stavka 1: Markup
- [ ] Korisnik može uneti `_italic_`, `**bold**`, `~sub~`, `^sup^` u title, subtitle, original_language_title, original_language_subtitle i abstract
- [ ] Na landing stranici tekst se renderuje sa odgovarajućim HTML formatiranjem
- [ ] U Crossref XML-u tekst sadrži odgovarajuće face markup tagove (`<i>`, `<b>`, `<sub>`, `<sup>`)
- [ ] Generisani XML prolazi XSD validaciju
- [ ] Help sekcija je vidljiva na article edit stranici sa tabelom sintakse i primerima
- [ ] Help sekcija sadrži specijalne karaktere za kopiranje sa copy-to-clipboard funkcionalnosti
- [ ] Help sekcija ima interaktivni preview (unos → prikaz)
- [ ] Neupareni delimiteri ostaju kao literal tekst (ne prave grešku)

### Stavka 2: Afilijacija proširenje
- [ ] Affiliation model ima nova polja: city i country
- [ ] ROR autocomplete radi na institution_name polju
- [ ] Izbor iz ROR-a automatski popunjava institution_name, institution_ror_id, city i country
- [ ] Korisnik može ručno uneti ili izmeniti sva polja
- [ ] Landing stranica prikazuje puno mesto: "Institucija, Departman, Grad, Država"
- [ ] Crossref XML ostaje nepromenjen (city/country se ne šalju)

### Stavka 3: Funding info
- [ ] ArticleFunding model postoji sa funder_name, funder_doi, funder_ror_id, award_number, order
- [ ] Forma za članak ima sekciju "Finansiranje" sa add/remove/reorder
- [ ] Open Funder Registry autocomplete radi za funder_name
- [ ] Izbor iz registra auto-popunjava funder_name i funder_doi
- [ ] Landing stranica prikazuje funding info sekciju
- [ ] Crossref XML sadrži `<fr:program name="fundref">` blok sa korektnom strukturom
- [ ] Generisani XML prolazi XSD validaciju

### Stavka 4: Keyword reordering
- [ ] Ključne reči se mogu reorderovati drag-and-drop-om
- [ ] Promena redosleda triggeruje auto-save
- [ ] Redosled se pravilno čuva i prikazuje na landing stranici
- [ ] Vizuelni indikatori za drag (grab cursor, handle ikonica)

### Stavka 5: Floating action bubble
- [ ] "Nazad" i "Sačuvaj izmene" su spojeni u jedan floating bubble (btn-group) u donjem desnom uglu
- [ ] Bubble je uvek vidljiv bez obzira na poziciju skrola (position: fixed)
- [ ] Levi deo (Nazad) ima svetliju/sivu boju, desni deo (Sačuvaj) ima istaknutu boju
- [ ] Bubble ima zaobljeni pill oblik i senku za floating efekat
- [ ] Stari blok sa dugmadima na dnu forme je uklonjen
- [ ] Responsive ponašanje na mobilnim uređajima

---

## Napomene za implementaciju

1. **Migracije:** Stavke 2 i 3 zahtevaju Django migracije (nova polja, novi model). Pokrenuti `makemigrations` i `migrate`.
2. **Testovi:** Markup parser zahteva temeljno testiranje (edge cases, nested markup, XSS prevencija). Koristiti pytest sa parametrize za sve kombinacije.
3. **Cache:** ROR i Funder API pozivi se cachiraju server-side. Koristiti Django cache framework.
4. **Postojeći podaci:** Nova polja su opciona — postojeći podaci ostaju nepromenjeni.
5. **XSD validacija:** Nakon implementacije, obavezno testirati generisani XML sa Crossref XSD šemom, posebno face markup u title-ovima i fr:program strukturu.
