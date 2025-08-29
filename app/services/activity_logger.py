"""
Activity Logging Service Layer
Centralized service for logging all user activities in the system.
"""

import logging
from datetime import datetime
from flask import request, current_app, g, has_request_context
from flask_login import current_user
from app import db
from app.models.activity_log import ActivityLog

# Configure logging for service errors
service_logger = logging.getLogger(__name__)


class ActivityLogger:
    """
    Centralized activity logging service for audit trail functionality.
    Handles all user activity logging with context-aware information.
    """
    
    # Action type constants for consistency
    MEMBER_ACTIONS = {
        'create': 'create_member',
        'update': 'update_member',
        'activate': 'activate_member',
        'deactivate': 'deactivate_member',
        'delete': 'delete_member'
    }
    
    PUBLICATION_ACTIONS = {
        'create': 'create_publication',
        'update': 'update_publication',
        'activate': 'activate_publication',
        'deactivate': 'deactivate_publication',
        'delete': 'delete_publication'
    }
    
    AUTH_ACTIONS = {
        'login': 'user_login',
        'logout': 'user_logout',
        'password_change': 'password_change',
        'profile_update': 'profile_update'
    }
    
    @staticmethod
    def log_activity(user_id, action, description, ip_address=None, member_id=None, publication_id=None):
        """
        Log a user activity with contextual information.
        
        Args:
            user_id (int): ID of user performing the action
            action (str): Action type being performed
            description (str): Detailed description of what was done
            ip_address (str): IP address of the user (auto-detected if None)
            member_id (int): Optional - related member ID
            publication_id (int): Optional - related publication ID
        
        Returns:
            ActivityLog: Created activity log entry or None if failed
        """
        try:
            # Auto-detect IP address if not provided
            if ip_address is None:
                ip_address = ActivityLogger._get_client_ip()
            
            # Create activity log entry
            activity_log = ActivityLog(
                user_id=user_id,
                action=action,
                description=description,
                ip_address=ip_address,
                member_id=member_id,
                publication_id=publication_id
            )
            
            # Save to database
            db.session.add(activity_log)
            db.session.commit()
            
            service_logger.info(f"Activity logged: {action} by user {user_id}")
            return activity_log
            
        except Exception as e:
            service_logger.error(f"Failed to log activity: {action} by user {user_id}. Error: {str(e)}")
            # Rollback any partial transaction
            db.session.rollback()
            
            # Activity logging failure should not break main operations
            # Log the error but don't raise exception
            return None
    
    @staticmethod
    def log_member_action(action_type, member_obj, user_id=None, ip_address=None, changes=None):
        """
        Log member-specific actions with detailed context.
        
        Args:
            action_type (str): Type of action ('create', 'update', 'activate', 'deactivate', 'delete')
            member_obj: Member object being acted upon
            user_id (int): User performing the action (auto-detected if None)
            ip_address (str): IP address (auto-detected if None)
            changes (dict): Dictionary of changed fields for update actions
        
        Returns:
            ActivityLog: Created activity log entry or None if failed
        """
        # Auto-detect user if not provided
        if user_id is None:
            user_id = ActivityLogger._get_current_user_id()
        
        if user_id is None:
            service_logger.warning("Cannot log member action - no user context available")
            return None
        
        # Get action constant
        action = ActivityLogger.MEMBER_ACTIONS.get(action_type, f'member_{action_type}')
        
        # Build description based on action type
        description = ActivityLogger._build_member_description(action_type, member_obj, changes)
        
        return ActivityLogger.log_activity(
            user_id=user_id,
            action=action,
            description=description,
            ip_address=ip_address,
            member_id=member_obj.id
        )
    
    @staticmethod
    def log_publication_action(action_type, publication_obj, user_id=None, ip_address=None, changes=None):
        """
        Log publication-specific actions with detailed context.
        
        Args:
            action_type (str): Type of action ('create', 'update', 'activate', 'deactivate', 'delete')
            publication_obj: Publication object being acted upon
            user_id (int): User performing the action (auto-detected if None)
            ip_address (str): IP address (auto-detected if None)
            changes (dict): Dictionary of changed fields for update actions
        
        Returns:
            ActivityLog: Created activity log entry or None if failed
        """
        # Auto-detect user if not provided
        if user_id is None:
            user_id = ActivityLogger._get_current_user_id()
        
        if user_id is None:
            service_logger.warning("Cannot log publication action - no user context available")
            return None
        
        # Get action constant
        action = ActivityLogger.PUBLICATION_ACTIONS.get(action_type, f'publication_{action_type}')
        
        # Build description based on action type
        description = ActivityLogger._build_publication_description(action_type, publication_obj, changes)
        
        return ActivityLogger.log_activity(
            user_id=user_id,
            action=action,
            description=description,
            ip_address=ip_address,
            publication_id=publication_obj.id
        )
    
    @staticmethod
    def log_auth_action(action_type, user_obj=None, user_id=None, ip_address=None, details=None):
        """
        Log authentication-related actions.
        
        Args:
            action_type (str): Type of auth action ('login', 'logout', 'password_change', 'profile_update')
            user_obj: User object for the action
            user_id (int): User ID if user_obj not provided
            ip_address (str): IP address (auto-detected if None)
            details (str): Additional details about the action
        
        Returns:
            ActivityLog: Created activity log entry or None if failed
        """
        # Determine user ID
        if user_obj:
            target_user_id = user_obj.id
            user_name = user_obj.full_name
        elif user_id:
            target_user_id = user_id
            user_name = f"User #{user_id}"
        else:
            service_logger.warning("Cannot log auth action - no user information provided")
            return None
        
        # Get action constant
        action = ActivityLogger.AUTH_ACTIONS.get(action_type, f'auth_{action_type}')
        
        # Build description
        if details:
            description = f"{action_type.replace('_', ' ').title()} for {user_name}: {details}"
        else:
            description = f"{action_type.replace('_', ' ').title()} for {user_name}"
        
        return ActivityLogger.log_activity(
            user_id=target_user_id,
            action=action,
            description=description,
            ip_address=ip_address
        )
    
    @staticmethod
    def _get_client_ip():
        """Get client IP address from Flask request context."""
        if not has_request_context():
            return '0.0.0.0'  # Fallback for non-request contexts
        
        # Check for forwarded IP (proxy/load balancer scenarios)
        forwarded_ips = request.headers.get('X-Forwarded-For')
        if forwarded_ips:
            # Take the first IP in the chain (original client)
            return forwarded_ips.split(',')[0].strip()
        
        # Check other common proxy headers
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback to direct connection IP
        return request.remote_addr or '0.0.0.0'
    
    @staticmethod
    def _get_current_user_id():
        """Get current authenticated user ID."""
        try:
            if hasattr(current_user, 'id') and current_user.id:
                return current_user.id
        except Exception:
            pass
        
        # Fallback: check if user ID is stored in g context
        try:
            if hasattr(g, 'user_id'):
                return g.user_id
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def _build_member_description(action_type, member_obj, changes=None):
        """Build descriptive message for member actions."""
        member_name = member_obj.name
        sponsor_name = member_obj.sponsor.name if member_obj.sponsor else "Unknown Sponsor"
        
        if action_type == 'create':
            return f"Created member '{member_name}' for sponsor '{sponsor_name}'"
        
        elif action_type == 'update':
            if changes and isinstance(changes, dict):
                changed_fields = ', '.join(changes.keys())
                return f"Updated member '{member_name}' - changed fields: {changed_fields}"
            else:
                return f"Updated member '{member_name}'"
        
        elif action_type == 'activate':
            return f"Activated member '{member_name}' - marked as active"
        
        elif action_type == 'deactivate':
            return f"Deactivated member '{member_name}' - marked as inactive"
        
        elif action_type == 'delete':
            return f"Deleted member '{member_name}' from sponsor '{sponsor_name}'"
        
        else:
            return f"Performed '{action_type}' action on member '{member_name}'"
    
    @staticmethod
    def _build_publication_description(action_type, publication_obj, changes=None):
        """Build descriptive message for publication actions."""
        publication_title = publication_obj.title
        publication_type = publication_obj.publication_type.value if publication_obj.publication_type else "unknown"
        member_name = publication_obj.member.name if publication_obj.member else "Unknown Member"
        
        if action_type == 'create':
            return f"Created {publication_type} publication '{publication_title}' for member '{member_name}'"
        
        elif action_type == 'update':
            if changes and isinstance(changes, dict):
                changed_fields = ', '.join(changes.keys())
                return f"Updated publication '{publication_title}' - changed fields: {changed_fields}"
            else:
                return f"Updated publication '{publication_title}'"
        
        elif action_type == 'activate':
            return f"Activated publication '{publication_title}' - marked as active"
        
        elif action_type == 'deactivate':
            return f"Deactivated publication '{publication_title}' - marked as inactive"
        
        elif action_type == 'delete':
            return f"Deleted publication '{publication_title}' from member '{member_name}'"
        
        else:
            return f"Performed '{action_type}' action on publication '{publication_title}'"
    
    @staticmethod
    def get_recent_activities(limit=10, user_id=None, sponsor_id=None):
        """
        Get recent activities for display.
        Wrapper around ActivityLog.get_recent_activities for service layer consistency.
        """
        return ActivityLog.get_recent_activities(limit=limit, user_id=user_id, sponsor_id=sponsor_id)
    
    @staticmethod
    def get_activities_for_entity(entity_type, entity_id, limit=50):
        """
        Get activities for specific entity.
        Wrapper around ActivityLog.get_activities_for_entity for service layer consistency.
        """
        return ActivityLog.get_activities_for_entity(entity_type, entity_id, limit=limit)
    
    @staticmethod
    def cleanup_old_activities(retention_days=365):
        """
        Clean up old activity logs.
        Wrapper around ActivityLog.cleanup_old_logs for service layer consistency.
        """
        try:
            count = ActivityLog.cleanup_old_logs(retention_days=retention_days)
            service_logger.info(f"Cleaned up {count} old activity log entries older than {retention_days} days")
            return count
        except Exception as e:
            service_logger.error(f"Failed to cleanup old activity logs: {str(e)}")
            return 0