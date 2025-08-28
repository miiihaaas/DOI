"""
Unit tests for Member model.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from app import create_app, db
from app.models import Sponsor, Member


@pytest.fixture
def app():
    """Create and configure a test app."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def sponsor(app):
    """Create a test sponsor."""
    sponsor = Sponsor(
        name='Test Sponsor',
        email='sponsor@test.com',
        crossref_member_id='12345',
        is_active=True
    )
    sponsor.save()
    return sponsor


class TestMemberModel:
    """Test cases for Member model."""

    def test_member_creation_with_valid_data(self, app, sponsor):
        """Test creating a member with valid data."""
        member = Member.create_member(
            sponsor_id=sponsor.id,
            name='Test University',
            institution='Faculty of Science',
            contact_email='contact@testuni.edu',
            billing_address='123 University St, Belgrade, Serbia',
            pib='123456789',
            matični_broj='987654321',
            šifra_delatnosti='8542',
            telefon='+381111234567',
            osoba_za_kontakt='Dr. Jane Doe',
            iban='RS35260005601001611379',
            naziv_banke='Komercijalna Banka',
            swift_bic='KOBBRSBG',
            pdv_status='Obveznik PDV-a',
            država_obveznika='Republika Srbija',
            website_url='https://testuni.edu',
            jmbg_lk='1234567890123'
        )
        
        assert member.id is not None
        assert member.sponsor_id == sponsor.id
        assert member.name == 'Test University'
        assert member.institution == 'Faculty of Science'
        assert member.contact_email == 'contact@testuni.edu'
        assert member.website_url == 'https://testuni.edu'
        assert member.billing_address == '123 University St, Belgrade, Serbia'
        assert member.pib == '123456789'
        assert member.matični_broj == '987654321'
        assert member.jmbg_lk == '1234567890123'
        assert member.šifra_delatnosti == '8542'
        assert member.telefon == '+381111234567'
        assert member.osoba_za_kontakt == 'Dr. Jane Doe'
        assert member.iban == 'RS35260005601001611379'
        assert member.naziv_banke == 'Komercijalna Banka'
        assert member.swift_bic == 'KOBBRSBG'
        assert member.pdv_status == 'Obveznik PDV-a'
        assert member.država_obveznika == 'Republika Srbija'
        assert member.is_active == True
        assert member.created_at is not None
        assert member.updated_at is not None

    def test_member_creation_with_minimal_data(self, app, sponsor):
        """Test creating a member with minimal required data."""
        member = Member.create_member(
            sponsor_id=sponsor.id,
            name='Minimal University',
            institution='Basic Faculty',
            contact_email='minimal@test.edu',
            billing_address='Basic Address',
            pib='111222333',
            matični_broj='333222111',
            šifra_delatnosti='1234',
            telefon='+381987654321',
            osoba_za_kontakt='John Smith',
            iban='RS35111111111111111111',
            naziv_banke='Test Bank',
            swift_bic='TESTBSBG',
            pdv_status='Test PDV Status',
            država_obveznika='Test Country'
        )
        
        assert member.id is not None
        assert member.website_url is None
        assert member.jmbg_lk is None
        assert member.is_active == True

    def test_member_creation_with_invalid_email(self, app, sponsor):
        """Test that creating a member with invalid email fails."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Member.create_member(
                sponsor_id=sponsor.id,
                name='Test University',
                institution='Faculty of Science',
                contact_email='invalid-email',
                billing_address='123 University St',
                pib='123456789',
                matični_broj='987654321',
                šifra_delatnosti='8542',
                telefon='+381111234567',
                osoba_za_kontakt='Dr. Jane Doe',
                iban='RS35260005601001611379',
                naziv_banke='Komercijalna Banka',
                swift_bic='KOBBRSBG',
                pdv_status='Obveznik PDV-a',
                država_obveznika='Republika Srbija'
            )

    def test_member_creation_with_missing_required_fields(self, app, sponsor):
        """Test that creating a member with missing required fields fails."""
        # Missing name
        with pytest.raises(ValueError, match="Member name is required"):
            Member.create_member(
                sponsor_id=sponsor.id,
                name='',
                institution='Faculty of Science',
                contact_email='contact@testuni.edu',
                billing_address='123 University St',
                pib='123456789',
                matični_broj='987654321',
                šifra_delatnosti='8542',
                telefon='+381111234567',
                osoba_za_kontakt='Dr. Jane Doe',
                iban='RS35260005601001611379',
                naziv_banke='Komercijalna Banka',
                swift_bic='KOBBRSBG',
                pdv_status='Obveznik PDV-a',
                država_obveznika='Republika Srbija'
            )

        # Missing institution
        with pytest.raises(ValueError, match="Institution name is required"):
            Member.create_member(
                sponsor_id=sponsor.id,
                name='Test University',
                institution='',
                contact_email='contact@testuni.edu',
                billing_address='123 University St',
                pib='123456789',
                matični_broj='987654321',
                šifra_delatnosti='8542',
                telefon='+381111234567',
                osoba_za_kontakt='Dr. Jane Doe',
                iban='RS35260005601001611379',
                naziv_banke='Komercijalna Banka',
                swift_bic='KOBBRSBG',
                pdv_status='Obveznik PDV-a',
                država_obveznika='Republika Srbija'
            )

    def test_member_relationship_with_sponsor(self, app, sponsor):
        """Test the relationship between Member and Sponsor."""
        member = Member.create_member(
            sponsor_id=sponsor.id,
            name='Test University',
            institution='Faculty of Science',
            contact_email='contact@testuni.edu',
            billing_address='123 University St',
            pib='123456789',
            matični_broj='987654321',
            šifra_delatnosti='8542',
            telefon='+381111234567',
            osoba_za_kontakt='Dr. Jane Doe',
            iban='RS35260005601001611379',
            naziv_banke='Komercijalna Banka',
            swift_bic='KOBBRSBG',
            pdv_status='Obveznik PDV-a',
            država_obveznika='Republika Srbija'
        )
        
        # Test forward relationship
        assert member.sponsor.id == sponsor.id
        assert member.sponsor.name == sponsor.name
        
        # Test backward relationship
        sponsor_members = sponsor.members.all()
        assert len(sponsor_members) == 1
        assert sponsor_members[0].id == member.id

    def test_member_repr_and_str(self, app, sponsor):
        """Test __repr__ and __str__ methods."""
        member = Member.create_member(
            sponsor_id=sponsor.id,
            name='Test University',
            institution='Faculty of Science',
            contact_email='contact@testuni.edu',
            billing_address='123 University St',
            pib='123456789',
            matični_broj='987654321',
            šifra_delatnosti='8542',
            telefon='+381111234567',
            osoba_za_kontakt='Dr. Jane Doe',
            iban='RS35260005601001611379',
            naziv_banke='Komercijalna Banka',
            swift_bic='KOBBRSBG',
            pdv_status='Obveznik PDV-a',
            država_obveznika='Republika Srbija'
        )
        
        repr_str = repr(member)
        str_str = str(member)
        
        assert 'Member' in repr_str
        assert 'Test University' in repr_str
        assert 'Faculty of Science' in repr_str
        assert 'contact@testuni.edu' in repr_str
        
        assert 'Member: Test University (Faculty of Science)' == str_str

    def test_member_to_dict(self, app, sponsor):
        """Test to_dict method."""
        member = Member.create_member(
            sponsor_id=sponsor.id,
            name='Test University',
            institution='Faculty of Science',
            contact_email='contact@testuni.edu',
            billing_address='123 University St',
            pib='123456789',
            matični_broj='987654321',
            šifra_delatnosti='8542',
            telefon='+381111234567',
            osoba_za_kontakt='Dr. Jane Doe',
            iban='RS35260005601001611379',
            naziv_banke='Komercijalna Banka',
            swift_bic='KOBBRSBG',
            pdv_status='Obveznik PDV-a',
            država_obveznika='Republika Srbija'
        )
        
        member_dict = member.to_dict()
        
        assert member_dict['id'] == member.id
        assert member_dict['sponsor_id'] == sponsor.id
        assert member_dict['name'] == 'Test University'
        assert member_dict['institution'] == 'Faculty of Science'
        assert member_dict['contact_email'] == 'contact@testuni.edu'
        assert member_dict['is_active'] == True
        assert 'created_at' in member_dict
        assert 'updated_at' in member_dict

    def test_get_by_sponsor(self, app, sponsor):
        """Test getting members by sponsor."""
        member1 = Member.create_member(
            sponsor_id=sponsor.id,
            name='University 1',
            institution='Faculty 1',
            contact_email='contact1@test.edu',
            billing_address='Address 1',
            pib='111111111',
            matični_broj='111111111',
            šifra_delatnosti='1111',
            telefon='+381111111111',
            osoba_za_kontakt='Person 1',
            iban='RS35111111111111111111',
            naziv_banke='Bank 1',
            swift_bic='BANK1SBG',
            pdv_status='PDV Status 1',
            država_obveznika='Country 1'
        )
        
        member2 = Member.create_member(
            sponsor_id=sponsor.id,
            name='University 2',
            institution='Faculty 2',
            contact_email='contact2@test.edu',
            billing_address='Address 2',
            pib='222222222',
            matični_broj='222222222',
            šifra_delatnosti='2222',
            telefon='+381222222222',
            osoba_za_kontakt='Person 2',
            iban='RS35222222222222222222',
            naziv_banke='Bank 2',
            swift_bic='BANK2SBG',
            pdv_status='PDV Status 2',
            država_obveznika='Country 2'
        )
        
        # Deactivate member2
        member2.deactivate()
        
        # Test getting all members
        all_members = Member.get_by_sponsor(sponsor.id, active_only=False)
        assert len(all_members) == 2
        
        # Test getting only active members
        active_members = Member.get_by_sponsor(sponsor.id, active_only=True)
        assert len(active_members) == 1
        assert active_members[0].id == member1.id

    def test_member_deactivate_activate(self, app, sponsor):
        """Test member deactivation and activation."""
        member = Member.create_member(
            sponsor_id=sponsor.id,
            name='Test University',
            institution='Faculty of Science',
            contact_email='contact@testuni.edu',
            billing_address='123 University St',
            pib='123456789',
            matični_broj='987654321',
            šifra_delatnosti='8542',
            telefon='+381111234567',
            osoba_za_kontakt='Dr. Jane Doe',
            iban='RS35260005601001611379',
            naziv_banke='Komercijalna Banka',
            swift_bic='KOBBRSBG',
            pdv_status='Obveznik PDV-a',
            država_obveznika='Republika Srbija'
        )
        
        assert member.is_active == True
        
        # Test deactivation
        member.deactivate()
        assert member.is_active == False
        
        # Test activation
        member.activate()
        assert member.is_active == True

    def test_update_contact_info(self, app, sponsor):
        """Test updating member contact information."""
        member = Member.create_member(
            sponsor_id=sponsor.id,
            name='Test University',
            institution='Faculty of Science',
            contact_email='old@testuni.edu',
            billing_address='123 University St',
            pib='123456789',
            matični_broj='987654321',
            šifra_delatnosti='8542',
            telefon='+381111111111',
            osoba_za_kontakt='Old Person',
            iban='RS35260005601001611379',
            naziv_banke='Komercijalna Banka',
            swift_bic='KOBBRSBG',
            pdv_status='Obveznik PDV-a',
            država_obveznika='Republika Srbija'
        )
        
        # Update contact info
        member.update_contact_info(
            contact_email='new@testuni.edu',
            telefon='+381222222222',
            osoba_za_kontakt='New Person'
        )
        
        assert member.contact_email == 'new@testuni.edu'
        assert member.telefon == '+381222222222'
        assert member.osoba_za_kontakt == 'New Person'

    def test_update_banking_info(self, app, sponsor):
        """Test updating member banking information."""
        member = Member.create_member(
            sponsor_id=sponsor.id,
            name='Test University',
            institution='Faculty of Science',
            contact_email='contact@testuni.edu',
            billing_address='123 University St',
            pib='123456789',
            matični_broj='987654321',
            šifra_delatnosti='8542',
            telefon='+381111234567',
            osoba_za_kontakt='Dr. Jane Doe',
            iban='RS35111111111111111111',
            naziv_banke='Old Bank',
            swift_bic='OLDBNKBG',
            pdv_status='Obveznik PDV-a',
            država_obveznika='Republika Srbija'
        )
        
        # Update banking info
        member.update_banking_info(
            iban='RS35222222222222222222',
            naziv_banke='New Bank',
            swift_bic='NEWBNKBG'
        )
        
        assert member.iban == 'RS35222222222222222222'
        assert member.naziv_banke == 'New Bank'
        assert member.swift_bic == 'NEWBNKBG'