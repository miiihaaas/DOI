from sqlalchemy import func
from flask_login import current_user
from app import db
from app.models.member import Member
from app.models.publication import Publication, PublicationType
from app.models.activity_log import ActivityLog
from datetime import datetime, timedelta


class DashboardService:
    """Service za agregaciju dashboard statistika i podataka."""
    
    @staticmethod
    def get_sponsor_statistics(sponsor_id):
        """
        Dobija kompletnu statistiku za određeni sponsor.
        
        Args:
            sponsor_id (int): ID sponzora
            
        Returns:
            dict: Statistike sponzora uključujući članove, publikacije i aktivnost
        """
        # Member statistike
        member_stats = DashboardService._get_member_statistics(sponsor_id)
        
        # Publication statistike
        publication_stats = DashboardService._get_publication_statistics(sponsor_id)
        
        # Activity statistike
        activity_stats = DashboardService._get_recent_activity_statistics(sponsor_id)
        
        # Draft statistike
        draft_stats = DashboardService._get_draft_statistics(sponsor_id)
        
        return {
            'members': member_stats,
            'publications': publication_stats,
            'activity': activity_stats,
            'drafts': draft_stats,
            'summary': {
                'total_entities': member_stats['total'] + publication_stats['total'],
                'active_entities': member_stats['active'] + publication_stats['active']
            }
        }
    
    @staticmethod
    def _get_member_statistics(sponsor_id):
        """Dobija member statistike za određeni sponsor."""
        total_query = db.session.query(func.count(Member.id)).filter_by(sponsor_id=sponsor_id)
        active_query = db.session.query(func.count(Member.id)).filter_by(
            sponsor_id=sponsor_id, is_active=True
        )
        inactive_query = db.session.query(func.count(Member.id)).filter_by(
            sponsor_id=sponsor_id, is_active=False
        )
        
        total = total_query.scalar() or 0
        active = active_query.scalar() or 0
        inactive = inactive_query.scalar() or 0
        
        return {
            'total': total,
            'active': active,
            'inactive': inactive,
            'percentage_active': round((active / total * 100) if total > 0 else 0, 1)
        }
    
    @staticmethod
    def _get_publication_statistics(sponsor_id):
        """Dobija publication statistike za određeni sponsor."""
        # Base query za publikacije kroz member relationship
        base_query = db.session.query(Publication).join(Member).filter(
            Member.sponsor_id == sponsor_id
        )
        
        total = base_query.count()
        active = base_query.filter(Publication.is_active == True).count()
        inactive = base_query.filter(Publication.is_active == False).count()
        
        # Breakdown po tipovima publikacija
        type_breakdown = {}
        for pub_type in PublicationType:
            count = base_query.filter(Publication.publication_type == pub_type).count()
            type_breakdown[pub_type.value] = count
        
        return {
            'total': total,
            'active': active,
            'inactive': inactive,
            'percentage_active': round((active / total * 100) if total > 0 else 0, 1),
            'by_type': type_breakdown
        }
    
    @staticmethod
    def _get_recent_activity_statistics(sponsor_id, days_back=7):
        """Dobija recent activity statistike za određeni sponsor."""
        # Since this is a single-sponsor system, just get recent activities
        # without complex sponsor filtering
        recent_activities = ActivityLog.get_recent_activities(limit=10, sponsor_id=sponsor_id)
        
        return {
            'recent_activities': [
                {
                    'id': activity.id,
                    'action': activity.action,
                    'description': activity.description,
                    'created_at': activity.created_at,
                    'user_name': activity.user.full_name if activity.user else 'Unknown User',
                    'member_id': activity.member_id,
                    'publication_id': activity.publication_id
                }
                for activity in recent_activities
            ],
            'action_counts': {},
            'total_recent': len(recent_activities)
        }
    
    @staticmethod
    def _get_draft_statistics(sponsor_id):
        """Dobija draft statistike za određeni sponsor."""
        # TODO: Implementirati kada se kreira DOIDraft model
        # Za sada vraćamo placeholder vrednosti
        return {
            'total': 0,
            'by_status': {
                'draft': 0,
                'xml_generated': 0,
                'xml_sent': 0,
                'confirmed': 0
            }
        }
    
    @staticmethod
    def get_member_detail_statistics(member_id):
        """
        Dobija detaljnu statistiku za određeni member.
        
        Args:
            member_id (int): ID člana
            
        Returns:
            dict: Statistike člana uključujući publikacije i draftove
        """
        member = Member.query.get_or_404(member_id)
        
        # Publication statistike za member
        publications = member.publications
        total_publications = len(publications)
        active_publications = len([p for p in publications if p.is_active])
        
        # Publication breakdown po tipovima
        type_breakdown = {}
        for pub_type in PublicationType:
            count = len([p for p in publications if p.publication_type == pub_type])
            type_breakdown[pub_type.value] = count
        
        # Draft statistike za member publications
        # TODO: Implementirati kada se kreira DOIDraft model
        total_drafts = 0
        draft_status_breakdown = {}
        
        return {
            'member_info': {
                'id': member.id,
                'name': member.name,
                'institution': member.institution,
                'is_active': member.is_active
            },
            'publications': {
                'total': total_publications,
                'active': active_publications,
                'inactive': total_publications - active_publications,
                'by_type': type_breakdown
            },
            'drafts': {
                'total': total_drafts,
                'by_status': draft_status_breakdown
            }
        }
    
    @staticmethod
    def get_publication_detail_statistics(publication_id):
        """
        Dobija detaljnu statistiku za određenu publikaciju.
        
        Args:
            publication_id (int): ID publikacije
            
        Returns:
            dict: Statistike publikacije uključujući draftove i aktivnost
        """
        publication = Publication.query.get_or_404(publication_id)
        
        # Draft statistike za publikaciju
        # TODO: Implementirati kada se kreira DOIDraft model
        total_drafts = 0
        status_breakdown = {
            'draft': 0,
            'xml_generated': 0,
            'xml_sent': 0,
            'confirmed': 0
        }
        recent_drafts = []
        
        return {
            'publication_info': {
                'id': publication.id,
                'title': publication.title,
                'type': publication.publication_type.value,
                'is_active': publication.is_active,
                'member_name': publication.member.name
            },
            'drafts': {
                'total': total_drafts,
                'by_status': status_breakdown,
                'recent': recent_drafts
            }
        }