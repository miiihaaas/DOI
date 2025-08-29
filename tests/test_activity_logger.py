"""
Unit tests for ActivityLogger service layer.
Tests activity logging functionality, IP capture, and context handling.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from flask import g
from datetime import datetime

from app.services.activity_logger import ActivityLogger
from app.models.activity_log import ActivityLog


class TestActivityLoggerService:
    """Test ActivityLogger service functionality."""
    
    def test_log_activity_basic(self, app, db_session, auth_user):
        """Test basic activity logging."""
        with app.app_context():
            # Log an activity
            activity = ActivityLogger.log_activity(
                user_id=auth_user.id,
                action='test_action',
                description='Test logging activity',
                ip_address='192.168.1.1'
            )
            
            # Verify activity was created
            assert activity is not None
            assert activity.user_id == auth_user.id
            assert activity.action == 'test_action'
            assert activity.description == 'Test logging activity'
            assert activity.ip_address == '192.168.1.1'
            
            # Verify it's in database
            db_activity = ActivityLog.query.filter_by(id=activity.id).first()
            assert db_activity is not None
    
    def test_log_activity_with_entity_references(self, app, db_session, auth_user, test_member, test_journal_publication):
        """Test logging activity with entity references."""
        with app.app_context():
            activity = ActivityLogger.log_activity(
                user_id=auth_user.id,
                action='update_member',
                description='Updated member info',
                ip_address='10.0.0.1',
                member_id=test_member.id,
                publication_id=test_journal_publication.id
            )
            
            assert activity.member_id == test_member.id
            assert activity.publication_id == test_journal_publication.id
    
    def test_log_activity_auto_ip_detection(self, app, db_session, auth_user):
        """Test automatic IP address detection."""
        with app.app_context():
            with patch('app.services.activity_logger.has_request_context') as mock_has_context, \
                 patch('app.services.activity_logger.request') as mock_request:
                
                # Mock request context availability and Flask request with IP
                mock_has_context.return_value = True
                
                # Create proper mock request object
                mock_request.headers = Mock()
                mock_request.headers.get = Mock(return_value=None)
                mock_request.remote_addr = '203.0.113.1'
                
                activity = ActivityLogger.log_activity(
                    user_id=auth_user.id,
                    action='test_auto_ip',
                    description='Test auto IP detection'
                    # No ip_address provided - should auto-detect
                )
                
                assert activity.ip_address == '203.0.113.1'
    
    def test_log_activity_forwarded_ip_detection(self, app, db_session, auth_user):
        """Test detection of forwarded IP addresses (proxy scenarios)."""
        with app.app_context():
            with patch('app.services.activity_logger.has_request_context') as mock_has_context, \
                 patch('app.services.activity_logger.request') as mock_request:
                
                # Mock request context availability and Flask request with X-Forwarded-For header
                mock_has_context.return_value = True
                
                # Setup mock headers with proper side_effect
                mock_request.headers = Mock()
                mock_headers = {
                    'X-Forwarded-For': '198.51.100.1, 203.0.113.1',
                    'X-Real-IP': None
                }
                mock_request.headers.get.side_effect = lambda header: mock_headers.get(header)
                mock_request.remote_addr = '10.0.0.1'
                
                activity = ActivityLogger.log_activity(
                    user_id=auth_user.id,
                    action='test_forwarded_ip',
                    description='Test forwarded IP detection'
                )
                
                # Should use the first IP from X-Forwarded-For
                assert activity.ip_address == '198.51.100.1'
    
    def test_log_activity_real_ip_header(self, app, db_session, auth_user):
        """Test detection using X-Real-IP header."""
        with app.app_context():
            with patch('app.services.activity_logger.has_request_context') as mock_has_context, \
                 patch('app.services.activity_logger.request') as mock_request:
                
                # Mock request context availability and Flask request
                mock_has_context.return_value = True
                
                # Setup mock headers with proper side_effect
                mock_request.headers = Mock()
                mock_headers = {
                    'X-Forwarded-For': None,
                    'X-Real-IP': '198.51.100.2'
                }
                mock_request.headers.get.side_effect = lambda header: mock_headers.get(header)
                mock_request.remote_addr = '10.0.0.1'
                
                activity = ActivityLogger.log_activity(
                    user_id=auth_user.id,
                    action='test_real_ip',
                    description='Test X-Real-IP detection'
                )
                
                assert activity.ip_address == '198.51.100.2'
    
    def test_log_activity_failure_handling(self, app, db_session):
        """Test that logging failures don't break main operations."""
        with app.app_context():
            with patch('app.services.activity_logger.has_request_context') as mock_has_context:
                # Mock no request context to avoid IP detection issues
                mock_has_context.return_value = False
                
                # Force a database constraint error by creating activity with invalid foreign key
                with patch('app.services.activity_logger.db') as mock_db:
                    mock_db.session.add.side_effect = Exception("Database error")
                    
                    # Try to log activity - should handle exception gracefully
                    activity = ActivityLogger.log_activity(
                        user_id=1,  # Valid user ID
                        action='test_failure',
                        description='Test failure handling',
                        ip_address='192.168.1.1'
                    )
                    
                    # Should return None without raising exception
                    assert activity is None
    
    def test_log_member_action_create(self, app, db_session, auth_user, test_member):
        """Test logging member creation action."""
        with app.app_context():
            with patch.object(ActivityLogger, '_get_current_user_id', return_value=auth_user.id):
                activity = ActivityLogger.log_member_action(
                    action_type='create',
                    member_obj=test_member
                )
                
                assert activity is not None
                assert activity.action == 'create_member'
                assert test_member.name in activity.description
                assert 'Created member' in activity.description
                assert activity.member_id == test_member.id
    
    def test_log_member_action_update_with_changes(self, app, db_session, auth_user, test_member):
        """Test logging member update with change tracking."""
        with app.app_context():
            changes = {'name': 'New Name', 'email': 'new@example.com'}
            
            with patch.object(ActivityLogger, '_get_current_user_id', return_value=auth_user.id):
                activity = ActivityLogger.log_member_action(
                    action_type='update',
                    member_obj=test_member,
                    changes=changes
                )
                
                assert activity is not None
                assert activity.action == 'update_member'
                assert 'changed fields: name, email' in activity.description
    
    def test_log_member_action_activate_deactivate(self, app, db_session, auth_user, test_member):
        """Test logging member activation/deactivation."""
        with app.app_context():
            with patch.object(ActivityLogger, '_get_current_user_id', return_value=auth_user.id):
                # Test activation
                activate_activity = ActivityLogger.log_member_action(
                    action_type='activate',
                    member_obj=test_member
                )
                
                assert activate_activity.action == 'activate_member'
                assert 'Activated member' in activate_activity.description
                
                # Test deactivation
                deactivate_activity = ActivityLogger.log_member_action(
                    action_type='deactivate',
                    member_obj=test_member
                )
                
                assert deactivate_activity.action == 'deactivate_member'
                assert 'Deactivated member' in deactivate_activity.description
    
    def test_log_publication_action_create(self, app, db_session, auth_user, test_journal_publication):
        """Test logging publication creation action."""
        with app.app_context():
            with patch.object(ActivityLogger, '_get_current_user_id', return_value=auth_user.id):
                activity = ActivityLogger.log_publication_action(
                    action_type='create',
                    publication_obj=test_journal_publication
                )
                
                assert activity is not None
                assert activity.action == 'create_publication'
                assert test_journal_publication.title in activity.description
                assert 'Created' in activity.description
                assert activity.publication_id == test_journal_publication.id
    
    def test_log_publication_action_with_changes(self, app, db_session, auth_user, test_journal_publication):
        """Test logging publication update with changes."""
        with app.app_context():
            changes = {'title': 'New Title', 'publication_type': 'journal'}
            
            with patch.object(ActivityLogger, '_get_current_user_id', return_value=auth_user.id):
                activity = ActivityLogger.log_publication_action(
                    action_type='update',
                    publication_obj=test_journal_publication,
                    changes=changes
                )
                
                assert activity is not None
                assert activity.action == 'update_publication'
                assert 'changed fields: title, publication_type' in activity.description
    
    def test_log_auth_action_login(self, app, db_session, auth_user):
        """Test logging authentication actions."""
        with app.app_context():
            activity = ActivityLogger.log_auth_action(
                action_type='login',
                user_obj=auth_user,
                ip_address='192.168.1.1'
            )
            
            assert activity is not None
            assert activity.action == 'user_login'
            assert 'Login for' in activity.description
            assert auth_user.full_name in activity.description
    
    def test_log_auth_action_password_change(self, app, db_session, auth_user):
        """Test logging password change action."""
        with app.app_context():
            activity = ActivityLogger.log_auth_action(
                action_type='password_change',
                user_obj=auth_user,
                details='Password changed via admin panel'
            )
            
            assert activity is not None
            assert activity.action == 'password_change'
            assert 'Password Change for' in activity.description
            assert 'Password changed via admin panel' in activity.description
    
    def test_get_current_user_id_with_current_user(self, app, auth_user):
        """Test getting current user ID from Flask-Login."""
        with app.app_context():
            # Mock current_user
            with patch('app.services.activity_logger.current_user') as mock_current_user:
                mock_current_user.id = auth_user.id
                
                user_id = ActivityLogger._get_current_user_id()
                assert user_id == auth_user.id
    
    def test_get_current_user_id_from_g_context(self, app, auth_user):
        """Test getting current user ID from g context fallback."""
        with app.app_context():
            # Set user ID in g context
            g.user_id = auth_user.id
            
            # Mock current_user to fail
            with patch('app.services.activity_logger.current_user') as mock_current_user:
                mock_current_user.id = None
                
                user_id = ActivityLogger._get_current_user_id()
                assert user_id == auth_user.id
    
    def test_build_member_description_create(self, app, test_member):
        """Test building member action descriptions."""
        with app.app_context():
            description = ActivityLogger._build_member_description('create', test_member)
            
            assert test_member.name in description
            assert 'Created member' in description
            if test_member.sponsor:
                assert test_member.sponsor.name in description
    
    def test_build_member_description_update_with_changes(self, app, test_member):
        """Test building member update description with changes."""
        with app.app_context():
            changes = {'name': 'New Name', 'institution': 'New Institution'}
            description = ActivityLogger._build_member_description('update', test_member, changes)
            
            assert test_member.name in description
            assert 'Updated member' in description
            assert 'changed fields: name, institution' in description
    
    def test_build_publication_description_create(self, app, test_journal_publication):
        """Test building publication action descriptions."""
        with app.app_context():
            description = ActivityLogger._build_publication_description('create', test_journal_publication)
            
            assert test_journal_publication.title in description
            assert 'Created' in description
            if test_journal_publication.publication_type:
                assert test_journal_publication.publication_type.value in description
    
    def test_build_publication_description_unknown_action(self, app, test_journal_publication):
        """Test building description for unknown action type."""
        with app.app_context():
            description = ActivityLogger._build_publication_description('unknown_action', test_journal_publication)
            
            assert test_journal_publication.title in description
            assert "Performed 'unknown_action' action" in description
    
    def test_get_recent_activities_wrapper(self, app, db_session, auth_user):
        """Test wrapper method for getting recent activities."""
        with app.app_context():
            # Create some activities first
            for i in range(3):
                ActivityLogger.log_activity(
                    user_id=auth_user.id,
                    action=f'test_action_{i}',
                    description=f'Test activity {i}',
                    ip_address='192.168.1.1'
                )
            
            # Get recent activities
            activities = ActivityLogger.get_recent_activities(limit=2)
            
            assert len(activities) <= 2
            # Should be most recent first
            if activities:
                assert activities[0].created_at >= activities[-1].created_at
    
    def test_get_activities_for_entity_wrapper(self, app, db_session, auth_user, test_member):
        """Test wrapper method for getting entity activities."""
        with app.app_context():
            # Create member activity
            ActivityLogger.log_activity(
                user_id=auth_user.id,
                action='test_member_action',
                description='Test member activity',
                ip_address='192.168.1.1',
                member_id=test_member.id
            )
            
            activities = ActivityLogger.get_activities_for_entity('member', test_member.id)
            
            assert len(activities) >= 1
            assert activities[0].member_id == test_member.id
    
    def test_cleanup_old_activities_wrapper(self, app, db_session, auth_user):
        """Test wrapper method for cleaning up old activities."""
        with app.app_context():
            # Create an activity
            ActivityLogger.log_activity(
                user_id=auth_user.id,
                action='test_cleanup',
                description='Test cleanup activity',
                ip_address='192.168.1.1'
            )
            
            # Test cleanup (should return 0 since no old activities)
            count = ActivityLogger.cleanup_old_activities(retention_days=365)
            assert isinstance(count, int)
            assert count >= 0
    
    def test_no_user_context_handling(self, app, db_session, test_member):
        """Test handling when no user context is available."""
        with app.app_context():
            # Mock no current user
            with patch.object(ActivityLogger, '_get_current_user_id', return_value=None):
                activity = ActivityLogger.log_member_action(
                    action_type='create',
                    member_obj=test_member
                )
                
                # Should return None when no user context
                assert activity is None
    
    @patch('app.services.activity_logger.has_request_context', return_value=False)
    def test_no_request_context_ip_fallback(self, mock_has_request_context, app, db_session, auth_user):
        """Test IP detection fallback when no request context."""
        with app.app_context():
            activity = ActivityLogger.log_activity(
                user_id=auth_user.id,
                action='test_no_context',
                description='Test no request context',
                # No IP provided, should fallback
            )
            
            assert activity.ip_address == '0.0.0.0'  # Fallback IP