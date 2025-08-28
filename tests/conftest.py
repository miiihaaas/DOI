"""
Pytest configuration and fixtures for DOI Management System tests
"""

import pytest
import tempfile
import os
from app import create_app, db
from app.models.user import User
from app.models.sponsor import Sponsor
from app.models.member import Member


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean up environment variables between tests to prevent isolation issues."""
    # Store original environment state
    original_env = dict(os.environ)
    
    # Keep essential Windows environment variables
    essential_vars = {
        'PATH', 'PATHEXT', 'SYSTEMROOT', 'USERNAME', 'USERPROFILE', 
        'TEMP', 'TMP', 'COMPUTERNAME', 'PROCESSOR_ARCHITECTURE'
    }
    
    yield  # Run the test
    
    # Restore original environment, but be careful with essential variables
    for key in list(os.environ.keys()):
        if key not in essential_vars and key not in original_env:
            # Remove variables that were added during test
            os.environ.pop(key, None)
        elif key in original_env:
            # Restore original values
            os.environ[key] = original_env[key]


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()

    # Create app with testing configuration
    app = create_app("testing")
    app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        }
    )

    # Create application context
    with app.app_context():
        # Create all database tables
        db.create_all()
        yield app
        # Clean up database tables
        db.drop_all()

    # Clean up temporary database file
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner for the Flask application."""
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """Create a database session for tests."""
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture
def sponsor(app, db_session):
    """Create a singleton sponsor for tests."""
    with app.app_context():
        sponsor = Sponsor.create_instance(
            name='Test Sponsor Organization',
            email='sponsor@test.com',
            crossref_member_id='TEST001',
            is_active=True
        )
        db_session.commit()
        yield sponsor


@pytest.fixture
def auth_user(app, db_session, sponsor):
    """Create an authenticated user for tests."""
    with app.app_context():
        user = User.create_user(
            email='test@example.com',
            password='password123',
            full_name='Test User',
            role='operator'
        )
        db_session.commit()
        yield user


@pytest.fixture
def admin_user(app, db_session, sponsor):
    """Create an admin user for tests."""
    with app.app_context():
        user = User.create_user(
            email='admin@example.com',
            password='password123',
            full_name='Admin User',
            role='admin'
        )
        db_session.commit()
        yield user


@pytest.fixture
def test_member(app, db_session, sponsor):
    """Create a test member for tests."""
    with app.app_context():
        member = Member.create_member(
            sponsor_id=sponsor.id,
            name='Test Member Organization',
            institution='Test Institution',
            contact_email='member@test.com',
            website_url='https://www.testmember.com',
            billing_address='Test Address 123\n11000 Belgrade\nSerbia',
            pib='123456789',
            matični_broj='12345678',
            jmbg_lk='1234567890123',
            šifra_delatnosti='7220',
            telefon='+381 11 123-4567',
            osoba_za_kontakt='Test Contact Person',
            iban='RS35260005601001611379',
            naziv_banke='Test Bank',
            swift_bic='TESTRS22',
            pdv_status='obveznik_pdv',
            država_obveznika='Srbija',
            is_active=True
        )
        db_session.commit()
        yield member


@pytest.fixture
def login_user(client):
    """Helper fixture to log in users during tests."""
    def _login_user(user):
        with client.session_transaction() as sess:
            sess['_user_id'] = user.get_id()
            sess['_fresh'] = True
    return _login_user
