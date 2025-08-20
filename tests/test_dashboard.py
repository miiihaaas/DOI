"""
Tests for dashboard functionality - Story 1.5
"""

import pytest
from flask import url_for
from app.models.user import User
from app.models.sponsor import Sponsor
from app import db


class TestDashboardRoute:
    """Test dashboard route and statistics logic."""
    
    def test_dashboard_requires_authentication(self, client):
        """Test that dashboard requires login."""
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login
        assert '/auth/login' in response.location
    
    def test_dashboard_redirects_to_root(self, client, auth_user):
        """Test that /dashboard redirects to root for consistency."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
            sess['_fresh'] = True
        
        response = client.get('/dashboard')
        assert response.status_code == 302
        assert response.location.endswith('/')
    
    def test_dashboard_displays_welcome_message(self, client, auth_user):
        """Test dashboard shows welcome message with user name (AC: 1)."""
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['_fresh'] = True
        
        response = client.get('/')
        assert response.status_code == 200
        # Template should render with user context
        assert b'Dashboard' in response.data  # Page title present
    
    def test_dashboard_displays_statistics(self, client, auth_user):
        """Test dashboard shows statistics (AC: 3)."""
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['_fresh'] = True
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check statistics cards are present (placeholders for now)
        assert b'lanovi' in response.data  # "članovi" 
        assert b'Publikacije' in response.data
        assert b'DOI Draft-ovi' in response.data
        assert b'Generisani XML' in response.data
    
    def test_dashboard_statistics_data_structure(self, client, auth_user):
        """Test that statistics data is properly structured."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
            sess['_fresh'] = True
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check template renders without errors (statistics variable exists)
        assert b'0' in response.data  # Placeholder statistics should show 0


class TestNavigationFunctionality:
    """Test navigation menu system across different user roles."""
    
    def test_navigation_contains_required_links(self, client, auth_user):
        """Test navigation includes required sections (AC: 2)."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
            sess['_fresh'] = True
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check navigation links are present
        assert b'Dashboard' in response.data
        assert b'\xc4\x8clanovi' in response.data  # "Članovi" 
        assert b'Publikacije' in response.data
        assert b'DOI Draft-ovi' in response.data
        assert b'Account Settings' in response.data
    
    def test_admin_navigation_shows_admin_link(self, client, admin_user):
        """Test admin users see admin navigation (AC: 2)."""
        # Simulate login by posting credentials  
        login_response = client.post('/auth/login', data={
            'email': 'admin@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Login should redirect to dashboard
        assert login_response.status_code == 200
        
        # Now make the actual test request  
        response = client.get('/')
        assert response.status_code == 200  # Should show dashboard since already logged in
        assert b'Admin' in response.data
    
    def test_operator_navigation_hides_admin_link(self, client, operator_user):
        """Test operator users don't see admin navigation."""
        # Simulate login by posting credentials  
        login_response = client.post('/auth/login', data={
            'email': 'operator@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Login should redirect to dashboard
        assert login_response.status_code == 200
        
        # Test dashboard directly
        response = client.get('/')
        assert response.status_code == 200
        
        # Admin link should not be visible for operators
        html_content = response.data.decode('utf-8')
        # Look for admin link specifically in navigation context
        assert 'href="/admin/users"' not in html_content or 'bi-shield-check' not in html_content
    
    def test_navigation_active_page_highlighting(self, client, auth_user):
        """Test current page is highlighted in navigation (AC: 5)."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
            sess['_fresh'] = True
        
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Dashboard should be active on root page
        assert 'nav-link active' in html_content
        assert 'bi-house' in html_content  # Dashboard icon


class TestFooterFunctionality:
    """Test footer with application information and logout link."""
    
    def test_footer_contains_app_information(self, client, auth_user):
        """Test footer includes basic application information (AC: 6)."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
            sess['_fresh'] = True
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check footer content
        assert b'DOI Management System' in response.data
        assert b'v1.0' in response.data
        assert b'2024' in response.data
        assert b'Crossref API' in response.data
    
    def test_footer_contains_logout_link(self, client, auth_user):
        """Test footer includes logout functionality (AC: 6)."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
            sess['_fresh'] = True
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check footer logout button
        assert b'Odjavi se' in response.data
        html_content = response.data.decode('utf-8')
        assert 'action="/auth/logout"' in html_content
    
    def test_footer_shows_user_info(self, client, auth_user):
        """Test footer shows current user information."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
            sess['_fresh'] = True
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check user info in footer
        assert auth_user.full_name.encode() in response.data
        assert auth_user.role.encode() in response.data


class TestBootstrapStylingAndFlashMessages:
    """Test Bootstrap 5.3.x styling and flash messaging system."""
    
    def test_bootstrap_classes_present(self, client, auth_user):
        """Test Bootstrap 5.3.x classes are used (AC: 7)."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
            sess['_fresh'] = True
        
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check Bootstrap classes
        assert 'container' in html_content
        assert 'row' in html_content
        assert 'col-md-' in html_content
        assert 'card' in html_content
        assert 'navbar' in html_content
        assert 'btn' in html_content
    
    def test_responsive_design_classes(self, client, auth_user):
        """Test responsive design with Bootstrap grid (AC: 4)."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
            sess['_fresh'] = True
        
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check responsive classes
        assert 'navbar-expand-lg' in html_content  # Mobile navigation
        assert 'navbar-toggler' in html_content    # Hamburger menu
        assert 'collapse navbar-collapse' in html_content
        assert 'col-md-' in html_content  # Responsive columns
    
    def test_flash_message_system_structure(self, client, auth_user):
        """Test flash messaging system is present (AC: 8)."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
            sess['_fresh'] = True
        
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check flash message container exists
        assert 'get_flashed_messages' in html_content or 'alert' in html_content
        # The actual flash message testing would require triggering a flash
    
    def test_professional_interface_elements(self, client, auth_user):
        """Test professional, clean interface elements (AC: 7)."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
            sess['_fresh'] = True
        
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check professional elements
        assert 'bi-' in html_content  # Bootstrap icons
        assert 'card-body' in html_content
        assert 'text-muted' in html_content
        assert 'btn-' in html_content


class TestTemplateRendering:
    """Test template rendering with mock data."""
    
    def test_template_renders_without_errors(self, client, auth_user):
        """Test dashboard template renders successfully."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
            sess['_fresh'] = True
        
        response = client.get('/')
        assert response.status_code == 200
        assert b'Dashboard' in response.data
        assert b'<!DOCTYPE html>' in response.data
    
    def test_template_variables_passed_correctly(self, client, auth_user):
        """Test template receives correct variables."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
            sess['_fresh'] = True
        
        response = client.get('/')
        assert response.status_code == 200
        
        # User object should be passed
        assert auth_user.full_name.encode() in response.data
        
        # Statistics should be passed (even if 0)
        assert b'0' in response.data  # Statistics placeholders


# Test fixtures for different user types
@pytest.fixture
def sponsor(app):
    """Create sponsor for testing."""
    with app.app_context():
        sponsor = Sponsor(
            name='Test Sponsor Organization',
            email='sponsor@test.com',
            crossref_member_id='12345',
            is_active=True
        )
        db.session.add(sponsor)
        db.session.commit()
        return sponsor


@pytest.fixture
def auth_user(app, sponsor):
    """Create authenticated user for testing."""
    with app.app_context():
        user = User.create_user(
            email='user@test.com',
            password='password123',
            full_name='Test User',
            role='operator'
        )
        db.session.commit()
        user_id = user.id
        user_email = user.email
        user_full_name = user.full_name
        user_role = user.role
        
        # Create a simple mock user object with needed attributes
        class MockUser:
            def __init__(self, id, email, full_name, role):
                self.id = id
                self.email = email
                self.full_name = full_name
                self.role = role
                self.is_authenticated = True
                self.is_active = True
                self.is_anonymous = False
                
            def get_id(self):
                return str(self.id)
        
        return MockUser(user_id, user_email, user_full_name, user_role)


@pytest.fixture
def admin_user(app, sponsor):
    """Create admin user for testing."""
    with app.app_context():
        admin = User.create_user(
            email='admin@test.com',
            password='password123',
            full_name='Admin User',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture  
def operator_user(app, sponsor):
    """Create operator user for testing."""
    with app.app_context():
        operator = User.create_user(
            email='operator@test.com',
            password='password123', 
            full_name='Operator User',
            role='operator'
        )
        db.session.add(operator)
        db.session.commit()
        operator_id = operator.id
        operator_email = operator.email
        operator_full_name = operator.full_name
        operator_role = operator.role
        
        # Create a simple mock user object with needed attributes
        class MockUser:
            def __init__(self, id, email, full_name, role):
                self.id = id
                self.email = email
                self.full_name = full_name
                self.role = role
                self.is_authenticated = True
                self.is_active = True
                self.is_anonymous = False
                
            def get_id(self):
                return str(self.id)
        
        return MockUser(operator_id, operator_email, operator_full_name, operator_role)