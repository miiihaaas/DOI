"""
Member form definitions using Flask-WTF for member management.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, BooleanField, 
    SubmitField, HiddenField
)
from wtforms.validators import (
    DataRequired, Email, Length, Optional, URL, Regexp, ValidationError
)
from wtforms.widgets import TextArea
from app.models.member import Member


class MemberBaseForm(FlaskForm):
    """Base form with common member fields."""
    
    # Core organization fields
    name = StringField(
        'Naziv člana *',
        validators=[
            DataRequired(message='Naziv člana je obavezan.'),
            Length(min=2, max=200, message='Naziv mora biti između 2 i 200 karaktera.')
        ],
        render_kw={
            'placeholder': 'Unesite naziv članove organizacije',
            'class': 'form-control'
        }
    )
    
    institution = StringField(
        'Naziv institucije *',
        validators=[
            DataRequired(message='Naziv institucije je obavezan.'),
            Length(min=2, max=200, message='Naziv institucije mora biti između 2 i 200 karaktera.')
        ],
        render_kw={
            'placeholder': 'Unesite puni naziv institucije',
            'class': 'form-control'
        }
    )
    
    contact_email = StringField(
        'Email za kontakt *',
        validators=[
            DataRequired(message='Email je obavezan.'),
            Email(message='Unesite validan email format.'),
            Length(max=120, message='Email ne može biti duži od 120 karaktera.')
        ],
        render_kw={
            'placeholder': 'contact@example.com',
            'class': 'form-control',
            'type': 'email'
        }
    )
    
    website_url = StringField(
        'Web sajt',
        validators=[
            Optional(),
            URL(message='Unesite validan URL format (http://... ili https://...)'),
            Length(max=255, message='URL ne može biti duži od 255 karaktera.')
        ],
        render_kw={
            'placeholder': 'https://www.example.com',
            'class': 'form-control',
            'type': 'url'
        }
    )
    
    # Billing and legal information
    billing_address = TextAreaField(
        'Adresa za naplatu *',
        validators=[
            DataRequired(message='Adresa za naplatu je obavezna.'),
            Length(min=5, max=500, message='Adresa mora biti između 5 i 500 karaktera.')
        ],
        render_kw={
            'placeholder': 'Unesite kompletnu adresu za naplatu',
            'class': 'form-control',
            'rows': 3
        }
    )
    
    pib = StringField(
        'PIB broj *',
        validators=[
            DataRequired(message='PIB broj je obavezan.'),
            Length(min=8, max=20, message='PIB broj mora biti između 8 i 20 karaktera.'),
            Regexp(
                r'^\d+$', 
                message='PIB broj može sadržavati samo brojeve.'
            )
        ],
        render_kw={
            'placeholder': '123456789',
            'class': 'form-control'
        }
    )
    
    matični_broj = StringField(
        'Matični broj *',
        validators=[
            DataRequired(message='Matični broj je obavezan.'),
            Length(min=8, max=20, message='Matični broj mora biti između 8 i 20 karaktera.'),
            Regexp(
                r'^\d+$', 
                message='Matični broj može sadržavati samo brojeve.'
            )
        ],
        render_kw={
            'placeholder': '12345678',
            'class': 'form-control'
        }
    )
    
    jmbg_lk = StringField(
        'JMBG/Lična karta',
        validators=[
            Optional(),
            Length(min=13, max=20, message='JMBG/LK mora biti između 13 i 20 karaktera.')
        ],
        render_kw={
            'placeholder': '1234567890123 (opciono)',
            'class': 'form-control'
        }
    )
    
    šifra_delatnosti = StringField(
        'Šifra delatnosti *',
        validators=[
            DataRequired(message='Šifra delatnosti je obavezna.'),
            Length(min=4, max=10, message='Šifra delatnosti mora biti između 4 i 10 karaktera.'),
            Regexp(
                r'^\d{4,6}$', 
                message='Šifra delatnosti mora biti broj od 4-6 cifara.'
            )
        ],
        render_kw={
            'placeholder': '7220',
            'class': 'form-control'
        }
    )
    
    # Contact information
    telefon = StringField(
        'Telefon *',
        validators=[
            DataRequired(message='Telefon je obavezan.'),
            Length(min=8, max=20, message='Telefon mora biti između 8 i 20 karaktera.'),
            Regexp(
                r'^[\+]?[\d\s\-\(\)]+$', 
                message='Telefon može sadržavati brojeve, +, -, (), razmake.'
            )
        ],
        render_kw={
            'placeholder': '+381 11 123-4567',
            'class': 'form-control'
        }
    )
    
    osoba_za_kontakt = StringField(
        'Osoba za kontakt *',
        validators=[
            DataRequired(message='Osoba za kontakt je obavezna.'),
            Length(min=2, max=100, message='Ime osobe mora biti između 2 i 100 karaktera.')
        ],
        render_kw={
            'placeholder': 'Ime i prezime osobe za kontakt',
            'class': 'form-control'
        }
    )
    
    # Banking information
    iban = StringField(
        'IBAN broj računa *',
        validators=[
            DataRequired(message='IBAN broj je obavezan.'),
            Length(min=15, max=34, message='IBAN mora biti između 15 i 34 karaktera.'),
            Regexp(
                r'^[A-Z]{2}\d{2}[\w\d]+$', 
                message='IBAN mora počinjati sa 2 slova, 2 broja, zatim alfanumerički karakteri.'
            )
        ],
        render_kw={
            'placeholder': 'RS35260005601001611379',
            'class': 'form-control',
            'style': 'text-transform: uppercase;'
        }
    )
    
    naziv_banke = StringField(
        'Naziv banke *',
        validators=[
            DataRequired(message='Naziv banke je obavezan.'),
            Length(min=2, max=100, message='Naziv banke mora biti između 2 i 100 karaktera.')
        ],
        render_kw={
            'placeholder': 'Naziv banke',
            'class': 'form-control'
        }
    )
    
    swift_bic = StringField(
        'SWIFT/BIC kod *',
        validators=[
            DataRequired(message='SWIFT/BIC kod je obavezan.'),
            Length(min=8, max=11, message='SWIFT/BIC mora biti 8 ili 11 karaktera.'),
            Regexp(
                r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$', 
                message='SWIFT/BIC mora biti u formatu: 6 slova + 2 alfanumerička + opciono 3 alfanumerička.'
            )
        ],
        render_kw={
            'placeholder': 'BKAUTWW1',
            'class': 'form-control',
            'style': 'text-transform: uppercase;'
        }
    )
    
    # Tax information
    pdv_status = SelectField(
        'PDV status *',
        choices=[
            ('', 'Izaberite PDV status'),
            ('obveznik_pdv', 'Obveznik PDV-a'),
            ('nije_obveznik_pdv', 'Nije obveznik PDV-a'),
            ('oslobodjen_pdv', 'Oslobođen PDV-a'),
            ('paušalni_obveznik', 'Paušalni obveznik')
        ],
        validators=[
            DataRequired(message='PDV status je obavezan.')
        ],
        render_kw={
            'class': 'form-select'
        }
    )
    
    država_obveznika = SelectField(
        'Država obveznika *',
        choices=[
            ('', 'Izaberite državu'),
            ('Srbija', 'Srbija'),
            ('Crna Gora', 'Crna Gora'),
            ('Bosna i Hercegovina', 'Bosna i Hercegovina'),
            ('Hrvatska', 'Hrvatska'),
            ('Slovenija', 'Slovenija'),
            ('Sjeverna Makedonija', 'Sjeverna Makedonija'),
            ('Ostalo', 'Ostalo')
        ],
        validators=[
            DataRequired(message='Država obveznika je obavezna.')
        ],
        render_kw={
            'class': 'form-select'
        }
    )
    
    def validate_pib(self, field):
        """Custom PIB validation."""
        pib = field.data.strip()
        if len(pib) not in [9, 12]:  # Common PIB lengths in Serbia
            raise ValidationError('PIB broj obično ima 9 ili 12 cifara.')
    
    def validate_iban(self, field):
        """Custom IBAN validation."""
        iban = field.data.strip().replace(' ', '').upper()
        field.data = iban  # Clean the data
        
        if not iban.startswith(('RS', 'ME', 'BA', 'HR', 'SI', 'MK')):
            raise ValidationError('IBAN mora biti iz Balkanske zemlje (RS, ME, BA, HR, SI, MK).')


class MemberCreateForm(MemberBaseForm):
    """Form for creating new members."""
    
    is_active = BooleanField(
        'Aktivan član',
        default=True,
        render_kw={
            'class': 'form-check-input'
        }
    )
    
    submit = SubmitField(
        'Kreiraj člana',
        render_kw={
            'class': 'btn btn-primary'
        }
    )
    
    def validate_contact_email(self, field):
        """Check if email is unique within sponsor."""
        # Note: This validation will be enhanced in service layer
        # to check uniqueness within sponsor context
        pass


class MemberEditForm(MemberBaseForm):
    """Form for editing existing members."""
    
    member_id = HiddenField()
    
    is_active = BooleanField(
        'Aktivan član',
        render_kw={
            'class': 'form-check-input'
        }
    )
    
    submit = SubmitField(
        'Ažuriraj člana',
        render_kw={
            'class': 'btn btn-success'
        }
    )
    
    def validate_contact_email(self, field):
        """Check if email is unique within sponsor (excluding current member)."""
        # Note: This validation will be enhanced in service layer
        # to check uniqueness within sponsor context excluding current member
        pass


class MemberSearchForm(FlaskForm):
    """Form for searching and filtering members."""
    
    search = StringField(
        'Pretraži članove',
        validators=[
            Optional(),
            Length(max=100, message='Pretraga ne može biti duža od 100 karaktera.')
        ],
        render_kw={
            'placeholder': 'Pretražite po nazivu ili instituciji...',
            'class': 'form-control',
            'autocomplete': 'off'
        }
    )
    
    status = SelectField(
        'Status',
        choices=[
            ('all', 'Svi članovi'),
            ('active', 'Samo aktivni'),
            ('inactive', 'Samo neaktivni')
        ],
        default='all',
        render_kw={
            'class': 'form-select'
        }
    )
    
    submit = SubmitField(
        'Pretraži',
        render_kw={
            'class': 'btn btn-outline-primary'
        }
    )


class MemberStatusToggleForm(FlaskForm):
    """Form for toggling member active status."""
    
    member_id = HiddenField(validators=[DataRequired()])
    
    submit_activate = SubmitField(
        'Aktiviraj',
        render_kw={
            'class': 'btn btn-success btn-sm',
            'onclick': 'return confirm("Da li ste sigurni da želite da aktivirajte ovog člana?");'
        }
    )
    
    submit_deactivate = SubmitField(
        'Deaktiviraj',
        render_kw={
            'class': 'btn btn-warning btn-sm',
            'onclick': 'return confirm("Da li ste sigurni da želite da deaktivirajte ovog člana?");'
        }
    )