"""
Tests for static files and templates
"""

import pytest
import os


def test_static_css_exists():
    """Test that main CSS file exists."""
    css_path = os.path.join("app", "static", "css", "main.css")
    assert os.path.exists(css_path)


def test_static_js_exists():
    """Test that main JS file exists."""
    js_path = os.path.join("app", "static", "js", "main.js")
    assert os.path.exists(js_path)


def test_static_css_accessible(client):
    """Test that CSS file is accessible via Flask."""
    response = client.get("/static/css/main.css")
    assert response.status_code == 200
    assert response.content_type == "text/css; charset=utf-8"


def test_static_js_accessible(client):
    """Test that JS file is accessible via Flask."""
    response = client.get("/static/js/main.js")
    assert response.status_code == 200
    assert "javascript" in response.content_type


def test_template_inheritance(client):
    """Test that template inheritance works."""
    response = client.get("/auth/login")
    assert response.status_code == 200

    # Check for elements from base template
    assert b"<!DOCTYPE html>" in response.data
    assert b"Bootstrap" in response.data or b"bootstrap" in response.data
    assert b"DOI Management" in response.data


def test_responsive_layout(client):
    """Test that responsive layout elements are present."""
    response = client.get("/auth/login")
    assert response.status_code == 200

    # Check for Bootstrap responsive classes
    assert b"container" in response.data
    assert b"navbar" in response.data
    assert b"viewport" in response.data
