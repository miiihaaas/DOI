"""
Models package initialization.
Import all models here for Flask-Migrate to discover them.
"""

from app.models.base import BaseModel
from app.models.sponsor import Sponsor
from app.models.user import User
from app.models.member import Member
from app.models.publication import Publication, PublicationType

# Import all models here so Flask-Migrate can discover them

__all__ = [
    'BaseModel',
    'Sponsor',
    'User',
    'Member',
    'Publication',
    'PublicationType'
]
