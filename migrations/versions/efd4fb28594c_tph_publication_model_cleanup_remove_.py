"""TPH Publication model cleanup - remove variable fields and update enum

Revision ID: efd4fb28594c
Revises: e46f5136f401
Create Date: 2025-08-28 12:25:03.154275

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'efd4fb28594c'
down_revision = 'e46f5136f401'
branch_labels = None
depends_on = None


def upgrade():
    """
    TPH Publication model cleanup:
    1. Update PublicationType enum with 4 new values
    2. Rename 'type' column to 'publication_type' 
    3. Add new TPH union fields
    4. Remove variable data fields (language, publisher, dates, DOI, metadata)
    5. Reorganize field names for consistency
    
    Note: MySQL/MariaDB specific enum handling
    """
    
    # Step 1: Add new publication_type column with new enum (MySQL/MariaDB approach)
    op.add_column('publications', sa.Column('publication_type', sa.Enum('journal', 'book_series', 'book_set', 'book', name='publicationtype_new'), nullable=True))
    
    # Step 2: Map old values to new (MySQL/MariaDB syntax)
    # Since we have 0 records, this is precautionary
    op.execute("""
        UPDATE publications 
        SET publication_type = CASE 
            WHEN type = 'JOURNAL' THEN 'journal'
            WHEN type = 'BOOK' THEN 'book'  
            WHEN type = 'MONOGRAPH' THEN 'book'
            ELSE 'journal'
        END
    """)
    
    # Step 3: Make publication_type NOT NULL and add index (MySQL approach)
    op.execute('ALTER TABLE publications MODIFY publication_type ENUM(\'journal\', \'book_series\', \'book_set\', \'book\') NOT NULL')
    op.create_index('idx_publication_type', 'publications', ['publication_type'])
    
    # Step 4: Add language_code column (will copy from language before dropping it)
    op.add_column('publications', sa.Column('language_code', sa.String(length=10), nullable=False, server_default='en'))
    
    # Copy data from language to language_code
    op.execute('UPDATE publications SET language_code = language WHERE language IS NOT NULL')
    
    # Step 5: Add new TPH union fields for journal
    op.add_column('publications', sa.Column('journal_issn', sa.String(length=20), nullable=True))
    op.add_column('publications', sa.Column('journal_electronic_issn', sa.String(length=20), nullable=True))
    
    # Step 6: Rename existing series fields for consistency (MySQL approach)
    op.execute('ALTER TABLE publications CHANGE series_issn_print series_issn VARCHAR(20)')
    op.execute('ALTER TABLE publications CHANGE series_issn_electronic series_electronic_issn VARCHAR(20)')
    
    # Step 7: Add new TPH union fields for book set
    op.add_column('publications', sa.Column('set_isbn', sa.String(length=20), nullable=True))
    op.add_column('publications', sa.Column('set_electronic_isbn', sa.String(length=20), nullable=True))
    op.execute('ALTER TABLE publications CHANGE part_number set_part_number VARCHAR(50)')
    
    # Step 8: Rename book fields for consistency (MySQL approach)
    op.execute('ALTER TABLE publications CHANGE isbn_print isbn VARCHAR(20)')
    op.execute('ALTER TABLE publications CHANGE isbn_electronic electronic_isbn VARCHAR(20)')
    op.add_column('publications', sa.Column('noisbn_reason', sa.String(length=100), nullable=True))
    
    # Step 9: Create new indexes for type-specific identifiers
    op.create_index('idx_journal_issn', 'publications', ['journal_issn'])
    op.create_index('idx_series_issn', 'publications', ['series_issn']) 
    op.create_index('idx_set_isbn', 'publications', ['set_isbn'])
    op.create_index('idx_book_isbn', 'publications', ['isbn'])
    
    # Step 10: Drop old columns (variable data that goes to DOIDraft)
    op.drop_column('publications', 'language')
    op.drop_column('publications', 'publisher')
    op.drop_column('publications', 'publisher_place') 
    op.drop_column('publications', 'publication_year')
    op.drop_column('publications', 'publication_month')
    op.drop_column('publications', 'publication_day')
    op.drop_column('publications', 'media_type')
    op.drop_column('publications', 'publication_doi')
    op.drop_column('publications', 'resource_url')
    op.drop_column('publications', 'crossref_metadata')
    op.drop_column('publications', 'original_language_title')
    op.drop_column('publications', 'issn_isbn')
    
    # Step 11: Drop old type column and enum
    op.drop_index('idx_publication_member_type', table_name='publications')
    op.drop_index('idx_publication_issn_isbn', table_name='publications')
    op.drop_column('publications', 'type')
    # MySQL/MariaDB will automatically handle enum cleanup
    
    # Step 12: Recreate member_type index with new column name
    op.create_index('idx_publication_member_type', 'publications', ['member_id', 'publication_type', 'is_active'])
    
    # Step 13: Drop old unused series/set fields
    op.drop_column('publications', 'set_isbn_print')
    op.drop_column('publications', 'set_isbn_electronic') 
    op.drop_column('publications', 'volume_number')
    op.drop_column('publications', 'issn_print')
    op.drop_column('publications', 'issn_electronic')


def downgrade():
    """
    Reverse the TPH cleanup - restore old structure
    """
    # This is complex rollback - for development, we'll recreate old structure
    
    # Step 1: Recreate old enum
    op.execute("CREATE TYPE publicationtype_old AS ENUM ('JOURNAL', 'BOOK', 'MONOGRAPH')")
    
    # Step 2: Add back old type column
    op.add_column('publications', sa.Column('type', sa.Enum('JOURNAL', 'BOOK', 'MONOGRAPH', name='publicationtype_old'), nullable=True))
    
    # Step 3: Map new values back to old
    op.execute("""
        UPDATE publications 
        SET type = CASE 
            WHEN publication_type = 'journal' THEN 'JOURNAL'::publicationtype_old
            WHEN publication_type = 'book_series' THEN 'BOOK'::publicationtype_old
            WHEN publication_type = 'book_set' THEN 'BOOK'::publicationtype_old  
            WHEN publication_type = 'book' THEN 'BOOK'::publicationtype_old
            ELSE 'JOURNAL'::publicationtype_old
        END
    """)
    
    # Step 4: Add back removed columns with defaults
    op.add_column('publications', sa.Column('language', sa.String(length=10), nullable=False, server_default='en'))
    op.add_column('publications', sa.Column('publisher', sa.String(length=200), nullable=False, server_default='Unknown'))
    op.add_column('publications', sa.Column('issn_isbn', sa.String(length=20), nullable=False, server_default='0000-0000'))
    # ... add other removed columns as needed
    
    # Step 5: Drop new TPH fields
    op.drop_column('publications', 'publication_type')
    op.drop_column('publications', 'language_code')
    op.drop_column('publications', 'journal_issn')
    op.drop_column('publications', 'journal_electronic_issn')
    op.drop_column('publications', 'noisbn_reason')
    # ... drop other new fields
    
    # Step 6: Rename enum back
    op.execute("ALTER TYPE publicationtype_old RENAME TO publicationtype")
