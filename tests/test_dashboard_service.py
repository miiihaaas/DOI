import pytest
from datetime import datetime, date
from app.services.dashboard_service import DashboardService
from app.models.member import Member
from app.models.publication import Publication, PublicationType
from app.models.doi_draft import DOIDraft
from app.models.activity_log import ActivityLog
from app.models.user import User, UserRole
from app.models.sponsor import Sponsor
from app import db


@pytest.fixture
def sample_sponsor(app):
    """Kreira test sponsor."""
    with app.app_context():
        sponsor = Sponsor(
            name="Test Sponsor",
            email="test@sponsor.com",
            phone="123456789"
        )
        db.session.add(sponsor)
        db.session.commit()
        return sponsor


@pytest.fixture
def sample_user(app, sample_sponsor):
    """Kreira test korisnika."""
    with app.app_context():
        user = User(
            email="user@test.com",
            password_hash="hashed_password",
            full_name="Test User",
            role=UserRole.USER,
            sponsor_id=sample_sponsor.id
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_members(app, sample_sponsor):
    """Kreira test članove."""
    with app.app_context():
        members = []
        for i in range(3):
            member = Member(
                sponsor_id=sample_sponsor.id,
                name=f"Test Member {i+1}",
                institution=f"Test Institution {i+1}",
                contact_email=f"member{i+1}@test.com",
                is_active=(i < 2)  # Prvi dva su aktivni
            )
            db.session.add(member)
            members.append(member)
        
        db.session.commit()
        return members


@pytest.fixture
def sample_publications(app, sample_members):
    """Kreira test publikacije."""
    with app.app_context():
        publications = []
        pub_types = [PublicationType.JOURNAL, PublicationType.BOOK, PublicationType.MONOGRAPH]
        
        for i, member in enumerate(sample_members):
            for j in range(2):  # 2 publikacije po članu
                publication = Publication(
                    member_id=member.id,
                    title=f"Test Publication {i+1}-{j+1}",
                    publication_type=pub_types[j % len(pub_types)],
                    publisher=f"Test Publisher {j+1}",
                    issn_isbn=f"TEST-{i+1}-{j+1}",
                    language="sr",
                    is_active=(j == 0)  # Prva publikacija je aktivna
                )
                db.session.add(publication)
                publications.append(publication)
        
        db.session.commit()
        return publications


@pytest.fixture
def sample_drafts(app, sample_publications, sample_user):
    """Kreira test DOI draftove."""
    with app.app_context():
        drafts = []
        statuses = ['draft', 'xml_generated', 'xml_sent', 'confirmed']
        
        for i, publication in enumerate(sample_publications):
            draft = DOIDraft(
                publication_id=publication.id,
                created_by=sample_user.id,
                title=f"Draft for {publication.title}",
                doi_number=f"10.test/{i+1:04d}",
                authors=[
                    {"given_name": "Test", "family_name": f"Author {i+1}"}
                ],
                publication_date=date(2024, 1, 1),
                status=statuses[i % len(statuses)]
            )
            db.session.add(draft)
            drafts.append(draft)
        
        db.session.commit()
        return drafts


class TestDashboardService:
    """Test class za DashboardService."""
    
    def test_get_sponsor_statistics_basic(self, app, sample_sponsor, sample_members, 
                                        sample_publications, sample_drafts):
        """Test osnovnih sponsor statistika."""
        with app.app_context():
            stats = DashboardService.get_sponsor_statistics(sample_sponsor.id)
            
            # Test member statistike
            assert stats['members']['total'] == 3
            assert stats['members']['active'] == 2
            assert stats['members']['inactive'] == 1
            assert stats['members']['percentage_active'] == 66.7
            
            # Test publication statistike
            assert stats['publications']['total'] == 6
            assert stats['publications']['active'] == 3
            assert stats['publications']['inactive'] == 3
            assert stats['publications']['percentage_active'] == 50.0
            
            # Test publication types
            assert stats['publications']['by_type']['journal'] == 2
            assert stats['publications']['by_type']['book'] == 2
            assert stats['publications']['by_type']['monograph'] == 2
            
            # Test draft statistike
            assert stats['drafts']['total'] == 6
            assert stats['drafts']['by_status']['draft'] == 2
            assert stats['drafts']['by_status']['xml_generated'] == 2
            assert stats['drafts']['by_status']['xml_sent'] == 1
            assert stats['drafts']['by_status']['confirmed'] == 1
    
    def test_get_sponsor_statistics_empty_sponsor(self, app):
        """Test statistika za sponzora bez podataka."""
        with app.app_context():
            # Kreiraj prazan sponsor
            empty_sponsor = Sponsor(
                name="Empty Sponsor",
                email="empty@sponsor.com"
            )
            db.session.add(empty_sponsor)
            db.session.commit()
            
            stats = DashboardService.get_sponsor_statistics(empty_sponsor.id)
            
            # Sve statistike treba da budu 0
            assert stats['members']['total'] == 0
            assert stats['members']['active'] == 0
            assert stats['members']['inactive'] == 0
            assert stats['members']['percentage_active'] == 0
            
            assert stats['publications']['total'] == 0
            assert stats['publications']['active'] == 0
            assert stats['publications']['inactive'] == 0
            assert stats['publications']['percentage_active'] == 0
            
            assert stats['drafts']['total'] == 0
            assert all(count == 0 for count in stats['drafts']['by_status'].values())
    
    def test_get_member_detail_statistics(self, app, sample_members, sample_publications, sample_drafts):
        """Test detaljnih statistika za člana."""
        with app.app_context():
            member = sample_members[0]
            stats = DashboardService.get_member_detail_statistics(member.id)
            
            # Test osnovnih informacija
            assert stats['member_info']['id'] == member.id
            assert stats['member_info']['name'] == member.name
            assert stats['member_info']['institution'] == member.institution
            assert stats['member_info']['is_active'] == member.is_active
            
            # Test publication statistike
            assert stats['publications']['total'] == 2
            assert stats['publications']['active'] == 1
            assert stats['publications']['inactive'] == 1
            
            # Test draft statistike
            assert stats['drafts']['total'] == 2
    
    def test_get_publication_detail_statistics(self, app, sample_publications, sample_drafts):
        """Test detaljnih statistika za publikaciju."""
        with app.app_context():
            publication = sample_publications[0]
            stats = DashboardService.get_publication_detail_statistics(publication.id)
            
            # Test osnovnih informacija
            assert stats['publication_info']['id'] == publication.id
            assert stats['publication_info']['title'] == publication.title
            assert stats['publication_info']['type'] == publication.publication_type.value
            assert stats['publication_info']['is_active'] == publication.is_active
            
            # Test draft statistike
            assert stats['drafts']['total'] == 1
            assert len(stats['drafts']['recent']) <= 5
    
    def test_member_statistics_calculation(self, app, sample_sponsor):
        """Test preciznosti kalkulacije member statistika."""
        with app.app_context():
            # Kreiraj specifičan scenario
            active_members = []
            inactive_members = []
            
            for i in range(7):  # 7 aktivnih
                member = Member(
                    sponsor_id=sample_sponsor.id,
                    name=f"Active Member {i}",
                    is_active=True
                )
                db.session.add(member)
                active_members.append(member)
            
            for i in range(3):  # 3 neaktivna
                member = Member(
                    sponsor_id=sample_sponsor.id,
                    name=f"Inactive Member {i}",
                    is_active=False
                )
                db.session.add(member)
                inactive_members.append(member)
            
            db.session.commit()
            
            stats = DashboardService._get_member_statistics(sample_sponsor.id)
            
            assert stats['total'] == 10
            assert stats['active'] == 7
            assert stats['inactive'] == 3
            assert stats['percentage_active'] == 70.0
    
    def test_publication_statistics_by_type(self, app, sample_sponsor):
        """Test kalkulacije publikacija po tipovima."""
        with app.app_context():
            # Kreiraj member
            member = Member(
                sponsor_id=sample_sponsor.id,
                name="Test Member",
                is_active=True
            )
            db.session.add(member)
            db.session.commit()
            
            # Kreiraj publikacije različitih tipova
            pub_counts = {
                PublicationType.JOURNAL: 5,
                PublicationType.BOOK: 3,
                PublicationType.MONOGRAPH: 2
            }
            
            for pub_type, count in pub_counts.items():
                for i in range(count):
                    publication = Publication(
                        member_id=member.id,
                        title=f"{pub_type.value.title()} {i}",
                        publication_type=pub_type,
                        is_active=True
                    )
                    db.session.add(publication)
            
            db.session.commit()
            
            stats = DashboardService._get_publication_statistics(sample_sponsor.id)
            
            assert stats['total'] == 10
            assert stats['active'] == 10
            assert stats['by_type']['journal'] == 5
            assert stats['by_type']['book'] == 3
            assert stats['by_type']['monograph'] == 2
    
    def test_draft_statistics_by_status(self, app, sample_sponsor, sample_user):
        """Test kalkulacije draft-ova po statusu."""
        with app.app_context():
            # Kreiraj member i publikaciju
            member = Member(
                sponsor_id=sample_sponsor.id,
                name="Test Member",
                is_active=True
            )
            db.session.add(member)
            
            publication = Publication(
                member_id=member.id,
                title="Test Publication",
                publication_type=PublicationType.JOURNAL,
                is_active=True
            )
            db.session.add(publication)
            db.session.commit()
            
            # Kreiraj draftove različitih statusa
            status_counts = {
                'draft': 4,
                'xml_generated': 2,
                'xml_sent': 1,
                'confirmed': 3
            }
            
            for status, count in status_counts.items():
                for i in range(count):
                    draft = DOIDraft(
                        publication_id=publication.id,
                        created_by=sample_user.id,
                        title=f"Draft {status} {i}",
                        doi_number=f"10.test/{status}.{i}",
                        authors=[{"given_name": "Test", "family_name": "Author"}],
                        publication_date=date(2024, 1, 1),
                        status=status
                    )
                    db.session.add(draft)
            
            db.session.commit()
            
            stats = DashboardService._get_draft_statistics(sample_sponsor.id)
            
            assert stats['total'] == 10
            assert stats['by_status']['draft'] == 4
            assert stats['by_status']['xml_generated'] == 2
            assert stats['by_status']['xml_sent'] == 1
            assert stats['by_status']['confirmed'] == 3