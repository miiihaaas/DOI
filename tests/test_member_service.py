"""
Tests for member service - business logic testing.
"""

import pytest
from app.services.member_service import MemberService
from app.models.member import Member
from app.models.sponsor import Sponsor


class TestMemberService:
    """Test suite for MemberService business logic."""

    def test_get_members_for_sponsor_basic(self, app, db_session, sponsor):
        """Test basic member retrieval for sponsor."""
        with app.app_context():
            # Create test members
            member1 = Member.create_member(
                sponsor_id=sponsor.id,
                name='Member 1',
                institution='Institution 1',
                contact_email='member1@test.com',
                billing_address='Address 1',
                pib='123456789',
                matični_broj='12345678',
                šifra_delatnosti='7220',
                telefon='+381 11 123-4567',
                osoba_za_kontakt='Person 1',
                iban='RS35260005601001611379',
                naziv_banke='Bank 1',
                swift_bic='TESTRS22',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija'
            )
            
            member2 = Member.create_member(
                sponsor_id=sponsor.id,
                name='Member 2',
                institution='Institution 2',
                contact_email='member2@test.com',
                billing_address='Address 2',
                pib='987654321',
                matični_broj='87654321',
                šifra_delatnosti='7220',
                telefon='+381 11 987-6543',
                osoba_za_kontakt='Person 2',
                iban='RS35160005601001611379',
                naziv_banke='Bank 2',
                swift_bic='TESTRS23',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija'
            )
            db_session.commit()
            
            # Test retrieval
            result = MemberService.get_members_for_sponsor(sponsor.id)
            
            assert result.total == 2
            assert len(result.items) == 2
            member_names = [member.name for member in result.items]
            assert 'Member 1' in member_names
            assert 'Member 2' in member_names

    def test_get_members_for_sponsor_with_search(self, app, db_session, sponsor):
        """Test member retrieval with search filtering."""
        with app.app_context():
            # Create test members
            Member.create_member(
                sponsor_id=sponsor.id,
                name='Apple Organization',
                institution='Apple Institute',
                contact_email='apple@test.com',
                billing_address='Apple Address',
                pib='111111111',
                matični_broj='11111111',
                šifra_delatnosti='7220',
                telefon='+381 11 111-1111',
                osoba_za_kontakt='Apple Person',
                iban='RS35260005601001611111',
                naziv_banke='Apple Bank',
                swift_bic='APLRS222',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija'
            )
            
            Member.create_member(
                sponsor_id=sponsor.id,
                name='Banana Corporation',
                institution='Banana Institute',
                contact_email='banana@test.com',
                billing_address='Banana Address',
                pib='222222222',
                matični_broj='22222222',
                šifra_delatnosti='7220',
                telefon='+381 11 222-2222',
                osoba_za_kontakt='Banana Person',
                iban='RS35260005601001612222',
                naziv_banke='Banana Bank',
                swift_bic='BANRS222',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija'
            )
            db_session.commit()
            
            # Test search by name
            result = MemberService.get_members_for_sponsor(
                sponsor_id=sponsor.id,
                search='Apple'
            )
            
            assert result.total == 1
            assert result.items[0].name == 'Apple Organization'
            
            # Test search by institution
            result = MemberService.get_members_for_sponsor(
                sponsor_id=sponsor.id,
                search='Banana Institute'
            )
            
            assert result.total == 1
            assert result.items[0].name == 'Banana Corporation'

    def test_get_members_for_sponsor_with_status_filter(self, app, db_session, sponsor):
        """Test member retrieval with status filtering."""
        with app.app_context():
            # Create active member
            active_member = Member.create_member(
                sponsor_id=sponsor.id,
                name='Active Member',
                institution='Active Institution',
                contact_email='active@test.com',
                billing_address='Active Address',
                pib='111111111',
                matični_broj='11111111',
                šifra_delatnosti='7220',
                telefon='+381 11 111-1111',
                osoba_za_kontakt='Active Person',
                iban='RS35260005601001611111',
                naziv_banke='Active Bank',
                swift_bic='ACTRS222',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija',
                is_active=True
            )
            
            # Create inactive member
            inactive_member = Member.create_member(
                sponsor_id=sponsor.id,
                name='Inactive Member',
                institution='Inactive Institution',
                contact_email='inactive@test.com',
                billing_address='Inactive Address',
                pib='222222222',
                matični_broj='22222222',
                šifra_delatnosti='7220',
                telefon='+381 11 222-2222',
                osoba_za_kontakt='Inactive Person',
                iban='RS35260005601001612222',
                naziv_banke='Inactive Bank',
                swift_bic='INARS222',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija',
                is_active=False
            )
            db_session.commit()
            
            # Test active filter
            result = MemberService.get_members_for_sponsor(
                sponsor_id=sponsor.id,
                status='active'
            )
            assert result.total == 1
            assert result.items[0].name == 'Active Member'
            
            # Test inactive filter
            result = MemberService.get_members_for_sponsor(
                sponsor_id=sponsor.id,
                status='inactive'
            )
            assert result.total == 1
            assert result.items[0].name == 'Inactive Member'
            
            # Test all filter
            result = MemberService.get_members_for_sponsor(
                sponsor_id=sponsor.id,
                status='all'
            )
            assert result.total == 2

    def test_get_member_by_id(self, app, db_session, sponsor):
        """Test retrieving member by ID with sponsor validation."""
        with app.app_context():
            # Create test member
            member = Member.create_member(
                sponsor_id=sponsor.id,
                name='Test Member',
                institution='Test Institution',
                contact_email='test@member.com',
                billing_address='Test Address',
                pib='123456789',
                matični_broj='12345678',
                šifra_delatnosti='7220',
                telefon='+381 11 123-4567',
                osoba_za_kontakt='Test Person',
                iban='RS35260005601001611379',
                naziv_banke='Test Bank',
                swift_bic='TESTRS22',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija'
            )
            db_session.commit()
            
            # Test successful retrieval
            retrieved_member = MemberService.get_member_by_id(member.id, sponsor.id)
            assert retrieved_member is not None
            assert retrieved_member.id == member.id
            assert retrieved_member.name == 'Test Member'
            
            # Test non-existent member
            non_existent = MemberService.get_member_by_id(99999, sponsor.id)
            assert non_existent is None

    def test_create_member_success(self, app, db_session, sponsor):
        """Test successful member creation."""
        with app.app_context():
            form_data = {
                'name': 'New Test Member',
                'institution': 'New Test Institution',
                'contact_email': 'newtest@member.com',
                'website_url': 'https://www.newtest.com',
                'billing_address': 'New Test Address 123',
                'pib': '999888777',
                'matični_broj': '99988777',
                'jmbg_lk': '',
                'šifra_delatnosti': '7220',
                'telefon': '+381 11 999-8877',
                'osoba_za_kontakt': 'New Test Person',
                'iban': 'RS35260005601001619999',
                'naziv_banke': 'New Test Bank',
                'swift_bic': 'NEWRS222',
                'pdv_status': 'obveznik_pdv',
                'država_obveznika': 'Srbija',
                'is_active': True
            }
            
            member = MemberService.create_member(sponsor.id, form_data)
            
            assert member is not None
            assert member.name == 'New Test Member'
            assert member.contact_email == 'newtest@member.com'
            assert member.sponsor_id == sponsor.id
            assert member.is_active is True
            
            # Verify in database
            db_member = Member.query.filter_by(id=member.id).first()
            assert db_member is not None
            assert db_member.name == 'New Test Member'

    def test_create_member_duplicate_email(self, app, db_session, sponsor):
        """Test member creation with duplicate email."""
        with app.app_context():
            # Create first member
            Member.create_member(
                sponsor_id=sponsor.id,
                name='First Member',
                institution='First Institution',
                contact_email='duplicate@test.com',
                billing_address='First Address',
                pib='111111111',
                matični_broj='11111111',
                šifra_delatnosti='7220',
                telefon='+381 11 111-1111',
                osoba_za_kontakt='First Person',
                iban='RS35260005601001611111',
                naziv_banke='First Bank',
                swift_bic='FIRRS222',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija'
            )
            db_session.commit()
            
            # Try to create second member with same email
            form_data = {
                'name': 'Second Member',
                'institution': 'Second Institution',
                'contact_email': 'duplicate@test.com',  # Same email
                'billing_address': 'Second Address',
                'pib': '222222222',
                'matični_broj': '22222222',
                'šifra_delatnosti': '7220',
                'telefon': '+381 11 222-2222',
                'osoba_za_kontakt': 'Second Person',
                'iban': 'RS35260005601001612222',
                'naziv_banke': 'Second Bank',
                'swift_bic': 'SECRS222',
                'pdv_status': 'obveznik_pdv',
                'država_obveznika': 'Srbija'
            }
            
            with pytest.raises(ValueError) as exc_info:
                MemberService.create_member(sponsor.id, form_data)
            
            assert 'već postoji' in str(exc_info.value)

    def test_update_member_success(self, app, db_session, sponsor):
        """Test successful member update."""
        with app.app_context():
            # Create member to update
            member = Member.create_member(
                sponsor_id=sponsor.id,
                name='Original Member',
                institution='Original Institution',
                contact_email='original@test.com',
                billing_address='Original Address',
                pib='123456789',
                matični_broj='12345678',
                šifra_delatnosti='7220',
                telefon='+381 11 123-4567',
                osoba_za_kontakt='Original Person',
                iban='RS35260005601001611379',
                naziv_banke='Original Bank',
                swift_bic='ORIGRS22',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija'
            )
            db_session.commit()
            
            # Update data
            form_data = {
                'name': 'Updated Member',
                'institution': 'Updated Institution',
                'contact_email': 'updated@test.com',
                'website_url': 'https://www.updated.com',
                'billing_address': member.billing_address,
                'pib': member.pib,
                'matični_broj': member.matični_broj,
                'jmbg_lk': '',
                'šifra_delatnosti': member.šifra_delatnosti,
                'telefon': member.telefon,
                'osoba_za_kontakt': member.osoba_za_kontakt,
                'iban': member.iban,
                'naziv_banke': member.naziv_banke,
                'swift_bic': member.swift_bic,
                'pdv_status': member.pdv_status,
                'država_obveznika': member.država_obveznika,
                'is_active': True
            }
            
            updated_member = MemberService.update_member(
                member.id, 
                sponsor.id, 
                form_data
            )
            
            assert updated_member.name == 'Updated Member'
            assert updated_member.institution == 'Updated Institution'
            assert updated_member.contact_email == 'updated@test.com'
            assert updated_member.website_url == 'https://www.updated.com'

    def test_update_member_not_found(self, app, db_session, sponsor):
        """Test updating non-existent member."""
        with app.app_context():
            form_data = {'name': 'Test'}
            
            with pytest.raises(ValueError) as exc_info:
                MemberService.update_member(99999, sponsor.id, form_data)
            
            assert 'nije pronađen' in str(exc_info.value)

    def test_toggle_member_status(self, app, db_session, sponsor):
        """Test toggling member active status."""
        with app.app_context():
            # Create active member
            member = Member.create_member(
                sponsor_id=sponsor.id,
                name='Test Member',
                institution='Test Institution',
                contact_email='test@member.com',
                billing_address='Test Address',
                pib='123456789',
                matični_broj='12345678',
                šifra_delatnosti='7220',
                telefon='+381 11 123-4567',
                osoba_za_kontakt='Test Person',
                iban='RS35260005601001611379',
                naziv_banke='Test Bank',
                swift_bic='TESTRS22',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija',
                is_active=True
            )
            db_session.commit()
            
            assert member.is_active is True
            
            # Toggle to inactive
            updated_member = MemberService.toggle_member_status(member.id, sponsor.id)
            assert updated_member.is_active is False
            
            # Toggle back to active
            updated_member = MemberService.toggle_member_status(member.id, sponsor.id)
            assert updated_member.is_active is True

    def test_search_members(self, app, db_session, sponsor):
        """Test member search functionality."""
        with app.app_context():
            # Create searchable members
            Member.create_member(
                sponsor_id=sponsor.id,
                name='Apple Corporation',
                institution='Apple Institute',
                contact_email='apple@search.com',
                billing_address='Apple Address',
                pib='111111111',
                matični_broj='11111111',
                šifra_delatnosti='7220',
                telefon='+381 11 111-1111',
                osoba_za_kontakt='Apple Person',
                iban='RS35260005601001611111',
                naziv_banke='Apple Bank',
                swift_bic='APLRS222',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija'
            )
            
            Member.create_member(
                sponsor_id=sponsor.id,
                name='Banana Organization',
                institution='Banana Institute',
                contact_email='banana@search.com',
                billing_address='Banana Address',
                pib='222222222',
                matični_broj='22222222',
                šifra_delatnosti='7220',
                telefon='+381 11 222-2222',
                osoba_za_kontakt='Banana Person',
                iban='RS35260005601001612222',
                naziv_banke='Banana Bank',
                swift_bic='BANRS222',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija'
            )
            db_session.commit()
            
            # Search for Apple
            result = MemberService.search_members(sponsor.id, 'Apple')
            assert result.total == 1
            assert result.items[0].name == 'Apple Corporation'
            
            # Search for Institute (should match both)
            result = MemberService.search_members(sponsor.id, 'Institute')
            assert result.total == 2
            
            # Search with too short term
            result = MemberService.search_members(sponsor.id, 'A')
            assert result.total == 0

    def test_get_member_statistics(self, app, db_session, sponsor):
        """Test member statistics generation."""
        with app.app_context():
            # Create test members with different statuses
            Member.create_member(
                sponsor_id=sponsor.id,
                name='Active Member 1',
                institution='Institution 1',
                contact_email='active1@test.com',
                billing_address='Address 1',
                pib='111111111',
                matični_broj='11111111',
                šifra_delatnosti='7220',
                telefon='+381 11 111-1111',
                osoba_za_kontakt='Person 1',
                iban='RS35260005601001611111',
                naziv_banke='Bank 1',
                swift_bic='ACT1RS22',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija',
                is_active=True
            )
            
            Member.create_member(
                sponsor_id=sponsor.id,
                name='Active Member 2',
                institution='Institution 2',
                contact_email='active2@test.com',
                billing_address='Address 2',
                pib='222222222',
                matični_broj='22222222',
                šifra_delatnosti='7220',
                telefon='+381 11 222-2222',
                osoba_za_kontakt='Person 2',
                iban='RS35260005601001612222',
                naziv_banke='Bank 2',
                swift_bic='ACT2RS22',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija',
                is_active=True
            )
            
            Member.create_member(
                sponsor_id=sponsor.id,
                name='Inactive Member',
                institution='Institution 3',
                contact_email='inactive@test.com',
                billing_address='Address 3',
                pib='333333333',
                matični_broj='33333333',
                šifra_delatnosti='7220',
                telefon='+381 11 333-3333',
                osoba_za_kontakt='Person 3',
                iban='RS35260005601001613333',
                naziv_banke='Bank 3',
                swift_bic='INARS222',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija',
                is_active=False
            )
            db_session.commit()
            
            stats = MemberService.get_member_statistics(sponsor.id)
            
            assert stats['total'] == 3
            assert stats['active'] == 2
            assert stats['inactive'] == 1
            assert stats['with_publications'] == 0  # No publications created

    def test_get_active_members_for_sponsor(self, app, db_session, sponsor):
        """Test retrieving only active members."""
        with app.app_context():
            # Create active and inactive members
            active_member = Member.create_member(
                sponsor_id=sponsor.id,
                name='Active Member',
                institution='Active Institution',
                contact_email='active@test.com',
                billing_address='Active Address',
                pib='111111111',
                matični_broj='11111111',
                šifra_delatnosti='7220',
                telefon='+381 11 111-1111',
                osoba_za_kontakt='Active Person',
                iban='RS35260005601001611111',
                naziv_banke='Active Bank',
                swift_bic='ACTRS222',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija',
                is_active=True
            )
            
            inactive_member = Member.create_member(
                sponsor_id=sponsor.id,
                name='Inactive Member',
                institution='Inactive Institution',
                contact_email='inactive@test.com',
                billing_address='Inactive Address',
                pib='222222222',
                matični_broj='22222222',
                šifra_delatnosti='7220',
                telefon='+381 11 222-2222',
                osoba_za_kontakt='Inactive Person',
                iban='RS35260005601001612222',
                naziv_banke='Inactive Bank',
                swift_bic='INARS222',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija',
                is_active=False
            )
            db_session.commit()
            
            active_members = MemberService.get_active_members_for_sponsor(sponsor.id)
            
            assert len(active_members) == 1
            assert active_members[0].name == 'Active Member'
            assert active_members[0].is_active is True

    def test_validate_member_data(self, app):
        """Test member data validation."""
        with app.app_context():
            # Test with valid data
            valid_data = {
                'name': 'Test Member',
                'institution': 'Test Institution',
                'contact_email': 'test@member.com',
                'billing_address': 'Test Address',
                'pib': '123456789',
                'matični_broj': '12345678',
                'šifra_delatnosti': '7220',
                'telefon': '+381 11 123-4567',
                'osoba_za_kontakt': 'Test Person',
                'iban': 'RS35260005601001611379',
                'naziv_banke': 'Test Bank',
                'swift_bic': 'TESTRS22',
                'pdv_status': 'obveznik_pdv',
                'država_obveznika': 'Srbija'
            }
            
            errors = MemberService.validate_member_data(valid_data)
            assert len(errors) == 0
            
            # Test with invalid data
            invalid_data = {
                'name': '',  # Missing required field
                'contact_email': 'invalid-email',  # Invalid email
                'pib': 'abc123',  # Invalid PIB format
                'matični_broj': '',  # Missing required field
            }
            
            errors = MemberService.validate_member_data(invalid_data)
            assert len(errors) > 0
            assert 'name' in errors
            assert 'contact_email' in errors
            assert 'pib' in errors
            assert 'matični_broj' in errors