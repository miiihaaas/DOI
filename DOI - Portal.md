## DOI \- Portal

## 1\. OPIS PROJEKTA

Cilj projekta je izrada portala za prikaz naučnih publikacija (časopisi, zbornici, monografije) i članaka u okviru njih kojima se dodeljuje DOI. Portal se nalazi na poddomenu glavnog sajta doi.rs (portal.doi.rs). Pristup portalu je otvoren za sve posetioce, a njegov cilj je da istovremeno pruži posetiocima pristup naučnim publikacijama i člancima u okviru njih i sa druge strane omogući veću promociju i vidljivost izdavačima i autorima naučnih publikacija i naučnih članaka. Portal mora biti razvijen u skladu sa GDPR standardima. Na svakoj strani portala postaviti breadcrumbs (navigacione putanje) radi lakše orijentacije korisnika.

Portal treba da omogući:

- jasan i pregledan prikaz publikacija,  
- da svaki članak ima svoju posebnu landing stranicu,  
- jednostavno korišćenje za administratore,  
- tehničku pripremljenost za naknadnu integraciju sa Crossref servisom.  
- Promociju portala doi.rs i usluga koje se nude u okviru njega

Portal ne služi za čitanje kompletnog teksta na sajtu, već za:

- prikaz metapodataka,  
- prikaz apstrakta,  
- preuzimanje PDF fajla.

## 2\. OSNOVNI PRINCIPI

### 2.1. Jedan članak – jedna stranica – jedan DOI

Svaki članak u okviru portala ima:

- jednu URL adresu,  
- jednu landing stranicu,  
- jedan DOI.

DOI uvek vodi na landing stranicu, nikada direktno na PDF.

### 2.2. Dizajn i brzina

- Moderan dizajn (inspiracija: MDPI, Frontiers)  
- Korišćenje boja i dizajnerskog stila sajta doi.rs  
- Brzo učitavanje stranica  
- Jednostavan, čist i pregledan izgled  
- Responzivni dizajn za pristup sa različitih uređaja (desktop, tablet, mobilni)

## 3\. STRUKTURA PORTALA – JAVNI DEO

## 3.1. Početna strana

Početna strana bi trebalo da bude moderog i minimalistočkog dizajna u skladu sa bojama i dizajnom osnovnog sajta (doi.rs).

Na početnoj strani se nalazi meni (sticky) sa sledećim stavkama:

- Početna  
- Publikacije (sa stavakama u podmeniju: Časopisi, Zbornici, Monografije, Ostalo)  
- Izdavači  
- O portalu  
- Kontakt

Iznad menija nalazi se top heder sa kontakt informacijama \- mejl adresom (info@doi.rs) i brojem telefona (+381 64 225 1101).

Na poziciji hero image nalazi se kratki uvodni tekst o samom portalu, sa leve strane, dok se na istoj poziciji sa desne strane nalazi polje za pretragu koje pruža mogućnost korisniku da pretraži članke po nazivu, autoru i ključnim rečima. U pozadini se nalazi grafika u skladu sa bojama i dizajnom glavnog portala koja omogućava laku čitljivost teksta i dobru vidljivost polja za pretragu.

Ispod bloka na poziciji hero image nalaze se blokovi sa efektnim grafičkim rešenjem (diskretnom animacijom), na kojima su prikazane vrste publikacija koje su zastupljene na portalu: 

- časopisi,   
- zbornici,   
- monografije,   
- ostalo

Blokovi su klikabilni i vode ka svim publikacijama iz odabrane vrste. Svaka vrsta publikacije trebalo bi da bude obeležena određenom ikonicom. Te ikonice stajale bi kasnije i uz svaku pojedinačnu publikaciju čime bi olakšala prepoznavanje vrste publikacije.

U sledećem bloku nalazi se filter (kao na portalu [mdpi.com](http://mdpi.com)) koji pruža korisniku prikaz toga koje sve publikacije su zastupljene na portalu, uz mogućnost filtriranja prema oblastima. U bloku se nalazi i dugme vidi sve koje vodi na stranu Publikacije.

U narednim blokovima na početnoj strani prikazano je po 8 publikacija sa najviše pregleda za svaku vrstu publikacije (osim za vrstu \- Ostalo) raspoređenih u 2 reda sa po 4 kolone, uz dugme VIDI SVE (publikacije određene vrste). Svaka vrsta publikacije ima svoj podnaslov i 8 publikacija. Pojedinačne publikacije jedne vrste prikazane su u vidu velikih blokova sa slikama naslovnih strana, kratkim informacijama i dugmetom koje vodi na stranu sa svim brojevima konkretne publikacije.

U sledeće bloku prikazani su poslednji članci postavljeni na portalu. Članci su prikazani sa naslovom, pored koga se nalazi ikonica koja prikazuju vrstu publikacije u kojoj se članak nalazi i ikonica koja prikazuje da li članak ima “open access”. Ispod naslova nalazi se podatak o autoru, a ispod toga kratak sažetak članka ograničen na određeni broj karaktera. Ispod sažetka nalazi se informacija o datumu objavljivanja i dugme OPŠIRNIJE koje vodi na lending stranu članka.

U bloku se nalazi 2 reda sa po 4 članka.

Ispod svih blokova nalazi se futer. Futer je podeljen u 4 bloka. U prvom bloku nalazi se impresum, u drugom su linkovi iz menija, u trećem korisni linkovi, a u četvrtom blok sa opcijom za prijavu za newsletter. Ispod futera nalazi se deo za copyright sa informacijama \- Copyright © 2026\. doi.rs. Sva prava zadržana. U istom delu desno poravnato nalaze se linkovi ka stranama:

- Politika privatnosti  
- Uslovi korišćenja

## 3.2. Publikacije

Stavka u meniju Publikacije vodi direktno na stranu svih publikacija na portalu. Publikacije su prikazane u tabeli sa sledećim kolonama:

- Naziv publikacije  
- Vrsta publikacije  
- Oblast  
- Pristup (otvoren pristup, pristup uz pomoć logovanja i plaćen pristup)  
- Izdavač  
- Jezik

Strana daje opcije filtriranja koje se nalaze u samom zaglavlju strane. Moguće je filtrirati publikacije prema sledećim kriterijumima:

- Vrsta publikacije (Časopis, Zbornik, Monografija, Ostalo)  
- Oblast (definisati oblasti \- možda je ovo dobar primer: https://hrcak.srce.hr/podrucja)  
- Pristup (otvoren, zatvoren ili plaćen)  
- Jezik 

Filter napraviti kao multiselect.

Omogućeno je sortiranje po abecednom redu. U zaglavlju strane postoji i polje za pretragu gde je moguće pretraživati publikacije po nazivu ili izdavaču, U bočnom meniju moguće nalazi se navigacija putem koje je moguće otići i na stranu svake pojedinačne vrste publikacije na kojoj se prikazuju isključivo publikacije iz odabrane vrste (časopisi, zbornici, monografije, ostalo). Svaka od tih strana ima istu strukturu kao i strana Publikacije (filtriranje, pretraga, tabela, bočni meni) s tim da se razlikuju kolone u tabeli zavisno od vrste publikacije. Klikom na naziv publikacije otvara se strana konkretne publikacije sa svim izdanjima.

Pored opcije da se u glavnom meniju ode direktno na stranu svih publikacija, vidljive su i stavke iz podmenija:

- Časopisi,   
- Zbornici,   
- Monografije,   
- Ostalo

Klikom na stavku iz podmenija otvara se strana na kojoj se prikazuju isključivo publikacije iz odabrane vrste (podmeni \= bočni meni na strani Publikacije). Kod prikaza većeg broja publikacija, izdanja ili članaka koristiti infinite scroll.

### 3.2.1 Časopisi

Kolone u tabeli:

- Naziv publikacije  
- Oblast  
- ISSN / eISSN  
- Prvo objavljivanje  
- Pristup  
- Izdavač  
- Jezik

Bilo bi dobro u nekom od narednih koraka omogućiti unos podataka, a zatim i sortiranje po nekim od kriterijuma koji su zastupljeni na portalu mdpi.com: 

- Impact factor  
- CiteScore

### 3.2.2 Zbornici

Kolone u tabeli:

- Naziv publikacije  
- Oblast  
- ISBN / ISSN  
- Godina izdanja  
- Pristup  
- Izdavač  
- Urednik / Urednici  
- Broj radova  
- Jezik

###  3.2.3 Monografije

Kolone u tabeli:

- Naziv publikacije  
- Oblast  
- ISBN  
- Godina izdanja  
- Pristup  
- Izdavač  
- Autor / Autori  
- Broj radova  
- Jezik

### 3.2.4 Ostalo

Kolone u tabeli:

- Naziv publikacije  
- Tip publikacije (definisati tipove \- npr. izveštaji, studije…)  
- Oblast  
- ISBN  
- Godina izdanja  
- Pristup  
- Izdavač  
- Autor / Autori  
- Jezik

## 

## 3.3. Strana pojedinačne publikacije

Strana pojedinačne publikacije razlikuje se zavisno od vrste publikacije. Razlika se ogleda u podacima koji se prikazuju za konkretnu vrstu publikacije. Potrebno je prikazati sve podatke prethodno definisane u kolonama tabele na stranama svake od vrsta publikacije.

Stranica ima sajdbar u kome su prikazani podaci o publikaciji (naziv, vrsta publikacije, oblast, godina izdanja, ISBN/ISSN, licenca…). Podaci u sajdbaru su grupisani u više boksova:

- Podaci o publikaciji uz kratak opis  
- Podaci o izdavaču  
- ?

Kod monografskih publikacija, otvara se odmah strana na kojoj se prikazuju svi članci iz publikacije raspoređeni u grafički zanimljivo rešenim blokovima, po 3 članka u jednom redu (primer: [https://www.frontierspartnerships.org/journals/dystonia/articles](https://www.frontierspartnerships.org/journals/dystonia/articles)). Kod serijskih publikacija otvara se strana na kojoj su izlistana sva izdanja serijske publikacije. Izdanja su raspoređena u 3 kolone, imaju sliku naslovne strane ili generičku sliku ukoliko nemaju sliku naslovne strane. Slika je uvek istog formata radi ujednačenog izgleda. Pored slike u boksu jednog izdanja prikazani su i sledeći podaci:

- Broj  
- Volume  
- Godina izdanja  
- Dugme OPŠIRNIJE

Klikom na dugme OPŠIRNIJE otvara se strana pojedinačnog izdanja serijske publikacije. Članci iz izdanja raspoređeni su u grafički zanimljivo rešenim blokovima, po 3 članka u jednom redu (primer: [https://www.frontierspartnerships.org/journals/dystonia/articles](https://www.frontierspartnerships.org/journals/dystonia/articles)). 

U oba slučaja (i kod monografskih i kod serijskih publikacija), u blokovima u kojima su prikazani članci nalaze se sledeći podaci:

- Naslov članka  
- Kratak sažetak  
- Autori  
- Datum objave  
- Naziv publikacije  
- DOI  
- Dugme OPŠIRNIJE

Ukoliko je u pitanju serijska publikacija, ispod čanaka prikazana je arhiva izdanja raspoređena po godinama i brojevima.

## 3.4. Lending stranica članka

Lending stranica ili odredišna stranica članka predstavlja prikaz jednog članka iz publikacije prema standardima propisanim od strane Crossref-a. Stranica treba da bude sadržajna i pregledna, jednostavnog i modernog dizajna, sa jasno izdvojenim celinama (Dobar primer \- https://www.frontierspartnerships.org/journals/dystonia/articles/10.3389/dyst.2025.14692/full). Kako bi se informacije jasno razdvojile, potrebno je da stranica ima sajdbar u koji će biti smešten deo podataka. Podaci koji se nalaze u sajdabru su razdvojeni u blokovima:  
   
PUBLIKACIJA

- Naslovna strana publikacije  
- ISSN / eISSN  
- Licenca

IZDAVAČ

- Naziv Izdavača  
- Ostali podaci o izdavaču

METRIKA

- Metrika povučena sa Crossref putem API (Citiranja, pregledi, preuzimanja)

Poželjno bi bilo da ukoliko tehnički nije teško izvodljivo imamo opciju generisanja citata u različitim formatima (APA, MLA, Chicago, BibTeX, RIS). Ukoliko postoji mogućnost, ovaj blok trebalo bi da stoji u sajdbaru.

U glavnom delu strane smešten je članak sa svim neophodnim podacima:

- Naziv časopisa  
- Datum objavljivanja  
- Volume i broj  
- DOI  
- Naslov članka  
- Podnaslov članka  
- Autori \+ ORCID ikonice sa linkom do njihovog ORCID naloga  
- Dugme za preuzimanje PDF-a  
- Ključne reči  
- Apstrakt  
- Ceo tekst

Sa desne strane, u floating bar-u prikazati opcije za preuzimanje PDF-a, opcija za “share” i dugme sa linkom za DOI grafički uređeni na sličan način kao u primeru ovde: [https://www.frontierspartnerships.org/journals/aerospace-research-communications/articles/10.3389/arc.2025.15466/full](https://www.frontierspartnerships.org/journals/aerospace-research-communications/articles/10.3389/arc.2025.15466/full) Ukoliko remeti vidljivost teksta na mobilnim uređajima ne prikazivati floating bar.

Predvideti prikazivanje referenci iz rada, čak i ukoliko ih ne budemo u početku prikazivali. Reference se nalaze ispod apstrakta ili spod celog teksta članka (ukoliko je primenljivo). Reference prikazati kao ovde \- https://journals.sagepub.com/doi/10.1177/20584601251412850

Ispod (referenci) apstrakta ili celog teksta (ukoliko je primenljivo) potrebno je da se nađe karusel sa ostalim člancima iz časopisa. Ispod ovog karusela nalazi se karusel za prikaz ostalih publikacija iz serije (ukoliko je primenljivo).

## 3.5. Stranica izdavača

Stranica Izdavači prikazuje sve izdavače koji se nalaze na portalu. Stranica olakšava pronalaženje časopisa ili izdanja prema izdavaču i pruža osnovne informacije o svakom izdavaču. Izdavači su prikazani u blokovima u 4 kolone. Iznad prikazanih blokova sa informacijama o izdavačima nalazi se polje za pretragu po nazivu izdavača i filter po oblasti publikacija. Omogućeno je sortiranje po dva kriterijuma:

- Abecedno  
- Broj publikacija

U bloku za izdavača nalaze se sledeće informacije:

- Logo izdavača (Ako ne postoji prikazati logo doi.rs)  
- Naziv izdavača  
- Kratak opis izdavača (2–3 rečenice)  
- Broj publikacija dostupnih na portalu  
- Dugme PRIKAŽI PUBLIKACIJE

Nakon klika na dugme PRIKAAŽI PUBLIKACIJE otvara se strana na kojoj se prikazuju sledeće informacije:

- Naziv i logo izdavača  
- Kratak opis izdavača  
- Kontakt informacije izdavača (adresa, imejl, sajt, telefon)  
- Lista publikacija koje izdavač objavljuje, sa linkovima ka publikacijama

## 3.6. Stranica O portalu

Stranica O portalu služi da posetiocima objasni čemu portal služi, koje publikacije sadrži i koja je njegova svrha i koristi za istraživače, bibliotekare i širu javnost. Na početku se nalazi tekst (pripremiti tekst) koji govori o portalu. Ispod teksta su u grafički zanimljivo rešenim blokovima prikazani su ciljevi portala:

- Povećanje dostupnosti naučnih publikacija  
- Omogućavanje lakog pronalaženja članaka i izdanja  
- Jednostavan pristup metapodacima

Ispod ovih blokova nalazi se dugme KONTAKTIRAJTE NAS koje vodi do KONTAKT stranice.

## 3.7. Stranica Kontakt

Stranica Kontakt omogućava posetiocima portala da brzo i jednostavno stupe u kontakt sa timom portala ili sa korisničkom podrškom. Stranica je informativna i praktična, ne služi za objavljivanje sadržaja ili komentara.

Stranica je podeljena u dva bloka, od kojih ⅓ zauzima deo sa kontakt informacijama (levo), a ⅔ zauzima deo sa kontakt formom.

U bloku Kontakt informacije potrebno je upisati sledeće podatke:

- Imejl: info@doi.rs  
- Telefon: \+381 64 2251101 | \+381 61 6183078  
- Web: doi.rs  
- Adresa: Nikole Lunjevice 3D, 32300 Gornji Milanovac, Srbija

Ispod ovih podataka potrebno je staviti podnaslov \-  RADNO VREME sa sledećim podacima:

ponedeljak \- petak  
08:00 \- 16:00

U bloku Kontaktirajte nas potrebno je kreirati kontakt formu koja upite šalje na mejl adresu info@doi.rs. Forma bi imala sledeća polja:

- Ime i prezime\*  
- Imejl adresa\*  
- Institucija  
- Poruka\*  
- Dugme za slanje poruke: POŠALJI

Ispod ova dva bloka nalazi se mapa celom širinom ekrana koja prikazuje adresu firme:

- Nikole Lunjevice 3, 32300 Gornji Milanovac, Srbija

Dodati CAPTCHA ili anti-spam zaštitu za kontakt formu kako bi se smanjio broj spam mejlova.

# 4\. Admin panel

Admin panel je mesto gde bibliotekar unosi, uređuje i objavljuje podatke o izdavačima, publikacijama, izdanjima i člancima. Njime upravlja nekoliko tipova korisnika:

- Superadmin  
- Administrator  
- Urednik  
- Bibliotekar

Sistem automatski priprema XML za Crossref i kreira landing stranicu na portalu. Admin panel treba da bude jednostavan. Polja imaju kratko objašnjenje, postoje validacije koje upozore korisnika pre nego što sačuva podatke i postoji opcija da se pregled (preview) landing strane vidi pre objave.

## 4.1. Uloge i prava (RBAC)

Na admin panelu postoji nekoliko tipova korisnika:

- **Superadmin** — pun pristup svemu (sistemska podešavanja, korisnici, logovi, Crossref).  
- **Administrator** — upravlja sadržajem, izdavačima, publikacijama, izdanjima, člancima, može slati Crossref XML, ali ne može da menja sistemska podešavanja.  
- **Urednik** — može kreirati i izmeniti članke i izdanja, ali ne može da briše ili upravlja korisnicima, kao ni da šalje XML za Crossref.  
- **Bibliotekar** — može unositi i uređivati metapodatke, uploadovati PDF i slike, a sve promene koje napravi idu na odobrenje korisniku više instance.

Kako bi se smanjio broj nepredviđenih grešaka, svi zahtevi za brisanje moraju imati potvrdu (soft delete, rollback moguć). Akcije poput slanja XML-a Crossref-u može da izvršava samo administrator i speradmin. Audit log beleži ko je šta radio (user-id, ip, vreme, akcija).

## 4.2. Stranice i funkcionalnosti

### 4.2.1. Dashboard

Svrha početne stranice admin panela je da pruži pregled stanja i brz pristup zadacima.

Na početnoj strani predviđeno je nekoliko blokova:

\- Statistika: broj publikacija, izdanja, članaka, neobjavljenih unosa (koji čekaju odobrenje)  
\- Lista zadataka: Članci na odobrenju, Uspešni i neuspešni Crossref zahtevi.  
\- Brzi linkovi: Novi članak, Novi izdavač, Pregled logova.  
\- Status: status konekcije sa Crossref

### 4.2.2. Korisnici

- **Lista:** ime, email, uloga, poslednja aktivnost, status (aktivno/zaključano).  
- **Edit:** ime, prezime, email, uloga,   
- **Akcije:** reset lozinke, aktiviraj/deaktiviraj, prikaz audit log-a za korisnika.  
- **Validacije:** email jedinstven, strong password policy pri kreiranju.

### 4.2.3. Izdavači

- **Lista:** logo, naziv, broj publikacija, država, status verifikacije.  
- **Form view polja:**  
  - Naziv izdavača\*  
  - Logo (png/jpg; automatski thumbnail)  
  - Kratak opis (2–3 rečenice)  
  - Sajt (URL)  
  - Email, telefon, adresa  
  - Kontakt osoba (ime, email)

### 4.2.4. Publikacije

- **Lista:** naziv, vrsta (Časopis / Zbornik / Monografija / Ostalo), oblast, ISSN/ISBN, pristup (otvoren, zatvoren, plaćen), izdavač.  
- **Form view polja:**  
  - Naziv publikacije\*  
  - Vrsta publikacije\*  
  - Kratak opis  
  - Naslovna slika / logo publikacije  
  - Oblast (multiselect)  
  - ISSN / eISSN / ISBN (polja)  
  - Prvo objavljivanje (godina)  
  - Jezik  
  - Pristup (otvoren, zatvoren, plaćen)  
  - Licenca (npr. CC-BY 4.0)  
  - Izdavač (lookup / link)  
  - Kontakt uredništva (ime, email)  
- **Akcije:** Pregled svih izdanja, dodaj izdanje, preview stranice publikacije.  
- **Validacije:** ISSN/ISBN format, obavezna vrsta i naziv.

### 4.2.5. Izdanja

- **Lista:** vezano za publikaciju — Volume, Broj, Godina, Datum objave, Broj članaka.  
- **Form view polja:**  
  - Odabrana publikacija (needitable kad je već vezano)  
  - Volume (tekst/broj)  
  - Broj (issue) (tekst/broj)  
  - Godina  
  - Datum objave (datum)  
  - Naslovna slika izdanja (opciono)  
  - Opis  
  - Status: draft / scheduled / published / archive  
- **Akcije:** Publish / Unpublish, preview izdanja, duplicate (kopiraj strukturu),   
- **Validacije:** Volume/Issue konzistentni, datum objave validan.

### 4.2.6. Članci

- **Lista:** naslov, autori, publikacija, volume/issue, DOI, status (draft/review/published), datum objave.  
- **Form view:**  
  - **Meta podaci**  
    - Naslov\*  
    - Podnaslov (opcionalno)  
    - DOI (polje readonly dokle god nije rezervisan; opciono ručni unos za postojeće)  
    - Status (Draft / For review / Ready to publish / Published / Withdrawn)  
    - Scheduled publish date (opciono)  
- **Autori**  
  - Polja za dodavanje autora (reorderable list):  
    - Ime i prezime\*  
    - Afilijacija (tekst)  
    - Email (opciono)  
    - ORCID (polje \+ validacija ORCID format i link)  
    - Corresponding author checkbox  
    - Author order (drag & drop)  
  - Dugme: Dodaj autora  
- **Sadržaj**  
  - Apstrakt\* (rich text ili plain text)  
  - Ključne reči (tag input)  
  - Tekst članka (HTML editor)  
  - Reference (plain text / structured input ili upload RIS / BibTeX)  
- **Datoteke**  
  - Upload PDF (obavezno za objavu)  
- **Bibliografski podaci**  
  - Naziv časopisa (linked)  
  - Volume / Izdanje (linked)  
  - Stranice (početna / poslednja) (opciono)  
  - Datum objave  
- **Dodatne opcije**  
  - Open Access ikonica \+ izbor licence  
  - Vidljiv / nevidljiv (switch)  
- **Akcije**  
  - Sačuvaj kao draft  
  - Spremno za pregled  
  - Preview landing strane (otvara lending stranu kao neobjavljeno)  
  - Objavi (samo Urednik i Administrator)  
  - Generiši Crossref XML \- Da li ovde ili kod izdanja? Da li bi trebalo dodati opciju za upis linka lending strane izdavača i PDF-a ukoliko su i oni napravili lending stranicu?  
  - Rezerviši DOI (opciono, rezervacija u Crossref-u) \- Da li je potrebno?  
  - Pošalji u  Crossref (deposit) — (Superadmin ili administrator) \- Da li ovde ili kod izdanja?  
  - Export metadata (RIS, BibTeX, Dublin Core XML) \- Da li i ovde i kod izdanja ili smao kod izdanja?  
  - Obriši (soft delete), Vrati

**Validacije i pomoći**

- Obavezna polja: Naslov, Autori (\>=1), Apstrakt, PDF (pre objave), Publikacija (Prethodno mora da postoji publikacija u bazi), Volume / Izdanje  (ako je vezano)  
- ORCID polje validira format (0000-0000-0000-0000)  
- PDF veličinat (maksimum. 100 MB) \+ eksterne provere (virus scan)


# 5\. Workflow

1. **Unos (Bibliotekar) \-** Kreira novi članak/izdanje/publikaciju, popuni metapodatke, uploaduje PDF. Sačuva kao *Draft*.

2. **Pregled (Urednik) \-** Urednik otvara draft, pregleda metapodatke, izvrši izmene ili prihvata za objavu.

3. **Odobrenje (Administrator) \-** Nakon odobrenja, Admin može:  
- rezervisati DOI (opciono),  
- generisati Crossref XML,  
- poslati deposit na Crossref (ako je integrisano),  
- objaviti članak (publish) — landing stranica postaje javna.

4. **Objava \-** Landing stranica kreirana automatski; PDF dostupan za download; metapodaci su i dalje izmenljivi (verzionisanje).

5. **Post-publish \-** Sistem periodično povlači metrike iz Crossref (npr. citati) i prikazuje ih na landing strani.

Za svaki korak postoji mogućnost vraćanja unazad (revert), beleženja ko je izvršio akciju i kada.

# 6\. Crossref i DOI upravljanje 

\- Vezano za prethodna pitanja \- da li to stoji ovde ili na izdanju?

- **Autogenerisanje Crossref XML** iz metapodataka (preview XML pre slanja).  
- **Rezervisanje/registracija DOI**: dva moda:  
  - Staging/Reserve — testni/depozitni mod (za proveru)  
  - Production — registracija  
- **Status DOI**: none / reserved / registered / failed  
- **Povlačenje / rollback** — moguće označiti članak kao povučen; u Crossref-u treba ažurirati stanje (ako je registracija već urađena).

Na stranici članka postoji dugme “Generate Crossref XML” i “Send to Crossref” (sa confirm modalom).

### **Validacije pre slanja**

- Svi obavezni Crossref polja su popunjeni (naslov, autori, DOI/prefix, publication metadata, date, access info).  
- XML validan prema Crossref XSD (server-side check).

# 7\. Tehnički i operativni zahtevi

## 7.1. Bezbednost i GDPR

- HTTPS (TLS1.2+)  
- Password policy, MFA/2FA za admin i superadmin.  
- Role-based access control (opisano gore).  
  Audit log: sve izmene sadržaja i administrativne akcije (čuvati 1+ godina).  
- PII handling:  
  - Autori: ime, afilijacija, email — moraju biti zaštićeni.  
  - Cookie / consent banner za newsletter i forms.  
  - Mehanizam za pravo na zaborav (data erase request) — admin funkcija.  
  - Backup policy: dnevni backup baze i fajlova, retencija minimum 90 dana

## 7.2. Performanse

- Indexovanje za brzo pretraživanje (Elasticsearch ili Postgres full-text).  
- Cache (CDN) za javne stranice i static assets.

## 7.3. Internacionalizacija (i18n)

- Podrška za srpski (latinica) i engleski. Svi tekstovi u adminu trebaju biti lako menjivi kroz translation files.

## 7.4. Logging i monitoring

- Centralni logging (error \+ access logs).  
- Alerting za failed Crossref deposits, storage errors, high error rate.

# 8\. UI/UX wireframe 

## 8.1. Globalni layout

- Levi vertikalni meni (collapsible): Dashboard, Publikacije, Izdanja, Članci, Izdavači, Korisnici, Crossref, Logovi, Podešavanja.

- Gornji bar: pretraga (global), korisnički meni (profile, logout), breadcrumbs.

## 8.2. Strana za kreiranje i uređivanje članka

Layout \- 2 kolone:

- Leva, šira kolona (2/3): Naslov, Podnaslov, Apstrakt, Tekst članka (HTML editor), Ključne reči, Reference.  
- Desna kolona (1/3, sajdbar): Publikacija (dropdown link za publikaciju i izdanje), Autori (expandable), Fajlovi (PDF upload), Pristupi i Licence, Status, Zakazivanje objave (datum), Dugmići (Sačuvaj draft, Podnesi na pregled, Preview, Objavi).  
- Footer: Istorija promena (ko i kada).

## 8.3. Strana: Lista izdanja (grid)

- Na vrhu: filteri (godina, volume, izdanje) \+ pretraga  
- Grid 3 kolone: svaka kartica ima: naslovnu stranu \+ meta podatke (Volume, Izdanje, Godinu) \+ OPŠIRNIJE dugme

## 8.4. Strana: Crossref depozit

- Lista stavki na čekanju  
- Za svaki: checkbox, Generiši XML (preview), Validiraj XML (prikaz grešaka i upozorenja), Pošalji za Crossref (sa modalom za potvrdu), log rezultata slanja.

# 9\. DB šema (samo ključne tabele)

- users (id, name, email, role, password\_hash, active, created\_at)  
- publishers (id, name, logo\_path, description, contact\_email, website, created\_at)  
- publications (id, publisher\_id, type, title, slug, issn\_isbn, language, access, license, created\_at)  
- issues (id, publication\_id, volume, issue\_number, year, cover\_image, status, publish\_date)  
- articles (id, issue\_id/null, publication\_id, title, subtitle, slug, abstract, full\_text, doi, status, publish\_date, pdf\_path, created\_by, created\_at, updated\_at)  
- authors (id, given\_names, family\_name, affiliation, orcid, email)  
- article\_authors (article\_id, author\_id, author\_order, corresponding)  
- files (id, article\_id, file\_type, path, size, checksum)  
- audit\_logs (id, user\_id, action, target\_type, target\_id, payload, ip, created\_at)  
- crossref\_deposits (id, article\_id, xml\_payload, status, response, created\_at)