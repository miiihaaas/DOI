"""
Tests for members blueprint - route and view logic testing.
"""

import pytest
from flask import url_for
from app import db
from app.models.member import Member
from app.models.sponsor import Sponsor
from app.models.user import User


class TestMembersBlueprint:
    """Test suite for members blueprint routes."""

    def test_members_index_requires_authentication(self, client):
        """Test that members index requires user to be logged in."""
        response = client.get('/members/')
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_members_index_with_authenticated_user(self, client, auth_user, login_user):
        """Test members index with authenticated user."""
        login_user(auth_user)
        response = client.get('/members/')
        assert response.status_code == 200
        assert 'Članovi' in response.get_data(as_text=True)

    def test_members_index_shows_sponsor_members(self, client, auth_user, login_user, db_session, sponsor):
        """Test that users can see their sponsor's members."""
        login_user(auth_user)
        
        # Create member for the singleton sponsor
        our_member = Member.create_member(
            sponsor_id=sponsor.id,
            name='Our Member',
            institution='Our Institution',
            contact_email='our@member.com',
            billing_address='Our Address 123',
            pib='123456789',
            matični_broj='12345678',
            šifra_delatnosti='7220',
            telefon='+381 11 123-4567',
            osoba_za_kontakt='Our Person',
            iban='RS35260005601001611379',
            naziv_banke='Our Bank',
            swift_bic='OURRS22X',
            pdv_status='obveznik_pdv',
            država_obveznika='Srbija'
        )
        db_session.commit()
        
        response = client.get('/members/')
        data = response.get_data(as_text=True)
        
        assert 'Our Member' in data

    def test_members_create_get(self, client, auth_user, login_user):
        """Test GET request to create member form."""
        login_user(auth_user)
        response = client.get('/members/create')
        assert response.status_code == 200
        assert 'Novi član' in response.get_data(as_text=True)
        assert 'form' in response.get_data(as_text=True)

    def test_members_create_post_valid_data(self, client, auth_user, login_user, db_session, sponsor):
        """Test POST request to create member with valid data."""
        login_user(auth_user)
        
        form_data = {
            'name': 'Test Member',
            'institution': 'Test Institution',
            'contact_email': 'test@member.com',
            'website_url': 'https://www.test.com',
            'billing_address': 'Test Address 123, Belgrade',
            'pib': '123456789',
            'matični_broj': '12345678',
            'jmbg_lk': '',
            'šifra_delatnosti': '7220',
            'telefon': '+381 11 123-4567',
            'osoba_za_kontakt': 'Test Person',
            'iban': 'RS35260005601001611379',
            'naziv_banke': 'Test Bank',
            'swift_bic': 'TESTRS22',
            'pdv_status': 'obveznik_pdv',
            'država_obveznika': 'Srbija',
            'is_active': True,
            'csrf_token': 'fake-token'  # In real tests, get actual CSRF token
        }
        
        response = client.post('/members/create', data=form_data)
        # Should redirect on success
        assert response.status_code == 302 or response.status_code == 200
        
        # Verify member was created
        member = Member.query.filter_by(
            name='Test Member',
            sponsor_id=sponsor.id
        ).first()
        assert member is not None
        assert member.contact_email == 'test@member.com'

    def test_members_create_post_invalid_data(self, client, auth_user, login_user):
        """Test POST request to create member with invalid data."""
        login_user(auth_user)
        
        # Missing required fields
        form_data = {
            'name': '',  # Required field missing
            'contact_email': 'invalid-email',  # Invalid email format
            'csrf_token': 'fake-token'
        }
        
        response = client.post('/members/create', data=form_data)
        # Should show form again with errors
        assert response.status_code == 200
        data = response.get_data(as_text=True)
        assert 'Naziv člana je obavezan' in data or 'error' in data.lower()

    def test_members_detail_existing_member(self, client, auth_user, login_user, test_member):
        """Test member detail view for existing member."""
        login_user(auth_user)
        
        response = client.get(f'/members/{test_member.id}')
        assert response.status_code == 200
        data = response.get_data(as_text=True)
        assert test_member.name in data
        assert test_member.contact_email in data

    def test_members_detail_nonexistent_member(self, client, auth_user, login_user):
        """Test member detail view for non-existent member."""
        login_user(auth_user)
        
        response = client.get('/members/99999')
        assert response.status_code == 404

    def test_members_edit_get(self, client, auth_user, login_user, test_member):
        """Test GET request to edit member form."""
        login_user(auth_user)
        
        response = client.get(f'/members/{test_member.id}/edit')
        assert response.status_code == 200
        data = response.get_data(as_text=True)
        assert 'Uredi član' in data
        assert test_member.name in data

    def test_members_edit_post_valid_data(self, client, auth_user, login_user, test_member):
        """Test POST request to edit member with valid data."""
        login_user(auth_user)
        
        form_data = {
            'name': 'Updated Member Name',
            'institution': test_member.institution,
            'contact_email': test_member.contact_email,
            'website_url': test_member.website_url or '',
            'billing_address': test_member.billing_address,
            'pib': test_member.pib,
            'matični_broj': test_member.matični_broj,
            'jmbg_lk': test_member.jmbg_lk or '',
            'šifra_delatnosti': test_member.šifra_delatnosti,
            'telefon': test_member.telefon,
            'osoba_za_kontakt': test_member.osoba_za_kontakt,
            'iban': test_member.iban,
            'naziv_banke': test_member.naziv_banke,
            'swift_bic': test_member.swift_bic,
            'pdv_status': test_member.pdv_status,
            'država_obveznika': test_member.država_obveznika,
            'is_active': True,
            'csrf_token': 'fake-token'
        }
        
        response = client.post(f'/members/{test_member.id}/edit', data=form_data)
        # Should redirect on success
        assert response.status_code == 302 or response.status_code == 200
        
        # Verify member was updated
        updated_member = db.session.get(Member, test_member.id)
        assert updated_member.name == 'Updated Member Name'

    def test_members_toggle_status(self, client, auth_user, login_user, test_member):
        """Test toggling member active status."""
        login_user(auth_user)
        
        original_status = test_member.is_active
        
        response = client.post(f'/members/{test_member.id}/toggle-status', data={'csrf_token': 'fake-token'})
        # Should redirect
        assert response.status_code == 302
        
        # Verify status was toggled
        updated_member = db.session.get(Member, test_member.id)
        assert updated_member.is_active != original_status

    def test_members_search_ajax(self, client, auth_user, login_user, test_member):
        """Test AJAX member search endpoint."""
        login_user(auth_user)
        
        response = client.get('/members/search', query_string={'q': test_member.name[:5]})
        assert response.status_code == 200
        assert response.is_json
        
        data = response.get_json()
        assert 'members' in data
        assert len(data['members']) > 0
        assert any(member['name'] == test_member.name for member in data['members'])

    def test_members_search_empty_query(self, client, auth_user, login_user):
        """Test AJAX search with empty query."""
        login_user(auth_user)
        
        response = client.get('/members/search', query_string={'q': ''})
        assert response.status_code == 200
        data = response.get_json()
        assert data['members'] == []

    def test_members_index_pagination(self, client, auth_user, login_user, db_session, sponsor):
        """Test member list pagination."""
        login_user(auth_user)
        
        # Create multiple members to test pagination
        for i in range(15):
            Member.create_member(
                sponsor_id=sponsor.id,
                name=f'Test Member {i}',
                institution=f'Institution {i}',
                contact_email=f'test{i}@member.com',
                billing_address=f'Address {i}',
                pib=f'12345678{i:01d}',
                matični_broj=f'1234567{i:01d}',
                šifra_delatnosti='7220',
                telefon=f'+381 11 123-456{i:01d}',
                osoba_za_kontakt=f'Person {i}',
                iban=f'RS3526000560100161137{i:01d}',
                naziv_banke=f'Bank {i}',
                swift_bic=f'TEST{i:02d}22',
                pdv_status='obveznik_pdv',
                država_obveznika='Srbija'
            )
        db_session.commit()
        
        # Test first page
        response = client.get('/members/')
        assert response.status_code == 200
        data = response.get_data(as_text=True)
        assert 'Test Member 0' in data
        
        # Test second page
        response = client.get('/members/', query_string={'page': 2})
        assert response.status_code == 200

    def test_members_index_search_filter(self, client, auth_user, login_user, db_session, sponsor):
        """Test member list search and filtering."""
        login_user(auth_user)
        
        # Create test members
        active_member = Member.create_member(
            sponsor_id=sponsor.id,
            name='Active Search Member',
            institution='Search Institution',
            contact_email='active@search.com',
            billing_address='Search Address 123',
            pib='111111111',
            matični_broj='11111111',
            šifra_delatnosti='7220',
            telefon='+381 11 111-1111',
            osoba_za_kontakt='Active Person',
            iban='RS35260005601001611111',
            naziv_banke='Active Bank',
            swift_bic='ACTIRS22',
            pdv_status='obveznik_pdv',
            država_obveznika='Srbija',
            is_active=True
        )
        
        inactive_member = Member.create_member(
            sponsor_id=sponsor.id,
            name='Inactive Search Member',
            institution='Search Institution',
            contact_email='inactive@search.com',
            billing_address='Search Address 456',
            pib='222222222',
            matični_broj='22222222',
            šifra_delatnosti='7220',
            telefon='+381 11 222-2222',
            osoba_za_kontakt='Inactive Person',
            iban='RS35260005601001612222',
            naziv_banke='Inactive Bank',
            swift_bic='INACRS22',
            pdv_status='obveznik_pdv',
            država_obveznika='Srbija',
            is_active=False
        )
        db_session.commit()
        
        # Test search by name
        response = client.get('/members/', query_string={'search': 'Search'})
        assert response.status_code == 200
        data = response.get_data(as_text=True)
        assert 'Active Search Member' in data
        assert 'Inactive Search Member' in data
        
        # Test filter by active status
        response = client.get('/members/', query_string={'status': 'active'})
        assert response.status_code == 200
        data = response.get_data(as_text=True)
        assert 'Active Search Member' in data
        assert 'Inactive Search Member' not in data
        
        # Test filter by inactive status
        response = client.get('/members/', query_string={'status': 'inactive'})
        assert response.status_code == 200
        data = response.get_data(as_text=True)
        assert 'Active Search Member' not in data
        assert 'Inactive Search Member' in data

    def test_members_index_no_sponsor_configured(self, client, auth_user, login_user, db_session):
        """Test members index when no sponsor is configured."""
        login_user(auth_user)
        
        # Delete the sponsor to simulate missing sponsor
        Sponsor.query.delete()
        db_session.commit()
        
        response = client.get('/members/')
        assert response.status_code == 302  # Should redirect
        # Check if redirected to main index with error message

    def test_members_create_no_sponsor_configured(self, client, auth_user, login_user, db_session):
        """Test member creation when no sponsor is configured."""
        login_user(auth_user)
        
        # Delete the sponsor
        Sponsor.query.delete()
        db_session.commit()
        
        form_data = {
            'name': 'Test Member',
            'institution': 'Test Institution',
            'contact_email': 'test@member.com',
            'billing_address': 'Test Address 123',
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
        
        response = client.post('/members/create', data=form_data)
        assert response.status_code == 302  # Should redirect due to missing sponsor