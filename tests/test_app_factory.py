"""
Tests for Flask application factory and basic application setup
"""

import pytest
from app import create_app


def test_config():
    """Test that the app factory works with different configurations."""
    # Test development config
    app = create_app("development")
    assert app.config["DEBUG"] is True
    assert app.config["TESTING"] is False

    # Test testing config
    app = create_app("testing")
    assert app.config["TESTING"] is True
    assert app.config["DEBUG"] is False
    assert app.config["WTF_CSRF_ENABLED"] is False


def test_app_creation():
    """Test that the application is created successfully."""
    app = create_app("testing")
    assert app is not None
    assert app.config["TESTING"] is True


def test_blueprints_registered(app):
    """Test that all blueprints are properly registered."""
    blueprint_names = [bp.name for bp in app.blueprints.values()]

    expected_blueprints = ["main", "auth", "members", "publications", "drafts"]
    for blueprint in expected_blueprints:
        assert blueprint in blueprint_names


def test_extensions_initialized(app):
    """Test that Flask extensions are properly initialized."""
    # Check that extensions are available in app
    from app import db, migrate, login_manager, cache, csrf

    # These should not be None after app creation
    assert db is not None
    assert migrate is not None
    assert login_manager is not None
    assert cache is not None
    assert csrf is not None
