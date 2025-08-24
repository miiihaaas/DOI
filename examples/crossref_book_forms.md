# Crossref Book Deposit Forms - Tabular Structure

## 1. Book Deposit (Single Book with Chapters)

### Book Metadata

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| Book Type | Kategorija knjige prema sadržaju | Opciono | edited_book | `book[@book_type]` | edited_book, monograph, reference, textbook, other | book_type |
| **Language** | Glavni jezik publikacije (ISO639 kod) | **Obavezno** | en | `book_metadata[@language]` | en, sr, de, fr, es, ... | language |
| **Title** | Glavni naslov knjige | **Obavezno** | Advanced Materials Science | `book_metadata/titles/title` | Tekst sa formatiranjem | - |
| Subtitle | Podnaslov ili objašnjavanje naslova | Opciono | Theory and Applications | `book_metadata/titles/subtitle` | Tekst sa formatiranjem | - |
| Original Language Title | Naslov na originalnom jeziku (za prevode) | Opciono | Fortgeschrittene Materialwissenschaft | `book_metadata/titles/original_language_title` | Tekst sa formatiranjem | language |
| Edition Number | Redni broj izdanja | Opciono | 3 | `book_metadata/edition_number` | Pozitivni broj | - |
| **Publication Year** | Godina kada je knjiga objavljena | **Obavezno** | 2024 | `book_metadata/publication_date/year` | YYYY format | - |
| Publication Month | Mesec objavljivanja | Opciono | 03 | `book_metadata/publication_date/month` | 01-12, 21-24 (sezone), 31-34 (kvartali) | - |
| Publication Day | Dan objavljivanja | Opciono | 15 | `book_metadata/publication_date/day` | 01-31 | - |
| Media Type | Tip medija za datum publikacije | Opciono | print | `book_metadata/publication_date[@media_type]` | print, electronic, online | media_type |
| Print ISBN | ISBN za štampano izdanje | Opciono* | 978-0-123-45678-9 | `book_metadata/isbn[print]` | ISBN-10 ili ISBN-13 format | media_type="print" |
| Electronic ISBN | ISBN za elektronsko izdanje | Opciono* | 978-0-123-45679-6 | `book_metadata/isbn[electronic]` | ISBN-10 ili ISBN-13 format | media_type="electronic" |
| No ISBN Reason | Razlog zašto knjiga nema ISBN | Opciono** | archive_volume | `book_metadata/noisbn[@reason]` | withdrawn_by_publisher, archive_volume, ... | reason |
| **Publisher Name** | Naziv izdavačke kuće | **Obavezno** | Academic Press | `book_metadata/publisher/publisher_name` | Tekst | - |
| Publisher Place | Grad/zemlja izdavača | Opciono | Boston, MA | `book_metadata/publisher/publisher_place` | Tekst | - |
| Book DOI | Digitalni identifikator knjige | Opciono | 10.1016/book.2024.001 | `book_metadata/doi_data/doi` | DOI format (10.xxxx/xxxxx) | - |
| **Resource URL** | Web adresa na koju DOI pokazuje | **Obavezno ako je DOI dat** | https://publisher.com/book/123 | `book_metadata/doi_data/resource` | Validna URL adresa | content_version, mime_type |

*\* ISBN ili noisbn - jedno od ova dva je obavezno*  
*\*\* Obavezno samo ako nema ISBN*

### Book Contributors (Autori/Editori/Urednici knjige)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| **Contributor Role** | Uloga osobe u stvaranju knjige | **Obavezno** | author | `book_metadata/contributors/person_name[@contributor_role]` | author, editor, chair, reviewer, translator, ... | contributor_role |
| **Sequence** | Da li je prva ili dodatna osoba u listi | **Obavezno** | first | `book_metadata/contributors/person_name[@sequence]` | first, additional | sequence |
| Given Name | Ime i srednje ime osobe | Opciono | John Michael | `book_metadata/contributors/person_name/given_name` | Tekst | - |
| **Surname** | Prezime osobe | **Obavezno** | Smith | `book_metadata/contributors/person_name/surname` | Tekst | - |
| Suffix | Dodatak uz ime (titula, generacija) | Opciono | Jr. | `book_metadata/contributors/person_name/suffix` | Jr., Sr., III, PhD, ... | - |
| ORCID | Jedinstveni identifikator istraživača | Opciono | 0000-0002-1825-0097 | `book_metadata/contributors/person_name/ORCID` | ORCID format (0000-0000-0000-0000) | authenticated |
| Institution Name | Naziv ustanove gde radi | Opciono | University of Belgrade | `book_metadata/contributors/person_name/affiliations/institution/institution_name` | Tekst | - |
| Institution ID | Jedinstveni identifikator ustanove | Opciono | https://ror.org/03ef5s567 | `book_metadata/contributors/person_name/affiliations/institution/institution_id` | URI format | type="ROR/ISNI/Wikidata" |

### Content Items (Poglavlja/Delovi)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| Component Type | Tip dela knjige | Opciono | chapter | `content_item[@component_type]` | chapter, section, part, other, ... | component_type |
| Language | Jezik poglavlja (ako se razlikuje) | Opciono | en | `content_item[@language]` | ISO639 kodovi | language |
| Publication Type | Tip sadržaja koji se registruje | Opciono | full_text | `content_item[@publication_type]` | full_text, abstract_only | publication_type |
| Level Sequence | Redni broj nivoa u hijerarhiji | Opciono | 1 | `content_item[@level_sequence_number]` | Pozitivni broj | level_sequence_number |
| Chapter Title | Naslov poglavlja ili dela | Opciono | Introduction to Nanomaterials | `content_item/titles/title` | Tekst sa formatiranjem | - |
| Chapter Subtitle | Podnaslov poglavlja | Opciono | Basic Principles and Methods | `content_item/titles/subtitle` | Tekst sa formatiranjem | - |
| Component Number | Broj/oznaka poglavlja | Opciono | Chapter 1 | `content_item/component_number` | Tekst ili broj | - |
| First Page | Početna strana poglavlja | Opciono | 15 | `content_item/pages/first_page` | Broj ili oznaka strane | - |
| Last Page | Završna strana poglavlja | Opciono | 45 | `content_item/pages/last_page` | Broj ili oznaka strane | - |
| **Chapter DOI** | Digitalni identifikator poglavlja | **Obavezno** | 10.1016/book.2024.001.ch01 | `content_item/doi_data/doi` | DOI format | - |
| **Chapter Resource URL** | Web adresa poglavlja | **Obavezno** | https://publisher.com/book/123/ch1 | `content_item/doi_data/resource` | Validna URL adresa | content_version, mime_type |

### Chapter Contributors (Autori/Editori poglavlja)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| **Contributor Role** | Uloga osobe u stvaranju poglavlja | **Obavezno** | author | `content_item/contributors/person_name[@contributor_role]` | author, editor, chair, reviewer, translator, ... | contributor_role |
| **Sequence** | Da li je prva ili dodatna osoba u listi | **Obavezno** | first | `content_item/contributors/person_name[@sequence]` | first, additional | sequence |
| Given Name | Ime i srednje ime autora | Opciono | Maria Elena | `content_item/contributors/person_name/given_name` | Tekst | - |
| **Surname** | Prezime autora | **Obavezno** | Rodriguez | `content_item/contributors/person_name/surname` | Tekst | - |
| Suffix | Dodatak uz ime | Opciono | PhD | `content_item/contributors/person_name/suffix` | Jr., Sr., III, PhD, ... | - |
| ORCID | ORCID identifikator autora | Opciono | 0000-0001-2345-6789 | `content_item/contributors/person_name/ORCID` | ORCID format | authenticated |
| Institution Name | Naziv institucije autora | Opciono | MIT | `content_item/contributors/person_name/affiliations/institution/institution_name` | Tekst | - |
| Institution ID | ID institucije | Opciono | https://ror.org/042nb2s44 | `content_item/contributors/person_name/affiliations/institution/institution_id` | URI format | type="ROR/ISNI/Wikidata" |

---

## 2. Book Series Deposit (Knjiga u okviru serije)

### Series Metadata (Podaci o seriji)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| **Series Title** | Naziv serije knjiga | **Obavezno** | Advances in Chemistry | `book_series_metadata/series_metadata/titles/title` | Tekst sa formatiranjem | - |
| Series Subtitle | Podnaslov serije | Opciono | Research and Applications | `book_series_metadata/series_metadata/titles/subtitle` | Tekst sa formatiranjem | - |
| **Series ISSN** | ISSN serije (štampano izdanje) | **Obavezno** | 1234-5678 | `book_series_metadata/series_metadata/issn[print]` | ISSN format (1234-5678) | media_type="print" |
| Series Electronic ISSN | ISSN serije (elektronsko izdanje) | Opciono | 1234-567X | `book_series_metadata/series_metadata/issn[electronic]` | ISSN format | media_type="electronic" |
| Series CODEN | CODEN kod serije | Opciono | ADCHAM | `book_series_metadata/series_metadata/coden` | 6-karakter CODEN | - |
| Series Number | Broj serije | Opciono | 15 | `book_series_metadata/series_metadata/series_number` | Tekst ili broj | - |
| Series DOI | DOI čitave serije | Opciono | 10.1016/series.chem | `book_series_metadata/series_metadata/doi_data/doi` | DOI format | - |
| Series Resource URL | Web stranica serije | Opciono | https://publisher.com/series/chem | `book_series_metadata/series_metadata/doi_data/resource` | URL | content_version, mime_type |

### Series Contributors (Autori/Editori serije)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| **Contributor Role** | Uloga u seriji | **Obavezno** | series-editor | `book_series_metadata/series_metadata/contributors/person_name[@contributor_role]` | author, editor, chair, series-editor, ... | contributor_role |
| **Sequence** | Redosled u listi | **Obavezno** | first | `book_series_metadata/series_metadata/contributors/person_name[@sequence]` | first, additional | sequence |
| Given Name | Ime urednika serije | Opciono | James Robert | `book_series_metadata/series_metadata/contributors/person_name/given_name` | Tekst | - |
| **Surname** | Prezime urednika serije | **Obavezno** | Wilson | `book_series_metadata/series_metadata/contributors/person_name/surname` | Tekst | - |
| Suffix | Dodatak uz ime | Opciono | Sr. | `book_series_metadata/series_metadata/contributors/person_name/suffix` | Jr., Sr., III, PhD, ... | - |
| ORCID | ORCID urednika serije | Opciono | 0000-0003-1234-5678 | `book_series_metadata/series_metadata/contributors/person_name/ORCID` | ORCID format | authenticated |
| Institution Name | Institucija urednika | Opciono | Stanford University | `book_series_metadata/series_metadata/contributors/person_name/affiliations/institution/institution_name` | Tekst | - |
| Institution ID | ID institucije | Opciono | https://ror.org/00f54p054 | `book_series_metadata/series_metadata/contributors/person_name/affiliations/institution/institution_id` | URI format | type="ROR/ISNI/Wikidata" |

### Volume Metadata (Podaci o konkretnom tomu)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| **Language** | Glavni jezik toma | **Obavezno** | en | `book_series_metadata[@language]` | ISO639 kodovi | language |
| **Volume Title** | Naslov konkretnog toma | **Obavezno** | Organic Synthesis Methods | `book_series_metadata/titles/title` | Tekst sa formatiranjem | - |
| Volume Subtitle | Podnaslov toma | Opciono | Modern Approaches | `book_series_metadata/titles/subtitle` | Tekst sa formatiranjem | - |
| Volume Number | Broj toma u seriji | Opciono | 25 | `book_series_metadata/volume` | Tekst ili broj | - |
| Edition Number | Broj izdanja toma | Opciono | 2 | `book_series_metadata/edition_number` | Pozitivni broj | - |
| **Publication Year** | Godina objavljivanja toma | **Obavezno** | 2024 | `book_series_metadata/publication_date/year` | YYYY format | - |
| Publication Month | Mesec objavljivanja | Opciono | 06 | `book_series_metadata/publication_date/month` | 01-12 | - |
| Publication Day | Dan objavljivanja | Opciono | 20 | `book_series_metadata/publication_date/day` | 01-31 | - |
| **Volume ISBN** | ISBN toma (štampano) | **Obavezno*** | 978-0-123-45678-9 | `book_series_metadata/isbn[print]` | ISBN format | media_type="print" |
| Volume Electronic ISBN | ISBN toma (elektronsko) | Opciono | 978-0-123-45679-6 | `book_series_metadata/isbn[electronic]` | ISBN format | media_type="electronic" |
| No ISBN Reason | Razlog nepostojanja ISBN | Opciono** | archive_volume | `book_series_metadata/noisbn[@reason]` | withdrawn_by_publisher, archive_volume, ... | reason |
| **Publisher Name** | Naziv izdavača | **Obavezno** | Academic Press | `book_series_metadata/publisher/publisher_name` | Tekst | - |
| Publisher Place | Mesto izdavača | Opciono | New York | `book_series_metadata/publisher/publisher_place` | Tekst | - |
| Volume DOI | DOI konkretnog toma | Opciono | 10.1016/series.chem.v25 | `book_series_metadata/doi_data/doi` | DOI format | - |
| Volume Resource URL | Web adresa toma | Opciono | https://publisher.com/series/chem/v25 | `book_series_metadata/doi_data/resource` | URL | content_version, mime_type |

*\* ISBN ili noisbn obavezno*  
*\*\* Obavezno samo ako nema ISBN*

### Volume Contributors (Autori/Editori toma)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| **Contributor Role** | Uloga u tomu | **Obavezno** | editor | `book_series_metadata/contributors/person_name[@contributor_role]` | author, editor, chair, reviewer, translator, ... | contributor_role |
| **Sequence** | Redosled u listi | **Obavezno** | first | `book_series_metadata/contributors/person_name[@sequence]` | first, additional | sequence |
| Given Name | Ime urednika toma | Opciono | Sarah Jane | `book_series_metadata/contributors/person_name/given_name` | Tekst | - |
| **Surname** | Prezime urednika toma | **Obavezno** | Thompson | `book_series_metadata/contributors/person_name/surname` | Tekst | - |
| Suffix | Dodatak uz ime | Opciono | PhD | `book_series_metadata/contributors/person_name/suffix` | Jr., Sr., III, PhD, ... | - |
| ORCID | ORCID urednika | Opciono | 0000-0004-5678-9012 | `book_series_metadata/contributors/person_name/ORCID` | ORCID format | authenticated |
| Institution Name | Institucija urednika | Opciono | Harvard University | `book_series_metadata/contributors/person_name/affiliations/institution/institution_name` | Tekst | - |
| Institution ID | ID institucije | Opciono | https://ror.org/03vek6s52 | `book_series_metadata/contributors/person_name/affiliations/institution/institution_id` | URI format | type="ROR/ISNI/Wikidata" |

### Content Items (Poglavlja u tomu)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| Component Type | Tip sadržaja | Opciono | chapter | `content_item[@component_type]` | chapter, section, part, other | component_type |
| Language | Jezik poglavlja | Opciono | en | `content_item[@language]` | ISO639 kodovi | language |
| Publication Type | Tip publikacije | Opciono | full_text | `content_item[@publication_type]` | full_text, abstract_only | publication_type |
| Level Sequence | Hijerarhijski nivo | Opciono | 1 | `content_item[@level_sequence_number]` | Pozitivni broj | level_sequence_number |
| Chapter Title | Naslov poglavlja | Opciono | Catalytic Reactions | `content_item/titles/title` | Tekst sa formatiranjem | - |
| Chapter Subtitle | Podnaslov poglavlja | Opciono | Mechanisms and Kinetics | `content_item/titles/subtitle` | Tekst sa formatiranjem | - |
| Component Number | Broj poglavlja | Opciono | 3 | `content_item/component_number` | Tekst | - |
| First Page | Početna strana | Opciono | 67 | `content_item/pages/first_page` | Broj/oznaka | - |
| Last Page | Završna strana | Opciono | 98 | `content_item/pages/last_page` | Broj/oznaka | - |
| **Chapter DOI** | DOI poglavlja | **Obavezno** | 10.1016/series.chem.v25.ch3 | `content_item/doi_data/doi` | DOI format | - |
| **Chapter Resource URL** | URL poglavlja | **Obavezno** | https://publisher.com/series/chem/v25/ch3 | `content_item/doi_data/resource` | URL | content_version, mime_type |

### Chapter Contributors (Autori poglavlja u seriji)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| **Contributor Role** | Uloga u poglavlje | **Obavezno** | author | `content_item/contributors/person_name[@contributor_role]` | author, editor, chair, reviewer, translator, ... | contributor_role |
| **Sequence** | Redosled autora | **Obavezno** | first | `content_item/contributors/person_name[@sequence]` | first, additional | sequence |
| Given Name | Ime autora poglavlja | Opciono | Michael David | `content_item/contributors/person_name/given_name` | Tekst | - |
| **Surname** | Prezime autora poglavlja | **Obavezno** | Johnson | `content_item/contributors/person_name/surname` | Tekst | - |
| Suffix | Dodatak uz ime | Opciono | III | `content_item/contributors/person_name/suffix` | Jr., Sr., III, PhD, ... | - |
| ORCID | ORCID autora | Opciono | 0000-0005-9876-5432 | `content_item/contributors/person_name/ORCID` | ORCID format | authenticated |
| Institution Name | Institucija autora | Opciono | Oxford University | `content_item/contributors/person_name/affiliations/institution/institution_name` | Tekst | - |
| Institution ID | ID institucije | Opciono | https://ror.org/052gg0110 | `content_item/contributors/person_name/affiliations/institution/institution_id` | URI format | type="ROR/ISNI/Wikidata" |

---

## 3. Book Set Deposit (Knjiga u okviru seta)

### Set Metadata (Podaci o celom setu)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| **Set Title** | Naslov celog seta knjiga | **Obavezno** | Encyclopedia of Materials | `book_set_metadata/set_metadata/titles/title` | Tekst sa formatiranjem | - |
| Set Subtitle | Podnaslov seta | Opciono | Science and Engineering | `book_set_metadata/set_metadata/titles/subtitle` | Tekst sa formatiranjem | - |
| **Set ISBN** | ISBN celog seta (štampano) | **Obavezno*** | 978-0-123-45000-0 | `book_set_metadata/set_metadata/isbn[print]` | ISBN format | media_type="print" |
| Set Electronic ISBN | ISBN seta (elektronsko) | Opciono | 978-0-123-45001-7 | `book_set_metadata/set_metadata/isbn[electronic]` | ISBN format | media_type="electronic" |
| No ISBN Reason | Razlog nepostojanja ISBN-a | Opciono** | archive_volume | `book_set_metadata/set_metadata/noisbn[@reason]` | withdrawn_by_publisher, archive_volume, ... | reason |
| Part Number | Broj dela u složenoj strukturi | Opciono | Part A | `book_set_metadata/set_metadata/part_number` | Tekst | - |
| Set DOI | DOI celog seta | Opciono | 10.1016/encyclopedia.materials | `book_set_metadata/set_metadata/doi_data/doi` | DOI format | - |
| Set Resource URL | Web stranica seta | Opciono | https://publisher.com/encyclopedia/materials | `book_set_metadata/set_metadata/doi_data/resource` | URL | content_version, mime_type |

*\* ISBN ili noisbn obavezno*  
*\*\* Obavezno samo ako nema ISBN*

### Set Contributors (Glavni editori seta)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| **Contributor Role** | Uloga u setu | **Obavezno** | editor | `book_set_metadata/set_metadata/contributors/person_name[@contributor_role]` | author, editor, chair, series-editor, ... | contributor_role |
| **Sequence** | Redosled u listi | **Obavezno** | first | `book_set_metadata/set_metadata/contributors/person_name[@sequence]` | first, additional | sequence |
| Given Name | Ime glavnog urednika | Opciono | Robert Charles | `book_set_metadata/set_metadata/contributors/person_name/given_name` | Tekst | - |
| **Surname** | Prezime glavnog urednika | **Obavezno** | Anderson | `book_set_metadata/set_metadata/contributors/person_name/surname` | Tekst | - |
| Suffix | Dodatak uz ime | Opciono | PhD | `book_set_metadata/set_metadata/contributors/person_name/suffix` | Jr., Sr., III, PhD, ... | - |
| ORCID | ORCID urednika | Opciono | 0000-0006-1111-2222 | `book_set_metadata/set_metadata/contributors/person_name/ORCID` | ORCID format | authenticated |
| Institution Name | Institucija urednika | Opciono | Cambridge University | `book_set_metadata/set_metadata/contributors/person_name/affiliations/institution/institution_name` | Tekst | - |
| Institution ID | ID institucije | Opciono | https://ror.org/013meh722 | `book_set_metadata/set_metadata/contributors/person_name/affiliations/institution/institution_id` | URI format | type="ROR/ISNI/Wikidata" |

### Volume Metadata (Podaci o konkretnom tomu seta)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| **Language** | Glavni jezik toma | **Obavezno** | en | `book_set_metadata[@language]` | ISO639 kodovi | language |
| **Volume Title** | Naslov konkretnog toma | **Obavezno** | Metallic Materials | `book_set_metadata/titles/title` | Tekst sa formatiranjem | - |
| Volume Subtitle | Podnaslov toma | Opciono | Properties and Applications | `book_set_metadata/titles/subtitle` | Tekst sa formatiranjem | - |
| **Volume Number** | Broj toma u setu | **Obavezno** | 2 | `book_set_metadata/volume` | Tekst ili broj | - |
| Edition Number | Broj izdanja | Opciono | 1 | `book_set_metadata/edition_number` | Pozitivni broj | - |
| **Publication Year** | Godina objavljivanja | **Obavezno** | 2024 | `book_set_metadata/publication_date/year` | YYYY format | - |
| Publication Month | Mesec objavljivanja | Opciono | 09 | `book_set_metadata/publication_date/month` | 01-12 | - |
| Publication Day | Dan objavljivanja | Opciono | 12 | `book_set_metadata/publication_date/day` | 01-31 | - |
| **Volume ISBN** | ISBN toma (štampano) | **Obavezno*** | 978-0-123-45002-4 | `book_set_metadata/isbn[print]` | ISBN format | media_type="print" |
| Volume Electronic ISBN | ISBN toma (elektronsko) | Opciono | 978-0-123-45003-1 | `book_set_metadata/isbn[electronic]` | ISBN format | media_type="electronic" |
| No ISBN Reason | Razlog nepostojanja ISBN | Opciono** | archive_volume | `book_set_metadata/noisbn[@reason]` | withdrawn_by_publisher, archive_volume, ... | reason |
| **Publisher Name** | Naziv izdavača | **Obavezno** | Academic Press | `book_set_metadata/publisher/publisher_name` | Tekst | - |
| Publisher Place | Mesto izdavača | Opciono | Amsterdam | `book_set_metadata/publisher/publisher_place` | Tekst | - |
| Volume DOI | DOI konkretnog toma | Opciono | 10.1016/encyclopedia.materials.v2 | `book_set_metadata/doi_data/doi` | DOI format | - |
| Volume Resource URL | Web adresa toma | Opciono | https://publisher.com/encyclopedia/materials/v2 | `book_set_metadata/doi_data/resource` | URL | content_version, mime_type |

*\* ISBN ili noisbn obavezno*  
*\*\* Obavezno samo ako nema ISBN*

### Volume Contributors (Editori konkretnog toma)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| **Contributor Role** | Uloga u tomu | **Obavezno** | editor | `book_set_metadata/contributors/person_name[@contributor_role]` | author, editor, chair, reviewer, translator, ... | contributor_role |
| **Sequence** | Redosled u listi | **Obavezno** | first | `book_set_metadata/contributors/person_name[@sequence]` | first, additional | sequence |
| Given Name | Ime urednika toma | Opciono | Jennifer Anne | `book_set_metadata/contributors/person_name/given_name` | Tekst | - |
| **Surname** | Prezime urednika toma | **Obavezno** | Martinez | `book_set_metadata/contributors/person_name/surname` | Tekst | - |
| Suffix | Dodatak uz ime | Opciono | PhD | `book_set_metadata/contributors/person_name/suffix` | Jr., Sr., III, PhD, ... | - |
| ORCID | ORCID urednika | Opciono | 0000-0007-3333-4444 | `book_set_metadata/contributors/person_name/ORCID` | ORCID format | authenticated |
| Institution Name | Institucija urednika | Opciono | ETH Zurich | `book_set_metadata/contributors/person_name/affiliations/institution/institution_name` | Tekst | - |
| Institution ID | ID institucije | Opciono | https://ror.org/05a28rw58 | `book_set_metadata/contributors/person_name/affiliations/institution/institution_id` | URI format | type="ROR/ISNI/Wikidata" |

### Content Items (Poglavlja u tomu seta)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| Component Type | Tip sadržaja poglavlja | Opciono | chapter | `content_item[@component_type]` | chapter, section, part, other | component_type |
| Language | Jezik poglavlja | Opciono | en | `content_item[@language]` | ISO639 kodovi | language |
| Publication Type | Tip sadržaja | Opciono | full_text | `content_item[@publication_type]` | full_text, abstract_only | publication_type |
| Level Sequence | Nivo u hijerarhiji | Opciono | 1 | `content_item[@level_sequence_number]` | Pozitivni broj | level_sequence_number |
| Chapter Title | Naslov poglavlja | Opciono | Steel Alloys | `content_item/titles/title` | Tekst sa formatiranjem | - |
| Chapter Subtitle | Podnaslov poglavlja | Opciono | Composition and Heat Treatment | `content_item/titles/subtitle` | Tekst sa formatiranjem | - |
| Component Number | Identifikator poglavlja | Opciono | 2.1 | `content_item/component_number` | Tekst | - |
| First Page | Početna strana | Opciono | 25 | `content_item/pages/first_page` | Broj/oznaka | - |
| Last Page | Završna strana | Opciono | 67 | `content_item/pages/last_page` | Broj/oznaka | - |
| **Chapter DOI** | DOI poglavlja | **Obavezno** | 10.1016/encyclopedia.materials.v2.ch2.1 | `content_item/doi_data/doi` | DOI format | - |
| **Chapter Resource URL** | URL poglavlja | **Obavezno** | https://publisher.com/encyclopedia/materials/v2/ch2.1 | `content_item/doi_data/resource` | URL | content_version, mime_type |

### Chapter Contributors (Autori poglavlja u setu)

| Label | Opis polja | **Obavezno**/Opciono | Primer vrednosti | XML struktura (put) | Tip podatka/Opcije | Atributi |
|-------|------------|---------------------|------------------|---------------------|-------------------|----------|
| **Contributor Role** | Uloga u poglavlje | **Obavezno** | author | `content_item/contributors/person_name[@contributor_role]` | author, editor, chair, reviewer, translator, ... | contributor_role |
| **Sequence** | Redosled autora | **Obavezno** | first | `content_item/contributors/person_name[@sequence]` | first, additional | sequence |
| Given Name | Ime autora poglavlja | Opciono | Thomas Edward | `content_item/contributors/person_name/given_name` | Tekst | - |
| **Surname** | Prezime autora poglavlja | **Obavezno** | Brown | `content_item/contributors/person_name/surname` | Tekst | - |
| Suffix | Dodatak uz ime | Opciono | Jr. | `content_item/contributors/person_name/suffix` | Jr., Sr., III, PhD, ... | - |
| ORCID | ORCID autora | Opciono | 0000-0008-5555-6666 | `content_item/contributors/person_name/ORCID` | ORCID format | authenticated |
| Institution Name | Institucija autora | Opciono | Technical University Munich | `content_item/contributors/person_name/affiliations/institution/institution_name` | Tekst | - |
| Institution ID | ID institucije | Opciono | https://ror.org/002k5k474 | `content_item/contributors/person_name/affiliations/institution/institution_id` | URI format | type="ROR/ISNI/Wikidata" |

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