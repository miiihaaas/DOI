import csv
import io
from datetime import datetime
from flask import current_app
from flask_login import current_user
from sqlalchemy import and_
from app import db
from app.models.member import Member
from app.models.publication import Publication


class ExportService:
    """Service za izvoz podataka u CSV format."""
    
    @staticmethod
    def export_members_csv(sponsor_id, filters=None):
        """
        Izvozi članove u CSV format.
        
        Args:
            sponsor_id (int): ID sponzora
            filters (dict): Opcioni filteri (active_only, date_range, search_query)
            
        Returns:
            tuple: (csv_content, filename)
        """
        # Base query
        query = Member.query.filter_by(sponsor_id=sponsor_id)
        
        # Primeni filtere
        if filters:
            if filters.get('active_only'):
                query = query.filter(Member.is_active == True)
            
            if filters.get('search_query'):
                search_term = f"%{filters['search_query']}%"
                query = query.filter(
                    Member.name.ilike(search_term) |
                    Member.institution.ilike(search_term) |
                    Member.contact_email.ilike(search_term)
                )
            
            if filters.get('date_from'):
                query = query.filter(Member.created_at >= filters['date_from'])
            
            if filters.get('date_to'):
                query = query.filter(Member.created_at <= filters['date_to'])
        
        members = query.order_by(Member.name).all()
        
        # Generiši CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        headers = [
            'ID',
            'Ime',
            'Institucija', 
            'Email',
            'Website',
            'Aktivni',
            'Broj publikacija',
            'Aktivne publikacije',
            'Ukupno DOI draftova',
            'Potvrđeni DOI',
            'Kreiran',
            'Poslednja izmena'
        ]
        writer.writerow(headers)
        
        # Data rows
        for member in members:
            # Aggregated statistics
            total_publications = len(member.publications)
            active_publications = len([p for p in member.publications if p.is_active])
            
            # TODO: Implementirati kada se kreira DOIDraft model
            total_drafts = 0
            confirmed_drafts = 0
            
            row = [
                member.id,
                member.name,
                member.institution or '',
                member.contact_email or '',
                member.website_url or '',
                'Da' if member.is_active else 'Ne',
                total_publications,
                active_publications,
                total_drafts,
                confirmed_drafts,
                member.created_at.strftime('%d.%m.%Y %H:%M') if member.created_at else '',
                member.updated_at.strftime('%d.%m.%Y %H:%M') if member.updated_at else ''
            ]
            writer.writerow(row)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'membres_export_{timestamp}.csv'
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content, filename
    
    @staticmethod
    def export_publications_csv(sponsor_id, filters=None):
        """
        Izvozi publikacije u CSV format.
        
        Args:
            sponsor_id (int): ID sponzora
            filters (dict): Opcioni filteri
            
        Returns:
            tuple: (csv_content, filename)
        """
        # Base query with join
        query = Publication.query.join(Member).filter(Member.sponsor_id == sponsor_id)
        
        # Primeni filtere
        if filters:
            if filters.get('active_only'):
                query = query.filter(Publication.is_active == True)
            
            if filters.get('publication_type'):
                query = query.filter(Publication.publication_type == filters['publication_type'])
            
            if filters.get('member_id'):
                query = query.filter(Publication.member_id == filters['member_id'])
            
            if filters.get('search_query'):
                search_term = f"%{filters['search_query']}%"
                query = query.filter(
                    Publication.title.ilike(search_term) |
                    Publication.publisher.ilike(search_term) |
                    Publication.issn_isbn.ilike(search_term) |
                    Member.name.ilike(search_term)
                )
            
            if filters.get('date_from'):
                query = query.filter(Publication.created_at >= filters['date_from'])
            
            if filters.get('date_to'):
                query = query.filter(Publication.created_at <= filters['date_to'])
        
        publications = query.order_by(Member.name, Publication.title).all()
        
        # Generiši CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        headers = [
            'ID',
            'Naslov',
            'Tip publikacije',
            'Član',
            'Institucija člana',
            'ISSN/ISBN',
            'Izdavač',
            'Jezik',
            'Aktivna',
            'Broj DOI draftova',
            'Draft DOI',
            'XML generirani',
            'XML poslati', 
            'Potvrđeni DOI',
            'Kreirana',
            'Poslednja izmena'
        ]
        writer.writerow(headers)
        
        # Data rows
        for publication in publications:
            # TODO: Implementirati kada se kreira DOIDraft model
            drafts = []
            draft_counts = {
                'draft': 0,
                'xml_generated': 0,
                'xml_sent': 0,
                'confirmed': 0
            }
            
            row = [
                publication.id,
                publication.title,
                publication.publication_type.value if publication.publication_type else '',
                publication.member.name,
                publication.member.institution or '',
                publication.issn_isbn or '',
                publication.publisher or '',
                publication.language or '',
                'Da' if publication.is_active else 'Ne',
                len(drafts),
                draft_counts['draft'],
                draft_counts['xml_generated'],
                draft_counts['xml_sent'],
                draft_counts['confirmed'],
                publication.created_at.strftime('%d.%m.%Y %H:%M') if publication.created_at else '',
                publication.updated_at.strftime('%d.%m.%Y %H:%M') if publication.updated_at else ''
            ]
            writer.writerow(row)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'publikacije_export_{timestamp}.csv'
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content, filename
    
    @staticmethod
    def export_doi_drafts_csv(sponsor_id, filters=None):
        """
        Izvozi DOI draftove u CSV format.
        
        Args:
            sponsor_id (int): ID sponzora 
            filters (dict): Opcioni filteri
            
        Returns:
            tuple: (csv_content, filename)
        """
        # TODO: Implementirati kada se kreira DOIDraft model
        # Za sada vraćamo prazan CSV sa header-ima
        
        # Generiši CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        headers = [
            'ID',
            'Naslov drafta',
            'DOI broj',
            'Status',
            'Publikacija',
            'Član',
            'Institucija',
            'Datum publikacije',
            'Broj autora',
            'Autori',
            'Kreiran',
            'Poslednja izmena',
            'Kreirao korisnik'
        ]
        writer.writerow(headers)
        
        # Note row indicating functionality not yet implemented
        writer.writerow([
            'N/A', 'DOI Draft funkcionalnost još uvek nije implementirana', 
            '', '', '', '', '', '', '', '', '', '', ''
        ])
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'doi_draftovi_export_{timestamp}.csv'
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content, filename
    
    @staticmethod
    def get_export_filters_metadata(sponsor_id):
        """
        Dobija metadata za export filtere.
        
        Args:
            sponsor_id (int): ID sponzora
            
        Returns:
            dict: Metadata za filtere
        """
        # Lista članova
        members = Member.query.filter_by(sponsor_id=sponsor_id).order_by(Member.name).all()
        member_options = [{'value': m.id, 'label': m.name} for m in members]
        
        # Lista publikacija
        publications = Publication.query.join(Member).filter(
            Member.sponsor_id == sponsor_id
        ).order_by(Member.name, Publication.title).all()
        
        publication_options = [
            {'value': p.id, 'label': f"{p.title} ({p.member.name})"}
            for p in publications
        ]
        
        # Tipovi publikacija
        from app.models.publication import PublicationType
        publication_type_options = [
            {'value': ptype.value, 'label': ptype.value.title()}
            for ptype in PublicationType
        ]
        
        # DOI draft statusi
        draft_status_options = [
            {'value': 'draft', 'label': 'Draft'},
            {'value': 'xml_generated', 'label': 'XML generirani'},
            {'value': 'xml_sent', 'label': 'XML poslati'},
            {'value': 'confirmed', 'label': 'Potvrđeni'}
        ]
        
        return {
            'members': member_options,
            'publications': publication_options,
            'publication_types': publication_type_options,
            'draft_statuses': draft_status_options
        }