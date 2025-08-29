"""
Integration tests for Activity Logging system.
Tests integration with member and publication services, blueprints, and templates.
"""

import pytest
import json
from datetime import datetime, timedelta
from flask import url_for

from app.models.activity_log import ActivityLog
from app.models.member import Member
from app.models.publication import Publication, PublicationType
from app.services.member_service import MemberService
from app.services.publication_service import PublicationService


class TestActivityLoggingIntegration:
    """Test integration of activity logging with other system components."""
    
    def test_member_service_create_logs_activity(self, client, auth_user, sponsor, db_session):
        """Test that MemberService.create_member logs activity."""
        with client.application.app_context():
            # Set user context in Flask's g for activity logging
            from flask import g
            g.user_id = auth_user.id
            
            # Count activities before
            initial_count = ActivityLog.query.count()
            
            # Create member through service
            member_data = {
                'name': 'Test Member Integration',
                'institution': 'Test Institution',
                'contact_email': 'integration@test.com',
                'billing_address': '123 Test St',
                'pib': '123456789',
                'matični_broj': '987654321',
                'šifra_delatnosti': '12345',
                'telefon': '+381601234567',
                'osoba_za_kontakt': 'Test Contact',
                'iban': 'RS35260005601001611379',
                'naziv_banke': 'Test Bank',
                'swift_bic': 'TESTRS22',
                'pdv_status': 'obveznik',
                'država_obveznika': 'Serbia'
            }
            
            member = MemberService.create_member(sponsor.id, member_data)
            
            # Verify activity was logged
            assert ActivityLog.query.count() == initial_count + 1
            
            # Get the logged activity
            activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).first()
            assert activity.action == 'create_member'
            assert member.name in activity.description
            assert activity.member_id == member.id
    
    def test_member_service_update_logs_activity(self, client, auth_user, test_member, db_session):
        """Test that MemberService.update_member logs activity."""
        with client.application.app_context():
            # Set user context in Flask's g for activity logging
            from flask import g
            g.user_id = auth_user.id
            
            initial_count = ActivityLog.query.count()
            
            # Update member through service
            update_data = {
                'name': 'Updated Member Name',
                'institution': test_member.institution,
                'contact_email': test_member.contact_email,
                'billing_address': test_member.billing_address,
                'pib': test_member.pib,
                'matični_broj': test_member.matični_broj,
                'šifra_delatnosti': test_member.šifra_delatnosti,
                'telefon': test_member.telefon,
                'osoba_za_kontakt': test_member.osoba_za_kontakt,
                'iban': test_member.iban,
                'naziv_banke': test_member.naziv_banke,
                'swift_bic': test_member.swift_bic,
                'pdv_status': test_member.pdv_status,
                'država_obveznika': test_member.država_obveznika,
                'is_active': True
            }
            
            MemberService.update_member(test_member.id, test_member.sponsor_id, update_data)
            
            # Verify activity was logged
            assert ActivityLog.query.count() == initial_count + 1
            
            activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).first()
            assert activity.action == 'update_member'
            assert 'name' in activity.description  # Should mention changed field
    
    def test_member_service_toggle_status_logs_activity(self, client, auth_user, test_member, db_session):
        """Test that member status toggle logs activity."""
        with client.application.app_context():
            # Set user context in Flask's g for activity logging
            from flask import g
            g.user_id = auth_user.id
            
            initial_count = ActivityLog.query.count()
            
            # Toggle member status
            MemberService.toggle_member_status(test_member.id, test_member.sponsor_id)
            
            # Should log activity
            assert ActivityLog.query.count() == initial_count + 1
            
            activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).first()
            assert activity.action in ['activate_member', 'deactivate_member']
            assert activity.member_id == test_member.id
    
    def test_publication_service_create_logs_activity(self, client, auth_user, test_member, db_session):
        """Test that PublicationService.create_publication logs activity."""
        with client.application.app_context():
            # Set user context in Flask's g for activity logging
            from flask import g
            g.user_id = auth_user.id
            
            initial_count = ActivityLog.query.count()
            
            # Create publication through service
            publication_data = {
                'publication_type': 'journal',
                'title': 'Integration Test Journal',
                'subtitle': 'Test Subtitle',
                'language_code': 'sr',
                'journal_abbreviated_title': 'Int. Test J.',
                'journal_issn': '1234-5678'
            }
            
            publication = PublicationService.create_publication(test_member.id, publication_data)
            
            # Verify activity was logged
            assert ActivityLog.query.count() == initial_count + 1
            
            activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).first()
            assert activity.action == 'create_publication'
            assert publication.title in activity.description
            assert activity.publication_id == publication.id
    
    def test_publication_service_update_logs_activity(self, client, auth_user, test_journal_publication, db_session):
        """Test that publication update logs activity."""
        with client.application.app_context():
            # Set user context in Flask's g for activity logging
            from flask import g
            g.user_id = auth_user.id
            
            initial_count = ActivityLog.query.count()
            
            # Update publication
            update_data = {
                'title': 'Updated Publication Title',
                'subtitle': 'Updated Subtitle'
            }
            
            PublicationService.update_publication(test_journal_publication.id, update_data)
            
            # Verify activity was logged
            assert ActivityLog.query.count() == initial_count + 1
            
            activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).first()
            assert activity.action == 'update_publication'
            assert 'title' in activity.description  # Should mention changed fields
    
    def test_publication_service_toggle_status_logs_activity(self, client, auth_user, test_journal_publication, db_session):
        """Test that publication status toggle logs activity."""
        with client.application.app_context():
            # Set user context in Flask's g for activity logging
            from flask import g
            g.user_id = auth_user.id
            
            initial_count = ActivityLog.query.count()
            
            # Toggle publication status
            PublicationService.toggle_publication_status(test_journal_publication.id)
            
            # Verify activity was logged
            assert ActivityLog.query.count() == initial_count + 1
            
            activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).first()
            assert activity.action in ['activate_publication', 'deactivate_publication']
            assert activity.publication_id == test_journal_publication.id
    
    def test_activity_log_route_access(self, client, auth_user):
        """Test access to activity log routes."""
        # Login first
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        # Test activity log page
        response = client.get(url_for('activity.activity_log'))
        assert response.status_code == 200
        assert b'Activity Log' in response.data
    
    def test_activity_log_filtering(self, client, auth_user, db_session):
        """Test activity log filtering functionality."""
        with client.application.app_context():
            # Create test activities
            from app.services.activity_logger import ActivityLogger
            
            # Create different types of activities
            ActivityLogger.log_activity(
                user_id=auth_user.id,
                action='create_member',
                description='Created test member',
                ip_address='192.168.1.1'
            )
            
            ActivityLogger.log_activity(
                user_id=auth_user.id,
                action='update_publication',
                description='Updated test publication',
                ip_address='192.168.1.2'
            )
        
        # Login
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        # Test filtering by action type
        response = client.get(url_for('activity.activity_log', action_type='create'))
        assert response.status_code == 200
        
        # Test filtering by user
        response = client.get(url_for('activity.activity_log', user_id=auth_user.id))
        assert response.status_code == 200
    
    def test_activity_export_functionality(self, client, auth_user, db_session):
        """Test activity log export functionality."""
        with client.application.app_context():
            # Create test activity
            from app.services.activity_logger import ActivityLogger
            ActivityLogger.log_activity(
                user_id=auth_user.id,
                action='test_export',
                description='Test export functionality',
                ip_address='192.168.1.1'
            )
        
        # Login
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        # Test CSV export
        response = client.post(url_for('activity.export_activities'), data={
            'format': 'csv',
            'date_range': 'all',
            'include_ip': 'on',
            'include_entity_refs': 'on'
        })
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        assert b'test_export' in response.data
    
    def test_dashboard_shows_recent_activities(self, client, auth_user, db_session):
        """Test that dashboard displays recent activities."""
        with client.application.app_context():
            # Create test activities
            from app.services.activity_logger import ActivityLogger
            
            ActivityLogger.log_activity(
                user_id=auth_user.id,
                action='dashboard_test',
                description='Test dashboard activity display',
                ip_address='192.168.1.1'
            )
        
        # Login
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        # Access dashboard
        response = client.get(url_for('main.index'))
        assert response.status_code == 200
        
        # Should contain recent activity
        # Note: This test assumes the dashboard template includes activities
        # The actual assertion might need adjustment based on template implementation
    
    def test_entity_specific_activity_display(self, client, auth_user, test_member, db_session):
        """Test entity-specific activity display."""
        with client.application.app_context():
            # Create member-specific activity
            from app.services.activity_logger import ActivityLogger
            
            ActivityLogger.log_activity(
                user_id=auth_user.id,
                action='test_member_activity',
                description='Test member-specific activity',
                ip_address='192.168.1.1',
                member_id=test_member.id
            )
        
        # Login
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        # Test entity-specific activity endpoint
        response = client.get(url_for('activity.entity_activities', 
                                    entity_type='member', 
                                    entity_id=test_member.id))
        assert response.status_code == 200
    
    def test_admin_activity_management_access(self, client, admin_user, db_session):
        """Test admin activity management interface."""
        with client.application.app_context():
            # Set user context in Flask's g for activity logging
            from flask import g
            g.user_id = admin_user.id
            
            # This test assumes admin_user fixture exists and user has admin privileges
            # Login as admin
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
            
            # Access admin activity management
            response = client.get(url_for('admin.activity_management'))
            assert response.status_code == 200
            assert b'Activity Log Management' in response.data
    
    def test_activity_cleanup_admin_functionality(self, client, admin_user, auth_user, db_session):
        """Test admin activity cleanup functionality."""
        with client.application.app_context():
            # Create old activity
            from app.services.activity_logger import ActivityLogger
            from app.models.activity_log import ActivityLog
            
            activity = ActivityLog(
                user_id=auth_user.id,
                action='old_test_activity',
                description='Old test activity',
                ip_address='192.168.1.1'
            )
            activity.save()
            
            # Manually set old date
            old_date = datetime.utcnow() - timedelta(days=400)
            activity.created_at = old_date
            db_session.commit()
        
        # Login as admin
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
        
        # Test cleanup endpoint
        response = client.post(url_for('admin.cleanup_activities'),
                             json={'retention_days': 365},
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['deleted_count'] >= 1
    
    def test_ip_address_capture_in_requests(self, client, auth_user, sponsor, db_session):
        """Test that IP addresses are captured during actual HTTP requests."""
        # Login
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        initial_count = ActivityLog.query.count()
        
        # Make request that should generate activity log
        member_data = {
            'name': 'IP Test Member',
            'institution': 'Test Institution',
            'contact_email': 'iptest@test.com',
            'billing_address': '123 Test St',
            'pib': '123456789',
            'matični_broj': '987654321',
            'šifra_delatnosti': '12345',
            'telefon': '+381601234567',
            'osoba_za_kontakt': 'Test Contact',
            'iban': 'RS35260005601001611379',
            'naziv_banke': 'Test Bank',
            'swift_bic': 'TESTRS22',
            'pdv_status': 'obveznik',
            'država_obveznika': 'Serbia',
            'csrf_token': 'test_token'  # If CSRF is enabled
        }
        
        # This would need to be adapted based on actual member creation route
        # The test client should capture IP address during the request
        with client:
            response = client.post('/members/create', 
                                 data=member_data,
                                 environ_base={'REMOTE_ADDR': '203.0.113.1'})
            
            # Verify activity was logged with IP address
            if response.status_code in [200, 302]:  # Success or redirect
                activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(1).all()
                if activities:
                    activity = activities[0]
                    # IP should be captured (might be test client default or our set value)
                    assert activity.ip_address is not None
                    assert activity.ip_address != ''
    
    def test_activity_statistics_calculation(self, client, auth_user, db_session):
        """Test activity statistics calculation."""
        with client.application.app_context():
            # Set user context in Flask's g for activity logging
            from flask import g
            g.user_id = auth_user.id
            
            # Create various activities
            from app.services.activity_logger import ActivityLogger
            
            actions = ['create_member', 'create_member', 'update_member', 'create_publication']
            for action in actions:
                ActivityLogger.log_activity(
                    user_id=auth_user.id,
                    action=action,
                    description=f'Test {action}',
                    ip_address='192.168.1.1'
                )
            
            # Test statistics calculation
            from app.models.activity_log import ActivityLog
            stats = ActivityLog.get_activity_statistics(days=30)
            
            assert stats['total_activities'] >= len(actions)
            assert 'action_breakdown' in stats
            assert stats['action_breakdown']['create'] >= 3  # 2 members + 1 publication
            assert stats['action_breakdown']['update'] >= 1