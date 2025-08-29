"""
Tests for Publication Forms - Flask-WTF form validation testing.
"""

import pytest
from app.forms.publication_forms import (
    UniversalPublicationForm,
    JournalPublicationForm,
    BookSeriesPublicationForm,
    BookSetPublicationForm,
    BookPublicationForm
)


class TestUniversalPublicationForm:
    """Test UniversalPublicationForm validation."""
    
    def test_form_initialization(self, app):
        """Test form can be initialized."""
        with app.app_context():
            form = UniversalPublicationForm()
            assert form is not None
            assert hasattr(form, 'publication_type')
            assert hasattr(form, 'title')
    
    def test_valid_journal_form(self, app):
        """Test valid journal form data."""
        with app.app_context():
            form_data = {
                'publication_type': 'journal',
                'title': 'Test Journal',
                'subtitle': 'Test Subtitle',
                'language_code': 'en',
                'journal_abbreviated_title': 'Test J.',
                'journal_issn': '1234-5678',
                'journal_electronic_issn': '1234-5679',
                'journal_coden': 'TESTJX',
                'csrf_token': 'test_token'
            }
            
            form = UniversalPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == True
            assert form.publication_type.data == 'journal'
            assert form.title.data == 'Test Journal'
    
    def test_required_fields_validation(self, app):
        """Test required field validation."""
        with app.app_context():
            form_data = {
                'csrf_token': 'test_token'
            }
            
            form = UniversalPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == False
            assert 'This field is required.' in str(form.publication_type.errors)
            assert 'This field is required.' in str(form.title.errors)
    
    def test_title_length_validation(self, app):
        """Test title length validation."""
        with app.app_context():
            # Too short title
            form_data = {
                'publication_type': 'journal',
                'title': 'ABC',  # Less than 5 characters
                'language_code': 'en',
                'csrf_token': 'test_token'
            }
            
            form = UniversalPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == False
            assert any('must be between 5 and 500 characters' in error for error in form.title.errors)
    
    def test_issn_format_validation(self, app):
        """Test ISSN format validation."""
        with app.app_context():
            from werkzeug.datastructures import MultiDict
            form_data = MultiDict([
                ('publication_type', 'journal'),
                ('title', 'Test Journal'),
                ('language_code', 'en'),
                ('journal_issn', 'invalid-issn'),
                ('csrf_token', 'test_token')
            ])
            
            form = UniversalPublicationForm(formdata=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == False
            assert 'ISSN format should be XXXX-XXXX' in str(form.journal_issn.errors)
    
    def test_valid_issn_formats(self, app):
        """Test valid ISSN formats."""
        with app.app_context():
            valid_issns = ['1234-5678', '0000-0000', '9999-999X']
            
            for issn in valid_issns:
                form_data = {
                    'publication_type': 'journal',
                    'title': 'Test Journal',
                    'language_code': 'en',
                    'journal_issn': issn,
                    'csrf_token': 'test_token'
                }
                
                form = UniversalPublicationForm(data=form_data)
                # CSRF is disabled in test config
                
                assert form.validate() == True, f"ISSN {issn} should be valid"
    
    def test_isbn_format_validation(self, app):
        """Test ISBN format validation."""
        with app.app_context():
            from werkzeug.datastructures import MultiDict
            form_data = MultiDict([
                ('publication_type', 'book'),
                ('title', 'Test Book'),
                ('language_code', 'en'),
                ('book_type', 'monograph'),
                ('isbn', 'invalid-isbn'),
                ('csrf_token', 'test_token')
            ])
            
            form = UniversalPublicationForm(formdata=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == False
            assert 'Invalid ISBN format' in str(form.isbn.errors)
    
    def test_valid_isbn_formats(self, app):
        """Test valid ISBN formats."""
        with app.app_context():
            valid_isbns = ['9781234567890', '123456789X']
            
            for isbn in valid_isbns:
                form_data = {
                    'publication_type': 'book',
                    'title': 'Test Book',
                    'language_code': 'en',
                    'book_type': 'monograph',
                    'isbn': isbn,
                    'csrf_token': 'test_token'
                }
                
                form = UniversalPublicationForm(data=form_data)
                # CSRF is disabled in test config
                
                assert form.validate() == True, f"ISBN {isbn} should be valid"
    
    def test_type_specific_validation_book_series(self, app):
        """Test type-specific validation for book series."""
        with app.app_context():
            # Missing series_title should fail validation
            form_data = {
                'publication_type': 'book_series',
                'title': 'Test Series',
                'language_code': 'en',
                # Missing series_title
                'csrf_token': 'test_token'
            }
            
            form = UniversalPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == False
            assert 'Series title is required for book series' in str(form.series_title.errors)
    
    def test_type_specific_validation_book_set(self, app):
        """Test type-specific validation for book set."""
        with app.app_context():
            form_data = {
                'publication_type': 'book_set',
                'title': 'Test Set',
                'language_code': 'en',
                # Missing set_title
                'csrf_token': 'test_token'
            }
            
            form = UniversalPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == False
            assert 'Set title is required for book sets' in str(form.set_title.errors)
    
    def test_type_specific_validation_book(self, app):
        """Test type-specific validation for book."""
        with app.app_context():
            form_data = {
                'publication_type': 'book',
                'title': 'Test Book',
                'language_code': 'en',
                # Missing book_type
                'csrf_token': 'test_token'
            }
            
            form = UniversalPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == False
            assert 'Book type is required for books' in str(form.book_type.errors)


class TestJournalPublicationForm:
    """Test JournalPublicationForm validation."""
    
    def test_valid_journal_form(self, app):
        """Test valid journal form."""
        with app.app_context():
            form_data = {
                'publication_type': 'journal',
                'title': 'Test Journal',
                'language_code': 'en',
                'journal_abbreviated_title': 'Test J.',
                'journal_issn': '1234-5678',
                'csrf_token': 'test_token'
            }
            
            form = JournalPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == True
    
    def test_journal_issn_validation(self, app):
        """Test journal ISSN validation."""
        with app.app_context():
            from werkzeug.datastructures import MultiDict
            form_data = MultiDict([
                ('publication_type', 'journal'),
                ('title', 'Test Journal'),
                ('language_code', 'en'),
                ('journal_issn', 'bad-format'),
                ('csrf_token', 'test_token')
            ])
            
            form = JournalPublicationForm(formdata=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == False
            assert 'ISSN format should be XXXX-XXXX' in str(form.journal_issn.errors)


class TestBookSeriesPublicationForm:
    """Test BookSeriesPublicationForm validation."""
    
    def test_valid_book_series_form(self, app):
        """Test valid book series form."""
        with app.app_context():
            form_data = {
                'publication_type': 'book_series',
                'title': 'Test Series',
                'language_code': 'en',
                'series_title': 'Academic Series',
                'series_issn': '9876-5432',
                'csrf_token': 'test_token'
            }
            
            form = BookSeriesPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == True
    
    def test_series_title_required(self, app):
        """Test that series title is required."""
        with app.app_context():
            form_data = {
                'publication_type': 'book_series',
                'title': 'Test Series',
                'language_code': 'en',
                # Missing series_title
                'csrf_token': 'test_token'
            }
            
            form = BookSeriesPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == False
            assert 'This field is required.' in str(form.series_title.errors)


class TestBookSetPublicationForm:
    """Test BookSetPublicationForm validation."""
    
    def test_valid_book_set_form(self, app):
        """Test valid book set form."""
        with app.app_context():
            form_data = {
                'publication_type': 'book_set',
                'title': 'Test Set',
                'language_code': 'en',
                'set_title': 'Academic Book Set',
                'set_isbn': '9781234567890',
                'csrf_token': 'test_token'
            }
            
            form = BookSetPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == True
    
    def test_set_isbn_validation(self, app):
        """Test set ISBN validation."""
        with app.app_context():
            from werkzeug.datastructures import MultiDict
            form_data = MultiDict([
                ('publication_type', 'book_set'),
                ('title', 'Test Set'),
                ('language_code', 'en'),
                ('set_title', 'Academic Book Set'),
                ('set_isbn', 'invalid-isbn'),
                ('csrf_token', 'test_token')
            ])
            
            form = BookSetPublicationForm(formdata=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == False
            assert 'Invalid ISBN format' in str(form.set_isbn.errors)


class TestBookPublicationForm:
    """Test BookPublicationForm validation."""
    
    def test_valid_book_form(self, app):
        """Test valid book form."""
        with app.app_context():
            form_data = {
                'publication_type': 'book',
                'title': 'Test Book',
                'language_code': 'en',
                'book_type': 'monograph',
                'edition_number': 1,
                'isbn': '9781234567890',
                'csrf_token': 'test_token'
            }
            
            form = BookPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == True
    
    def test_book_type_required(self, app):
        """Test that book type is required."""
        with app.app_context():
            form_data = {
                'publication_type': 'book',
                'title': 'Test Book',
                'language_code': 'en',
                # Missing book_type
                'csrf_token': 'test_token'
            }
            
            form = BookPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == False
            assert 'This field is required.' in str(form.book_type.errors)
    
    def test_edition_number_validation(self, app):
        """Test edition number validation."""
        with app.app_context():
            form_data = {
                'publication_type': 'book',
                'title': 'Test Book',
                'language_code': 'en',
                'book_type': 'monograph',
                'edition_number': 'invalid',  # Should be integer
                'csrf_token': 'test_token'
            }
            
            form = BookPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            # Edition number field should handle invalid input gracefully
            assert form.validate() == False or form.edition_number.data is None


class TestFormRenderAttributes:
    """Test form render attributes for frontend integration."""
    
    def test_form_field_classes(self, app):
        """Test that form fields have correct CSS classes."""
        with app.app_context():
            form = UniversalPublicationForm()
            
            # Check that fields have Bootstrap classes
            assert 'form-control' in form.title.render_kw.get('class', '')
            assert 'form-control' in form.publication_type.render_kw.get('class', '')
            assert 'form-control' in form.journal_issn.render_kw.get('class', '')
    
    def test_form_field_data_attributes(self, app):
        """Test that type-specific fields have correct data attributes."""
        with app.app_context():
            form = UniversalPublicationForm()
            
            # Check data-type attributes for conditional display
            assert form.journal_issn.render_kw.get('data-type') == 'journal'
            assert form.series_title.render_kw.get('data-type') == 'book_series'
            assert form.set_title.render_kw.get('data-type') == 'book_set'
            assert form.book_type.render_kw.get('data-type') == 'book'
    
    def test_form_placeholders(self, app):
        """Test that fields have appropriate placeholders."""
        with app.app_context():
            form = UniversalPublicationForm()
            
            assert 'XXXX-XXXX' in form.journal_issn.render_kw.get('placeholder', '')
            assert 'ISBN-10 or ISBN-13' in form.isbn.render_kw.get('placeholder', '')
            assert 'CODEN' in form.journal_coden.render_kw.get('placeholder', '')


class TestFormIntegration:
    """Test form integration with models and services."""
    
    def test_form_data_extraction_pattern(self, app):
        """Test that form data can be extracted in expected pattern."""
        with app.app_context():
            form_data = {
                'publication_type': 'journal',
                'title': 'Integration Test Journal',
                'subtitle': 'Test Subtitle',
                'language_code': 'sr',
                'journal_abbreviated_title': 'Int. Test J.',
                'journal_issn': '1111-2222',
                'journal_electronic_issn': '1111-2223',
                'journal_coden': 'ITJNLX',
                'csrf_token': 'test_token'
            }
            
            form = UniversalPublicationForm(data=form_data)
            # CSRF is disabled in test config
            
            assert form.validate() == True
            
            # Test that data can be extracted in service-compatible format
            extracted_data = {
                'publication_type': form.publication_type.data,
                'title': form.title.data,
                'subtitle': form.subtitle.data,
                'language_code': form.language_code.data,
                'journal_abbreviated_title': form.journal_abbreviated_title.data,
                'journal_issn': form.journal_issn.data,
                'journal_electronic_issn': form.journal_electronic_issn.data,
                'journal_coden': form.journal_coden.data
            }
            
            assert extracted_data['publication_type'] == 'journal'
            assert extracted_data['title'] == 'Integration Test Journal'
            assert extracted_data['journal_issn'] == '1111-2222'