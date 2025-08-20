"""
Simple functional tests for dashboard functionality - Story 1.5
"""

import pytest
from app.models.user import User
from app.models.sponsor import Sponsor
from app import db


class TestDashboardBasicFunctionality:
    """Basic functional tests for dashboard."""
    
    def test_dashboard_route_requires_login(self, client):
        """Test dashboard redirects unauthenticated users to login."""
        response = client.get('/')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_dashboard_route_with_mock_session(self, client, app):
        """Test dashboard renders for authenticated user."""
        # Create a real user in test database
        with app.app_context():
            sponsor = Sponsor(
                name='Test Sponsor',
                email='sponsor@test.com', 
                crossref_member_id='12345',
                is_active=True
            )
            db.session.add(sponsor)
            db.session.commit()
            
            user = User.create_user(
                email='test@test.com',
                password='password123',
                full_name='Test User',
                role='operator'
            )
            db.session.commit()
            
            # Mock login session
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
            
            response = client.get('/')
            assert response.status_code == 200
            assert b'Dashboard' in response.data
    
    def test_dashboard_template_structure(self, client, app):
        """Test dashboard template contains required elements."""
        with app.app_context():
            sponsor = Sponsor(
                name='Test Sponsor',
                email='sponsor@test.com',
                crossref_member_id='12345', 
                is_active=True
            )
            db.session.add(sponsor)
            db.session.commit()
            
            user = User.create_user(
                email='test@test.com',
                password='password123',
                full_name='Test User',
                role='operator'
            )
            db.session.commit()
            
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
            
            response = client.get('/')
            html_content = response.data.decode('utf-8')
            
            # Check key elements are present
            assert 'Dashboard' in html_content
            assert 'Publikacije' in html_content  
            assert 'DOI Draft-ovi' in html_content
            assert 'lanovi' in html_content  # "članovi"
            assert 'Generisani XML' in html_content
            
            # Check Bootstrap classes
            assert 'container' in html_content
            assert 'card' in html_content
            assert 'navbar' in html_content
    
    def test_navigation_structure(self, client, app):
        """Test navigation contains required links."""
        with app.app_context():
            sponsor = Sponsor(
                name='Test Sponsor',
                email='sponsor@test.com',
                crossref_member_id='12345',
                is_active=True
            )
            db.session.add(sponsor)
            db.session.commit()
            
            user = User.create_user(
                email='test@test.com',
                password='password123',
                full_name='Test User',
                role='operator'
            )
            db.session.commit()
            
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
            
            response = client.get('/')
            html_content = response.data.decode('utf-8')
            
            # Check navigation elements
            assert 'Dashboard' in html_content
            assert 'lanovi' in html_content  # "Članovi"
            assert 'Publikacije' in html_content
            assert 'DOI Draft-ovi' in html_content
            assert 'navbar-toggler' in html_content  # Mobile hamburger
    
    def test_footer_structure(self, client, app):
        """Test footer contains required information.""" 
        with app.app_context():
            sponsor = Sponsor(
                name='Test Sponsor',
                email='sponsor@test.com',
                crossref_member_id='12345',
                is_active=True
            )
            db.session.add(sponsor)
            db.session.commit()
            
            user = User.create_user(
                email='test@test.com',
                password='password123',
                full_name='Test User', 
                role='operator'
            )
            db.session.commit()
            
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
            
            response = client.get('/')
            html_content = response.data.decode('utf-8')
            
            # Check footer elements
            assert 'DOI Management System' in html_content
            assert 'v1.0' in html_content
            assert '2024' in html_content
            assert 'Crossref API' in html_content
            assert 'Odjavi se' in html_content  # Logout link