"""
Base SQLAlchemy model class with common fields and methods.
"""

from datetime import datetime, timezone
from app import db


class BaseModel(db.Model):
    """Base model class for all database models."""

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        """String representation for debugging."""
        return f"<{self.__class__.__name__}(id={self.id})>"

    def __str__(self):
        """Human-readable string representation."""
        return f"{self.__class__.__name__} #{self.id}"

    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def save(self):
        """Save the model to the database."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Delete the model from the database."""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        """Get model by ID."""
        return db.session.get(cls, id)

    @classmethod
    def get_all(cls):
        """Get all records of this model."""
        return cls.query.all()
