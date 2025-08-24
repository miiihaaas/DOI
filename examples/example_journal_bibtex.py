article_dict = {
    "type": "article",
    "id": "james:2025transferlearning",

    "author": "James, Mark A.",  # doi_batch>body>journal>journal_article>contributors>person_name>surname; doi_batch>body>journal>journal_article>contributors>person_name>given_name
    "orcid": "0000-0002-1371-8949",  # doi_batch>body>journal>journal_article>contributors>person_name>ORCID
    "affiliation": "Arizona State University",  # doi_batch>body>journal>journal_article>contributors>person_name>affiliations>institution>institution_name
    "affid": "https://ror.org/03efmqc40", # doi_batch>body>journal>journal_article>contributors>person_name>affiliations>institution>institution_id
    "affplace": "Tempe, USA", # doi_batch>body>journal>journal_article>contributors>person_name>affiliations>institution>institution_place
    "department": "nodepartment", # doi_batch>body>journal>journal_article>contributors>person_name>affiliations>institution>institution_department

    "title": "Factors Influencing Students' Motivation to Transfer Learning from EAP Courses to Disciplinary Courses in a US University Context", # doi_batch>body>journal>journal_article>titles>title
    "journal": "ESP Today", # doi_batch>body>journal>journal_metadata>full_title
    "license": "https://creativecommons.org/licenses/by/4.0/", # doi_batch>body>journal>journal_article>ai:program>ai:license_ref
    "issn": "2334-9050", # doi_batch>body>journal>journal_metadata>issn
    "eissn": "2334-9050", #?! da li je eissn ili issn? možda je issn print, a eissn online?

    "year": 2025,  # doi_batch>body>journal>journal_issue>publication_date>year
    "volume": 13,  # doi_batch>body>journal>journal_issue>journal_volume>volume
    "number": 2,  # doi_batch>body>journal>journal_issue>issue #?! da li je number zapravo issue number?

    "howpublished": "online", #?! da li ako je jedan članak online to pordrazumeva da i ostali članci moraju da su online? i obrnuto (print)? ako je tako onda taj podatak treba vezati za časopis da se ne bi za svaki članak unosio isti podatak
    "language": "english", # doi_batch>body>journal>journal_metadata:language>; doi_batch>body>journal>journal_article:language
    "pages": "243--267", # doi_batch>body>journal>journal_article>pages>first_page; doi_batch>body>journal>journal_article>pages>last_page
    "note": "1", # redni broj članka u issue-u #?! da li je neophodan podatak za crossref-u?

    "doi": "10.18485/esptoday.2025.13.2.1", # doi_batch>body>journal>journal_article>doi_data>doi
    "doiurl": "http://doi.fil.bg.ac.rs/volume.php?pt=journals&issue=esptoday-2025-13-2&i=1", # doi_batch>body>journal>journal_article>doi_data>resource
    "url": "http://doi.fil.bg.ac.rs/pdf/journals/esptoday/2025-2/esptoday-2025-13-2-1.pdf" #?! da li treba ovo da se šalje crossref-u?
}
