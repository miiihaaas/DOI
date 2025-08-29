import pytest
from datetime import datetime, date
from app.services.dashboard_service import DashboardService
from app.models.member import Member
from app.models.publication import Publication, PublicationType
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.models.sponsor import Sponsor
from app import db


class TestDashboardIntegration:
    """Integration testovi za DashboardService."""
    
    def test_dashboard_service_basic_integration(self, app):
        """Osnovni integration test za DashboardService."""
        with app.app_context():
            # Kreiraj test data u jednom app.app_context
            sponsor = Sponsor(
                name="Integration Test Sponsor",
                email="integration@test.com",
                crossref_member_id="INT123"
            )
            db.session.add(sponsor)
            db.session.commit()
            
            # Kreiraj test membre
            member1 = Member(
                sponsor_id=sponsor.id,
                name="Integration Member 1",
                institution="Test Institution 1",
                contact_email="member1@test.com",
                billing_address="Test Address 1",
                pib="123456780",
                matični_broj="07123456",
                šifra_delatnosti="58.11",
                telefon="0112345670",
                osoba_za_kontakt="Contact Person 1",
                iban="RS352600056010016113790",
                naziv_banke="Test Bank",
                swift_bic="TESTRS22",
                pdv_status="obveznik_pdv",
                država_obveznika="RS",
                is_active=True
            )
            
            member2 = Member(
                sponsor_id=sponsor.id,
                name="Integration Member 2",
                institution="Test Institution 2",
                contact_email="member2@test.com",
                billing_address="Test Address 2",
                pib="123456781",
                matični_broj="07123457",
                šifra_delatnosti="58.11",
                telefon="0112345671",
                osoba_za_kontakt="Contact Person 2",
                iban="RS352600056010016113791",
                naziv_banke="Test Bank",
                swift_bic="TESTRS22",
                pdv_status="obveznik_pdv",
                država_obveznika="RS",
                is_active=False
            )
            
            db.session.add_all([member1, member2])
            db.session.commit()
            
            # Kreiraj test publikacije
            pub1 = Publication(
                member_id=member1.id,
                title="Test Journal Publication",
                publication_type=PublicationType.journal,
                language_code="sr",
                journal_issn="1234-5678",
                is_active=True
            )
            
            pub2 = Publication(
                member_id=member1.id,
                title="Test Book Publication",
                publication_type=PublicationType.book,
                language_code="en",
                isbn="978-0-123456-78-9",
                is_active=False
            )
            
            pub3 = Publication(
                member_id=member2.id,
                title="Test Book Series Publication",
                publication_type=PublicationType.book_series,
                language_code="sr",
                series_issn="2345-6789",
                is_active=True
            )
            
            db.session.add_all([pub1, pub2, pub3])
            db.session.commit()
            
            # Test sponsor statistike
            sponsor_stats = DashboardService.get_sponsor_statistics(sponsor.id)
            
            assert sponsor_stats['members']['total'] == 2
            assert sponsor_stats['members']['active'] == 1
            assert sponsor_stats['members']['inactive'] == 1
            assert sponsor_stats['members']['percentage_active'] == 50.0
            
            assert sponsor_stats['publications']['total'] == 3
            assert sponsor_stats['publications']['active'] == 2
            assert sponsor_stats['publications']['inactive'] == 1
            
            assert sponsor_stats['publications']['by_type']['journal'] == 1
            assert sponsor_stats['publications']['by_type']['book'] == 1
            assert sponsor_stats['publications']['by_type']['book_series'] == 1
            
            # Draft statistics su placeholder - treba da budu 0
            assert sponsor_stats['drafts']['total'] == 0
            
            # Test member detail statistics
            member_stats = DashboardService.get_member_detail_statistics(member1.id)
            
            assert member_stats['member_info']['name'] == "Integration Member 1"
            assert member_stats['member_info']['is_active'] == True
            assert member_stats['publications']['total'] == 2
            assert member_stats['publications']['active'] == 1
            assert member_stats['publications']['inactive'] == 1
            
            # Test publication detail statistics
            pub_stats = DashboardService.get_publication_detail_statistics(pub1.id)
            
            assert pub_stats['publication_info']['title'] == "Test Journal Publication"
            assert pub_stats['publication_info']['type'] == "journal"
            assert pub_stats['publication_info']['is_active'] == True
            assert pub_stats['publication_info']['member_name'] == "Integration Member 1"
            
            # Draft statistics su placeholder
            assert pub_stats['drafts']['total'] == 0
            
            print("OK Dashboard Integration testovi prosli uspesno")
    
    def test_dashboard_service_empty_data(self, app):
        """Test sa praznim podacima."""
        with app.app_context():
            # Kreiraj prazan sponsor
            sponsor = Sponsor(
                name="Empty Sponsor",
                email="empty@sponsor.com",
                crossref_member_id="EMPTY123"
            )
            db.session.add(sponsor)
            db.session.commit()
            
            # Test sa praznim podacima
            stats = DashboardService.get_sponsor_statistics(sponsor.id)
            
            assert stats['members']['total'] == 0
            assert stats['publications']['total'] == 0
            assert stats['drafts']['total'] == 0
            
            print("OK Empty data test prosao uspesno")