"""
Tests for blueprint routes and basic functionality
"""

import pytest


def test_main_index_route(client):
    """Test the main index route redirects to login."""
    response = client.get("/")
    assert response.status_code == 302  # Redirect to login
    assert "/auth/login" in response.location


def test_dashboard_route_requires_login(client):
    """Test that dashboard route requires login."""
    response = client.get("/dashboard")
    assert response.status_code == 302  # Redirect to login
    assert "/auth/login" in response.location


def test_auth_login_route(client):
    """Test the auth login route."""
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert "Prijava".encode("utf-8") in response.data


def test_auth_register_route(client):
    """Test the auth register route."""
    response = client.get("/auth/register")
    assert response.status_code == 200
    assert "Registracija".encode("utf-8") in response.data


def test_members_index_route_requires_login(client):
    """Test that members index route requires login."""
    response = client.get("/members/")
    assert response.status_code == 302  # Redirect to login
    assert "/auth/login" in response.location


def test_publications_index_route_requires_login(client):
    """Test that publications index route requires login."""
    response = client.get("/publications/")
    assert response.status_code == 302  # Redirect to login
    assert "/auth/login" in response.location


def test_drafts_index_route_requires_login(client):
    """Test that drafts index route requires login."""
    response = client.get("/drafts/")
    assert response.status_code == 302  # Redirect to login
    assert "/auth/login" in response.location


def test_404_error(client):
    """Test 404 error handling."""
    response = client.get("/nonexistent-page")
    assert response.status_code == 404
    assert "Stranica nije pronađena".encode("utf-8") in response.data


def test_login_post_with_invalid_credentials(client):
    """Test login POST route with invalid credentials."""
    response = client.post(
        "/auth/login", data={"email": "test@example.com", "password": "password"}
    )
    # Should return 200 with error message since credentials are invalid
    assert response.status_code == 200
    assert "Neispravni podaci za prijavu.".encode("utf-8") in response.data


def test_register_post_placeholder(client):
    """Test register POST route placeholder."""
    response = client.post(
        "/auth/register",
        data={
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "password",
            "password_confirm": "password",
        },
    )
    # Should redirect to login page since registration isn't implemented yet
    assert response.status_code == 302
