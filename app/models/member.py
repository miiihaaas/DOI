"""
Member model - represents member organizations under the DOI sponsor.
"""

from email_validator import validate_email, EmailNotValidError
from sqlalchemy.exc import IntegrityError
from app import db
from app.models.base import BaseModel


class Member(BaseModel):
    """
    Member model - represents member organizations that publish content.
    Members belong to the sponsor organization and have their publications registered.
    """

    __tablename__ = 'members'

    # Foreign key relationship to Sponsor
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsors.id', ondelete='CASCADE'), 
                          nullable=False, index=True)

    # Core organization fields
    name = db.Column(db.String(200), nullable=False, index=True)
    institution = db.Column(db.String(200), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False, index=True)
    website_url = db.Column(db.String(255), nullable=True)
    
    # Billing and legal information
    billing_address = db.Column(db.Text, nullable=False)
    pib = db.Column(db.String(20), nullable=False)  # PIB number
    matični_broj = db.Column(db.String(20), nullable=False)  # Company registration number
    jmbg_lk = db.Column(db.String(20), nullable=True)  # JMBG or ID card for individuals
    šifra_delatnosti = db.Column(db.String(10), nullable=False)  # Business activity code
    
    # Contact information
    telefon = db.Column(db.String(20), nullable=False)
    osoba_za_kontakt = db.Column(db.String(100), nullable=False)  # Contact person name
    
    # Banking information
    iban = db.Column(db.String(34), nullable=False)  # Bank account IBAN
    naziv_banke = db.Column(db.String(100), nullable=False)  # Bank name
    swift_bic = db.Column(db.String(11), nullable=False)  # SWIFT/BIC code
    
    # Tax information
    pdv_status = db.Column(db.String(50), nullable=False)  # VAT system status
    država_obveznika = db.Column(db.String(50), nullable=False)  # Tax obligor country
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)

    # Relationships
    sponsor = db.relationship('Sponsor', backref=db.backref('members', lazy='dynamic', cascade='all, delete-orphan'))
    # publications relationship je definisan u Publication modelu preko backref

    # Indexes for performance
    __table_args__ = (
        db.Index('idx_member_sponsor_active', 'sponsor_id', 'is_active'),
        db.Index('idx_member_name', 'name'),
        db.Index('idx_member_email', 'contact_email'),
    )

    def __repr__(self):
        """String representation for debugging."""
        return f"<Member(id={self.id}, name='{self.name}', institution='{self.institution}', email='{self.contact_email}')>"

    def __str__(self):
        """Human-readable string representation."""
        return f"Member: {self.name} ({self.institution})"

    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            'sponsor_id': self.sponsor_id,
            'name': self.name,
            'institution': self.institution,
            'contact_email': self.contact_email,
            'website_url': self.website_url,
            'billing_address': self.billing_address,
            'pib': self.pib,
            'matični_broj': self.matični_broj,
            'jmbg_lk': self.jmbg_lk,
            'šifra_delatnosti': self.šifra_delatnosti,
            'telefon': self.telefon,
            'osoba_za_kontakt': self.osoba_za_kontakt,
            'iban': self.iban,
            'naziv_banke': self.naziv_banke,
            'swift_bic': self.swift_bic,
            'pdv_status': self.pdv_status,
            'država_obveznika': self.država_obveznika,
            'is_active': self.is_active
        })
        return base_dict

    @classmethod
    def create_member(cls, sponsor_id, name, institution, contact_email, billing_address, 
                     pib, matični_broj, šifra_delatnosti, telefon, osoba_za_kontakt, 
                     iban, naziv_banke, swift_bic, pdv_status, država_obveznika,
                     website_url=None, jmbg_lk=None, is_active=True):
        """Create a new member with validation."""
        
        # Validate email format
        if not cls._validate_email(contact_email):
            raise ValueError("Invalid email format")
        
        # Validate required fields
        if not name or not name.strip():
            raise ValueError("Member name is required")
        if not institution or not institution.strip():
            raise ValueError("Institution name is required")
        if not billing_address or not billing_address.strip():
            raise ValueError("Billing address is required")
        if not pib or not pib.strip():
            raise ValueError("PIB number is required")
        if not matični_broj or not matični_broj.strip():
            raise ValueError("Company registration number is required")
        if not šifra_delatnosti or not šifra_delatnosti.strip():
            raise ValueError("Business activity code is required")
        if not telefon or not telefon.strip():
            raise ValueError("Phone number is required")
        if not osoba_za_kontakt or not osoba_za_kontakt.strip():
            raise ValueError("Contact person name is required")
        if not iban or not iban.strip():
            raise ValueError("IBAN is required")
        if not naziv_banke or not naziv_banke.strip():
            raise ValueError("Bank name is required")
        if not swift_bic or not swift_bic.strip():
            raise ValueError("SWIFT/BIC code is required")
        if not pdv_status or not pdv_status.strip():
            raise ValueError("VAT status is required")
        if not država_obveznika or not država_obveznika.strip():
            raise ValueError("Tax obligor country is required")

        # Create new member
        member = cls(
            sponsor_id=sponsor_id,
            name=name.strip(),
            institution=institution.strip(),
            contact_email=contact_email.strip().lower(),
            website_url=website_url.strip() if website_url else None,
            billing_address=billing_address.strip(),
            pib=pib.strip(),
            matični_broj=matični_broj.strip(),
            jmbg_lk=jmbg_lk.strip() if jmbg_lk else None,
            šifra_delatnosti=šifra_delatnosti.strip(),
            telefon=telefon.strip(),
            osoba_za_kontakt=osoba_za_kontakt.strip(),
            iban=iban.strip(),
            naziv_banke=naziv_banke.strip(),
            swift_bic=swift_bic.strip(),
            pdv_status=pdv_status.strip(),
            država_obveznika=država_obveznika.strip(),
            is_active=is_active
        )

        return member.save()

    @staticmethod
    def _validate_email(email):
        """Validate email format using email-validator library."""
        try:
            # Use check_deliverability=False to avoid DNS checks in tests
            validate_email(email, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False

    @classmethod
    def get_by_sponsor(cls, sponsor_id, active_only=True):
        """Get all members for a sponsor."""
        query = cls.query.filter_by(sponsor_id=sponsor_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()

    @classmethod
    def get_active_members(cls):
        """Get all active members."""
        return cls.query.filter_by(is_active=True).all()

    def deactivate(self):
        """Deactivate the member."""
        self.is_active = False
        return self.save()

    def activate(self):
        """Activate the member."""
        self.is_active = True
        return self.save()

    def update_contact_info(self, contact_email=None, telefon=None, osoba_za_kontakt=None):
        """Update member contact information."""
        if contact_email is not None:
            if not self._validate_email(contact_email):
                raise ValueError("Invalid email format")
            self.contact_email = contact_email.strip().lower()
        
        if telefon is not None:
            self.telefon = telefon.strip()
        
        if osoba_za_kontakt is not None:
            self.osoba_za_kontakt = osoba_za_kontakt.strip()
        
        return self.save()

    def update_banking_info(self, iban=None, naziv_banke=None, swift_bic=None):
        """Update member banking information."""
        if iban is not None:
            self.iban = iban.strip()
        
        if naziv_banke is not None:
            self.naziv_banke = naziv_banke.strip()
        
        if swift_bic is not None:
            self.swift_bic = swift_bic.strip()
        
        return self.save()