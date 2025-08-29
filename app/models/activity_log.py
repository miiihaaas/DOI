from app import db
from app.models.base import BaseModel
from datetime import datetime, timedelta
from sqlalchemy import Index


class ActivityLog(BaseModel):
    """
    Model for tracking all user activities in the system.
    Immutable logs for audit trail and compliance.
    """
    __tablename__ = 'activity_logs'
    
    # Core fields
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    
    # Optional entity references
    member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='SET NULL'), nullable=True)
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='activity_logs')
    member = db.relationship('Member', backref='activity_logs')
    publication = db.relationship('Publication', backref='activity_logs')
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_activity_user', 'user_id'),
        Index('idx_activity_action', 'action'),
        Index('idx_activity_created', 'created_at'),
        Index('idx_activity_member', 'member_id'),
        Index('idx_activity_publication', 'publication_id'),
        Index('idx_activity_composite', 'user_id', 'action', 'created_at'),
    )
    
    def __init__(self, **kwargs):
        """Initialize ActivityLog with immutable fields."""
        super().__init__(**kwargs)
    
    def __repr__(self):
        return f'<ActivityLog {self.id}: {self.action} by user {self.user_id}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else 'Unknown User',
            'action': self.action,
            'description': self.description,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'member_id': self.member_id,
            'publication_id': self.publication_id
        }
    
    @classmethod
    def cleanup_old_logs(cls, retention_days=365):
        """
        Remove activity logs older than specified retention period.
        Default: 1 year retention as per story requirements.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        old_logs = cls.query.filter(cls.created_at < cutoff_date)
        count = old_logs.count()
        old_logs.delete()
        db.session.commit()
        return count
    
    @classmethod
    def get_recent_activities(cls, limit=10, user_id=None, sponsor_id=None):
        """Get recent activities with optional filtering."""
        if sponsor_id:
            # Since User doesn't have sponsor_id, and this is a single-sponsor system,
            # just return all recent activities (in a single-sponsor system, all activities belong to that sponsor)
            query = cls.query
        else:
            query = cls.query
        
        if user_id:
            query = query.filter(cls.user_id == user_id)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_activities_for_entity(cls, entity_type, entity_id, limit=50):
        """Get activities for specific entity (member, publication)."""
        if entity_type == 'member':
            return cls.query.filter(cls.member_id == entity_id).order_by(cls.created_at.desc()).limit(limit).all()
        elif entity_type == 'publication':
            return cls.query.filter(cls.publication_id == entity_id).order_by(cls.created_at.desc()).limit(limit).all()
        else:
            return []
    
    @classmethod
    def get_activity_statistics(cls, user_id=None, sponsor_id=None, days=30):
        """Get activity statistics for dashboard."""
        from sqlalchemy import func
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = cls.query.filter(cls.created_at >= cutoff_date)
        
        if user_id:
            query = query.filter(cls.user_id == user_id)
        
        if sponsor_id:
            query = query.join(cls.user).filter(cls.user.has(sponsor_id=sponsor_id))
        
        # Activity count by action type - grouped by prefix (database-aware)
        from app import db
        
        # Check database type for appropriate function usage
        db_url = str(db.engine.url)
        if 'sqlite' in db_url:
            # SQLite-compatible approach: use SUBSTR and CASE for action prefix extraction
            from sqlalchemy import case
            action_prefix_expr = case(
                (cls.action.like('%_%'), 
                 func.substr(cls.action, 1, func.instr(cls.action, '_') - 1)),
                else_=cls.action
            )
            action_stats = query.with_entities(
                action_prefix_expr.label('action_prefix'),
                func.count(cls.id).label('count')
            ).group_by(action_prefix_expr).all()
        else:
            # MySQL-compatible approach using substring_index
            action_stats = query.with_entities(
                func.substring_index(cls.action, '_', 1).label('action_prefix'),
                func.count(cls.id).label('count')
            ).group_by(
                func.substring_index(cls.action, '_', 1)
            ).all()
        
        total_activities = query.count()
        
        return {
            'total_activities': total_activities,
            'action_breakdown': {action: count for action, count in action_stats},
            'period_days': days
        }
    
    # Prevent modification of log entries (immutable)
    def save(self):
        """Override save to prevent updates after creation."""
        if self.id is not None:
            raise ValueError("Activity log entries cannot be modified after creation")
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Prevent deletion of individual log entries."""
        raise ValueError("Activity log entries cannot be deleted individually")