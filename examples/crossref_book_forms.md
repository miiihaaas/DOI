# Crossref Book Deposit Forms - Tabular Structure

## 1. Book Deposit (Single Book with Chapters)

### Book Metadata

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| Book Type | Kategorija knjige prema sadržaju | `book[@book_type]` | Opciono | edited_book, monograph, reference, textbook, other | book_type | edited_book |
| **Language** | Glavni jezik publikacije (ISO639 kod) | `book_metadata[@language]` | **Obavezno** | en, sr, de, fr, es, ... | language | en |
| **Title** | Glavni naslov knjige | `book_metadata/titles/title` | **Obavezno** | Tekst sa formatiranjem | - | Advanced Materials Science |
| Subtitle | Podnaslov ili objašnjavanje naslova | `book_metadata/titles/subtitle` | Opciono | Tekst sa formatiranjem | - | Theory and Applications |
| Original Language Title | Naslov na originalnom jeziku (za prevode) | `book_metadata/titles/original_language_title` | Opciono | Tekst sa formatiranjem | language | Fortgeschrittene Materialwissenschaft |
| Edition Number | Redni broj izdanja | `book_metadata/edition_number` | Opciono | Pozitivni broj | - | 3 |
| **Publication Year** | Godina kada je knjiga objavljena | `book_metadata/publication_date/year` | **Obavezno** | YYYY format | - | 2024 |
| Publication Month | Mesec objavljivanja | `book_metadata/publication_date/month` | Opciono | 01-12, 21-24 (sezone), 31-34 (kvartali) | - | 03 |
| Publication Day | Dan objavljivanja | `book_metadata/publication_date/day` | Opciono | 01-31 | - | 15 |
| Media Type | Tip medija za datum publikacije | `book_metadata/publication_date[@media_type]` | Opciono | print, electronic, online | media_type | print |
| Print ISBN | ISBN za štampano izdanje | `book_metadata/isbn[print]` | Opciono* | ISBN-10 ili ISBN-13 format | media_type="print" | 978-0-123-45678-9 |
| Electronic ISBN | ISBN za elektronsko izdanje | `book_metadata/isbn[electronic]` | Opciono* | ISBN-10 ili ISBN-13 format | media_type="electronic" | 978-0-123-45679-6 |
| No ISBN Reason | Razlog zašto knjiga nema ISBN | `book_metadata/noisbn[@reason]` | Opciono** | withdrawn_by_publisher, archive_volume, ... | reason | archive_volume |
| **Publisher Name** | Naziv izdavačke kuće | `book_metadata/publisher/publisher_name` | **Obavezno** | Tekst | - | Academic Press |
| Publisher Place | Grad/zemlja izdavača | `book_metadata/publisher/publisher_place` | Opciono | Tekst | - | Boston, MA |
| Book DOI | Digitalni identifikator knjige | `book_metadata/doi_data/doi` | Opciono | DOI format (10.xxxx/xxxxx) | - | 10.1016/book.2024.001 |
| **Resource URL** | Web adresa na koju DOI pokazuje | `book_metadata/doi_data/resource` | **Obavezno ako je DOI dat** | Validna URL adresa | content_version, mime_type | https://publisher.com/book/123 |

*\* ISBN ili noisbn - jedno od ova dva je obavezno*  
*\*\* Obavezno samo ako nema ISBN*

### Book Contributors (Autori/Editori/Urednici knjige)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| **Contributor Role** | Uloga osobe u stvaranju knjige | `book_metadata/contributors/person_name[@contributor_role]` | **Obavezno** | author, editor, chair, reviewer, translator, ... | contributor_role | author |
| **Sequence** | Da li je prva ili dodatna osoba u listi | `book_metadata/contributors/person_name[@sequence]` | **Obavezno** | first, additional | sequence | first |
| Given Name | Ime i srednje ime osobe | `book_metadata/contributors/person_name/given_name` | Opciono | Tekst | - | John Michael |
| **Surname** | Prezime osobe | `book_metadata/contributors/person_name/surname` | **Obavezno** | Tekst | - | Smith |
| Suffix | Dodatak uz ime (titula, generacija) | `book_metadata/contributors/person_name/suffix` | Opciono | Jr., Sr., III, PhD, ... | - | Jr. |
| ORCID | Jedinstveni identifikator istraživača | `book_metadata/contributors/person_name/ORCID` | Opciono | ORCID format (0000-0000-0000-0000) | authenticated | 0000-0002-1825-0097 |
| Institution Name | Naziv ustanove gde radi | `book_metadata/contributors/person_name/affiliations/institution/institution_name` | Opciono | Tekst | - | University of Belgrade |
| Institution ID | Jedinstveni identifikator ustanove | `book_metadata/contributors/person_name/affiliations/institution/institution_id` | Opciono | URI format | type="ROR/ISNI/Wikidata" | https://ror.org/03ef5s567 |

### Content Items (Poglavlja/Delovi)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| Component Type | Tip dela knjige | `content_item[@component_type]` | Opciono | chapter, section, part, other, ... | component_type | chapter |
| Language | Jezik poglavlja (ako se razlikuje) | `content_item[@language]` | Opciono | ISO639 kodovi | language | en |
| Publication Type | Tip sadržaja koji se registruje | `content_item[@publication_type]` | Opciono | full_text, abstract_only | publication_type | full_text |
| Level Sequence | Redni broj nivoa u hijerarhiji | `content_item[@level_sequence_number]` | Opciono | Pozitivni broj | level_sequence_number | 1 |
| Chapter Title | Naslov poglavlja ili dela | `content_item/titles/title` | Opciono | Tekst sa formatiranjem | - | Introduction to Nanomaterials |
| Chapter Subtitle | Podnaslov poglavlja | `content_item/titles/subtitle` | Opciono | Tekst sa formatiranjem | - | Basic Principles and Methods |
| Component Number | Broj/oznaka poglavlja | `content_item/component_number` | Opciono | Tekst ili broj | - | Chapter 1 |
| First Page | Početna strana poglavlja | `content_item/pages/first_page` | Opciono | Broj ili oznaka strane | - | 15 |
| Last Page | Završna strana poglavlja | `content_item/pages/last_page` | Opciono | Broj ili oznaka strane | - | 45 |
| **Chapter DOI** | Digitalni identifikator poglavlja | `content_item/doi_data/doi` | **Obavezno** | DOI format | - | 10.1016/book.2024.001.ch01 |
| **Chapter Resource URL** | Web adresa poglavlja | `content_item/doi_data/resource` | **Obavezno** | Validna URL adresa | content_version, mime_type | https://publisher.com/book/123/ch1 |

### Chapter Contributors (Autori/Editori poglavlja)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| **Contributor Role** | Uloga osobe u stvaranju poglavlja | `content_item/contributors/person_name[@contributor_role]` | **Obavezno** | author, editor, chair, reviewer, translator, ... | contributor_role | author |
| **Sequence** | Da li je prva ili dodatna osoba u listi | `content_item/contributors/person_name[@sequence]` | **Obavezno** | first, additional | sequence | first |
| Given Name | Ime i srednje ime autora | `content_item/contributors/person_name/given_name` | Opciono | Tekst | - | Maria Elena |
| **Surname** | Prezime autora | `content_item/contributors/person_name/surname` | **Obavezno** | Tekst | - | Rodriguez |
| Suffix | Dodatak uz ime | `content_item/contributors/person_name/suffix` | Opciono | Jr., Sr., III, PhD, ... | - | PhD |
| ORCID | ORCID identifikator autora | `content_item/contributors/person_name/ORCID` | Opciono | ORCID format | authenticated | 0000-0001-2345-6789 |
| Institution Name | Naziv institucije autora | `content_item/contributors/person_name/affiliations/institution/institution_name` | Opciono | Tekst | - | MIT |
| Institution ID | ID institucije | `content_item/contributors/person_name/affiliations/institution/institution_id` | Opciono | URI format | type="ROR/ISNI/Wikidata" | https://ror.org/042nb2s44 |

---

## 2. Book Series Deposit (Knjiga u okviru serije)

### Series Metadata (Podaci o seriji)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| **Series Title** | Naziv serije knjiga | `book_series_metadata/series_metadata/titles/title` | **Obavezno** | Tekst sa formatiranjem | - | Advances in Chemistry |
| Series Subtitle | Podnaslov serije | `book_series_metadata/series_metadata/titles/subtitle` | Opciono | Tekst sa formatiranjem | - | Research and Applications |
| **Series ISSN** | ISSN serije (štampano izdanje) | `book_series_metadata/series_metadata/issn[print]` | **Obavezno** | ISSN format (1234-5678) | media_type="print" | 1234-5678 |
| Series Electronic ISSN | ISSN serije (elektronsko izdanje) | `book_series_metadata/series_metadata/issn[electronic]` | Opciono | ISSN format | media_type="electronic" | 1234-567X |
| Series CODEN | CODEN kod serije | `book_series_metadata/series_metadata/coden` | Opciono | 6-karakter CODEN | - | ADCHAM |
| Series Number | Broj serije | `book_series_metadata/series_metadata/series_number` | Opciono | Tekst ili broj | - | 15 |
| Series DOI | DOI čitave serije | `book_series_metadata/series_metadata/doi_data/doi` | Opciono | DOI format | - | 10.1016/series.chem |
| Series Resource URL | Web stranica serije | `book_series_metadata/series_metadata/doi_data/resource` | Opciono | URL | content_version, mime_type | https://publisher.com/series/chem |

### Series Contributors (Autori/Editori serije)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| **Contributor Role** | Uloga u seriji | `book_series_metadata/series_metadata/contributors/person_name[@contributor_role]` | **Obavezno** | author, editor, chair, series-editor, ... | contributor_role | series-editor |
| **Sequence** | Redosled u listi | `book_series_metadata/series_metadata/contributors/person_name[@sequence]` | **Obavezno** | first, additional | sequence | first |
| Given Name | Ime urednika serije | `book_series_metadata/series_metadata/contributors/person_name/given_name` | Opciono | Tekst | - | James Robert |
| **Surname** | Prezime urednika serije | `book_series_metadata/series_metadata/contributors/person_name/surname` | **Obavezno** | Tekst | - | Wilson |
| Suffix | Dodatak uz ime | `book_series_metadata/series_metadata/contributors/person_name/suffix` | Opciono | Jr., Sr., III, PhD, ... | - | Sr. |
| ORCID | ORCID urednika serije | `book_series_metadata/series_metadata/contributors/person_name/ORCID` | Opciono | ORCID format | authenticated | 0000-0003-1234-5678 |
| Institution Name | Institucija urednika | `book_series_metadata/series_metadata/contributors/person_name/affiliations/institution/institution_name` | Opciono | Tekst | - | Stanford University |
| Institution ID | ID institucije | `book_series_metadata/series_metadata/contributors/person_name/affiliations/institution/institution_id` | Opciono | URI format | type="ROR/ISNI/Wikidata" | https://ror.org/00f54p054 |

### Volume Metadata (Podaci o konkretnom tomu)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| **Language** | Glavni jezik toma | `book_series_metadata[@language]` | **Obavezno** | ISO639 kodovi | language | en |
| **Volume Title** | Naslov konkretnog toma | `book_series_metadata/titles/title` | **Obavezno** | Tekst sa formatiranjem | - | Organic Synthesis Methods |
| Volume Subtitle | Podnaslov toma | `book_series_metadata/titles/subtitle` | Opciono | Tekst sa formatiranjem | - | Modern Approaches |
| Volume Number | Broj toma u seriji | `book_series_metadata/volume` | Opciono | Tekst ili broj | - | 25 |
| Edition Number | Broj izdanja toma | `book_series_metadata/edition_number` | Opciono | Pozitivni broj | - | 2 |
| **Publication Year** | Godina objavljivanja toma | `book_series_metadata/publication_date/year` | **Obavezno** | YYYY format | - | 2024 |
| Publication Month | Mesec objavljivanja | `book_series_metadata/publication_date/month` | Opciono | 01-12 | - | 06 |
| Publication Day | Dan objavljivanja | `book_series_metadata/publication_date/day` | Opciono | 01-31 | - | 20 |
| **Volume ISBN** | ISBN toma (štampano) | `book_series_metadata/isbn[print]` | **Obavezno*** | ISBN format | media_type="print" | 978-0-123-45678-9 |
| Volume Electronic ISBN | ISBN toma (elektronsko) | `book_series_metadata/isbn[electronic]` | Opciono | ISBN format | media_type="electronic" | 978-0-123-45679-6 |
| No ISBN Reason | Razlog nepostojanja ISBN | `book_series_metadata/noisbn[@reason]` | Opciono** | withdrawn_by_publisher, archive_volume, ... | reason | archive_volume |
| **Publisher Name** | Naziv izdavača | `book_series_metadata/publisher/publisher_name` | **Obavezno** | Tekst | - | Academic Press |
| Publisher Place | Mesto izdavača | `book_series_metadata/publisher/publisher_place` | Opciono | Tekst | - | New York |
| Volume DOI | DOI konkretnog toma | `book_series_metadata/doi_data/doi` | Opciono | DOI format | - | 10.1016/series.chem.v25 |
| Volume Resource URL | Web adresa toma | `book_series_metadata/doi_data/resource` | Opciono | URL | content_version, mime_type | https://publisher.com/series/chem/v25 |

*\* ISBN ili noisbn obavezno*  
*\*\* Obavezno samo ako nema ISBN*

### Volume Contributors (Autori/Editori toma)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| **Contributor Role** | Uloga u tomu | `book_series_metadata/contributors/person_name[@contributor_role]` | **Obavezno** | author, editor, chair, reviewer, translator, ... | contributor_role | editor |
| **Sequence** | Redosled u listi | `book_series_metadata/contributors/person_name[@sequence]` | **Obavezno** | first, additional | sequence | first |
| Given Name | Ime urednika toma | `book_series_metadata/contributors/person_name/given_name` | Opciono | Tekst | - | Sarah Jane |
| **Surname** | Prezime urednika toma | `book_series_metadata/contributors/person_name/surname` | **Obavezno** | Tekst | - | Thompson |
| Suffix | Dodatak uz ime | `book_series_metadata/contributors/person_name/suffix` | Opciono | Jr., Sr., III, PhD, ... | - | PhD |
| ORCID | ORCID urednika | `book_series_metadata/contributors/person_name/ORCID` | Opciono | ORCID format | authenticated | 0000-0004-5678-9012 |
| Institution Name | Institucija urednika | `book_series_metadata/contributors/person_name/affiliations/institution/institution_name` | Opciono | Tekst | - | Harvard University |
| Institution ID | ID institucije | `book_series_metadata/contributors/person_name/affiliations/institution/institution_id` | Opciono | URI format | type="ROR/ISNI/Wikidata" | https://ror.org/03vek6s52 |

### Content Items (Poglavlja u tomu)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| Component Type | Tip sadržaja | `content_item[@component_type]` | Opciono | chapter, section, part, other | component_type | chapter |
| Language | Jezik poglavlja | `content_item[@language]` | Opciono | ISO639 kodovi | language | en |
| Publication Type | Tip publikacije | `content_item[@publication_type]` | Opciono | full_text, abstract_only | publication_type | full_text |
| Level Sequence | Hijerarhijski nivo | `content_item[@level_sequence_number]` | Opciono | Pozitivni broj | level_sequence_number | 1 |
| Chapter Title | Naslov poglavlja | `content_item/titles/title` | Opciono | Tekst sa formatiranjem | - | Catalytic Reactions |
| Chapter Subtitle | Podnaslov poglavlja | `content_item/titles/subtitle` | Opciono | Tekst sa formatiranjem | - | Mechanisms and Kinetics |
| Component Number | Broj poglavlja | `content_item/component_number` | Opciono | Tekst | - | 3 |
| First Page | Početna strana | `content_item/pages/first_page` | Opciono | Broj/oznaka | - | 67 |
| Last Page | Završna strana | `content_item/pages/last_page` | Opciono | Broj/oznaka | - | 98 |
| **Chapter DOI** | DOI poglavlja | `content_item/doi_data/doi` | **Obavezno** | DOI format | - | 10.1016/series.chem.v25.ch3 |
| **Chapter Resource URL** | URL poglavlja | `content_item/doi_data/resource` | **Obavezno** | URL | content_version, mime_type | https://publisher.com/series/chem/v25/ch3 |

### Chapter Contributors (Autori poglavlja u seriji)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| **Contributor Role** | Uloga u poglavlje | `content_item/contributors/person_name[@contributor_role]` | **Obavezno** | author, editor, chair, reviewer, translator, ... | contributor_role | author |
| **Sequence** | Redosled autora | `content_item/contributors/person_name[@sequence]` | **Obavezno** | first, additional | sequence | first |
| Given Name | Ime autora poglavlja | `content_item/contributors/person_name/given_name` | Opciono | Tekst | - | Michael David |
| **Surname** | Prezime autora poglavlja | `content_item/contributors/person_name/surname` | **Obavezno** | Tekst | - | Johnson |
| Suffix | Dodatak uz ime | `content_item/contributors/person_name/suffix` | Opciono | Jr., Sr., III, PhD, ... | - | III |
| ORCID | ORCID autora | `content_item/contributors/person_name/ORCID` | Opciono | ORCID format | authenticated | 0000-0005-9876-5432 |
| Institution Name | Institucija autora | `content_item/contributors/person_name/affiliations/institution/institution_name` | Opciono | Tekst | - | Oxford University |
| Institution ID | ID institucije | `content_item/contributors/person_name/affiliations/institution/institution_id` | Opciono | URI format | type="ROR/ISNI/Wikidata" | https://ror.org/052gg0110 |

---

## 3. Book Set Deposit (Knjiga u okviru seta)

### Set Metadata (Podaci o celom setu)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| **Set Title** | Naslov celog seta knjiga | `book_set_metadata/set_metadata/titles/title` | **Obavezno** | Tekst sa formatiranjem | - | Encyclopedia of Materials |
| Set Subtitle | Podnaslov seta | `book_set_metadata/set_metadata/titles/subtitle` | Opciono | Tekst sa formatiranjem | - | Science and Engineering |
| **Set ISBN** | ISBN celog seta (štampano) | `book_set_metadata/set_metadata/isbn[print]` | **Obavezno*** | ISBN format | media_type="print" | 978-0-123-45000-0 |
| Set Electronic ISBN | ISBN seta (elektronsko) | `book_set_metadata/set_metadata/isbn[electronic]` | Opciono | ISBN format | media_type="electronic" | 978-0-123-45001-7 |
| No ISBN Reason | Razlog nepostojanja ISBN-a | `book_set_metadata/set_metadata/noisbn[@reason]` | Opciono** | withdrawn_by_publisher, archive_volume, ... | reason | archive_volume |
| Part Number | Broj dela u složenoj strukturi | `book_set_metadata/set_metadata/part_number` | Opciono | Tekst | - | Part A |
| Set DOI | DOI celog seta | `book_set_metadata/set_metadata/doi_data/doi` | Opciono | DOI format | - | 10.1016/encyclopedia.materials |
| Set Resource URL | Web stranica seta | `book_set_metadata/set_metadata/doi_data/resource` | Opciono | URL | content_version, mime_type | https://publisher.com/encyclopedia/materials |

*\* ISBN ili noisbn obavezno*  
*\*\* Obavezno samo ako nema ISBN*

### Set Contributors (Glavni editori seta)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| **Contributor Role** | Uloga u setu | `book_set_metadata/set_metadata/contributors/person_name[@contributor_role]` | **Obavezno** | author, editor, chair, series-editor, ... | contributor_role | editor |
| **Sequence** | Redosled u listi | `book_set_metadata/set_metadata/contributors/person_name[@sequence]` | **Obavezno** | first, additional | sequence | first |
| Given Name | Ime glavnog urednika | `book_set_metadata/set_metadata/contributors/person_name/given_name` | Opciono | Tekst | - | Robert Charles |
| **Surname** | Prezime glavnog urednika | `book_set_metadata/set_metadata/contributors/person_name/surname` | **Obavezno** | Tekst | - | Anderson |
| Suffix | Dodatak uz ime | `book_set_metadata/set_metadata/contributors/person_name/suffix` | Opciono | Jr., Sr., III, PhD, ... | - | PhD |
| ORCID | ORCID urednika | `book_set_metadata/set_metadata/contributors/person_name/ORCID` | Opciono | ORCID format | authenticated | 0000-0006-1111-2222 |
| Institution Name | Institucija urednika | `book_set_metadata/set_metadata/contributors/person_name/affiliations/institution/institution_name` | Opciono | Tekst | - | Cambridge University |
| Institution ID | ID institucije | `book_set_metadata/set_metadata/contributors/person_name/affiliations/institution/institution_id` | Opciono | URI format | type="ROR/ISNI/Wikidata" | https://ror.org/013meh722 |

### Volume Metadata (Podaci o konkretnom tomu seta)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| **Language** | Glavni jezik toma | `book_set_metadata[@language]` | **Obavezno** | ISO639 kodovi | language | en |
| **Volume Title** | Naslov konkretnog toma | `book_set_metadata/titles/title` | **Obavezno** | Tekst sa formatiranjem | - | Metallic Materials |
| Volume Subtitle | Podnaslov toma | `book_set_metadata/titles/subtitle` | Opciono | Tekst sa formatiranjem | - | Properties and Applications |
| **Volume Number** | Broj toma u setu | `book_set_metadata/volume` | **Obavezno** | Tekst ili broj | - | 2 |
| Edition Number | Broj izdanja | `book_set_metadata/edition_number` | Opciono | Pozitivni broj | - | 1 |
| **Publication Year** | Godina objavljivanja | `book_set_metadata/publication_date/year` | **Obavezno** | YYYY format | - | 2024 |
| Publication Month | Mesec objavljivanja | `book_set_metadata/publication_date/month` | Opciono | 01-12 | - | 09 |
| Publication Day | Dan objavljivanja | `book_set_metadata/publication_date/day` | Opciono | 01-31 | - | 12 |
| **Volume ISBN** | ISBN toma (štampano) | `book_set_metadata/isbn[print]` | **Obavezno*** | ISBN format | media_type="print" | 978-0-123-45002-4 |
| Volume Electronic ISBN | ISBN toma (elektronsko) | `book_set_metadata/isbn[electronic]` | Opciono | ISBN format | media_type="electronic" | 978-0-123-45003-1 |
| No ISBN Reason | Razlog nepostojanja ISBN | `book_set_metadata/noisbn[@reason]` | Opciono** | withdrawn_by_publisher, archive_volume, ... | reason | archive_volume |
| **Publisher Name** | Naziv izdavača | `book_set_metadata/publisher/publisher_name` | **Obavezno** | Tekst | - | Academic Press |
| Publisher Place | Mesto izdavača | `book_set_metadata/publisher/publisher_place` | Opciono | Tekst | - | Amsterdam |
| Volume DOI | DOI konkretnog toma | `book_set_metadata/doi_data/doi` | Opciono | DOI format | - | 10.1016/encyclopedia.materials.v2 |
| Volume Resource URL | Web adresa toma | `book_set_metadata/doi_data/resource` | Opciono | URL | content_version, mime_type | https://publisher.com/encyclopedia/materials/v2 |

*\* ISBN ili noisbn obavezno*  
*\*\* Obavezno samo ako nema ISBN*

### Volume Contributors (Editori konkretnog toma)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| **Contributor Role** | Uloga u tomu | `book_set_metadata/contributors/person_name[@contributor_role]` | **Obavezno** | author, editor, chair, reviewer, translator, ... | contributor_role | editor |
| **Sequence** | Redosled u listi | `book_set_metadata/contributors/person_name[@sequence]` | **Obavezno** | first, additional | sequence | first |
| Given Name | Ime urednika toma | `book_set_metadata/contributors/person_name/given_name` | Opciono | Tekst | - | Jennifer Anne |
| **Surname** | Prezime urednika toma | `book_set_metadata/contributors/person_name/surname` | **Obavezno** | Tekst | - | Martinez |
| Suffix | Dodatak uz ime | `book_set_metadata/contributors/person_name/suffix` | Opciono | Jr., Sr., III, PhD, ... | - | PhD |
| ORCID | ORCID urednika | `book_set_metadata/contributors/person_name/ORCID` | Opciono | ORCID format | authenticated | 0000-0007-3333-4444 |
| Institution Name | Institucija urednika | `book_set_metadata/contributors/person_name/affiliations/institution/institution_name` | Opciono | Tekst | - | ETH Zurich |
| Institution ID | ID institucije | `book_set_metadata/contributors/person_name/affiliations/institution/institution_id` | Opciono | URI format | type="ROR/ISNI/Wikidata" | https://ror.org/05a28rw58 |

### Content Items (Poglavlja u tomu seta)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| Component Type | Tip sadržaja poglavlja | `content_item[@component_type]` | Opciono | chapter, section, part, other | component_type | chapter |
| Language | Jezik poglavlja | `content_item[@language]` | Opciono | ISO639 kodovi | language | en |
| Publication Type | Tip sadržaja | `content_item[@publication_type]` | Opciono | full_text, abstract_only | publication_type | full_text |
| Level Sequence | Nivo u hijerarhiji | `content_item[@level_sequence_number]` | Opciono | Pozitivni broj | level_sequence_number | 1 |
| Chapter Title | Naslov poglavlja | `content_item/titles/title` | Opciono | Tekst sa formatiranjem | - | Steel Alloys |
| Chapter Subtitle | Podnaslov poglavlja | `content_item/titles/subtitle` | Opciono | Tekst sa formatiranjem | - | Composition and Heat Treatment |
| Component Number | Identifikator poglavlja | `content_item/component_number` | Opciono | Tekst | - | 2.1 |
| First Page | Početna strana | `content_item/pages/first_page` | Opciono | Broj/oznaka | - | 25 |
| Last Page | Završna strana | `content_item/pages/last_page` | Opciono | Broj/oznaka | - | 67 |
| **Chapter DOI** | DOI poglavlja | `content_item/doi_data/doi` | **Obavezno** | DOI format | - | 10.1016/encyclopedia.materials.v2.ch2.1 |
| **Chapter Resource URL** | URL poglavlja | `content_item/doi_data/resource` | **Obavezno** | URL | content_version, mime_type | https://publisher.com/encyclopedia/materials/v2/ch2.1 |

### Chapter Contributors (Autori poglavlja u setu)

| Label | Opis polja | XML struktura (put) | **Obavezno**/Opciono | Tip podatka/Opcije | Atributi | Primer vrednosti |
|-------|------------|---------------------|---------------------|-------------------|----------|------------------|
| **Contributor Role** | Uloga u poglavlje | `content_item/contributors/person_name[@contributor_role]` | **Obavezno** | author, editor, chair, reviewer, translator, ... | contributor_role | author |
| **Sequence** | Redosled autora | `content_item/contributors/person_name[@sequence]` | **Obavezno** | first, additional | sequence | first |
| Given Name | Ime autora poglavlja | `content_item/contributors/person_name/given_name` | Opciono | Tekst | - | Thomas Edward |
| **Surname** | Prezime autora poglavlja | `content_item/contributors/person_name/surname` | **Obavezno** | Tekst | - | Brown |
| Suffix | Dodatak uz ime | `content_item/contributors/person_name/suffix` | Opciono | Jr., Sr., III, PhD, ... | - | Jr. |
| ORCID | ORCID autora | `content_item/contributors/person_name/ORCID` | Opciono | ORCID format | authenticated | 0000-0008-5555-6666 |
| Institution Name | Institucija autora | `content_item/contributors/person_name/affiliations/institution/institution_name` | Opciono | Tekst | - | Technical University Munich |
| Institution ID | ID institucije | `content_item/contributors/person_name/affiliations/institution/institution_id` | Opciono | URI format | type="ROR/ISNI/Wikidata" | https://ror.org/002k5k474 |

---

## Zajedničke napomene za sve tipove:

1. **Contributors** se mogu dodavati na više nivoa:
   - Nivo serije/seta (glavani editori)
   - Nivo knjige/toma (editori toma)
   - Nivo poglavlja (autori poglavlja)

2. **Abstract** može biti više abstrakta sa različitim tipovima (JATS format)

3. **Citation List** se može dodati za reference na bilo kom nivou

4. **Archive Locations** za informacije o arhiviranim lokacijama

5. **Publisher Item** za interne identifikatore izdavača

6. **CrossMark** i **Program** elementi za dodatne metapodatke

7. **Version Info** za informacije o verziji sadržaja

8. **Obavezna polja** su označena podebljanim fontom (****)