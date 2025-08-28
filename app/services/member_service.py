"""
Member service layer - business logic for member management.
"""

from typing import Optional, Dict, Any
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from flask import current_app
from app import db
from app.models.member import Member
from app.models.publication import Publication


class MemberService:
    """Service class for member-related business operations."""
    
    @staticmethod
    def get_members_for_sponsor(sponsor_id: int, page: int = 1, per_page: int = 10, 
                               search: str = '', status: str = 'all') -> object:
        """
        Get paginated members for a sponsor with search and filtering.
        
        Args:
            sponsor_id: ID of the sponsor
            page: Page number for pagination
            per_page: Number of items per page
            search: Search term for name/institution
            status: Filter by status (all, active, inactive)
            
        Returns:
            Pagination object with members
        """
        query = Member.query.filter_by(sponsor_id=sponsor_id)
        
        # Apply search filter
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Member.name.ilike(search_term),
                    Member.institution.ilike(search_term),
                    Member.contact_email.ilike(search_term)
                )
            )
        
        # Apply status filter
        if status == 'active':
            query = query.filter_by(is_active=True)
        elif status == 'inactive':
            query = query.filter_by(is_active=False)
        
        # Order by name
        query = query.order_by(Member.name.asc())
        
        # Paginate
        return query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    @staticmethod
    def get_member_by_id(member_id: int, sponsor_id: int) -> Optional[Member]:
        """
        Get a member by ID, ensuring it belongs to the sponsor.
        
        Args:
            member_id: ID of the member
            sponsor_id: ID of the sponsor (for security)
            
        Returns:
            Member object or None if not found
        """
        return Member.query.filter_by(
            id=member_id,
            sponsor_id=sponsor_id
        ).first()
    
    @staticmethod
    def create_member(sponsor_id: int, form_data: Dict[str, Any]) -> Member:
        """
        Create a new member with validation.
        
        Args:
            sponsor_id: ID of the sponsor
            form_data: Form data dictionary
            
        Returns:
            Created Member object
            
        Raises:
            ValueError: If validation fails
            IntegrityError: If database constraints are violated
        """
        try:
            # Check if email already exists for this sponsor
            existing_member = Member.query.filter_by(
                sponsor_id=sponsor_id,
                contact_email=form_data['contact_email'].lower().strip()
            ).first()
            
            if existing_member:
                raise ValueError("Član sa ovim email adresom već postoji.")
            
            # Create new member using model's create method
            member = Member.create_member(
                sponsor_id=sponsor_id,
                name=form_data['name'],
                institution=form_data['institution'],
                contact_email=form_data['contact_email'],
                website_url=form_data.get('website_url'),
                billing_address=form_data['billing_address'],
                pib=form_data['pib'],
                matični_broj=form_data['matični_broj'],
                jmbg_lk=form_data.get('jmbg_lk'),
                šifra_delatnosti=form_data['šifra_delatnosti'],
                telefon=form_data['telefon'],
                osoba_za_kontakt=form_data['osoba_za_kontakt'],
                iban=form_data['iban'],
                naziv_banke=form_data['naziv_banke'],
                swift_bic=form_data['swift_bic'],
                pdv_status=form_data['pdv_status'],
                država_obveznika=form_data['država_obveznika'],
                is_active=form_data.get('is_active', True)
            )
            
            current_app.logger.info(f"Member created: {member.name} (ID: {member.id}) for sponsor {sponsor_id}")
            return member
            
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"IntegrityError creating member: {str(e)}")
            raise ValueError("Greška pri kreiranju člana - možda već postoje slični podaci.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating member: {str(e)}")
            raise
    
    @staticmethod
    def update_member(member_id: int, sponsor_id: int, form_data: Dict[str, Any]) -> Member:
        """
        Update an existing member with validation.
        
        Args:
            member_id: ID of the member to update
            sponsor_id: ID of the sponsor (for security)
            form_data: Form data dictionary
            
        Returns:
            Updated Member object
            
        Raises:
            ValueError: If validation fails or member not found
        """
        member = MemberService.get_member_by_id(member_id, sponsor_id)
        if not member:
            raise ValueError("Član nije pronađen.")
        
        try:
            # Check if email already exists for this sponsor (excluding current member)
            existing_member = Member.query.filter(
                Member.sponsor_id == sponsor_id,
                Member.contact_email == form_data['contact_email'].lower().strip(),
                Member.id != member_id
            ).first()
            
            if existing_member:
                raise ValueError("Član sa ovim email adresom već postoji.")
            
            # Update member fields
            member.name = form_data['name'].strip()
            member.institution = form_data['institution'].strip()
            member.contact_email = form_data['contact_email'].lower().strip()
            member.website_url = form_data.get('website_url', '').strip() or None
            member.billing_address = form_data['billing_address'].strip()
            member.pib = form_data['pib'].strip()
            member.matični_broj = form_data['matični_broj'].strip()
            member.jmbg_lk = form_data.get('jmbg_lk', '').strip() or None
            member.šifra_delatnosti = form_data['šifra_delatnosti'].strip()
            member.telefon = form_data['telefon'].strip()
            member.osoba_za_kontakt = form_data['osoba_za_kontakt'].strip()
            member.iban = form_data['iban'].strip()
            member.naziv_banke = form_data['naziv_banke'].strip()
            member.swift_bic = form_data['swift_bic'].strip()
            member.pdv_status = form_data['pdv_status']
            member.država_obveznika = form_data['država_obveznika']
            member.is_active = form_data.get('is_active', True)
            
            # Save changes
            member = member.save()
            
            current_app.logger.info(f"Member updated: {member.name} (ID: {member.id}) for sponsor {sponsor_id}")
            return member
            
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"IntegrityError updating member: {str(e)}")
            raise ValueError("Greška pri ažuriranju člana - možda već postoje slični podaci.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating member: {str(e)}")
            raise
    
    @staticmethod
    def toggle_member_status(member_id: int, sponsor_id: int) -> Member:
        """
        Toggle member active/inactive status (soft delete).
        
        Args:
            member_id: ID of the member
            sponsor_id: ID of the sponsor (for security)
            
        Returns:
            Updated Member object
            
        Raises:
            ValueError: If member not found
        """
        member = MemberService.get_member_by_id(member_id, sponsor_id)
        if not member:
            raise ValueError("Član nije pronađen.")
        
        try:
            # Toggle status
            old_status = member.is_active
            if member.is_active:
                member = member.deactivate()
            else:
                member = member.activate()
            
            status_change = f"{'active' if member.is_active else 'inactive'} (was {'active' if old_status else 'inactive'})"
            current_app.logger.info(f"Member status toggled: {member.name} (ID: {member.id}) -> {status_change}")
            
            return member
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error toggling member status: {str(e)}")
            raise
    
    @staticmethod
    def search_members(sponsor_id: int, search_term: str, page: int = 1, per_page: int = 5) -> object:
        """
        Search members by name or institution with pagination.
        
        Args:
            sponsor_id: ID of the sponsor
            search_term: Search term
            page: Page number
            per_page: Items per page
            
        Returns:
            Pagination object with search results
        """
        if not search_term or len(search_term) < 2:
            # Return empty pagination
            return Member.query.filter_by(sponsor_id=sponsor_id).filter(Member.id == -1).paginate(
                page=page, per_page=per_page, error_out=False
            )
        
        search_pattern = f"%{search_term.strip()}%"
        
        query = Member.query.filter_by(sponsor_id=sponsor_id).filter(
            or_(
                Member.name.ilike(search_pattern),
                Member.institution.ilike(search_pattern),
                Member.contact_email.ilike(search_pattern)
            )
        ).order_by(Member.name.asc())
        
        return query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    @staticmethod
    def get_member_statistics(sponsor_id: int) -> Dict[str, int]:
        """
        Get member statistics for a sponsor.
        
        Args:
            sponsor_id: ID of the sponsor
            
        Returns:
            Dictionary with statistics
        """
        try:
            total_members = Member.query.filter_by(sponsor_id=sponsor_id).count()
            active_members = Member.query.filter_by(sponsor_id=sponsor_id, is_active=True).count()
            inactive_members = total_members - active_members
            
            # Get members with publications
            members_with_publications = db.session.query(Member.id).join(Publication).filter(
                Member.sponsor_id == sponsor_id
            ).distinct().count()
            
            return {
                'total': total_members,
                'active': active_members,
                'inactive': inactive_members,
                'with_publications': members_with_publications
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting member statistics: {str(e)}")
            return {
                'total': 0,
                'active': 0,
                'inactive': 0,
                'with_publications': 0
            }
    
    @staticmethod
    def get_member_publication_count(member_id: int) -> int:
        """
        Get publication count for a member.
        
        Args:
            member_id: ID of the member
            
        Returns:
            Number of publications
        """
        try:
            return Publication.query.filter_by(member_id=member_id).count()
        except Exception as e:
            current_app.logger.error(f"Error getting publication count for member {member_id}: {str(e)}")
            return 0
    
    @staticmethod
    def get_active_members_for_sponsor(sponsor_id: int) -> list:
        """
        Get all active members for a sponsor (for dropdowns, etc.).
        
        Args:
            sponsor_id: ID of the sponsor
            
        Returns:
            List of active Member objects
        """
        return Member.query.filter_by(
            sponsor_id=sponsor_id,
            is_active=True
        ).order_by(Member.name.asc()).all()
    
    @staticmethod
    def validate_member_data(form_data: Dict[str, Any], member_id: Optional[int] = None) -> Dict[str, str]:
        """
        Validate member data and return errors.
        
        Args:
            form_data: Form data to validate
            member_id: ID of existing member (for updates)
            
        Returns:
            Dictionary of field_name: error_message
        """
        errors = {}
        
        # Required fields validation
        required_fields = [
            'name', 'institution', 'contact_email', 'billing_address',
            'pib', 'matični_broj', 'šifra_delatnosti', 'telefon',
            'osoba_za_kontakt', 'iban', 'naziv_banke', 'swift_bic',
            'pdv_status', 'država_obveznika'
        ]
        
        for field in required_fields:
            if not form_data.get(field, '').strip():
                errors[field] = f"{field.replace('_', ' ').title()} je obavezan."
        
        # Email format validation
        if 'contact_email' in form_data:
            if not Member._validate_email(form_data['contact_email']):
                errors['contact_email'] = "Nevaljan format email adrese."
        
        # PIB validation
        if 'pib' in form_data:
            pib = form_data['pib'].strip()
            if pib and not pib.isdigit():
                errors['pib'] = "PIB može sadržavati samo brojeve."
            elif pib and len(pib) not in [9, 12]:
                errors['pib'] = "PIB obično ima 9 ili 12 cifara."
        
        # Matični broj validation
        if 'matični_broj' in form_data:
            mb = form_data['matični_broj'].strip()
            if mb and not mb.isdigit():
                errors['matični_broj'] = "Matični broj može sadržavati samo brojeve."
        
        return errors