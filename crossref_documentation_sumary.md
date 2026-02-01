# Specifikacija formi za Crossref DOI registraciju

Ovaj dokument sadrži kompletne specifikacije za kreiranje formi za registraciju DOI brojeva kod Crossref-a za tri tipa publikacija: časopis, zbornik radova i monografija/knjiga.

---

## Sadržaj

1. [Časopis (Journal)](#1-časopis-journal---forma)
2. [Zbornik radova (Conference Proceedings)](#2-zbornik-radova-conference-proceedings---forma)
3. [Monografija / Knjiga (Book)](#3-monografija--knjiga-book---forma)
4. [Zajednički elementi](#zajednički-elementi-za-sve-tipove)
5. [XML zaglavlje](#xml-zaglavlje-head---zajedničko-za-sve-tipove)
6. [Verzija sheme](#preporučena-verzija-sheme)

---

## 1. ČASOPIS (Journal) - Forma

### Struktura XML-a

Glavni kontejner: `<journal>` → `<journal_metadata>` → `<journal_issue>` → `<journal_article>`

### A) Podaci o časopisu (journal_metadata)

| Polje | Obavezno | Tip | Napomena |
|-------|----------|-----|----------|
| full_title | ✅ DA | text | Pun naziv časopisa |
| abbrev_title | Preporučeno | text | Skraćeni naziv |
| issn (print) | ✅ DA* | text | Format: XXXX-XXXX |
| issn (electronic) | Preporučeno | text | e-ISSN |
| coden | Opciono | text | 6-karakterni kod |
| doi (journal-level) | Preporučeno | text | DOI na nivou časopisa |
| url | Preporučeno | URL | URL landing page časopisa |

> *ISSN ili DOI+URL obavezni

### B) Podaci o svesku/broju (journal_issue)

| Polje | Obavezno | Tip |
|-------|----------|-----|
| volume | Preporučeno | number |
| issue | Preporučeno | text |
| publication_date (year) | ✅ DA | YYYY |
| publication_date (month) | Preporučeno | MM |
| publication_date (day) | Opciono | DD |

### C) Podaci o članku (journal_article)

| Polje | Obavezno | Tip | Napomena |
|-------|----------|-----|----------|
| title | ✅ DA | text | Naslov članka |
| subtitle | Opciono | text | Podnaslov |
| contributors | Preporučeno | array | Lista autora |
| publication_date (year) | ✅ DA | YYYY | |
| publication_date (month, day) | Preporučeno | MM, DD | |
| first_page | Preporučeno | text | |
| last_page | Preporučeno | text | |
| article_number | Opciono | text | Za online-only članke |
| doi | ✅ DA | text | Format: 10.XXXX/suffix |
| resource_url | ✅ DA | URL | Landing page članka |
| abstract | Preporučeno | text (JATS) | U JATS formatu |
| publication_type | ✅ DA | select | full_text, abstract_only, bibliographic_record |
| language | Preporučeno | select | ISO639 kod (sr, en, de...) |

### Primer XML strukture za časopis
```xml
<journal>
  <journal_metadata language="en">
    <full_title>Naziv časopisa</full_title>
    <abbrev_title>Skraćeni naziv</abbrev_title>
    <issn media_type="print">0000-0000</issn>
    <issn media_type="electronic">0000-0001</issn>
  </journal_metadata>
  <journal_issue>
    <publication_date media_type="print">
      <month>01</month>
      <year>2024</year>
    </publication_date>
    <journal_volume>
      <volume>1</volume>
    </journal_volume>
    <issue>1</issue>
  </journal_issue>
  <journal_article publication_type="full_text">
    <titles>
      <title>Naslov članka</title>
    </titles>
    <contributors>
      <!-- vidi sekciju Kontributor -->
    </contributors>
    <publication_date media_type="print">
      <year>2024</year>
    </publication_date>
    <pages>
      <first_page>1</first_page>
      <last_page>10</last_page>
    </pages>
    <doi_data>
      <doi>10.xxxxx/suffix</doi>
      <resource>https://example.com/article</resource>
    </doi_data>
  </journal_article>
</journal>
```

---

## 2. ZBORNIK RADOVA (Conference Proceedings) - Forma

### Struktura XML-a

Glavni kontejner: `<conference>` → `<event_metadata>` + `<proceedings_metadata>` → `<conference_paper>`

### A) Podaci o konferenciji (event_metadata)

| Polje | Obavezno | Tip |
|-------|----------|-----|
| conference_name | ✅ DA | text |
| conference_theme | Opciono | text |
| conference_acronym | Preporučeno | text |
| conference_sponsor | Opciono | text |
| conference_number | Opciono | number |
| conference_location | Preporučeno | text |
| conference_date (start) | Preporučeno | YYYY-MM-DD |
| conference_date (end) | Preporučeno | YYYY-MM-DD |

### B) Podaci o zborniku (proceedings_metadata)

| Polje | Obavezno | Tip |
|-------|----------|-----|
| proceedings_title | ✅ DA | text |
| proceedings_subject | Opciono | text |
| publisher_name | ✅ DA | text |
| publisher_place | Opciono | text |
| publication_date (year) | ✅ DA | YYYY |
| isbn | Preporučeno | text |
| issn | Opciono* | text |
| volume | Opciono | number |
| doi | Preporučeno | text |
| resource_url | Preporučeno | URL |

> *Ako je konferencija deo serije, ISSN je obavezan

### C) Podaci o radu (conference_paper)

| Polje | Obavezno | Tip |
|-------|----------|-----|
| title | ✅ DA | text |
| contributors | ✅ DA | array |
| publication_date (year) | Preporučeno | YYYY |
| first_page | Preporučeno | text |
| last_page | Preporučeno | text |
| doi | ✅ DA | text |
| resource_url | ✅ DA | URL |
| abstract | Preporučeno | text |
| publication_type | DA | select |

### Primer XML strukture za zbornik
```xml
<conference>
  <contributors>
    <!-- urednici konferencije -->
  </contributors>
  <event_metadata>
    <conference_name>Naziv konferencije</conference_name>
    <conference_acronym>KONF2024</conference_acronym>
    <conference_number>5</conference_number>
    <conference_location>Beograd, Srbija</conference_location>
    <conference_date start_month="06" start_year="2024" start_day="15" 
                     end_year="2024" end_month="06" end_day="17"/>
  </event_metadata>
  <proceedings_metadata language="sr">
    <proceedings_title>Zbornik radova 5. konferencije</proceedings_title>
    <publisher>
      <publisher_name>Naziv izdavača</publisher_name>
      <publisher_place>Beograd</publisher_place>
    </publisher>
    <publication_date>
      <year>2024</year>
    </publication_date>
    <isbn>978-86-0000-000-0</isbn>
    <doi_data>
      <doi>10.xxxxx/proceedings</doi>
      <resource>https://example.com/proceedings</resource>
    </doi_data>
  </proceedings_metadata>
  <conference_paper publication_type="full_text">
    <contributors>
      <!-- autori rada -->
    </contributors>
    <titles>
      <title>Naslov rada</title>
    </titles>
    <publication_date>
      <year>2024</year>
    </publication_date>
    <pages>
      <first_page>1</first_page>
      <last_page>10</last_page>
    </pages>
    <doi_data>
      <doi>10.xxxxx/paper1</doi>
      <resource>https://example.com/paper1</resource>
    </doi_data>
  </conference_paper>
</conference>
```

---

## 3. MONOGRAFIJA / KNJIGA (Book) - Forma

### Struktura XML-a

Glavni kontejner: `<book>` → `<book_metadata>` / `<book_series_metadata>` / `<book_set_metadata>` → `<content_item>`

### A) Tip knjige (book_type atribut)

| Vrednost | Opis |
|----------|------|
| edited_book | Zbornik sa uređivačem |
| monograph | Autorska monografija |
| reference | Referentno delo |
| other | Ostalo |

### B) Podaci o knjizi (book_metadata)

| Polje | Obavezno | Tip | Napomena |
|-------|----------|-----|----------|
| title | ✅ DA | text | |
| subtitle | Opciono | text | |
| contributors | Preporučeno | array | Autori/urednici |
| edition_number | Opciono | number | Samo broj (npr. 3, ne "treće izdanje") |
| publication_date (year) | ✅ DA | YYYY | |
| isbn (print) | Preporučeno* | text | |
| isbn (electronic) | Preporučeno | text | |
| noisbn | Uslovni | element | Ako nema ISBN |
| publisher_name | ✅ DA | text | |
| publisher_place | Opciono | text | |
| doi | ✅ DA | text | Obavezan za celu knjigu |
| resource_url | ✅ DA | URL | |
| language | Preporučeno | select | ISO639 |

> *ISBN ili noisbn element

### C) Podaci o seriji (book_series_metadata) - ako je deo serije

| Polje | Obavezno | Tip |
|-------|----------|-----|
| series_title | ✅ DA | text |
| issn | ✅ DA | text |
| volume | ✅ DA | number |

### D) Podaci o poglavlju (content_item)

| Polje | Obavezno | Tip |
|-------|----------|-----|
| component_type | ✅ DA | select: chapter, section, part, reference_entry, other |
| title | Preporučeno | text |
| contributors | Preporučeno | array |
| first_page | Preporučeno | text |
| last_page | Preporučeno | text |
| doi | Preporučeno | text |
| resource_url | Preporučeno | URL |
| publication_type | DA | select |

### Primer XML strukture za monografiju
```xml
<book book_type="monograph">
  <book_metadata language="sr">
    <contributors>
      <!-- autori knjige -->
    </contributors>
    <titles>
      <title>Naslov monografije</title>
      <subtitle>Podnaslov</subtitle>
    </titles>
    <edition_number>1</edition_number>
    <publication_date>
      <year>2024</year>
    </publication_date>
    <isbn media_type="print">978-86-0000-000-0</isbn>
    <isbn media_type="electronic">978-86-0000-000-1</isbn>
    <publisher>
      <publisher_name>Naziv izdavača</publisher_name>
      <publisher_place>Beograd</publisher_place>
    </publisher>
    <doi_data>
      <doi>10.xxxxx/book</doi>
      <resource>https://example.com/book</resource>
    </doi_data>
  </book_metadata>
  <content_item component_type="chapter" publication_type="full_text">
    <contributors>
      <!-- autori poglavlja ako su različiti -->
    </contributors>
    <titles>
      <title>Naslov poglavlja</title>
    </titles>
    <pages>
      <first_page>1</first_page>
      <last_page>25</last_page>
    </pages>
    <doi_data>
      <doi>10.xxxxx/chapter1</doi>
      <resource>https://example.com/chapter1</resource>
    </doi_data>
  </content_item>
</book>
```

---

## ZAJEDNIČKI ELEMENTI ZA SVE TIPOVE

### Kontributor (autor/urednik)
```json
{
  "contributors": [
    {
      "given_name": "string (preporučeno)",
      "surname": "string (✅ OBAVEZNO)",
      "suffix": "string (opciono - Jr., III, itd.)",
      "orcid": "string (preporučeno - format: https://orcid.org/0000-0000-0000-0000)",
      "orcid_authenticated": "boolean",
      "sequence": "first | additional (✅ OBAVEZNO)",
      "contributor_role": "author | editor | chair | translator | reviewer (✅ OBAVEZNO)",
      "affiliations": [
        {
          "institution_name": "string",
          "institution_id_ror": "string (ROR ID - https://ror.org/...)",
          "department": "string"
        }
      ]
    }
  ]
}
```

#### XML primer za kontributora
```xml
<contributors>
  <person_name sequence="first" contributor_role="author">
    <given_name>Petar</given_name>
    <surname>Petrović</surname>
    <affiliations>
      <institution>
        <institution_id type="ror">https://ror.org/01bj3aw27</institution_id>
        <institution_department>Departman za informatiku</institution_department>
      </institution>
    </affiliations>
    <ORCID authenticated="true">https://orcid.org/0000-0002-4011-3590</ORCID>
  </person_name>
  <person_name sequence="additional" contributor_role="author">
    <given_name>Marija</given_name>
    <surname>Marković</surname>
  </person_name>
  <organization sequence="additional" contributor_role="author">
    Istraživački tim XYZ
  </organization>
</contributors>
```

### Uloge kontributora

| Vrednost | Opis |
|----------|------|
| author | Autor |
| editor | Urednik |
| chair | Predsedavajući |
| reviewer | Recenzent |
| review-assistant | Asistent recenzenta |
| stats-reviewer | Statistički recenzent |
| reviewer-external | Eksterni recenzent |
| reader | Čitalac |
| translator | Prevodilac |

---

### Informacije o finansiranju (funding)
```json
{
  "funding": [
    {
      "funder_name": "string",
      "funder_identifier": "string (DOI iz Open Funder Registry - 10.13039/...)",
      "ror_id": "string (https://ror.org/...)",
      "award_number": "string",
      "grant_doi": "string (Crossref grant DOI)"
    }
  ]
}
```

#### XML primer za finansiranje
```xml
<fr:program name="fundref" xmlns:fr="http://www.crossref.org/fundref.xsd">
  <fr:assertion name="fundgroup">
    <fr:assertion name="funder_name">Ministarstvo nauke
      <fr:assertion name="funder_identifier">https://doi.org/10.13039/501100004564</fr:assertion>
    </fr:assertion>
    <fr:assertion name="award_number">OI 123456</fr:assertion>
  </fr:assertion>
  <fr:assertion name="fundgroup">
    <fr:assertion name="ror">https://ror.org/021nxhr62</fr:assertion>
    <fr:assertion name="grant_doi">10.46936/grant123</fr:assertion>
  </fr:assertion>
</fr:program>
```

---

### Informacije o licenci (license)
```json
{
  "license": {
    "license_url": "URL (npr. https://creativecommons.org/licenses/by/4.0/)",
    "applies_to": "vor | am | tdm | stm-asf",
    "start_date": "YYYY-MM-DD",
    "free_to_read": "boolean",
    "free_to_read_start_date": "YYYY-MM-DD"
  }
}
```

#### Vrednosti za applies_to

| Vrednost | Opis |
|----------|------|
| vor | Version of Record (verzija zapisa) |
| am | Accepted Manuscript (prihvaćeni rukopis) |
| tdm | Text and Data Mining |
| stm-asf | Article Sharing Framework |

#### XML primer za licencu
```xml
<ai:program name="AccessIndicators" xmlns:ai="http://www.crossref.org/AccessIndicators.xsd">
  <ai:free_to_read start_date="2024-01-01"/>
  <ai:license_ref applies_to="vor" start_date="2024-01-01">
    https://creativecommons.org/licenses/by/4.0/
  </ai:license_ref>
  <ai:license_ref applies_to="tdm" start_date="2024-01-01">
    https://creativecommons.org/licenses/by/4.0/
  </ai:license_ref>
</ai:program>
```

---

### Reference (citation_list)
```json
{
  "citations": [
    {
      "key": "string (✅ OBAVEZNO - jedinstveni ključ)",
      "type": "journal_article | book | dataset | conference_paper | ...",
      "doi": "string (ako je poznat)",
      "journal_title": "string",
      "author": "string (prvi autor)",
      "volume": "string",
      "issue": "string",
      "first_page": "string",
      "cYear": "string (godina)",
      "article_title": "string",
      "isbn": "string",
      "volume_title": "string (naslov knjige)",
      "series_title": "string",
      "unstructured_citation": "string (ako nema strukturiranih podataka)"
    }
  ]
}
```

#### Tipovi citata (type atribut)

| XML vrednost | JSON vrednost | Opis |
|--------------|---------------|------|
| journal_article | journal-article | Članak u časopisu |
| book | book | Knjiga |
| book_chapter | book-chapter | Poglavlje |
| conference_paper | conference-paper | Rad na konferenciji |
| dataset | dataset | Dataset |
| dissertation | dissertation | Disertacija |
| preprint | preprint | Preprint |
| software | software | Softver |
| standard | standard | Standard |
| report | report | Izveštaj |
| web_resource | web-resource | Web stranica |
| other | other | Ostalo |

#### XML primer za reference
```xml
<citation_list>
  <citation type="journal_article" key="ref1">
    <journal_title>Journal of Science</journal_title>
    <author>Smith</author>
    <volume>10</volume>
    <issue>2</issue>
    <first_page>123</first_page>
    <cYear>2023</cYear>
  </citation>
  <citation type="book" key="ref2">
    <volume_title>Introduction to Programming</volume_title>
    <author>Johnson</author>
    <isbn>978-0-123456-78-9</isbn>
    <cYear>2022</cYear>
  </citation>
  <citation type="dataset" key="ref3">
    <doi>10.5555/dataset123</doi>
  </citation>
  <citation key="ref4">
    <unstructured_citation>
      Petrović P. (2021). Naslov rada. Časopis, 5(1), 10-20.
    </unstructured_citation>
  </citation>
</citation_list>
```

---

### Apstrakt (JATS format)
```json
{
  "abstract": {
    "content": "string (tekst apstrakta)",
    "format": "jats"
  }
}
```

#### XML primer za apstrakt
```xml
<jats:abstract xmlns:jats="http://www.ncbi.nlm.nih.gov/JATS1">
  <jats:p>
    Ovo je tekst apstrakta. Može sadržati više pasusa i jednostavno formatiranje
    kao što su <jats:italic>kurziv</jats:italic> i <jats:bold>podebljano</jats:bold>.
  </jats:p>
  <jats:p>
    Drugi pasus apstrakta.
  </jats:p>
</jats:abstract>
```

---

## XML ZAGLAVLJE (HEAD) - Zajedničko za sve tipove

Svaki XML fajl za Crossref mora imati zaglavlje sa sledećim elementima:
```xml
<head>
  <doi_batch_id>jedinstveni_id_123456</doi_batch_id>  <!-- OBAVEZNO: jedinstveni ID -->
  <timestamp>20240115120000</timestamp>               <!-- OBAVEZNO: format YYYYMMDDHHmmss -->
  <depositor>
    <depositor_name>Ime deponenta ili institucije</depositor_name>  <!-- OBAVEZNO -->
    <email_address>email@example.com</email_address>                 <!-- OBAVEZNO -->
  </depositor>
  <registrant>Naziv registranta/organizacije</registrant>  <!-- OBAVEZNO -->
</head>
```

### Napomene za zaglavlje

- `doi_batch_id` - mora biti jedinstven za svaki deposit; preporučuje se korišćenje UUID ili timestamp-a
- `timestamp` - mora se povećavati sa svakim ažuriranjem metapodataka
- `email_address` - na ovu adresu Crossref šalje submission log

---

## PREPORUČENA VERZIJA SHEME

Koristite najnoviju verziju sheme: **5.4.0**

### Kompletan XML šablon
```xml
<?xml version="1.0" encoding="UTF-8"?>
<doi_batch 
  xmlns="http://www.crossref.org/schema/5.4.0" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:jats="http://www.ncbi.nlm.nih.gov/JATS1"
  xmlns:fr="http://www.crossref.org/fundref.xsd"
  xmlns:ai="http://www.crossref.org/AccessIndicators.xsd"
  xmlns:mml="http://www.w3.org/1998/Math/MathML"
  version="5.4.0"
  xsi:schemaLocation="http://www.crossref.org/schema/5.4.0 
    https://data.crossref.org/schemas/crossref5.4.0.xsd">
  
  <head>
    <!-- zaglavlje -->
  </head>
  
  <body>
    <!-- journal, conference, ili book element -->
  </body>
  
</doi_batch>
```

### Namespace-ovi

| Prefix | URI | Namena |
|--------|-----|--------|
| (default) | http://www.crossref.org/schema/5.4.0 | Glavni Crossref namespace |
| jats | http://www.ncbi.nlm.nih.gov/JATS1 | Za apstrakte |
| fr | http://www.crossref.org/fundref.xsd | Za podatke o finansiranju |
| ai | http://www.crossref.org/AccessIndicators.xsd | Za licence |
| mml | http://www.w3.org/1998/Math/MathML | Za matematičke formule |

---

## KORISNI LINKOVI

- [Crossref dokumentacija](https://www.crossref.org/documentation/)
- [Schema library](https://www.crossref.org/documentation/schema-library/)
- [XSD shema 5.4.0](https://data.crossref.org/schemas/crossref5.4.0.xsd)
- [Testiranje XML-a](https://www.crossref.org/documentation/register-maintain-records/direct-deposit-xml/testing-your-xml/)
- [Open Funder Registry](https://www.crossref.org/services/funder-registry/)
- [ROR (Research Organization Registry)](https://ror.org/)
- [ORCID](https://orcid.org/)

---

## VALIDACIJA I SLANJE

### Testiranje XML-a

Pre slanja produkcijskog XML-a, testirajte ga na:
- https://test.crossref.org (test okruženje)

### Načini slanja

1. **Admin tool** - upload XML fajlova kroz web interfejs
2. **HTTPS POST** - programski upload
3. **OJS plugin** - za korisnike Open Journal Systems

### Verifikacija

Nakon slanja, proverite submission log na email adresi navedenoj u `<depositor>`.

---

*Dokument kreiran na osnovu Crossref dokumentacije. Poslednje ažuriranje: Januar 2024.*