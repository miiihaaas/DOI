# Crossref Journal Registration Form Fields

## DOI Batch Header Fields

| Label | Detaljniji Opis | XML Struktura | Obavezno/Opciono | Opcije | Atributi | Primer Vrednosti |
|-------|-----------------|---------------|------------------|--------|----------|------------------|
| **DOI Batch ID** | Jedinstveni identifikator koji izdavač generiše za DOI submission batch | `/doi_batch/head/doi_batch_id` | **Obavezno** | - | - | `grma_123456` |
| **Timestamp** | Reprezentacija datuma i vremena u integeru koja služi kao broj verzije za record koji se deponuje | `/doi_batch/head/timestamp` | **Obavezno** | - | - | `20250824201600` |
| **Depositor Name** | Ime organizacije koja registruje DOI-jeve | `/doi_batch/head/depositor/depositor_name` | **Obavezno** | - | - | `Studio Grma` |
| **Email Address** | Email adresa na koju će biti poslate poruke o uspešnosti/grešci batch-a | `/doi_batch/head/depositor/email_address` | **Obavezno** | - | - | `info@grma.rs` |
| **Registrant** | Organizacija odgovorna za informacije koje se registruju | `/doi_batch/head/registrant` | **Obavezno** | - | - | `Studio Grma` |

## Journal Metadata Fields

| Label | Detaljniji Opis | XML Struktura | Obavezno/Opciono | Opcije | Atributi | Primer Vrednosti |
|-------|-----------------|---------------|------------------|--------|----------|------------------|
| **Full Title** | Pun naziv časopisa kako je opšte poznato ili se citira | `/doi_batch/body/journal/journal_metadata/full_title` | **Obavezno** (1-10) | - | - | `Applied Physics Letters` |
| Abbreviated Title | Uobičajene skraćenice ili alternative korišćene pri citiranju časopisa | `/doi_batch/body/journal/journal_metadata/abbrev_title` | Opciono (0-10) | - | - | `Appl. Phys. Lett.` |
| ISSN | ISSN broj dodeljen časopisu | `/doi_batch/body/journal/journal_metadata/issn` | Opciono (0-6) | - | `media_type`: print/electronic | `0003-6951` |
| CODEN | CODEN dodeljen časopisu ili konferencijskim zbornicima | `/doi_batch/body/journal/journal_metadata/coden` | Opciono | - | - | `applab` |
| Journal Language | Jezik časopisa | `/doi_batch/body/journal/journal_metadata` | Opciono | ISO 639 kodovi | `language` | `en` |

## Journal Issue Fields

| Label | Detaljniji Opis | XML Struktura | Obavezno/Opciono | Opcije | Atributi | Primer Vrednosti |
|-------|-----------------|---------------|------------------|--------|----------|------------------|
| **Publication Year** | Godina publikovanja | `/doi_batch/body/journal/journal_issue/publication_date/year` | **Obavezno** | - | - | `1999` |
| Publication Month | Mesec publikovanja (numerički format sa leading zero) | `/doi_batch/body/journal/journal_issue/publication_date/month` | Opciono | 01-12, 21-24 (seasons), 31-34 (quarters) | - | `03` |
| Publication Day | Dan publikovanja (sa leading zero ako je manji od 10) | `/doi_batch/body/journal/journal_issue/publication_date/day` | Opciono | 01-31 | - | `15` |
| Media Type | Tip medija za datum publikovanja | `/doi_batch/body/journal/journal_issue/publication_date` | Opciono | print, online | `media_type` | `print` |
| Volume | Broj volumena časopisa | `/doi_batch/body/journal/journal_issue/journal_volume/volume` | Opciono | - | - | `74` |
| Issue | Broj izdanja u kome je članak objavljen | `/doi_batch/body/journal/journal_issue/issue` | Opciono | - | - | `16` |
| Special Numbering | Numeracija za suplement ili specijalna izdanja | `/doi_batch/body/journal/journal_issue/special_numbering` | Opciono | - | - | `suppl 1` |

## Journal Article Fields

| Label | Detaljniji Opis | XML Struktura | Obavezno/Opciono | Opcije | Atributi | Primer Vrednosti |
|-------|-----------------|---------------|------------------|--------|----------|------------------|
| **Article Title** | Naslov članka koji se registruje | `/doi_batch/body/journal/journal_article/titles/title` | **Obavezno** (1-20) | - | - | `Sub-5-fs visible pulse generation` |
| Subtitle | Podnaslov članka | `/doi_batch/body/journal/journal_article/titles/subtitle` | Opciono | - | - | `A comprehensive study` |
| Original Language Title | Naslov članka na originalnom jeziku ako se registruje prevod | `/doi_batch/body/journal/journal_article/titles/original_language_title` | Opciono | - | `language` | `Генерација видљивих импулса` |
| Article Language | Jezik članka | `/doi_batch/body/journal/journal_article` | Opciono | ISO 639 kodovi | `language` | `en` |
| Publication Type | Tip publikacije | `/doi_batch/body/journal/journal_article` | Opciono | full_text, abstract_only | `publication_type` | `full_text` |

## Contributors Fields

| Label | Detaljniji Opis | XML Struktura | Obavezno/Opciono | Opcije | Atributi | Primer Vrednosti |
|-------|-----------------|---------------|------------------|--------|----------|------------------|
| Given Name | Ime kontributora | `/doi_batch/body/journal/journal_article/contributors/person_name/given_name` | Opciono | - | - | `Ann P.` |
| **Surname** | Prezime kontributora | `/doi_batch/body/journal/journal_article/contributors/person_name/surname` | **Obavezno** | - | - | `Shirakawa` |
| Suffix | Sufiks imena autora (Jr, Sr, III, itd.) | `/doi_batch/body/journal/journal_article/contributors/person_name/suffix` | Opciono | - | - | `III` |
| Contributor Role | Uloga kontributora | `/doi_batch/body/journal/journal_article/contributors/person_name` | Opciono | author, editor, translator, chair, etc. | `contributor_role` | `author` |
| Sequence | Redosled kontributora | `/doi_batch/body/journal/journal_article/contributors/person_name` | Opciono | first, additional | `sequence` | `first` |
| Name Style | Stil imena | `/doi_batch/body/journal/journal_article/contributors/person_name` | Opciono | western, eastern, given-only, islensk | `name-style` | `western` |
| ORCID | ORCID iD autora | `/doi_batch/body/journal/journal_article/contributors/person_name/ORCID` | Opciono | - | `authenticated`: true/false | `0000-0002-1825-0097` |
| Institution Name | Puno ime institucije | `/doi_batch/body/journal/journal_article/contributors/person_name/affiliations/institution/institution_name` | Opciono | - | - | `University of Belgrade` |
| Institution ID | Identifikator institucije (ROR, ISNI, Wikidata) | `/doi_batch/body/journal/journal_article/contributors/person_name/affiliations/institution/institution_id` | Opciono | ROR, ISNI, Wikidata | `type` | `https://ror.org/123456789` |

## Article Details Fields

| Label | Detaljniji Opis | XML Struktura | Obavezno/Opciono | Opcije | Atributi | Primer Vrednosti |
|-------|-----------------|---------------|------------------|--------|----------|------------------|
| **Article Publication Year** | Godina publikovanja članka | `/doi_batch/body/journal/journal_article/publication_date/year` | **Obavezno** | - | - | `1999` |
| Article Publication Month | Mesec publikovanja članka | `/doi_batch/body/journal/journal_article/publication_date/month` | Opciono | 01-12 | - | `06` |
| Article Publication Day | Dan publikovanja članka | `/doi_batch/body/journal/journal_article/publication_date/day` | Opciono | 01-31 | - | `28` |
| Acceptance Year | Godina prihvatanja manuskripra | `/doi_batch/body/journal/journal_article/acceptance_date/year` | Opciono | - | - | `1999` |
| Acceptance Month | Mesec prihvatanja manuskripra | `/doi_batch/body/journal/journal_article/acceptance_date/month` | Opciono | 01-12 | - | `05` |
| Acceptance Day | Dan prihvatanja manuskripra | `/doi_batch/body/journal/journal_article/acceptance_date/day` | Opciono | 01-31 | - | `15` |
| First Page | Prva strana članka | `/doi_batch/body/journal/journal_article/pages/first_page` | Opciono | - | - | `2268` |
| Last Page | Poslednja strana članka | `/doi_batch/body/journal/journal_article/pages/last_page` | Opciono | - | - | `2275` |
| Other Pages | Dodatne strane kada članak ima nekontigiuosne strane | `/doi_batch/body/journal/journal_article/pages/other_pages` | Opciono | - | - | `2280-2285, 2290` |

## DOI and Resource Fields

| Label | Detaljniji Opis | XML Struktura | Obavezno/Opciono | Opcije | Atributi | Primer Vrednosti |
|-------|-----------------|---------------|------------------|--------|----------|------------------|
| **Article DOI** | DOI za entitet koji se registruje kod Crossref-a | `/doi_batch/body/journal/journal_article/doi_data/doi` | **Obavezno** | - | - | `10.9876/S000369519903216` |
| **Resource URL** | URI povezan sa DOI-jem (landing page) | `/doi_batch/body/journal/journal_article/doi_data/resource` | **Obavezno** | - | `content_version`: vor/am, `mime_type` | `http://ojps.crossref.org/link/?apl/74/2268/ab` |

## Publisher Item Fields

| Label | Detaljniji Opis | XML Struktura | Obavezno/Opciono | Opcije | Atributi | Primer Vrednosti |
|-------|-----------------|---------------|------------------|--------|----------|------------------|
| Item Number | Izdavačev broj koji jedinstveno identifikuje stavku | `/doi_batch/body/journal/journal_article/publisher_item/item_number` | Opciono (0-3) | - | `item_number_type`: article-number/index/sequence | `S000369519903216` |
| Identifier | Javni standardni identifikator koji može jedinstveno da identifikuje stavku | `/doi_batch/body/journal/journal_article/publisher_item/identifier` | Opciono (0-10) | - | `id_type`: doi/issn/isbn/uri/pii/sici/pmid/pmcid/pmid/publisher-id/other | `S000369519903216` |

## Abstract Fields

| Label | Detaljniji Opis | XML Struktura | Obavezno/Opciono | Opcije | Atributi | Primer Vrednosti |
|-------|-----------------|---------------|------------------|--------|----------|------------------|
| Abstract | Apstrakt članka | `/doi_batch/body/journal/journal_article/abstract` | Opciono (0-unbounded) | - | `abstract-type`, `xml:lang`, `specific-use` | `This paper presents...` |

## Collection Fields (Multiple Resolution)

| Label | Detaljniji Opis | XML Struktura | Obavezno/Opciono | Opcije | Atributi | Primer Vrednosti |
|-------|-----------------|---------------|------------------|--------|----------|------------------|
| Collection Property | Tip kolekcije za Multiple Resolution | `/doi_batch/body/journal/journal_article/doi_data/collection` | Opciono | list-based, country-based, crawler-based, text-mining, unspecified, syndication, link-header | `property` | `text-mining` |
| Collection Item Resource | URI u okviru kolekcije | `/doi_batch/body/journal/journal_article/doi_data/collection/item/resource` | Opciono | - | `content_version`, `mime_type` | `http://example.com/fulltext.pdf` |
| Collection Item DOI | DOI u okviru kolekcije | `/doi_batch/body/journal/journal_article/doi_data/collection/item/doi` | Opciono | - | - | `10.9876/S000369519903216` |