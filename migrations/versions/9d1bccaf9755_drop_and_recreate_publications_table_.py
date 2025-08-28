"""DROP and recreate publications table with clean TPH structure

Revision ID: 9d1bccaf9755
Revises: efd4fb28594c
Create Date: 2025-08-28 13:25:08.718014

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d1bccaf9755'
down_revision = 'efd4fb28594c'
branch_labels = None
depends_on = None


def upgrade():
    """
    Clean TPH Publication model - DROP/CREATE approach
    Safe since we have 0 production data
    """
    
    # Step 1: Drop existing publications table (safe since 0 data)
    op.drop_table('publications')
    
    # Step 2: Create new publications table with clean TPH structure
    op.create_table('publications',
        # Base fields
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        
        # TPH Union - Common fields
        sa.Column('publication_type', sa.Enum('journal', 'book_series', 'book_set', 'book', name='publicationtype'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('subtitle', sa.String(length=500), nullable=True),
        sa.Column('language_code', sa.String(length=10), nullable=False, default='en'),
        
        # TPH Union - Journal specific fields
        sa.Column('journal_abbreviated_title', sa.String(length=200), nullable=True),
        sa.Column('journal_issn', sa.String(length=20), nullable=True),
        sa.Column('journal_electronic_issn', sa.String(length=20), nullable=True),
        sa.Column('journal_coden', sa.String(length=10), nullable=True),
        
        # TPH Union - Book Series specific fields  
        sa.Column('series_title', sa.String(length=200), nullable=True),
        sa.Column('series_subtitle', sa.String(length=200), nullable=True),
        sa.Column('series_issn', sa.String(length=20), nullable=True),
        sa.Column('series_electronic_issn', sa.String(length=20), nullable=True),
        sa.Column('series_coden', sa.String(length=10), nullable=True),
        sa.Column('series_number', sa.String(length=50), nullable=True),
        
        # TPH Union - Book Set specific fields
        sa.Column('set_title', sa.String(length=200), nullable=True),
        sa.Column('set_subtitle', sa.String(length=200), nullable=True),
        sa.Column('set_isbn', sa.String(length=20), nullable=True),
        sa.Column('set_electronic_isbn', sa.String(length=20), nullable=True),
        sa.Column('set_part_number', sa.String(length=50), nullable=True),
        
        # TPH Union - Book specific fields
        sa.Column('book_type', sa.String(length=50), nullable=True),
        sa.Column('edition_number', sa.Integer(), nullable=True),
        sa.Column('isbn', sa.String(length=20), nullable=True),
        sa.Column('electronic_isbn', sa.String(length=20), nullable=True),
        sa.Column('noisbn_reason', sa.String(length=100), nullable=True),
        
        # Constraints
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Step 3: Create indexes for performance
    op.create_index('idx_publication_member_type', 'publications', ['member_id', 'publication_type', 'is_active'])
    op.create_index('idx_publication_title', 'publications', ['title'])  
    op.create_index('idx_publication_type', 'publications', ['publication_type'])
    
    # Type-specific identifier indexes
    op.create_index('idx_journal_issn', 'publications', ['journal_issn'])
    op.create_index('idx_series_issn', 'publications', ['series_issn'])
    op.create_index('idx_set_isbn', 'publications', ['set_isbn'])
    op.create_index('idx_book_isbn', 'publications', ['isbn'])
    
    # Standard BaseModel indexes
    op.create_index(op.f('ix_publications_is_active'), 'publications', ['is_active'], unique=False)
    op.create_index(op.f('ix_publications_member_id'), 'publications', ['member_id'], unique=False)


def downgrade():
    """
    Restore old publications table structure
    """
    # Drop new table
    op.drop_table('publications')
    
    # Recreate old structure (simplified version)
    op.create_table('publications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        
        # Old fields
        sa.Column('type', sa.Enum('JOURNAL', 'BOOK', 'MONOGRAPH', name='publicationtype'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('subtitle', sa.String(length=500), nullable=True),
        sa.Column('issn_isbn', sa.String(length=20), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False, default='en'),
        sa.Column('publisher', sa.String(length=200), nullable=False),
        
        # Constraints
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
