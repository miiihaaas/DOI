"""
Unit tests for database models.
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app import create_app, db
from app.models import Sponsor, User


class TestSponsorModel:
    """Test cases for Sponsor model."""

    def test_sponsor_creation(self, app):
        """Test basic sponsor creation."""
        with app.app_context():
            # Clear existing sponsors first
            Sponsor.query.delete()
            db.session.commit()
            
            sponsor = Sponsor.create_instance(
                name="Test Organization",
                email="test@org.com",
                crossref_member_id="1234"
            )
            
            assert sponsor.id is not None
            assert sponsor.name == "Test Organization"
            assert sponsor.email == "test@org.com"
            assert sponsor.crossref_member_id == "1234"
            assert sponsor.is_active is True
            assert sponsor.created_at is not None
            assert sponsor.updated_at is not None

    def test_sponsor_singleton_behavior(self, app):
        """Test that only one sponsor can exist."""
        with app.app_context():
            # Clear existing sponsors
            Sponsor.query.delete()
            db.session.commit()
            
            # Create first sponsor
            sponsor1 = Sponsor.create_instance(
                name="First Org",
                email="first@org.com",
                crossref_member_id="1111"
            )
            assert sponsor1.id is not None
            
            # Try to create second sponsor - should fail
            with pytest.raises(IntegrityError):
                Sponsor.create_instance(
                    name="Second Org",
                    email="second@org.com",
                    crossref_member_id="2222"
                )

    def test_sponsor_get_instance(self, app):
        """Test getting the singleton sponsor instance."""
        with app.app_context():
            # Clear existing sponsors
            Sponsor.query.delete()
            db.session.commit()
            
            # Should return None when no sponsor exists
            assert Sponsor.get_instance() is None
            
            # Create sponsor
            created = Sponsor.create_instance(
                name="Test Org",
                email="test@org.com", 
                crossref_member_id="1234"
            )
            
            # Should return the created sponsor
            retrieved = Sponsor.get_instance()
            assert retrieved is not None
            assert retrieved.id == created.id
            assert retrieved.email == created.email

    def test_sponsor_email_validation(self, app):
        """Test email format validation."""
        with app.app_context():
            # Clear existing sponsors
            Sponsor.query.delete()
            db.session.commit()
            
            # Valid email should work
            sponsor = Sponsor.create_instance(
                name="Test Org",
                email="valid@example.com",
                crossref_member_id="1234"
            )
            assert sponsor.email == "valid@example.com"
            
            # Clean up for next test
            Sponsor.query.delete()
            db.session.commit()
            
            # Invalid email should fail
            with pytest.raises(ValueError, match="Invalid email format"):
                Sponsor.create_instance(
                    name="Test Org",
                    email="invalid-email",
                    crossref_member_id="1234"
                )

    def test_sponsor_crossref_validation(self, app):
        """Test Crossref member ID validation."""
        with app.app_context():
            # Clear existing sponsors
            Sponsor.query.delete()
            db.session.commit()
            
            # Valid member ID should work
            sponsor = Sponsor.create_instance(
                name="Test Org",
                email="test@org.com",
                crossref_member_id="ABC123"
            )
            assert sponsor.crossref_member_id == "ABC123"
            
            # Clean up for next test
            Sponsor.query.delete()
            db.session.commit()
            
            # Empty member ID should fail
            with pytest.raises(ValueError, match="Invalid Crossref member ID format"):
                Sponsor.create_instance(
                    name="Test Org",
                    email="test@org.com",
                    crossref_member_id=""
                )

    def test_sponsor_update_details(self, app):
        """Test updating sponsor details."""
        with app.app_context():
            # Clear existing sponsors
            Sponsor.query.delete()
            db.session.commit()
            
            sponsor = Sponsor.create_instance(
                name="Original Name",
                email="original@org.com",
                crossref_member_id="1234"
            )
            original_id = sponsor.id
            
            # Update details
            sponsor.update_details(
                name="Updated Name",
                email="updated@org.com",
                crossref_member_id="5678"
            )
            
            # Verify updates
            assert sponsor.id == original_id  # ID should not change
            assert sponsor.name == "Updated Name"
            assert sponsor.email == "updated@org.com"
            assert sponsor.crossref_member_id == "5678"

    def test_sponsor_activation_deactivation(self, app):
        """Test sponsor activation/deactivation."""
        with app.app_context():
            # Clear existing sponsors
            Sponsor.query.delete()
            db.session.commit()
            
            sponsor = Sponsor.create_instance(
                name="Test Org",
                email="test@org.com",
                crossref_member_id="1234"
            )
            
            # Should be active by default
            assert sponsor.is_active is True
            
            # Deactivate
            sponsor.deactivate()
            assert sponsor.is_active is False
            
            # Reactivate
            sponsor.activate()
            assert sponsor.is_active is True


class TestUserModel:
    """Test cases for User model."""

    def test_user_creation(self, app):
        """Test basic user creation."""
        with app.app_context():
            user = User.create_user(
                email="test@example.com",
                password="password123",
                full_name="Test User",
                role="admin"
            )
            
            assert user.id is not None
            assert user.email == "test@example.com"
            assert user.full_name == "Test User"
            assert user.role == "admin"
            assert user.password_hash is not None
            assert user.password_hash != "password123"  # Should be hashed
            assert user.created_at is not None
            assert user.updated_at is not None

    def test_user_email_uniqueness(self, app):
        """Test that user emails must be unique."""
        with app.app_context():
            # Create first user
            user1 = User.create_user(
                email="test@example.com",
                password="password123",
                full_name="Test User 1"
            )
            assert user1.id is not None
            
            # Try to create second user with same email - should fail
            with pytest.raises(IntegrityError):
                User.create_user(
                    email="test@example.com",
                    password="password456",
                    full_name="Test User 2"
                )

    def test_user_password_hashing(self, app):
        """Test password hashing and verification."""
        with app.app_context():
            user = User.create_user(
                email="test@example.com",
                password="mypassword123",
                full_name="Test User"
            )
            
            # Password should be hashed
            assert user.password_hash != "mypassword123"
            assert len(user.password_hash) > 50  # Hashed passwords are long
            
            # Should be able to verify correct password
            assert user.check_password("mypassword123") is True
            
            # Should reject incorrect password
            assert user.check_password("wrongpassword") is False

    def test_user_role_validation(self, app):
        """Test user role validation."""
        with app.app_context():
            # Valid roles should work
            admin_user = User.create_user(
                email="admin@example.com",
                password="password123",
                full_name="Admin User",
                role="admin"
            )
            assert admin_user.role == "admin"
            assert admin_user.is_admin() is True
            assert admin_user.is_operator() is False
            
            operator_user = User.create_user(
                email="operator@example.com",
                password="password123",
                full_name="Operator User",
                role="operator"
            )
            assert operator_user.role == "operator"
            assert operator_user.is_admin() is False
            assert operator_user.is_operator() is True
            
            # Invalid role should fail
            with pytest.raises(ValueError, match="Role must be 'admin' or 'operator'"):
                User.create_user(
                    email="invalid@example.com",
                    password="password123",
                    full_name="Invalid User",
                    role="invalid_role"
                )

    def test_user_email_validation(self, app):
        """Test email format validation."""
        with app.app_context():
            # Valid email should work
            user = User.create_user(
                email="valid@example.com",
                password="password123",
                full_name="Valid User"
            )
            assert user.email == "valid@example.com"
            
            # Invalid email should fail
            with pytest.raises(ValueError, match="Invalid email format"):
                User.create_user(
                    email="invalid-email",
                    password="password123",
                    full_name="Invalid User"
                )

    def test_user_password_validation(self, app):
        """Test password length validation."""
        with app.app_context():
            # Short password should fail
            with pytest.raises(ValueError, match="Password must be at least 6 characters long"):
                User.create_user(
                    email="test@example.com",
                    password="123",
                    full_name="Test User"
                )
            
            # Empty password should fail
            with pytest.raises(ValueError, match="Password must be at least 6 characters long"):
                User.create_user(
                    email="test@example.com",
                    password="",
                    full_name="Test User"
                )

    def test_user_get_by_email(self, app):
        """Test getting user by email."""
        with app.app_context():
            # Create user
            created_user = User.create_user(
                email="findme@example.com",
                password="password123",
                full_name="Find Me"
            )
            
            # Find by email
            found_user = User.get_by_email("findme@example.com")
            assert found_user is not None
            assert found_user.id == created_user.id
            assert found_user.email == created_user.email
            
            # Should be case insensitive
            found_user_caps = User.get_by_email("FINDME@EXAMPLE.COM")
            assert found_user_caps is not None
            assert found_user_caps.id == created_user.id
            
            # Non-existent email should return None
            not_found = User.get_by_email("notfound@example.com")
            assert not_found is None

    def test_user_last_login_update(self, app):
        """Test updating last login timestamp."""
        with app.app_context():
            user = User.create_user(
                email="test@example.com",
                password="password123",
                full_name="Test User"
            )
            
            # Initially no last login
            assert user.last_login is None
            
            # Update last login
            user.update_last_login()
            assert user.last_login is not None
            assert isinstance(user.last_login, datetime)

    def test_user_role_queries(self, app):
        """Test role-based queries."""
        with app.app_context():
            # Create users with different roles
            admin1 = User.create_user(
                email="admin1@example.com",
                password="password123",
                full_name="Admin One",
                role="admin"
            )
            admin2 = User.create_user(
                email="admin2@example.com",
                password="password123",
                full_name="Admin Two",
                role="admin"
            )
            operator1 = User.create_user(
                email="operator1@example.com",
                password="password123",
                full_name="Operator One",
                role="operator"
            )
            
            # Test role queries
            admins = User.get_admins()
            assert len(admins) >= 2
            admin_emails = [u.email for u in admins]
            assert "admin1@example.com" in admin_emails
            assert "admin2@example.com" in admin_emails
            
            operators = User.get_operators()
            assert len(operators) >= 1
            operator_emails = [u.email for u in operators]
            assert "operator1@example.com" in operator_emails

    def test_flask_login_integration(self, app):
        """Test Flask-Login UserMixin integration."""
        with app.app_context():
            user = User.create_user(
                email="test@example.com",
                password="password123",
                full_name="Test User"
            )
            
            # Test Flask-Login required properties
            assert user.is_authenticated is True
            assert user.is_active is True
            assert user.is_anonymous is False
            assert user.get_id() == str(user.id)