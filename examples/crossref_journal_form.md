# Crossref Journal Registration Form Fields

## DOI Batch Header Fields

| Label | Detaljniji Opis | Obavezno/Opciono | Primer Vrednosti | XML Struktura | Opcije | Atributi |
|-------|-----------------|------------------|------------------|---------------|--------|----------|
| **DOI Batch ID** | Jedinstveni identifikator koji izdavač generiše za DOI submission batch | **Obavezno** | `grma_123456` | `/doi_batch/head/doi_batch_id` | - | - |
| **Timestamp** | Reprezentacija datuma i vremena u integeru koja služi kao broj verzije za record koji se deponuje | **Obavezno** | `20250824201600` | `/doi_batch/head/timestamp` | - | - |
| **Depositor Name** | Ime organizacije koja registruje DOI-jeve | **Obavezno** | `Studio Grma` | `/doi_batch/head/depositor/depositor_name` | - | - |
| **Email Address** | Email adresa na koju će biti poslate poruke o uspešnosti/grešci batch-a | **Obavezno** | `info@grma.rs` | `/doi_batch/head/depositor/email_address` | - | - |
| **Registrant** | Organizacija odgovorna za informacije koje se registruju | **Obavezno** | `Studio Grma` | `/doi_batch/head/registrant` | - | - |

## Journal Metadata Fields

| Label | Detaljniji Opis | Obavezno/Opciono | Primer Vrednosti | XML Struktura | Opcije | Atributi |
|-------|-----------------|------------------|------------------|---------------|--------|----------|
| **Full Title** | Pun naziv časopisa kako je opšte poznato ili se citira | **Obavezno** (1-10) | `Applied Physics Letters` | `/doi_batch/body/journal/journal_metadata/full_title` | - | - |
| Abbreviated Title | Uobičajene skraćenice ili alternative korišćene pri citiranju časopisa | Opciono (0-10) | `Appl. Phys. Lett.` | `/doi_batch/body/journal/journal_metadata/abbrev_title` | - | - |
| ISSN | ISSN broj dodeljen časopisu | Opciono (0-6) | `0003-6951` | `/doi_batch/body/journal/journal_metadata/issn` | - | `media_type`: print/electronic |
| CODEN | CODEN dodeljen časopisu ili konferencijskim zbornicima | Opciono | `applab` | `/doi_batch/body/journal/journal_metadata/coden` | - | - |
| Journal Language | Jezik časopisa | Opciono | `en` | `/doi_batch/body/journal/journal_metadata` | ISO 639 kodovi | `language` |

## Journal Issue Fields

| Label | Detaljniji Opis | Obavezno/Opciono | Primer Vrednosti | XML Struktura | Opcije | Atributi |
|-------|-----------------|------------------|------------------|---------------|--------|----------|
| **Publication Year** | Godina publikovanja | **Obavezno** | `1999` | `/doi_batch/body/journal/journal_issue/publication_date/year` | - | - |
| Publication Month | Mesec publikovanja (numerički format sa leading zero) | Opciono | `03` | `/doi_batch/body/journal/journal_issue/publication_date/month` | 01-12, 21-24 (seasons), 31-34 (quarters) | - |
| Publication Day | Dan publikovanja (sa leading zero ako je manji od 10) | Opciono | `15` | `/doi_batch/body/journal/journal_issue/publication_date/day` | 01-31 | - |
| Media Type | Tip medija za datum publikovanja | Opciono | `print` | `/doi_batch/body/journal/journal_issue/publication_date` | print, online | `media_type` |
| Volume | Broj volumena časopisa | Opciono | `74` | `/doi_batch/body/journal/journal_issue/journal_volume/volume` | - | - |
| Issue | Broj izdanja u kome je članak objavljen | Opciono | `16` | `/doi_batch/body/journal/journal_issue/issue` | - | - |
| Special Numbering | Numeracija za suplement ili specijalna izdanja | Opciono | `suppl 1` | `/doi_batch/body/journal/journal_issue/special_numbering` | - | - |

## Journal Article Fields

| Label | Detaljniji Opis | Obavezno/Opciono | Primer Vrednosti | XML Struktura | Opcije | Atributi |
|-------|-----------------|------------------|------------------|---------------|--------|----------|
| **Article Title** | Naslov članka koji se registruje | **Obavezno** (1-20) | `Sub-5-fs visible pulse generation` | `/doi_batch/body/journal/journal_article/titles/title` | - | - |
| Subtitle | Podnaslov članka | Opciono | `A comprehensive study` | `/doi_batch/body/journal/journal_article/titles/subtitle` | - | - |
| Original Language Title | Naslov članka na originalnom jeziku ako se registruje prevod | Opciono | `Генерација видљивих импулса` | `/doi_batch/body/journal/journal_article/titles/original_language_title` | - | `language` |
| Article Language | Jezik članka | Opciono | `en` | `/doi_batch/body/journal/journal_article` | ISO 639 kodovi | `language` |
| Publication Type | Tip publikacije | Opciono | `full_text` | `/doi_batch/body/journal/journal_article` | full_text, abstract_only | `publication_type` |

## Contributors Fields

| Label | Detaljniji Opis | Obavezno/Opciono | Primer Vrednosti | XML Struktura | Opcije | Atributi |
|-------|-----------------|------------------|------------------|---------------|--------|----------|
| Given Name | Ime kontributora | Opciono | `Ann P.` | `/doi_batch/body/journal/journal_article/contributors/person_name/given_name` | - | - |
| **Surname** | Prezime kontributora | **Obavezno** | `Shirakawa` | `/doi_batch/body/journal/journal_article/contributors/person_name/surname` | - | - |
| Suffix | Sufiks imena autora (Jr, Sr, III, itd.) | Opciono | `III` | `/doi_batch/body/journal/journal_article/contributors/person_name/suffix` | - | - |
| Contributor Role | Uloga kontributora | Opciono | `author` | `/doi_batch/body/journal/journal_article/contributors/person_name` | author, editor, translator, chair, etc. | `contributor_role` |
| Sequence | Redosled kontributora | Opciono | `first` | `/doi_batch/body/journal/journal_article/contributors/person_name` | first, additional | `sequence` |
| Name Style | Stil imena | Opciono | `western` | `/doi_batch/body/journal/journal_article/contributors/person_name` | western, eastern, given-only, islensk | `name-style` |
| ORCID | ORCID iD autora | Opciono | `0000-0002-1825-0097` | `/doi_batch/body/journal/journal_article/contributors/person_name/ORCID` | - | `authenticated`: true/false |
| Institution Name | Puno ime institucije | Opciono | `University of Belgrade` | `/doi_batch/body/journal/journal_article/contributors/person_name/affiliations/institution/institution_name` | - | - |
| Institution ID | Identifikator institucije (ROR, ISNI, Wikidata) | Opciono | `https://ror.org/123456789` | `/doi_batch/body/journal/journal_article/contributors/person_name/affiliations/institution/institution_id` | ROR, ISNI, Wikidata | `type` |

## Article Details Fields

| Label | Detaljniji Opis | Obavezno/Opciono | Primer Vrednosti | XML Struktura | Opcije | Atributi |
|-------|-----------------|------------------|------------------|---------------|--------|----------|
| **Article Publication Year** | Godina publikovanja članka | **Obavezno** | `1999` | `/doi_batch/body/journal/journal_article/publication_date/year` | - | - |
| Article Publication Month | Mesec publikovanja članka | Opciono | `06` | `/doi_batch/body/journal/journal_article/publication_date/month` | 01-12 | - |
| Article Publication Day | Dan publikovanja članka | Opciono | `28` | `/doi_batch/body/journal/journal_article/publication_date/day` | 01-31 | - |
| Acceptance Year | Godina prihvatanja manuskripra | Opciono | `1999` | `/doi_batch/body/journal/journal_article/acceptance_date/year` | - | - |
| Acceptance Month | Mesec prihvatanja manuskripra | Opciono | `05` | `/doi_batch/body/journal/journal_article/acceptance_date/month` | 01-12 | - |
| Acceptance Day | Dan prihvatanja manuskripra | Opciono | `15` | `/doi_batch/body/journal/journal_article/acceptance_date/day` | 01-31 | - |
| First Page | Prva strana članka | Opciono | `2268` | `/doi_batch/body/journal/journal_article/pages/first_page` | - | - |
| Last Page | Poslednja strana članka | Opciono | `2275` | `/doi_batch/body/journal/journal_article/pages/last_page` | - | - |
| Other Pages | Dodatne strane kada članak ima nekontigiuosne strane | Opciono | `2280-2285, 2290` | `/doi_batch/body/journal/journal_article/pages/other_pages` | - | - |

## DOI and Resource Fields

| Label | Detaljniji Opis | Obavezno/Opciono | Primer Vrednosti | XML Struktura | Opcije | Atributi |
|-------|-----------------|------------------|------------------|---------------|--------|----------|
| **Article DOI** | DOI za entitet koji se registruje kod Crossref-a | **Obavezno** | `10.9876/S000369519903216` | `/doi_batch/body/journal/journal_article/doi_data/doi` | - | - |
| **Resource URL** | URI povezan sa DOI-jem (landing page) | **Obavezno** | `http://ojps.crossref.org/link/?apl/74/2268/ab` | `/doi_batch/body/journal/journal_article/doi_data/resource` | - | `content_version`: vor/am, `mime_type` |

## Publisher Item Fields

| Label | Detaljniji Opis | Obavezno/Opciono | Primer Vrednosti | XML Struktura | Opcije | Atributi |
|-------|-----------------|------------------|------------------|---------------|--------|----------|
| Item Number | Izdavačev broj koji jedinstveno identifikuje stavku | Opciono (0-3) | `S000369519903216` | `/doi_batch/body/journal/journal_article/publisher_item/item_number` | - | `item_number_type`: article-number/index/sequence |
| Identifier | Javni standardni identifikator koji može jedinstveno da identifikuje stavku | Opciono (0-10) | `S000369519903216` | `/doi_batch/body/journal/journal_article/publisher_item/identifier` | - | `id_type`: doi/issn/isbn/uri/pii/sici/pmid/pmcid/pmid/publisher-id/other |

## Abstract Fields

| Label | Detaljniji Opis | Obavezno/Opciono | Primer Vrednosti | XML Struktura | Opcije | Atributi |
|-------|-----------------|------------------|------------------|---------------|--------|----------|
| Abstract | Apstrakt članka | Opciono (0-unbounded) | `This paper presents...` | `/doi_batch/body/journal/journal_article/abstract` | - | `abstract-type`, `xml:lang`, `specific-use` |

## Collection Fields (Multiple Resolution)

| Label | Detaljniji Opis | Obavezno/Opciono | Primer Vrednosti | XML Struktura | Opcije | Atributi |
|-------|-----------------|------------------|------------------|---------------|--------|----------|
| Collection Property | Tip kolekcije za Multiple Resolution | Opciono | `text-mining` | `/doi_batch/body/journal/journal_article/doi_data/collection` | list-based, country-based, crawler-based, text-mining, unspecified, syndication, link-header | `property` |
| Collection Item Resource | URI u okviru kolekcije | Opciono | `http://example.com/fulltext.pdf` | `/doi_batch/body/journal/journal_article/doi_data/collection/item/resource` | - | `content_version`, `mime_type` |
| Collection Item DOI | DOI u okviru kolekcije | Opciono | `10.9876/S000369519903216` | `/doi_batch/body/journal/journal_article/doi_data/collection/item/doi` | - | - |