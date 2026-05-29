"""Add session management columns to users table

Revision ID: 004_session_management
Revises: 003_add_comments
Create Date: 2024-12-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_session_management'
down_revision = '003_add_comments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add session management columns to users table
    op.add_column('users', sa.Column('active_session_token', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('session_created_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'session_created_at')
    op.drop_column('users', 'active_session_token')


