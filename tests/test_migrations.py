"""
Test database migrations.
"""

import pytest
from flask import Flask
from app import create_app, db
from app.models import Sponsor, User


class TestMigrations:
    """Test database migration functionality."""

    def test_database_connection(self, app):
        """Test that database connection works."""
        with app.app_context():
            # Basic connection test
            result = db.session.execute(db.text("SELECT 1"))
            assert result.scalar() == 1

    def test_models_work_with_database(self, app):
        """Test that models work properly with the database."""
        with app.app_context():
            # Test Sponsor model
            sponsor = Sponsor.create_instance(
                name="Migration Test Org",
                email="migration@test.com",
                crossref_member_id="MT123"
            )
            assert sponsor.id is not None
            
            # Test User model
            user = User.create_user(
                email="migrationuser@test.com",
                password="password123",
                full_name="Migration User",
                role="admin"
            )
            assert user.id is not None
            
            # Test relationships and queries work
            retrieved_sponsor = Sponsor.get_instance()
            assert retrieved_sponsor.id == sponsor.id
            
            retrieved_user = User.get_by_email("migrationuser@test.com")
            assert retrieved_user.id == user.id

    def test_sponsor_constraints(self, app):
        """Test that database constraints work for Sponsor model."""
        with app.app_context():
            # Create first sponsor
            sponsor1 = Sponsor.create_instance(
                name="First Sponsor",
                email="first@test.com",
                crossref_member_id="FS123"
            )
            assert sponsor1.id is not None
            
            # Try to create another sponsor - should fail due to singleton constraint
            with pytest.raises(Exception):  # IntegrityError or similar
                Sponsor.create_instance(
                    name="Second Sponsor",
                    email="second@test.com",
                    crossref_member_id="SS123"
                )

    def test_user_constraints(self, app):
        """Test that database constraints work for User model."""
        with app.app_context():
            # Create first user
            user1 = User.create_user(
                email="constraint@test.com",
                password="password123",
                full_name="Constraint User 1"
            )
            assert user1.id is not None
            
            # Try to create user with same email - should fail
            with pytest.raises(Exception):  # IntegrityError
                User.create_user(
                    email="constraint@test.com",
                    password="password456",
                    full_name="Constraint User 2"
                )

    def test_indexes_work(self, app):
        """Test that database indexes are working."""
        with app.app_context():
            # Create test data
            sponsor = Sponsor.create_instance(
                name="Index Test Org",
                email="index@test.com",
                crossref_member_id="IT123"
            )
            
            user = User.create_user(
                email="indexuser@test.com",
                password="password123",
                full_name="Index User",
                role="operator"
            )
            
            # Test indexed queries work efficiently
            found_sponsor = Sponsor.query.filter_by(email="index@test.com").first()
            assert found_sponsor.id == sponsor.id
            
            found_user = User.query.filter_by(email="indexuser@test.com").first()
            assert found_user.id == user.id
            
            role_users = User.query.filter_by(role="operator").all()
            assert len(role_users) >= 1
            assert user.id in [u.id for u in role_users]

    def test_enum_constraints(self, app):
        """Test that enum constraints work for User role."""
        with app.app_context():
            # Valid roles should work
            admin_user = User.create_user(
                email="admin@enum.test",
                password="password123",
                full_name="Admin User",
                role="admin"
            )
            assert admin_user.role == "admin"
            
            operator_user = User.create_user(
                email="operator@enum.test",
                password="password123",
                full_name="Operator User",
                role="operator"
            )
            assert operator_user.role == "operator"