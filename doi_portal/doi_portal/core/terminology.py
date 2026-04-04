"""
Centralized terminology system for contextual Serbian terms.

Maps publication_type to Serbian terms with grammatical cases
(nominative, genitive, paucal, accusative) for UI localization.
"""

from doi_portal.publications.models import PublicationType

TERMINOLOGY_MAP = {
    PublicationType.JOURNAL: {
        "issue": "Izdanje",
        "issue_plural": "Izdanja",
        "issue_genitive": "izdanja",
        "article": "Članak",
        "article_plural": "Članci",
        "article_genitive": "članaka",
        "article_genitive_paucal": "članka",
        "article_accusative": "članak",
        "new_article": "Novi članak",
        "create_article": "Kreiraj članak",
        "edit_article": "Izmeni članak",
        "new_issue": "Novo izdanje",
        "create_issue": "Kreiraj izdanje",
        "edit_issue": "Izmeni izdanje",
        "add_first_article": "Dodaj prvi članak",
        "add_first_issue": "Dodaj prvo izdanje",
        "delete_article": "Obriši članak",
        "delete_issue": "Obriši izdanje",
        "article_created": "Članak uspešno kreiran.",
        "article_updated": "Članak uspešno ažuriran.",
        "article_deleted": "Članak uspešno obrisan.",
        "article_submitted": "Članak poslat na pregled.",
        "article_approved": "Članak odobren.",
        "article_returned": "Članak vraćen na doradu.",
        "article_published": "Članak objavljen.",
        "article_withdrawn": "Članak povučen.",
        "issue_created": "Izdanje uspešno kreirano.",
        "issue_updated": "Izdanje uspešno ažurirano.",
        "issue_deleted": "Izdanje uspešno obrisano.",
        "issue_has_articles_warning": (
            "Izdanje ima {count} {article_genitive}. "
            "Izdanje je označeno kao obrisano ali podaci su sačuvani."
        ),
        # Portal-specific keys (Task 8)
        "article_withdrawn_title": "Povučen članak",
        "cite_article": "Citiraj članak",
        "share_article": "Podeli članak",
        "article_actions": "Akcije za članak",
        "article_available_externally": "Ovaj članak je dostupan i na sajtu izdavača",
    },
    PublicationType.CONFERENCE: {
        "issue": "Zbornik radova",
        "issue_plural": "Zbornici radova",
        "issue_genitive": "zbornika radova",
        "article": "Rad",
        "article_plural": "Radovi",
        "article_genitive": "radova",
        "article_genitive_paucal": "rada",
        "article_accusative": "rad",
        "new_article": "Novi rad",
        "create_article": "Kreiraj rad",
        "edit_article": "Izmeni rad",
        "new_issue": "Novi zbornik radova",
        "create_issue": "Kreiraj zbornik",
        "edit_issue": "Izmeni zbornik",
        "add_first_article": "Dodaj prvi rad",
        "add_first_issue": "Dodaj prvi zbornik",
        "delete_article": "Obriši rad",
        "delete_issue": "Obriši zbornik",
        "article_created": "Rad uspešno kreiran.",
        "article_updated": "Rad uspešno ažuriran.",
        "article_deleted": "Rad uspešno obrisan.",
        "article_submitted": "Rad poslat na pregled.",
        "article_approved": "Rad odobren.",
        "article_returned": "Rad vraćen na doradu.",
        "article_published": "Rad objavljen.",
        "article_withdrawn": "Rad povučen.",
        "issue_created": "Zbornik uspešno kreiran.",
        "issue_updated": "Zbornik uspešno ažuriran.",
        "issue_deleted": "Zbornik uspešno obrisan.",
        "issue_has_articles_warning": (
            "Zbornik ima {count} {article_genitive}. "
            "Zbornik je označen kao obrisan ali podaci su sačuvani."
        ),
        # Portal-specific keys (Task 8)
        "article_withdrawn_title": "Povučen rad",
        "cite_article": "Citiraj rad",
        "share_article": "Podeli rad",
        "article_actions": "Akcije za rad",
        "article_available_externally": "Ovaj rad je dostupan i na sajtu izdavača",
    },
    PublicationType.BOOK: {
        "issue": "Tom",
        "issue_plural": "Tomovi",
        "issue_genitive": "toma",
        "article": "Poglavlje",
        "article_plural": "Poglavlja",
        "article_genitive": "poglavlja",
        "article_genitive_paucal": "poglavlja",
        "article_accusative": "poglavlje",
        "new_article": "Novo poglavlje",
        "create_article": "Kreiraj poglavlje",
        "edit_article": "Izmeni poglavlje",
        "new_issue": "Novi tom",
        "create_issue": "Kreiraj tom",
        "edit_issue": "Izmeni tom",
        "add_first_article": "Dodaj prvo poglavlje",
        "add_first_issue": "Dodaj prvi tom",
        "delete_article": "Obriši poglavlje",
        "delete_issue": "Obriši tom",
        "article_created": "Poglavlje uspešno kreirano.",
        "article_updated": "Poglavlje uspešno ažurirano.",
        "article_deleted": "Poglavlje uspešno obrisano.",
        "article_submitted": "Poglavlje poslato na pregled.",
        "article_approved": "Poglavlje odobreno.",
        "article_returned": "Poglavlje vraćeno na doradu.",
        "article_published": "Poglavlje objavljeno.",
        "article_withdrawn": "Poglavlje povučeno.",
        "issue_created": "Tom uspešno kreiran.",
        "issue_updated": "Tom uspešno ažuriran.",
        "issue_deleted": "Tom uspešno obrisan.",
        "issue_has_articles_warning": (
            "Tom ima {count} {article_genitive}. "
            "Tom je označen kao obrisan ali podaci su sačuvani."
        ),
        # Portal-specific keys (Task 8)
        "article_withdrawn_title": "Povučeno poglavlje",
        "cite_article": "Citiraj poglavlje",
        "share_article": "Podeli poglavlje",
        "article_actions": "Akcije za poglavlje",
        "article_available_externally": "Ovo poglavlje je dostupno i na sajtu izdavača",
    },
    PublicationType.OTHER: {
        "issue": "Izdanje",
        "issue_plural": "Izdanja",
        "issue_genitive": "izdanja",
        "article": "Članak",
        "article_plural": "Članci",
        "article_genitive": "članaka",
        "article_genitive_paucal": "članka",
        "article_accusative": "članak",
        "new_article": "Novi članak",
        "create_article": "Kreiraj članak",
        "edit_article": "Izmeni članak",
        "new_issue": "Novo izdanje",
        "create_issue": "Kreiraj izdanje",
        "edit_issue": "Izmeni izdanje",
        "add_first_article": "Dodaj prvi članak",
        "add_first_issue": "Dodaj prvo izdanje",
        "delete_article": "Obriši članak",
        "delete_issue": "Obriši izdanje",
        "article_created": "Članak uspešno kreiran.",
        "article_updated": "Članak uspešno ažuriran.",
        "article_deleted": "Članak uspešno obrisan.",
        "article_submitted": "Članak poslat na pregled.",
        "article_approved": "Članak odobren.",
        "article_returned": "Članak vraćen na doradu.",
        "article_published": "Članak objavljen.",
        "article_withdrawn": "Članak povučen.",
        "issue_created": "Izdanje uspešno kreirano.",
        "issue_updated": "Izdanje uspešno ažurirano.",
        "issue_deleted": "Izdanje uspešno obrisano.",
        "issue_has_articles_warning": (
            "Izdanje ima {count} {article_genitive}. "
            "Izdanje je označeno kao obrisano ali podaci su sačuvani."
        ),
        # Portal-specific keys (Task 8)
        "article_withdrawn_title": "Povučen članak",
        "cite_article": "Citiraj članak",
        "share_article": "Podeli članak",
        "article_actions": "Akcije za članak",
        "article_available_externally": "Ovaj članak je dostupan i na sajtu izdavača",
    },
}


def get_term(term_key: str, publication_type: str) -> str:
    """
    Get a contextual term for the given key and publication type.

    Args:
        term_key: Key from TERMINOLOGY_MAP (e.g. "article", "new_issue")
        publication_type: PublicationType value (e.g. "JOURNAL", "CONFERENCE")

    Returns:
        Localized Serbian term. Falls back to JOURNAL if type is unknown or None.
    """
    type_map = TERMINOLOGY_MAP.get(publication_type, TERMINOLOGY_MAP[PublicationType.JOURNAL])
    return type_map.get(term_key, term_key)


def get_article_count_label(count: int, publication_type: str) -> str:
    """
    Get grammatically correct article count label using Serbian paucal logic.

    Args:
        count: Number of articles
        publication_type: PublicationType value

    Returns:
        String like "1 članak", "3 članka", "5 članaka"
    """
    type_map = TERMINOLOGY_MAP.get(publication_type, TERMINOLOGY_MAP[PublicationType.JOURNAL])

    if count == 1:
        # Singular: "članak" / "rad" / "poglavlje"
        label = type_map["article_accusative"]
    elif 2 <= count <= 4:
        # Paucal: "članka" / "rada" / "poglavlja"
        label = type_map["article_genitive_paucal"]
    else:
        # Genitive plural (0, 5+): "članaka" / "radova" / "poglavlja"
        label = type_map["article_genitive"]

    return f"{count} {label}"


def get_issue_delete_warning(count: int, publication_type: str) -> str:
    """
    Get compound warning message for deleting an issue that has articles.

    Args:
        count: Number of articles in the issue
        publication_type: PublicationType value

    Returns:
        Warning message string with article count and genitive form
    """
    type_map = TERMINOLOGY_MAP.get(publication_type, TERMINOLOGY_MAP[PublicationType.JOURNAL])

    # Determine correct genitive form based on count
    if count == 1:
        article_genitive = type_map["article_accusative"]
    elif 2 <= count <= 4:
        article_genitive = type_map["article_genitive_paucal"]
    else:
        article_genitive = type_map["article_genitive"]

    template = type_map["issue_has_articles_warning"]
    return template.format(count=count, article_genitive=article_genitive)
