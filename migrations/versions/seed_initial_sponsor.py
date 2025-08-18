"""Add initial sponsor data

Revision ID: seed_initial_sponsor
Revises: ec5536d1a051
Create Date: 2025-08-18 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'seed_initial_sponsor'
down_revision = 'ec5536d1a051'
branch_labels = None
depends_on = None


def upgrade():
    """Add initial sponsor data."""
    # Get table references
    sponsors_table = sa.table(
        'sponsors',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('email', sa.String),
        sa.column('crossref_member_id', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime)
    )
    
    # Insert initial sponsor record
    current_time = datetime.utcnow()
    op.bulk_insert(
        sponsors_table,
        [
            {
                'name': 'DOI Management Organization',
                'email': 'admin@doiorg.com',
                'crossref_member_id': '1000',
                'is_active': True,
                'created_at': current_time,
                'updated_at': current_time
            }
        ]
    )


def downgrade():
    """Remove initial sponsor data."""
    # Remove the initial sponsor record
    op.execute("DELETE FROM sponsors WHERE email = 'admin@doiorg.com'")