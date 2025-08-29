from sqlalchemy import or_, func, and_
from flask_login import current_user
from app import db
from app.models.member import Member
from app.models.publication import Publication, PublicationType


class SearchService:
    """Service za globalno pretraživanje kroz članove i publikacije."""
    
    @staticmethod
    def search_all(query, sponsor_id, entity_types=None, limit=50, page=1):
        """
        Izvršava globalno pretraživanje kroz članove i publikacije.
        
        Args:
            query (str): Pretraživana reč/fraza
            sponsor_id (int): ID sponzora za filtriranje rezultata
            entity_types (list): Lista tipova entiteta ['member', 'publication'] ili None za sve
            limit (int): Maksimalni broj rezultata po stranici
            page (int): Broj stranice za paginaciju
            
        Returns:
            dict: Kombinovani rezultati pretrage sa metadata
        """
        if not query or not query.strip():
            return {
                'results': [],
                'total_results': 0,
                'members_count': 0,
                'publications_count': 0,
                'page': page,
                'total_pages': 0,
                'has_more': False
            }
        
        query = query.strip()
        
        # Određi koje tipove entiteta treba pretraživati
        search_members = entity_types is None or 'member' in entity_types
        search_publications = entity_types is None or 'publication' in entity_types
        
        members = []
        publications = []
        
        if search_members:
            members = SearchService._search_members(query, sponsor_id)
        
        if search_publications:
            publications = SearchService._search_publications(query, sponsor_id)
        
        # Kombinuj rezultate i sortiraj po relevantnosti
        combined_results = []
        
        for member in members:
            combined_results.append({
                'type': 'member',
                'id': member.id,
                'title': member.name,
                'subtitle': member.institution or 'No Institution',
                'description': f"Kontakt: {member.contact_email or 'N/A'}",
                'url': f"/members/{member.id}",
                'is_active': member.is_active,
                'created_at': member.created_at,
                'relevance_score': SearchService._calculate_member_relevance(member, query)
            })
        
        for publication in publications:
            combined_results.append({
                'type': 'publication',
                'id': publication.id,
                'title': publication.title,
                'subtitle': f"{publication.publication_type.value.title()} • {publication.member.name}",
                'description': f"Izdavač: {publication.publisher or 'N/A'} • ISSN/ISBN: {publication.issn_isbn or 'N/A'}",
                'url': f"/publications/{publication.id}",
                'is_active': publication.is_active,
                'created_at': publication.created_at,
                'member_name': publication.member.name,
                'relevance_score': SearchService._calculate_publication_relevance(publication, query)
            })
        
        # Sortiraj po relevantnosti (veći skor = veća relevantnost)
        combined_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Paginacija
        total_results = len(combined_results)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_results = combined_results[start_idx:end_idx]
        
        total_pages = (total_results + limit - 1) // limit
        has_more = page < total_pages
        
        return {
            'results': paginated_results,
            'total_results': total_results,
            'members_count': len(members),
            'publications_count': len(publications),
            'page': page,
            'total_pages': total_pages,
            'has_more': has_more,
            'query': query
        }
    
    @staticmethod
    def _search_members(query, sponsor_id):
        """Pretraživanje članova po imenu, instituciji i email-u."""
        return Member.query.filter(
            and_(
                Member.sponsor_id == sponsor_id,
                or_(
                    Member.name.ilike(f'%{query}%'),
                    Member.institution.ilike(f'%{query}%'),
                    Member.contact_email.ilike(f'%{query}%'),
                    Member.website_url.ilike(f'%{query}%')
                )
            )
        ).all()
    
    @staticmethod
    def _search_publications(query, sponsor_id):
        """Pretraživanje publikacija po naslovu, izdavaču i metadata."""
        return Publication.query.join(Member).filter(
            and_(
                Member.sponsor_id == sponsor_id,
                or_(
                    Publication.title.ilike(f'%{query}%'),
                    Publication.publisher.ilike(f'%{query}%'),
                    Publication.issn_isbn.ilike(f'%{query}%'),
                    Publication.language.ilike(f'%{query}%'),
                    Member.name.ilike(f'%{query}%')  # Pretraži i ime člana
                )
            )
        ).all()
    
    @staticmethod
    def _calculate_member_relevance(member, query):
        """Računa relevantnost člana na osnovu lokacije pronađene reči."""
        score = 0
        query_lower = query.lower()
        
        # Exact match u imenu = najveći skor
        if member.name and query_lower == member.name.lower():
            score += 100
        elif member.name and query_lower in member.name.lower():
            score += 50
        
        # Match u instituciji
        if member.institution and query_lower == member.institution.lower():
            score += 80
        elif member.institution and query_lower in member.institution.lower():
            score += 30
        
        # Match u email-u
        if member.contact_email and query_lower in member.contact_email.lower():
            score += 20
        
        # Bonus za aktivne članove
        if member.is_active:
            score += 10
        
        # Bonus za novije članove
        if member.created_at:
            days_old = (member.created_at.date() - member.created_at.date()).days
            if days_old < 30:  # Članovi mlađi od 30 dana
                score += 5
        
        return score
    
    @staticmethod
    def _calculate_publication_relevance(publication, query):
        """Računa relevantnost publikacije na osnovu lokacije pronađene reči."""
        score = 0
        query_lower = query.lower()
        
        # Exact match u naslovu = najveći skor
        if publication.title and query_lower == publication.title.lower():
            score += 100
        elif publication.title and query_lower in publication.title.lower():
            score += 60
        
        # Match u izdavaču
        if publication.publisher and query_lower == publication.publisher.lower():
            score += 70
        elif publication.publisher and query_lower in publication.publisher.lower():
            score += 25
        
        # Match u ISSN/ISBN
        if publication.issn_isbn and query_lower in publication.issn_isbn.lower():
            score += 40
        
        # Match u imenu člana
        if publication.member.name and query_lower in publication.member.name.lower():
            score += 15
        
        # Bonus za aktivne publikacije
        if publication.is_active:
            score += 10
        
        # Bonus po tipu publikacije (časopisi imaju veći prioritet)
        if publication.publication_type == PublicationType.JOURNAL:
            score += 5
        elif publication.publication_type == PublicationType.BOOK:
            score += 3
        elif publication.publication_type == PublicationType.MONOGRAPH:
            score += 2
        
        return score
    
    @staticmethod
    def get_search_suggestions(query, sponsor_id, limit=5):
        """
        Dobija predloge za pretraživanje na osnovu postojećih podataka.
        
        Args:
            query (str): Parcijalna reč za predlog
            sponsor_id (int): ID sponzora
            limit (int): Maksimalni broj predloga
            
        Returns:
            list: Lista predloga sa tipom i tekstom
        """
        if not query or len(query) < 2:
            return []
        
        suggestions = []
        query_pattern = f'%{query}%'
        
        # Predlozi imena članova
        member_names = db.session.query(Member.name).filter(
            and_(
                Member.sponsor_id == sponsor_id,
                Member.name.ilike(query_pattern),
                Member.name.isnot(None)
            )
        ).limit(limit).all()
        
        for name_tuple in member_names:
            suggestions.append({
                'type': 'member',
                'text': name_tuple[0],
                'label': f"Član: {name_tuple[0]}"
            })
        
        # Predlozi naslova publikacija
        remaining_limit = limit - len(suggestions)
        if remaining_limit > 0:
            publication_titles = db.session.query(Publication.title).join(Member).filter(
                and_(
                    Member.sponsor_id == sponsor_id,
                    Publication.title.ilike(query_pattern),
                    Publication.title.isnot(None)
                )
            ).limit(remaining_limit).all()
            
            for title_tuple in publication_titles:
                suggestions.append({
                    'type': 'publication',
                    'text': title_tuple[0],
                    'label': f"Publikacija: {title_tuple[0][:50]}..."
                })
        
        return suggestions[:limit]
    
    @staticmethod
    def get_advanced_search_filters(sponsor_id):
        """
        Dobija dostupne filtere za naprednu pretragu.
        
        Args:
            sponsor_id (int): ID sponzora
            
        Returns:
            dict: Dostupni filteri za pretragu
        """
        # Dostupni tipovi publikacija
        publication_types = [
            {'value': PublicationType.JOURNAL.value, 'label': 'Časopisi'},
            {'value': PublicationType.BOOK.value, 'label': 'Knjige'},
            {'value': PublicationType.MONOGRAPH.value, 'label': 'Monografije'}
        ]
        
        # Active status options
        status_options = [
            {'value': 'active', 'label': 'Aktivni'},
            {'value': 'inactive', 'label': 'Neaktivni'},
            {'value': 'all', 'label': 'Svi'}
        ]
        
        # Lista članova za filtriranje publikacija
        members = Member.query.filter_by(sponsor_id=sponsor_id).order_by(Member.name).all()
        member_options = [{'value': m.id, 'label': m.name} for m in members]
        
        return {
            'publication_types': publication_types,
            'status_options': status_options,
            'members': member_options
        }