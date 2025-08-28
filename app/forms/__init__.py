"""
Forms package for DOI Management application.
"""

from .member_forms import *
from .publication_forms import (
    BasePublicationForm,
    JournalPublicationForm,
    BookSeriesPublicationForm,
    BookSetPublicationForm,
    BookPublicationForm,
    UniversalPublicationForm
)