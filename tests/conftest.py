"""
Pytest configuration and fixtures for DOI Management System tests
"""

import pytest
import tempfile
import os
from app import create_app, db


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
