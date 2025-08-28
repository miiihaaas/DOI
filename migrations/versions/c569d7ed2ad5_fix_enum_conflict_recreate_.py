"""Fix enum conflict - recreate publicationtype enum with correct values

Revision ID: c569d7ed2ad5
Revises: 9d1bccaf9755
Create Date: 2025-08-28 14:28:24.397176

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c569d7ed2ad5'
down_revision = '9d1bccaf9755'
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix enum conflict - MySQL doesn't handle ENUM changes well
    Drop and recreate enum with correct values
    """
    
    # Step 1: Use direct SQL to recreate the enum
    # MySQL requires specific syntax for enum modification
    op.execute("ALTER TABLE publications MODIFY COLUMN publication_type ENUM('journal', 'book_series', 'book_set', 'book') NOT NULL")


def downgrade():
    """
    Restore previous enum values (if needed)
    """
    # Restore old enum values 
    op.execute("ALTER TABLE publications MODIFY COLUMN publication_type ENUM('JOURNAL', 'BOOK_SERIES', 'BOOK_SET', 'BOOK') NOT NULL")
