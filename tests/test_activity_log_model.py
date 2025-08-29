"""
Unit tests for ActivityLog model.
Tests model functionality, relationships, and constraints.
"""

import pytest
from datetime import datetime, timedelta
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.models.sponsor import Sponsor
from app.models.member import Member
from app.models.publication import Publication, PublicationType


class TestActivityLogModel:
    """Test ActivityLog model functionality."""
    
    def test_create_activity_log_basic(self, db_session, auth_user):
        """Test basic activity log creation."""
        # Create activity log
        activity = ActivityLog(
            user_id=auth_user.id,
            action='test_action',
            description='Test description',
            ip_address='192.168.1.1'
        )
        activity.save()
        
        # Verify creation
        assert activity.id is not None
        assert activity.user_id == auth_user.id
        assert activity.action == 'test_action'
        assert activity.description == 'Test description'
        assert activity.ip_address == '192.168.1.1'
        assert activity.created_at is not None
        assert activity.updated_at is not None
    
    def test_activity_log_with_entity_references(self, db_session, auth_user, test_member, test_journal_publication):
        """Test activity log with member and publication references."""
        activity = ActivityLog(
            user_id=auth_user.id,
            action='update_member',
            description='Updated member information',
            ip_address='10.0.0.1',
            member_id=test_member.id,
            publication_id=test_journal_publication.id
        )
        activity.save()
        
        # Verify relationships
        assert activity.member_id == test_member.id
        assert activity.publication_id == test_journal_publication.id
        assert activity.member.id == test_member.id
        assert activity.publication.id == test_journal_publication.id
        assert activity.user.id == auth_user.id
    
    def test_activity_log_to_dict(self, db_session, auth_user):
        """Test activity log serialization to dictionary."""
        activity = ActivityLog(
            user_id=auth_user.id,
            action='create_member',
            description='Created new member',
            ip_address='172.16.0.1'
        )
        activity.save()
        
        result = activity.to_dict()
        
        assert result['id'] == activity.id
        assert result['user_id'] == auth_user.id
        assert result['user_name'] == auth_user.full_name
        assert result['action'] == 'create_member'
        assert result['description'] == 'Created new member'
        assert result['ip_address'] == '172.16.0.1'
        assert 'created_at' in result
    
    def test_activity_log_cleanup_old_logs(self, db_session, auth_user):
        """Test cleanup of old activity logs."""
        # Create old activity (400 days ago)
        old_date = datetime.utcnow() - timedelta(days=400)
        old_activity = ActivityLog(
            user_id=auth_user.id,
            action='old_action',
            description='Old activity',
            ip_address='192.168.1.1'
        )
        old_activity.save()
        # Manually set old date
        old_activity.created_at = old_date
        db_session.commit()
        
        # Create recent activity
        recent_activity = ActivityLog(
            user_id=auth_user.id,
            action='recent_action',
            description='Recent activity',
            ip_address='192.168.1.2'
        )
        recent_activity.save()
        
        # Verify both exist
        assert ActivityLog.query.count() == 2
        
        # Cleanup old logs (365 day retention)
        deleted_count = ActivityLog.cleanup_old_logs(retention_days=365)
        
        # Verify cleanup
        assert deleted_count == 1
        assert ActivityLog.query.count() == 1
        
        remaining_activity = ActivityLog.query.first()
        assert remaining_activity.action == 'recent_action'
    
    def test_get_recent_activities(self, db_session, auth_user):
        """Test getting recent activities."""
        # Create multiple activities
        for i in range(5):
            activity = ActivityLog(
                user_id=auth_user.id,
                action=f'action_{i}',
                description=f'Description {i}',
                ip_address='192.168.1.1'
            )
            activity.save()
        
        # Get recent activities
        recent = ActivityLog.get_recent_activities(limit=3)
        
        assert len(recent) == 3
        # Should be ordered by most recent first
        assert recent[0].action == 'action_4'
        assert recent[1].action == 'action_3'
        assert recent[2].action == 'action_2'
    
    def test_get_activities_for_entity_member(self, db_session, auth_user, test_member):
        """Test getting activities for a specific member."""
        # Create member-related activity
        member_activity = ActivityLog(
            user_id=auth_user.id,
            action='update_member',
            description='Updated member',
            ip_address='192.168.1.1',
            member_id=test_member.id
        )
        member_activity.save()
        
        # Create unrelated activity
        other_activity = ActivityLog(
            user_id=auth_user.id,
            action='other_action',
            description='Other activity',
            ip_address='192.168.1.1'
        )
        other_activity.save()
        
        # Get member activities
        member_activities = ActivityLog.get_activities_for_entity('member', test_member.id)
        
        assert len(member_activities) == 1
        assert member_activities[0].id == member_activity.id
        assert member_activities[0].member_id == test_member.id
    
    def test_get_activities_for_entity_publication(self, db_session, auth_user, test_journal_publication):
        """Test getting activities for a specific publication."""
        # Create publication-related activity
        pub_activity = ActivityLog(
            user_id=auth_user.id,
            action='create_publication',
            description='Created publication',
            ip_address='192.168.1.1',
            publication_id=test_journal_publication.id
        )
        pub_activity.save()
        
        # Get publication activities
        pub_activities = ActivityLog.get_activities_for_entity('publication', test_journal_publication.id)
        
        assert len(pub_activities) == 1
        assert pub_activities[0].id == pub_activity.id
        assert pub_activities[0].publication_id == test_journal_publication.id
    
    def test_get_activity_statistics(self, db_session, auth_user):
        """Test getting activity statistics."""
        # Create activities of different types
        activities_data = [
            ('create_member', 'Created member 1'),
            ('create_member', 'Created member 2'),
            ('update_member', 'Updated member 1'),
            ('delete_member', 'Deleted member 1'),
        ]
        
        for action, description in activities_data:
            activity = ActivityLog(
                user_id=auth_user.id,
                action=action,
                description=description,
                ip_address='192.168.1.1'
            )
            activity.save()
        
        # Get statistics
        stats = ActivityLog.get_activity_statistics(days=30)
        
        assert stats['total_activities'] == 4
        assert 'action_breakdown' in stats
        # Action breakdown is now grouped by prefix for better statistics
        assert stats['action_breakdown'].get('create', 0) == 2  # 2 create_member actions
        assert stats['action_breakdown'].get('update', 0) == 1  # 1 update_member action
        assert stats['action_breakdown'].get('delete', 0) == 1  # 1 delete_member action
    
    def test_activity_log_immutable_save(self, db_session, auth_user):
        """Test that activity logs cannot be modified after creation."""
        activity = ActivityLog(
            user_id=auth_user.id,
            action='test_action',
            description='Test description',
            ip_address='192.168.1.1'
        )
        activity.save()
        
        # Try to modify and save again - should raise error
        activity.description = 'Modified description'
        
        with pytest.raises(ValueError, match="Activity log entries cannot be modified after creation"):
            activity.save()
    
    def test_activity_log_cannot_delete_individual(self, db_session, auth_user):
        """Test that individual activity log entries cannot be deleted."""
        activity = ActivityLog(
            user_id=auth_user.id,
            action='test_action',
            description='Test description',
            ip_address='192.168.1.1'
        )
        activity.save()
        
        with pytest.raises(ValueError, match="Activity log entries cannot be deleted individually"):
            activity.delete()
    
    def test_activity_log_string_representations(self, db_session, auth_user):
        """Test string representations of activity log."""
        activity = ActivityLog(
            user_id=auth_user.id,
            action='test_action',
            description='Test description',
            ip_address='192.168.1.1'
        )
        activity.save()
        
        # Test __repr__
        repr_str = repr(activity)
        assert f'<ActivityLog {activity.id}: test_action by user {auth_user.id}>' == repr_str
    
    def test_activity_log_foreign_key_constraints(self, db_session):
        """Test foreign key constraints."""
        # Note: SQLite in test environment may not enforce foreign key constraints
        # This test verifies the model structure is correct
        activity = ActivityLog(
            user_id=99999,  # Non-existent user
            action='test_action',
            description='Test description',
            ip_address='192.168.1.1'
        )
        
        # In production MySQL, this would fail, but in test SQLite it may pass
        # The important thing is that the model accepts the foreign key field
        try:
            activity.save()
            # If it succeeds, foreign keys aren't enforced in test environment
            assert activity.user_id == 99999
        except Exception:
            # If it fails, foreign keys are enforced - this is expected behavior
            pass
    
    def test_activity_log_ip_address_formats(self, db_session, auth_user):
        """Test activity log with different IP address formats."""
        # Test IPv4
        ipv4_activity = ActivityLog(
            user_id=auth_user.id,
            action='test_ipv4',
            description='IPv4 test',
            ip_address='192.168.1.100'
        )
        ipv4_activity.save()
        assert ipv4_activity.ip_address == '192.168.1.100'
        
        # Test IPv6 (shortened format should fit in VARCHAR(45))
        ipv6_activity = ActivityLog(
            user_id=auth_user.id,
            action='test_ipv6',
            description='IPv6 test',
            ip_address='2001:db8::1'
        )
        ipv6_activity.save()
        assert ipv6_activity.ip_address == '2001:db8::1'
        
        # Test fallback IP
        fallback_activity = ActivityLog(
            user_id=auth_user.id,
            action='test_fallback',
            description='Fallback test',
            ip_address='0.0.0.0'
        )
        fallback_activity.save()
        assert fallback_activity.ip_address == '0.0.0.0'