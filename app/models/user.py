"""
User model - represents admin users of the DOI management system.
"""

import re
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.base import BaseModel


class User(BaseModel, UserMixin):
    """
    User model - represents admin users of the DOI management system.
    All users are admin-level users of the single sponsor organization.
    """

    __tablename__ = 'users'

    # Core fields
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(
        db.Enum('admin', 'operator', name='user_roles'),
        default='operator',
        nullable=False,
        index=True
    )
    last_login = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        """String representation for debugging."""
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    def __str__(self):
        """Human-readable string representation."""
        return f"{self.full_name} ({self.email})"

    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'last_login': self.last_login.isoformat() if self.last_login else None
        })
        return base_dict

    def set_password(self, password):
        """Set password hash from plain text password."""
        if not password or len(password.strip()) < 6:
            raise ValueError("Password must be at least 6 characters long")

        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'admin'

    def is_operator(self):
        """Check if user has operator role."""
        return self.role == 'operator'

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.now(timezone.utc)
        db.session.commit()

    @classmethod
    def create_user(cls, email, password, full_name, role='operator'):
        """
        Create a new user with validation.
        """
        # Validate email format
        if not cls._validate_email(email):
            raise ValueError("Invalid email format")

        # Validate role
        if role not in ['admin', 'operator']:
            raise ValueError("Role must be 'admin' or 'operator'")

        # Validate full name
        if not full_name or len(full_name.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters long")

        # Create new user
        user = cls(
            email=email.lower().strip(),
            full_name=full_name.strip(),
            role=role
        )

        # Set password (will validate length)
        user.set_password(password)

        return user.save()

    @classmethod
    def get_by_email(cls, email):
        """Get user by email address."""
        return cls.query.filter_by(email=email.lower().strip()).first()

    @classmethod
    def get_by_id(cls, user_id):
        """Get user by ID."""
        from app import db
        return db.session.get(cls, user_id)

    @classmethod
    def get_admins(cls):
        """Get all admin users."""
        return cls.query.filter_by(role='admin').all()

    @classmethod
    def get_operators(cls):
        """Get all operator users."""
        return cls.query.filter_by(role='operator').all()

    @staticmethod
    def _validate_email(email):
        """Validate email format using regex."""
        if not email:
            return False

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email.strip()) is not None

    def update_profile(self, full_name=None, email=None):
        """Update user profile information."""
        if full_name is not None:
            if not full_name or len(full_name.strip()) < 2:
                raise ValueError("Full name must be at least 2 characters long")
            self.full_name = full_name.strip()

        if email is not None:
            if not self._validate_email(email):
                raise ValueError("Invalid email format")
            self.email = email.lower().strip()

        return self.save()

    def change_role(self, new_role):
        """Change user role with validation."""
        if new_role not in ['admin', 'operator']:
            raise ValueError("Role must be 'admin' or 'operator'")

        self.role = new_role
        return self.save()

    def change_password(self, new_password):
        """Change user password."""
        self.set_password(new_password)
        return self.save()

    # Flask-Login required methods
    def get_id(self):
        """Return user ID as string for Flask-Login."""
        return str(self.id)

    @property
    def is_authenticated(self):
        """Always return True for authenticated users."""
        return True

    @property
    def is_active(self):
        """Return True if user is active (all users are active by default)."""
        return True

    @property
    def is_anonymous(self):
        """Always return False for authenticated users."""
        return False
