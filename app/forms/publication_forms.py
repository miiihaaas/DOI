"""
Publication forms with type-specific validation for TPH model.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp
from wtforms.widgets import TextArea

from app.models.publication import PublicationType


class BasePublicationForm(FlaskForm):
    """Base form with common fields for all publication types."""
    
    publication_type = SelectField(
        'Publication Type',
        choices=[
            ('journal', 'Journal'),
            ('book_series', 'Book Series'), 
            ('book_set', 'Book Set'),
            ('book', 'Book')
        ],
        validators=[DataRequired()],
        render_kw={'class': 'form-control', 'id': 'publication_type'}
    )
    
    title = StringField(
        'Title',
        validators=[DataRequired(), Length(min=5, max=500)],
        render_kw={'class': 'form-control', 'placeholder': 'Publication title'}
    )
    
    subtitle = StringField(
        'Subtitle',
        validators=[Optional(), Length(max=500)],
        render_kw={'class': 'form-control', 'placeholder': 'Publication subtitle (optional)'}
    )
    
    language_code = SelectField(
        'Language',
        choices=[
            ('en', 'English'),
            ('sr', 'Serbian'),
            ('hr', 'Croatian'),
            ('bs', 'Bosnian'),
            ('de', 'German'),
            ('fr', 'French'),
            ('ru', 'Russian')
        ],
        default='en',
        validators=[DataRequired()],
        render_kw={'class': 'form-control'}
    )


class JournalPublicationForm(BasePublicationForm):
    """Form for Journal publications."""
    
    journal_abbreviated_title = StringField(
        'Abbreviated Title',
        validators=[Optional(), Length(max=200)],
        render_kw={
            'class': 'form-control',
            'placeholder': 'e.g., Appl. Phys. Lett.',
            'data-type': 'journal'
        }
    )
    
    journal_issn = StringField(
        'ISSN (Print)',
        validators=[
            Optional(),
            Regexp(r'^\d{4}-\d{3}[\dX]$', message='ISSN format should be XXXX-XXXX')
        ],
        render_kw={
            'class': 'form-control',
            'placeholder': 'XXXX-XXXX',
            'data-type': 'journal'
        }
    )
    
    journal_electronic_issn = StringField(
        'E-ISSN (Electronic)',
        validators=[
            Optional(),
            Regexp(r'^\d{4}-\d{3}[\dX]$', message='E-ISSN format should be XXXX-XXXX')
        ],
        render_kw={
            'class': 'form-control',
            'placeholder': 'XXXX-XXXX',
            'data-type': 'journal'
        }
    )
    
    journal_coden = StringField(
        'CODEN',
        validators=[Optional(), Length(max=10)],
        render_kw={
            'class': 'form-control',
            'placeholder': 'CODEN (optional)',
            'data-type': 'journal'
        }
    )


class BookSeriesPublicationForm(BasePublicationForm):
    """Form for Book Series publications."""
    
    series_title = StringField(
        'Series Title',
        validators=[DataRequired(), Length(min=5, max=200)],
        render_kw={
            'class': 'form-control',
            'placeholder': 'Name of the book series',
            'data-type': 'book_series'
        }
    )
    
    series_subtitle = StringField(
        'Series Subtitle',
        validators=[Optional(), Length(max=200)],
        render_kw={
            'class': 'form-control',
            'placeholder': 'Series subtitle (optional)',
            'data-type': 'book_series'
        }
    )
    
    series_issn = StringField(
        'Series ISSN (Print)',
        validators=[
            Optional(),
            Regexp(r'^\d{4}-\d{3}[\dX]$', message='ISSN format should be XXXX-XXXX')
        ],
        render_kw={
            'class': 'form-control',
            'placeholder': 'XXXX-XXXX',
            'data-type': 'book_series'
        }
    )
    
    series_electronic_issn = StringField(
        'Series E-ISSN (Electronic)',
        validators=[
            Optional(),
            Regexp(r'^\d{4}-\d{3}[\dX]$', message='E-ISSN format should be XXXX-XXXX')
        ],
        render_kw={
            'class': 'form-control',
            'placeholder': 'XXXX-XXXX',
            'data-type': 'book_series'
        }
    )
    
    series_coden = StringField(
        'Series CODEN',
        validators=[Optional(), Length(max=10)],
        render_kw={
            'class': 'form-control',
            'placeholder': 'CODEN (optional)',
            'data-type': 'book_series'
        }
    )
    
    series_number = StringField(
        'Series Number/Volume',
        validators=[Optional(), Length(max=50)],
        render_kw={
            'class': 'form-control',
            'placeholder': 'Volume or series number',
            'data-type': 'book_series'
        }
    )


class BookSetPublicationForm(BasePublicationForm):
    """Form for Book Set publications."""
    
    set_title = StringField(
        'Set Title',
        validators=[DataRequired(), Length(min=5, max=200)],
        render_kw={
            'class': 'form-control',
            'placeholder': 'Name of the book set',
            'data-type': 'book_set'
        }
    )
    
    set_subtitle = StringField(
        'Set Subtitle',
        validators=[Optional(), Length(max=200)],
        render_kw={
            'class': 'form-control',
            'placeholder': 'Set subtitle (optional)',
            'data-type': 'book_set'
        }
    )
    
    set_isbn = StringField(
        'Set ISBN (Print)',
        validators=[
            Optional(),
            Regexp(r'^97[89]\d{10}$|^\d{9}[\dX]$', message='Invalid ISBN format')
        ],
        render_kw={
            'class': 'form-control',
            'placeholder': 'ISBN-10 or ISBN-13',
            'data-type': 'book_set'
        }
    )
    
    set_electronic_isbn = StringField(
        'Set E-ISBN (Electronic)',
        validators=[
            Optional(),
            Regexp(r'^97[89]\d{10}$|^\d{9}[\dX]$', message='Invalid ISBN format')
        ],
        render_kw={
            'class': 'form-control',
            'placeholder': 'ISBN-10 or ISBN-13',
            'data-type': 'book_set'
        }
    )
    
    set_part_number = StringField(
        'Part Number',
        validators=[Optional(), Length(max=50)],
        render_kw={
            'class': 'form-control',
            'placeholder': 'Part or volume number in set',
            'data-type': 'book_set'
        }
    )


class BookPublicationForm(BasePublicationForm):
    """Form for single Book publications."""
    
    book_type = SelectField(
        'Book Type',
        choices=[
            ('edited_book', 'Edited Book'),
            ('monograph', 'Monograph'),
            ('reference', 'Reference Book'),
            ('textbook', 'Textbook'),
            ('other', 'Other')
        ],
        validators=[DataRequired()],
        render_kw={'class': 'form-control', 'data-type': 'book'}
    )
    
    edition_number = IntegerField(
        'Edition Number',
        validators=[Optional()],
        render_kw={
            'class': 'form-control',
            'placeholder': 'e.g., 2 (for 2nd edition)',
            'data-type': 'book'
        }
    )
    
    isbn = StringField(
        'ISBN (Print)',
        validators=[
            Optional(),
            Regexp(r'^97[89]\d{10}$|^\d{9}[\dX]$', message='Invalid ISBN format')
        ],
        render_kw={
            'class': 'form-control',
            'placeholder': 'ISBN-10 or ISBN-13',
            'data-type': 'book'
        }
    )
    
    electronic_isbn = StringField(
        'E-ISBN (Electronic)',
        validators=[
            Optional(),
            Regexp(r'^97[89]\d{10}$|^\d{9}[\dX]$', message='Invalid ISBN format')
        ],
        render_kw={
            'class': 'form-control',
            'placeholder': 'ISBN-10 or ISBN-13',
            'data-type': 'book'
        }
    )
    
    noisbn_reason = StringField(
        'No ISBN Reason',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'class': 'form-control',
            'placeholder': 'Reason if no ISBN available',
            'data-type': 'book'
        }
    )


class UniversalPublicationForm(FlaskForm):
    """Universal form that contains all fields and uses JavaScript for conditional display."""
    
    # Base fields
    publication_type = SelectField(
        'Publication Type',
        choices=[
            ('journal', 'Journal'),
            ('book_series', 'Book Series'), 
            ('book_set', 'Book Set'),
            ('book', 'Book')
        ],
        validators=[DataRequired()],
        render_kw={'class': 'form-control', 'id': 'publication_type'}
    )
    
    title = StringField(
        'Title',
        validators=[DataRequired(), Length(min=5, max=500)],
        render_kw={'class': 'form-control', 'placeholder': 'Publication title'}
    )
    
    subtitle = StringField(
        'Subtitle',
        validators=[Optional(), Length(max=500)],
        render_kw={'class': 'form-control', 'placeholder': 'Publication subtitle (optional)'}
    )
    
    language_code = SelectField(
        'Language',
        choices=[
            ('en', 'English'),
            ('sr', 'Serbian'),
            ('hr', 'Croatian'),
            ('bs', 'Bosnian'),
            ('de', 'German'),
            ('fr', 'French'),
            ('ru', 'Russian')
        ],
        default='en',
        validators=[DataRequired()],
        render_kw={'class': 'form-control'}
    )
    
    # Journal fields
    journal_abbreviated_title = StringField(
        'Abbreviated Title',
        validators=[Optional(), Length(max=200)],
        render_kw={
            'class': 'form-control journal-field',
            'placeholder': 'e.g., Appl. Phys. Lett.',
            'data-type': 'journal'
        }
    )
    
    journal_issn = StringField(
        'ISSN (Print)',
        validators=[
            Optional(),
            Regexp(r'^\d{4}-\d{3}[\dX]$', message='ISSN format should be XXXX-XXXX')
        ],
        render_kw={
            'class': 'form-control journal-field',
            'placeholder': 'XXXX-XXXX',
            'data-type': 'journal'
        }
    )
    
    journal_electronic_issn = StringField(
        'E-ISSN (Electronic)',
        validators=[
            Optional(),
            Regexp(r'^\d{4}-\d{3}[\dX]$', message='E-ISSN format should be XXXX-XXXX')
        ],
        render_kw={
            'class': 'form-control journal-field',
            'placeholder': 'XXXX-XXXX',
            'data-type': 'journal'
        }
    )
    
    journal_coden = StringField(
        'CODEN',
        validators=[Optional(), Length(max=10)],
        render_kw={
            'class': 'form-control journal-field',
            'placeholder': 'CODEN (optional)',
            'data-type': 'journal'
        }
    )
    
    # Book Series fields
    series_title = StringField(
        'Series Title',
        validators=[Optional(), Length(max=200)],  # Will be required via JS for book_series
        render_kw={
            'class': 'form-control book-series-field',
            'placeholder': 'Name of the book series',
            'data-type': 'book_series'
        }
    )
    
    series_subtitle = StringField(
        'Series Subtitle',
        validators=[Optional(), Length(max=200)],
        render_kw={
            'class': 'form-control book-series-field',
            'placeholder': 'Series subtitle (optional)',
            'data-type': 'book_series'
        }
    )
    
    series_issn = StringField(
        'Series ISSN (Print)',
        validators=[
            Optional(),
            Regexp(r'^\d{4}-\d{3}[\dX]$', message='ISSN format should be XXXX-XXXX')
        ],
        render_kw={
            'class': 'form-control book-series-field',
            'placeholder': 'XXXX-XXXX',
            'data-type': 'book_series'
        }
    )
    
    series_electronic_issn = StringField(
        'Series E-ISSN (Electronic)',
        validators=[
            Optional(),
            Regexp(r'^\d{4}-\d{3}[\dX]$', message='E-ISSN format should be XXXX-XXXX')
        ],
        render_kw={
            'class': 'form-control book-series-field',
            'placeholder': 'XXXX-XXXX',
            'data-type': 'book_series'
        }
    )
    
    series_coden = StringField(
        'Series CODEN',
        validators=[Optional(), Length(max=10)],
        render_kw={
            'class': 'form-control book-series-field',
            'placeholder': 'CODEN (optional)',
            'data-type': 'book_series'
        }
    )
    
    series_number = StringField(
        'Series Number/Volume',
        validators=[Optional(), Length(max=50)],
        render_kw={
            'class': 'form-control book-series-field',
            'placeholder': 'Volume or series number',
            'data-type': 'book_series'
        }
    )
    
    # Book Set fields
    set_title = StringField(
        'Set Title',
        validators=[Optional(), Length(max=200)],  # Will be required via JS for book_set
        render_kw={
            'class': 'form-control book-set-field',
            'placeholder': 'Name of the book set',
            'data-type': 'book_set'
        }
    )
    
    set_subtitle = StringField(
        'Set Subtitle',
        validators=[Optional(), Length(max=200)],
        render_kw={
            'class': 'form-control book-set-field',
            'placeholder': 'Set subtitle (optional)',
            'data-type': 'book_set'
        }
    )
    
    set_isbn = StringField(
        'Set ISBN (Print)',
        validators=[
            Optional(),
            Regexp(r'^97[89]\d{10}$|^\d{9}[\dX]$', message='Invalid ISBN format')
        ],
        render_kw={
            'class': 'form-control book-set-field',
            'placeholder': 'ISBN-10 or ISBN-13',
            'data-type': 'book_set'
        }
    )
    
    set_electronic_isbn = StringField(
        'Set E-ISBN (Electronic)',
        validators=[
            Optional(),
            Regexp(r'^97[89]\d{10}$|^\d{9}[\dX]$', message='Invalid ISBN format')
        ],
        render_kw={
            'class': 'form-control book-set-field',
            'placeholder': 'ISBN-10 or ISBN-13',
            'data-type': 'book_set'
        }
    )
    
    set_part_number = StringField(
        'Part Number',
        validators=[Optional(), Length(max=50)],
        render_kw={
            'class': 'form-control book-set-field',
            'placeholder': 'Part or volume number in set',
            'data-type': 'book_set'
        }
    )
    
    # Book fields
    book_type = SelectField(
        'Book Type',
        choices=[
            ('', 'Select book type...'),
            ('edited_book', 'Edited Book'),
            ('monograph', 'Monograph'),
            ('reference', 'Reference Book'),
            ('textbook', 'Textbook'),
            ('other', 'Other')
        ],
        validators=[Optional()],  # Will be required via JS for book
        render_kw={'class': 'form-control book-field', 'data-type': 'book'}
    )
    
    edition_number = IntegerField(
        'Edition Number',
        validators=[Optional()],
        render_kw={
            'class': 'form-control book-field',
            'placeholder': 'e.g., 2 (for 2nd edition)',
            'data-type': 'book'
        }
    )
    
    isbn = StringField(
        'ISBN (Print)',
        validators=[
            Optional(),
            Regexp(r'^97[89]\d{10}$|^\d{9}[\dX]$', message='Invalid ISBN format')
        ],
        render_kw={
            'class': 'form-control book-field',
            'placeholder': 'ISBN-10 or ISBN-13',
            'data-type': 'book'
        }
    )
    
    electronic_isbn = StringField(
        'E-ISBN (Electronic)',
        validators=[
            Optional(),
            Regexp(r'^97[89]\d{10}$|^\d{9}[\dX]$', message='Invalid ISBN format')
        ],
        render_kw={
            'class': 'form-control book-field',
            'placeholder': 'ISBN-10 or ISBN-13',
            'data-type': 'book'
        }
    )
    
    noisbn_reason = StringField(
        'No ISBN Reason',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'class': 'form-control book-field',
            'placeholder': 'Reason if no ISBN available',
            'data-type': 'book'
        }
    )
    
    def validate(self, **kwargs):
        """Custom validation based on publication type."""
        result = super().validate(**kwargs)
        
        # Type-specific validation
        pub_type = self.publication_type.data
        
        if pub_type == 'book_series':
            if not self.series_title.data:
                self.series_title.errors.append('Series title is required for book series.')
                result = False
                
        elif pub_type == 'book_set':
            if not self.set_title.data:
                self.set_title.errors.append('Set title is required for book sets.')
                result = False
                
        elif pub_type == 'book':
            if not self.book_type.data:
                self.book_type.errors.append('Book type is required for books.')
                result = False
        
        return result