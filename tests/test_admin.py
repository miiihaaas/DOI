"""
Tests for admin blueprint functionality.
"""

import pytest
from flask import url_for
from app import db
from app.models.user import User
from app.models.sponsor import Sponsor


def login_user(client, user, password='testpassword'):
    """Helper function to login a user with CSRF token."""
    with client.session_transaction() as sess:
        from flask_wtf.csrf import generate_csrf
        sess['_csrf_token'] = generate_csrf()
    
    return client.post('/auth/login', data={
        'email': user.email,
        'password': password,
        'csrf_token': sess['_csrf_token']
    })


class TestAdminAuthorization:
    """Test admin authorization and access control."""
    
    def test_admin_required_decorator_blocks_anonymous_users(self, client):
        """Anonymous users should be redirected to login."""
        response = client.get('/admin/users')
        assert response.status_code == 302
        assert 'auth/login' in response.location
    
    def test_admin_required_decorator_blocks_operator_users(self, client, auth_user_operator):
        """Operator users should get 403 Forbidden."""
        # Login as operator
        login_user(client, auth_user_operator)
        
        response = client.get('/admin/users')
        # Could be 302 redirect to dashboard with flash message, or 403 forbidden
        assert response.status_code in [302, 403]
    
    def test_admin_required_decorator_allows_admin_users(self, client, auth_user_admin):
        """Admin users should have access."""
        # Login as admin
        login_user(client, auth_user_admin)
        
        response = client.get('/admin/users')
        assert response.status_code == 200


class TestUserListing:
    """Test user listing functionality."""
    
    def test_users_list_displays_all_users(self, client, auth_user_admin, multiple_users):
        """User listing should display all users."""
        # Login as admin
        login_user(client, auth_user_admin)
        
        response = client.get('/admin/users')
        assert response.status_code == 200
        
        # Check that some test users are displayed
        data = response.get_data(as_text=True)
        assert 'user0@test.com' in data
        assert 'user1@test.com' in data
    
    def test_users_list_pagination(self, client, auth_user_admin, app):
        """User listing should support pagination."""
        with app.app_context():
            # Create many users (more than per_page limit)
            for i in range(25):
                user = User.create_user(
                    email=f'user{i}@test.com',
                    password='testpass',
                    full_name=f'Test User {i}',
                    role='operator'
                )
        
        # Login as admin
        login_user(client, auth_user_admin)
        
        response = client.get('/admin/users')
        assert response.status_code == 200
        
        data = response.get_data(as_text=True)
        # Should have pagination controls
        assert 'pagination' in data or 'page' in data


class TestUserCreation:
    """Test user creation functionality."""
    
    def test_create_user_get_form(self, client, auth_user_admin):
        """GET request should display user creation form."""
        client.post('/auth/login', data={
            'email': auth_user_admin.email,
            'password': 'testpassword'
        })
        
        response = client.get('/admin/users/create')
        assert response.status_code == 200
        
        data = response.get_data(as_text=True)
        assert 'Kreiraj novog korisnika' in data
        assert 'name="email"' in data
        assert 'name="full_name"' in data
        assert 'name="password"' in data
        assert 'name="role"' in data
    
    def test_create_user_valid_data(self, client, auth_user_admin, app):
        """Valid user creation should succeed."""
        client.post('/auth/login', data={
            'email': auth_user_admin.email,
            'password': 'testpassword'
        })
        
        with app.app_context():
            initial_count = User.query.count()
        
        response = client.post('/admin/users/create', data={
            'email': 'newuser@test.com',
            'full_name': 'New Test User',
            'password': 'newpassword',
            'role': 'operator'
        })
        
        assert response.status_code == 302  # Redirect after successful creation
        
        with app.app_context():
            assert User.query.count() == initial_count + 1
            new_user = User.get_by_email('newuser@test.com')
            assert new_user is not None
            assert new_user.full_name == 'New Test User'
            assert new_user.role == 'operator'
            assert new_user.check_password('newpassword')
    
    def test_create_user_duplicate_email(self, client, auth_user_admin, auth_user_operator):
        """Creating user with duplicate email should fail."""
        client.post('/auth/login', data={
            'email': auth_user_admin.email,
            'password': 'testpassword'
        })
        
        response = client.post('/admin/users/create', data={
            'email': auth_user_operator.email,  # Duplicate email
            'full_name': 'Another User',
            'password': 'password123',
            'role': 'operator'
        })
        
        # Should return to form with error message
        assert response.status_code == 200
        data = response.get_data(as_text=True)
        assert 'već postoji' in data
    
    def test_create_user_invalid_password(self, client, auth_user_admin):
        """Creating user with short password should fail."""
        client.post('/auth/login', data={
            'email': auth_user_admin.email,
            'password': 'testpassword'
        })
        
        response = client.post('/admin/users/create', data={
            'email': 'newuser@test.com',
            'full_name': 'New Test User',
            'password': '123',  # Too short
            'role': 'operator'
        })
        
        assert response.status_code == 200
        data = response.get_data(as_text=True)
        assert 'Greška' in data


class TestUserEditing:
    """Test user editing functionality."""
    
    def test_edit_user_get_form(self, client, auth_user_admin, auth_user_operator):
        """GET request should display user edit form with pre-filled data."""
        client.post('/auth/login', data={
            'email': auth_user_admin.email,
            'password': 'testpassword'
        })
        
        response = client.get(f'/admin/users/{auth_user_operator.id}/edit')
        assert response.status_code == 200
        
        data = response.get_data(as_text=True)
        assert 'Uredi korisnika' in data
        assert auth_user_operator.email in data
        assert auth_user_operator.full_name in data
    
    def test_edit_user_valid_data(self, client, auth_user_admin, auth_user_operator, app):
        """Valid user editing should succeed."""
        client.post('/auth/login', data={
            'email': auth_user_admin.email,
            'password': 'testpassword'
        })
        
        response = client.post(f'/admin/users/{auth_user_operator.id}/edit', data={
            'email': 'updated@test.com',
            'full_name': 'Updated Name',
            'role': 'admin'
        })
        
        assert response.status_code == 302  # Redirect after successful update
        
        with app.app_context():
            updated_user = User.query.get(auth_user_operator.id)
            assert updated_user.email == 'updated@test.com'
            assert updated_user.full_name == 'Updated Name'
            assert updated_user.role == 'admin'
    
    def test_edit_user_prevent_self_role_change(self, client, auth_user_admin):
        """Admin users should not be able to change their own role."""
        client.post('/auth/login', data={
            'email': auth_user_admin.email,
            'password': 'testpassword'
        })
        
        response = client.get(f'/admin/users/{auth_user_admin.id}/edit')
        assert response.status_code == 200
        
        data = response.get_data(as_text=True)
        assert 'Ne možete promeniti svoju ulogu' in data


class TestPasswordReset:
    """Test password reset functionality."""
    
    def test_reset_password_valid(self, client, auth_user_admin, auth_user_operator, app):
        """Valid password reset should succeed."""
        client.post('/auth/login', data={
            'email': auth_user_admin.email,
            'password': 'testpassword'
        })
        
        response = client.post(f'/admin/users/{auth_user_operator.id}/reset-password', data={
            'new_password': 'newpassword123'
        })
        
        assert response.status_code == 302  # Redirect after successful reset
        
        with app.app_context():
            updated_user = User.query.get(auth_user_operator.id)
            assert updated_user.check_password('newpassword123')
            assert not updated_user.check_password('testpassword')  # Old password should not work
    
    def test_reset_password_invalid_short(self, client, auth_user_admin, auth_user_operator):
        """Password reset with short password should fail."""
        client.post('/auth/login', data={
            'email': auth_user_admin.email,
            'password': 'testpassword'
        })
        
        response = client.post(f'/admin/users/{auth_user_operator.id}/reset-password', data={
            'new_password': '123'  # Too short
        })
        
        assert response.status_code == 302  # Redirect back to edit page
        # Note: Error message will be in flash messages


class TestErrorHandling:
    """Test error handling in admin routes."""
    
    def test_edit_nonexistent_user(self, client, auth_user_admin):
        """Editing non-existent user should return 404."""
        client.post('/auth/login', data={
            'email': auth_user_admin.email,
            'password': 'testpassword'
        })
        
        response = client.get('/admin/users/99999/edit')
        assert response.status_code == 404
    
    def test_reset_password_nonexistent_user(self, client, auth_user_admin):
        """Resetting password for non-existent user should return 404."""
        client.post('/auth/login', data={
            'email': auth_user_admin.email,
            'password': 'testpassword'
        })
        
        response = client.post('/admin/users/99999/reset-password', data={
            'new_password': 'newpassword123'
        })
        assert response.status_code == 404


# Test fixtures
@pytest.fixture
def auth_user_admin(app):
    """Create an admin user for testing."""
    with app.app_context():
        # Create sponsor first if it doesn't exist
        sponsor = Sponsor.get_instance()
        if not sponsor:
            sponsor = Sponsor.create_instance(
                name='Test Sponsor',
                email='sponsor@test.com',
                crossref_member_id='12345'
            )
        
        user = User.create_user(
            email='admin@test.com',
            password='testpassword',
            full_name='Admin User',
            role='admin'
        )
        db.session.refresh(user)  # Refresh to avoid detached instance
        return user


@pytest.fixture
def auth_user_operator(app):
    """Create an operator user for testing."""
    with app.app_context():
        # Create sponsor first if it doesn't exist
        sponsor = Sponsor.get_instance()
        if not sponsor:
            sponsor = Sponsor.create_instance(
                name='Test Sponsor',
                email='sponsor@test.com',
                crossref_member_id='12345'
            )
            
        user = User.create_user(
            email='operator@test.com',
            password='testpassword',
            full_name='Operator User',
            role='operator'
        )
        db.session.refresh(user)  # Refresh to avoid detached instance
        return user


@pytest.fixture
def multiple_users(app):
    """Create multiple users for testing."""
    with app.app_context():
        # Create sponsor first if it doesn't exist
        sponsor = Sponsor.get_instance()
        if not sponsor:
            sponsor = Sponsor.create_instance(
                name='Test Sponsor',
                email='sponsor@test.com',
                crossref_member_id='12345'
            )
            
        users = []
        for i in range(5):
            user = User.create_user(
                email=f'user{i}@test.com',
                password='testpassword',
                full_name=f'Test User {i}',
                role='operator' if i % 2 == 0 else 'admin'
            )
            db.session.refresh(user)  # Refresh to avoid detached instance
            users.append(user)
        return users