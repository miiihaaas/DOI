"""
Script to create test data for manual validation testing.
Run with: docker-compose -f docker-compose.local.yml exec django python create_validation_test_data.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
sys.path.insert(0, "/app")
django.setup()

from datetime import date
from django.db import transaction
from doi_portal.core.models import SiteSettings
from doi_portal.publishers.models import Publisher
from doi_portal.publications.models import Publication, PublicationType
from doi_portal.issues.models import Issue
from doi_portal.articles.models import Article, Author, ArticleStatus, AuthorSequence, ContributorRole

def create_test_data():
    """Create test data for manual validation testing."""

    with transaction.atomic():
        # Ensure SiteSettings exists with depositor data
        site_settings, _ = SiteSettings.objects.get_or_create(pk=1)
        site_settings.depositor_name = "DOI Portal Test"
        site_settings.depositor_email = "depositor@test.com"
        site_settings.save()
        print("✅ SiteSettings configured with depositor data")

        # Create or get publisher
        publisher, created = Publisher.objects.get_or_create(
            name="Test Izdavač za Validaciju",
            defaults={
                "doi_prefix": "10.99999",
                "slug": "test-izdavac-validacija",
            }
        )
        print(f"{'✅ Created' if created else '📌 Using existing'} Publisher: {publisher.name} (ID: {publisher.pk})")

        # =================================================================
        # TEST 2: Journal without ISSN
        # =================================================================
        journal_no_issn, created = Publication.objects.get_or_create(
            title="Test Časopis BEZ ISSN",
            publisher=publisher,
            defaults={
                "publication_type": PublicationType.JOURNAL,
                "issn_print": "",
                "issn_online": "",
                "slug": "test-casopis-bez-issn",
            }
        )
        if not created:
            journal_no_issn.issn_print = ""
            journal_no_issn.issn_online = ""
            journal_no_issn.save()

        issue_no_issn, created = Issue.objects.get_or_create(
            publication=journal_no_issn,
            volume="1",
            issue_number="1",
            year=2026,
            defaults={
                "publication_date": date(2026, 1, 15),
            }
        )

        # Create valid article for this issue
        article_test2, _ = Article.objects.get_or_create(
            issue=issue_no_issn,
            title="Članak u časopisu bez ISSN-a",
            defaults={
                "doi_suffix": "test2.2026.001",
                "status": ArticleStatus.PUBLISHED,
            }
        )
        # Create valid author
        Author.objects.get_or_create(
            article=article_test2,
            surname="Petrović",
            defaults={
                "given_name": "Marko",
                "sequence": AuthorSequence.FIRST,
                "contributor_role": ContributorRole.AUTHOR,
                "order": 1,
            }
        )
        print(f"✅ TEST 2: Issue ID {issue_no_issn.pk} - Journal without ISSN")

        # =================================================================
        # TEST 3: Article without authors
        # =================================================================
        journal_valid, created = Publication.objects.get_or_create(
            title="Test Časopis SA ISSN",
            publisher=publisher,
            defaults={
                "publication_type": PublicationType.JOURNAL,
                "issn_print": "1234-5678",
                "issn_online": "",
                "slug": "test-casopis-sa-issn",
            }
        )
        if not created and not journal_valid.issn_print:
            journal_valid.issn_print = "1234-5678"
            journal_valid.save()

        issue_valid, created = Issue.objects.get_or_create(
            publication=journal_valid,
            volume="1",
            issue_number="1",
            year=2026,
            defaults={
                "publication_date": date(2026, 2, 15),
            }
        )

        # Create article WITHOUT authors
        article_no_authors, created = Article.objects.get_or_create(
            issue=issue_valid,
            title="Članak BEZ autora",
            defaults={
                "doi_suffix": "test3.2026.001",
                "status": ArticleStatus.PUBLISHED,
            }
        )
        if not created:
            # Remove any existing authors
            article_no_authors.authors.all().delete()
        print(f"✅ TEST 3: Article ID {article_no_authors.pk} - Article without authors (Issue ID: {issue_valid.pk})")

        # =================================================================
        # TEST 4: Author without surname
        # =================================================================
        article_no_surname, created = Article.objects.get_or_create(
            issue=issue_valid,
            title="Članak sa autorom BEZ prezimena",
            defaults={
                "doi_suffix": "test4.2026.001",
                "status": ArticleStatus.PUBLISHED,
            }
        )
        if created:
            Author.objects.create(
                article=article_no_surname,
                given_name="Jovan",
                surname="",  # No surname!
                sequence=AuthorSequence.FIRST,
                contributor_role=ContributorRole.AUTHOR,
                order=1,
            )
        else:
            # Ensure author has no surname
            author = article_no_surname.authors.first()
            if author:
                author.surname = ""
                author.save()
            else:
                Author.objects.create(
                    article=article_no_surname,
                    given_name="Jovan",
                    surname="",
                    sequence=AuthorSequence.FIRST,
                    contributor_role=ContributorRole.AUTHOR,
                    order=1,
                )
        print(f"✅ TEST 4: Article ID {article_no_surname.pk} - Author without surname (Issue ID: {issue_valid.pk})")

        # =================================================================
        # TEST 5: Author without given_name (warning only)
        # =================================================================
        article_no_given_name, created = Article.objects.get_or_create(
            issue=issue_valid,
            title="Članak sa autorom BEZ imena",
            defaults={
                "doi_suffix": "test5.2026.001",
                "status": ArticleStatus.PUBLISHED,
            }
        )
        if created:
            Author.objects.create(
                article=article_no_given_name,
                given_name="",  # No given name - should be warning
                surname="Nikolić",
                sequence=AuthorSequence.FIRST,
                contributor_role=ContributorRole.AUTHOR,
                order=1,
            )
        else:
            author = article_no_given_name.authors.first()
            if author:
                author.given_name = ""
                author.surname = "Nikolić"
                author.save()
            else:
                Author.objects.create(
                    article=article_no_given_name,
                    given_name="",
                    surname="Nikolić",
                    sequence=AuthorSequence.FIRST,
                    contributor_role=ContributorRole.AUTHOR,
                    order=1,
                )
        print(f"✅ TEST 5: Article ID {article_no_given_name.pk} - Author without given_name (Issue ID: {issue_valid.pk})")

        # =================================================================
        # TEST 6: Everything valid
        # =================================================================
        journal_complete, created = Publication.objects.get_or_create(
            title="Kompletan Validan Časopis",
            publisher=publisher,
            defaults={
                "publication_type": PublicationType.JOURNAL,
                "issn_print": "9876-5432",
                "issn_online": "9876-5433",
                "slug": "kompletan-validan-casopis",
            }
        )
        if not created:
            journal_complete.issn_print = "9876-5432"
            journal_complete.issn_online = "9876-5433"
            journal_complete.save()

        issue_complete, created = Issue.objects.get_or_create(
            publication=journal_complete,
            volume="1",
            issue_number="1",
            year=2026,
            defaults={
                "publication_date": date(2026, 3, 15),
            }
        )

        article_complete, created = Article.objects.get_or_create(
            issue=issue_complete,
            title="Potpuno validan članak",
            defaults={
                "doi_suffix": "test6.2026.001",
                "status": ArticleStatus.PUBLISHED,
            }
        )

        # Ensure valid author exists
        Author.objects.get_or_create(
            article=article_complete,
            surname="Jovanović",
            defaults={
                "given_name": "Ana",
                "sequence": AuthorSequence.FIRST,
                "contributor_role": ContributorRole.AUTHOR,
                "order": 1,
            }
        )
        print(f"✅ TEST 6: Issue ID {issue_complete.pk} - Everything valid")

        # =================================================================
        # SUMMARY
        # =================================================================
        print("\n" + "="*60)
        print("SUMMARY - Test URLs:")
        print("="*60)
        print(f"\nTEST 2 (Journal bez ISSN):")
        print(f"  http://localhost:8000/dashboard/crossref/issues/{issue_no_issn.pk}/validate/")
        print(f"\nTEST 3 (Članak bez autora):")
        print(f"  http://localhost:8000/dashboard/crossref/issues/{issue_valid.pk}/validate/")
        print(f"  (Article ID: {article_no_authors.pk})")
        print(f"\nTEST 4 (Autor bez prezimena):")
        print(f"  http://localhost:8000/dashboard/crossref/issues/{issue_valid.pk}/validate/")
        print(f"  (Article ID: {article_no_surname.pk})")
        print(f"\nTEST 5 (Autor bez imena - warning):")
        print(f"  http://localhost:8000/dashboard/crossref/issues/{issue_valid.pk}/validate/")
        print(f"  (Article ID: {article_no_given_name.pk})")
        print(f"\nTEST 6 (Sve ispravno):")
        print(f"  http://localhost:8000/dashboard/crossref/issues/{issue_complete.pk}/validate/")
        print("="*60)

if __name__ == "__main__":
    create_test_data()
