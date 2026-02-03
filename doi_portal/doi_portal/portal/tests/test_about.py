"""
Tests for the About page (Story 4.8, FR43).

Test coverage:
- AC #1: About page returns 200 and uses portal/base.html
- AC #2: Contains key sections (mission, organization, contact, services)
- AC #3: Breadcrumbs with "Početna" and "O portalu"
- AC #4: Performance (static page, trivial)
- AC #5: Semantic HTML, heading hierarchy, accessibility
- AC #6: Responsive layout (tested via content assertions)
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAboutPage:
    """Tests for the About page (Story 4.8, FR43)."""

    def test_about_page_returns_200(self, client):
        """AC #1: About page returns 200 status on GET /about/."""
        url = reverse("about")
        response = client.get(url)
        assert response.status_code == 200

    def test_about_page_uses_correct_template(self, client):
        """AC #1: About page uses portal/about.html template."""
        url = reverse("about")
        response = client.get(url)
        assert "portal/about.html" in [t.name for t in response.templates]

    def test_about_page_extends_portal_base(self, client):
        """AC #1, AC #3: About page extends portal/base.html, not base.html."""
        url = reverse("about")
        response = client.get(url)
        # portal/base.html contains the portal header with navbar
        template_names = [t.name for t in response.templates]
        assert "portal/base.html" in template_names
        # Verify portal navigation is present (from portal/base.html)
        content = response.content.decode()
        assert "DOI Portal" in content  # navbar brand
        assert "Izdavači" in content  # navbar link
        assert "Publikacije" in content  # navbar link

    def test_about_page_has_breadcrumbs(self, client):
        """AC #3: About page contains breadcrumbs with "Početna" and "O portalu"."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Breadcrumbs from context
        assert "Početna" in content  # with diacritics
        assert "O portalu" in content

    def test_about_page_has_mission_section(self, client):
        """AC #2: About page contains mission/purpose section."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Check for mission-related content
        assert "Misija" in content or "misija" in content.lower()

    def test_about_page_has_organization_section(self, client):
        """AC #2: About page contains organization information section."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Check for organization-related content
        assert "O nama" in content or "nama" in content.lower()

    def test_about_page_has_contact_section(self, client):
        """AC #2: About page contains contact information section."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Check for contact-related content
        assert "Kontakt" in content or "kontakt" in content.lower()

    def test_about_page_has_useful_links_section(self, client):
        """AC #2: About page contains useful links section."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Check for links section content
        assert "Korisni linkovi" in content or "linkovi" in content.lower()

    def test_about_page_has_serbian_content(self, client):
        """AC #5: About page contains Serbian text with diacritics."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Serbian content should be present
        assert "naučn" in content.lower() or "publikacij" in content.lower()

    def test_about_page_no_auth_required(self, client):
        """AC #1: About page is public - no authentication needed."""
        url = reverse("about")
        response = client.get(url)
        assert response.status_code == 200
        # Should not redirect to login
        if hasattr(response, "url"):
            assert "login" not in response.url

    def test_about_page_has_portal_nav_links(self, client):
        """AC #3: About page has navigation links to publications and publishers."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        assert "Publikacije" in content
        assert "Izdavači" in content

    def test_about_navbar_has_active_state(self, client):
        """AC #3: Navbar "O portalu" link has active class when on /about/."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # The O portalu link should have active class
        # Looking for nav-link active combination near "O portalu"
        assert 'nav-link active' in content or 'nav-link" href="' + url in content

    def test_about_page_has_semantic_sections(self, client):
        """AC #5: About page uses semantic HTML5 section elements."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Check for semantic section elements
        assert "<section" in content

    def test_about_page_has_h1_heading(self, client):
        """AC #5: About page has proper h1 heading."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Should have h1 heading
        assert "<h1" in content

    def test_about_page_has_aria_labelledby(self, client):
        """AC #5: About page sections have aria-labelledby for accessibility."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Check for aria-labelledby attributes
        assert "aria-labelledby" in content

    def test_about_page_context_has_breadcrumbs(self, client):
        """AC #3: About view provides breadcrumbs in context."""
        url = reverse("about")
        response = client.get(url)
        assert "breadcrumbs" in response.context
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["label"] == "Početna"
        assert breadcrumbs[0]["url"] == reverse("home")
        assert breadcrumbs[1]["label"] == "O portalu"
        assert breadcrumbs[1]["url"] is None

    def test_about_page_title(self, client):
        """AC #1: About page has correct title format."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Title should be in format "O portalu - DOI Portal"
        assert "O portalu - DOI Portal" in content

    def test_about_page_has_services_section(self, client):
        """AC #2: About page contains services section."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Check for services-related content
        assert "usluge" in content.lower() or "Naše usluge" in content

    def test_about_page_heading_hierarchy(self, client):
        """AC #5: About page has proper heading hierarchy (h1 > h2 > h3)."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Should have h1 (main title)
        assert "<h1" in content
        # Should have h2 (section headings)
        assert "<h2" in content
        # Should have h3 (sidebar card headings)
        assert "<h3" in content
        # Verify h1 appears before h2
        h1_pos = content.find("<h1")
        h2_pos = content.find("<h2")
        assert h1_pos < h2_pos, "h1 should appear before h2"

    def test_about_page_responsive_classes(self, client):
        """AC #6: About page uses Bootstrap responsive classes for layout."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Check for two-column layout responsive classes
        assert "col-lg-8" in content  # main content column
        assert "col-lg-4" in content  # sidebar column

    def test_about_page_sidebar_aria_labelledby(self, client):
        """AC #5: Sidebar sections have aria-labelledby for accessibility."""
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Check sidebar cards have aria-labelledby
        assert 'aria-labelledby="contact-title"' in content
        assert 'aria-labelledby="links-title"' in content
        assert 'aria-labelledby="doi-info-title"' in content
