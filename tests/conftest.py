"""
Pytest configuration and fixtures for DOI Management System tests
"""

import pytest
import tempfile
import os
from app import create_app, db


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
