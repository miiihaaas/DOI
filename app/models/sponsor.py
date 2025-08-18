"""
Sponsor model - Singleton model representing the single DOI sponsor organization.
"""

import re
from sqlalchemy.exc import IntegrityError
from app import db
from app.models.base import BaseModel


class Sponsor(BaseModel):
    """
    Sponsor model - represents the single DOI sponsor organization.
    This is a singleton model - only one record should exist in the database.
    """
    
    __tablename__ = 'sponsors'

    # Core fields
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    crossref_member_id = db.Column(db.String(50), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)

    def __repr__(self):
        """String representation for debugging."""
        return f"<Sponsor(id={self.id}, name='{self.name}', email='{self.email}')>"

    def __str__(self):
        """Human-readable string representation."""
        return f"Sponsor: {self.name}"

    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            'name': self.name,
            'email': self.email,
            'crossref_member_id': self.crossref_member_id,
            'is_active': self.is_active
        })
        return base_dict

    @classmethod
    def get_instance(cls):
        """
        Get the single sponsor instance.
        Returns the first (and should be only) sponsor record.
        """
        return cls.query.first()

    @classmethod
    def create_instance(cls, name, email, crossref_member_id, is_active=True):
        """
        Create the sponsor instance.
        Raises IntegrityError if a sponsor already exists.
        """
        # Check if sponsor already exists
        existing = cls.get_instance()
        if existing:
            raise IntegrityError(
                "Sponsor already exists. Only one sponsor record is allowed.",
                None, None
            )

        # Validate email format
        if not cls._validate_email(email):
            raise ValueError("Invalid email format")

        # Validate crossref_member_id format
        if not cls._validate_crossref_member_id(crossref_member_id):
            raise ValueError("Invalid Crossref member ID format")

        # Create new sponsor
        sponsor = cls(
            name=name,
            email=email,
            crossref_member_id=crossref_member_id,
            is_active=is_active
        )
        
        return sponsor.save()

    @staticmethod
    def _validate_email(email):
        """Validate email format using regex."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

    @staticmethod
    def _validate_crossref_member_id(member_id):
        """
        Validate Crossref member ID format.
        Should be a string with numbers and possibly letters.
        """
        if not member_id or len(member_id.strip()) == 0:
            return False
        
        # Basic validation - alphanumeric characters
        return re.match(r'^[a-zA-Z0-9]+$', member_id.strip()) is not None

    def update_details(self, name=None, email=None, crossref_member_id=None, is_active=None):
        """Update sponsor details with validation."""
        if name is not None:
            self.name = name

        if email is not None:
            if not self._validate_email(email):
                raise ValueError("Invalid email format")
            self.email = email

        if crossref_member_id is not None:
            if not self._validate_crossref_member_id(crossref_member_id):
                raise ValueError("Invalid Crossref member ID format")
            self.crossref_member_id = crossref_member_id

        if is_active is not None:
            self.is_active = is_active

        return self.save()

    def deactivate(self):
        """Deactivate the sponsor."""
        self.is_active = False
        return self.save()

    def activate(self):
        """Activate the sponsor."""
        self.is_active = True
        return self.save()