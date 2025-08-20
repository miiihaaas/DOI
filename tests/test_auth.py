"""
Tests for authentication system - login, logout, and session management.
"""

import pytest
from flask import url_for
from app import db
from app.models.user import User
from app.models.sponsor import Sponsor


@pytest.fixture
def sponsor(app):
    """Create a test sponsor."""
    with app.app_context():
        sponsor = Sponsor(
            name="Test Organization",
            email="test@organization.rs",
            crossref_member_id="1234"
        )
        sponsor.save()
        return sponsor


@pytest.fixture
def test_user(app, sponsor):
    """Create a test user."""
    with app.app_context():
        user = User.create_user(
            email="test@example.com",
            password="testpassword123",
            full_name="Test User",
            role="admin"
        )
        return user


class TestLogin:
    """Test login functionality."""

    def test_login_page_loads(self, client):
        """Test that login page loads correctly."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Prijava' in response.data
        assert b'Email adresa' in response.data
        assert b'Lozinka' in response.data

    def test_successful_login(self, client, test_user):
        """Test successful user login."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'Dobrodošli, Test User!'.encode('utf-8') in response.data

    def test_login_with_wrong_password(self, client, test_user):
        """Test login with incorrect password."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert 'Neispravni podaci za prijavu.'.encode('utf-8') in response.data

    def test_login_with_nonexistent_email(self, client):
        """Test login with nonexistent email."""
        response = client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        assert 'Neispravni podaci za prijavu.'.encode('utf-8') in response.data

    def test_login_with_empty_fields(self, client):
        """Test login with empty email and password."""
        response = client.post('/auth/login', data={
            'email': '',
            'password': ''
        })
        
        assert response.status_code == 200
        assert 'Email i lozinka su obavezni.'.encode('utf-8') in response.data

    def test_login_with_empty_email(self, client):
        """Test login with empty email."""
        response = client.post('/auth/login', data={
            'email': '',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        assert 'Email i lozinka su obavezni.'.encode('utf-8') in response.data

    def test_login_with_empty_password(self, client):
        """Test login with empty password."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': ''
        })
        
        assert response.status_code == 200
        assert 'Email i lozinka su obavezni.'.encode('utf-8') in response.data

    def test_redirect_to_dashboard_after_login(self, client, test_user):
        """Test redirect to dashboard after successful login."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        assert response.status_code == 302
        assert '/dashboard' in response.location

    def test_redirect_to_next_page_after_login(self, client, test_user):
        """Test redirect to next page after login when ?next is provided."""
        response = client.post('/auth/login?next=/members/', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        assert response.status_code == 302
        assert '/members/' in response.location

    def test_redirect_authenticated_user_from_login(self, client, test_user):
        """Test that authenticated users are redirected away from login page."""
        # First login
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        # Try to access login page again
        response = client.get('/auth/login')
        assert response.status_code == 302
        assert '/dashboard' in response.location


class TestLogout:
    """Test logout functionality."""

    def test_logout_redirects_to_login(self, client, test_user):
        """Test that logout redirects to login page."""
        # First login
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        # Then logout
        response = client.post('/auth/logout')
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_logout_shows_success_message(self, client, test_user):
        """Test that logout shows success message."""
        # First login
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        # Then logout
        response = client.post('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert 'Uspešno ste se odjavili, Test User.'.encode('utf-8') in response.data

    def test_logout_requires_login(self, client):
        """Test that logout requires user to be logged in."""
        response = client.post('/auth/logout')
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_logout_only_accepts_post(self, client, test_user):
        """Test that logout only accepts POST requests."""
        # First login
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        # Try GET request to logout
        response = client.get('/auth/logout')
        assert response.status_code == 405  # Method Not Allowed


class TestSessionManagement:
    """Test session management and route protection."""

    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires login."""
        response = client.get('/')
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_members_index_requires_login(self, client):
        """Test that members index requires login."""
        response = client.get('/members/')
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_publications_index_requires_login(self, client):
        """Test that publications index requires login."""
        response = client.get('/publications/')
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_drafts_index_requires_login(self, client):
        """Test that drafts index requires login."""
        response = client.get('/drafts/')
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_authenticated_user_can_access_dashboard(self, client, test_user):
        """Test that authenticated user can access dashboard."""
        # Login first
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        # Access dashboard
        response = client.get('/')
        assert response.status_code == 200

    def test_authenticated_user_can_access_protected_routes(self, client, test_user):
        """Test that authenticated user can access protected routes."""
        # Login first
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        # Test access to protected routes
        routes = ['/members/', '/publications/', '/drafts/']
        for route in routes:
            response = client.get(route)
            assert response.status_code == 200

    def test_session_persists_across_requests(self, client, test_user):
        """Test that user session persists across multiple requests."""
        # Login
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        # Make multiple requests to protected routes
        for _ in range(3):
            response = client.get('/')
            assert response.status_code == 200

    def test_last_login_updated_on_successful_login(self, client, test_user, app):
        """Test that last_login is updated on successful login."""
        with app.app_context():
            # Check initial last_login (should be None)
            user = User.get_by_email('test@example.com')
            assert user.last_login is None
            
            # Login
            client.post('/auth/login', data={
                'email': 'test@example.com',
                'password': 'testpassword123'
            })
            
            # Check that last_login was updated
            user = User.get_by_email('test@example.com')
            assert user.last_login is not None


class TestPasswordSecurity:
    """Test password hashing and verification."""

    def test_password_is_hashed(self, app, sponsor):
        """Test that password is properly hashed when user is created."""
        with app.app_context():
            user = User.create_user(
                email="hash@example.com",
                password="plainpassword",
                full_name="Hash Test User"
            )
            
            # Password should not be stored in plain text
            assert user.password_hash != "plainpassword"
            assert len(user.password_hash) > 50  # Hashed passwords are long

    def test_password_verification(self, app, sponsor):
        """Test password verification works correctly."""
        with app.app_context():
            user = User.create_user(
                email="verify@example.com",
                password="testpassword",
                full_name="Verify Test User"
            )
            
            # Correct password should verify
            assert user.check_password("testpassword") is True
            
            # Wrong password should not verify
            assert user.check_password("wrongpassword") is False

    def test_password_minimum_length_validation(self, app, sponsor):
        """Test that password minimum length is enforced."""
        with app.app_context():
            with pytest.raises(ValueError, match="Password must be at least 6 characters long"):
                User.create_user(
                    email="short@example.com",
                    password="12345",  # Only 5 characters
                    full_name="Short Password User"
                )


class TestFormValidation:
    """Test form validation and error handling."""

    def test_email_case_insensitive_login(self, client, test_user):
        """Test that email login is case insensitive."""
        # Login with uppercase email
        response = client.post('/auth/login', data={
            'email': 'TEST@EXAMPLE.COM',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'Dobrodošli, Test User!'.encode('utf-8') in response.data

    def test_email_whitespace_handling(self, client, test_user):
        """Test that email whitespace is handled correctly."""
        # Login with email that has leading/trailing spaces
        response = client.post('/auth/login', data={
            'email': '  test@example.com  ',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'Dobrodošli, Test User!'.encode('utf-8') in response.data

    def test_login_form_retains_email_on_error(self, client, test_user):
        """Test that login form retains email value on validation error."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'value="test@example.com"' in response.data