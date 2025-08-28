"""Force recreate enum type completely

Revision ID: 38659bec4f1b
Revises: c569d7ed2ad5
Create Date: 2025-08-28 14:44:27.663992

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '38659bec4f1b'
down_revision = 'c569d7ed2ad5'
branch_labels = None
depends_on = None


def upgrade():
    """
    Force complete recreation of publicationtype enum
    Drop and recreate the enum entirely to avoid SQLAlchemy caching issues
    """
    
    # Step 1: Change column to VARCHAR temporarily 
    op.execute("ALTER TABLE publications MODIFY COLUMN publication_type VARCHAR(20) NOT NULL")
    
    # Step 2: Recreate column with new enum (MySQL doesn't use separate enum types like PostgreSQL)
    op.execute("ALTER TABLE publications MODIFY COLUMN publication_type ENUM('journal', 'book_series', 'book_set', 'book') NOT NULL")


def downgrade():
    """
    Restore previous state
    """
    op.execute("ALTER TABLE publications MODIFY COLUMN publication_type VARCHAR(20) NOT NULL")
    op.execute("ALTER TABLE publications MODIFY COLUMN publication_type ENUM('JOURNAL', 'BOOK_SERIES', 'BOOK_SET', 'BOOK') NOT NULL")
