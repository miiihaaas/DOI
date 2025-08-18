"""
Models package initialization.
Import all models here for Flask-Migrate to discover them.
"""

from app.models.base import BaseModel
from app.models.sponsor import Sponsor
from app.models.user import User

# Import all models here so Flask-Migrate can discover them

__all__ = [
    'BaseModel',
    'Sponsor', 
    'User'
]