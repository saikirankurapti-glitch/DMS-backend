"""add_document_view_tracking

Revision ID: d4a9c2c8603f
Revises: 007_controlled_versioning
Create Date: 2025-12-15 17:29:22.699116

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4a9c2c8603f'
down_revision = '007_controlled_versioning'  # This should match the revision ID from 007_add_controlled_versioning.py
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create document_views table to track when users view document versions
    This enforces that reviewers/approvers must view content before taking workflow actions
    """
    op.create_table(
        'document_views',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('viewed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['version_id'], ['document_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version_id', 'user_id', name='uq_version_user_view')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_document_views_document_id', 'document_views', ['document_id'])
    op.create_index('ix_document_views_version_id', 'document_views', ['version_id'])
    op.create_index('ix_document_views_user_id', 'document_views', ['user_id'])
    op.create_index('ix_document_views_viewed_at', 'document_views', ['viewed_at'])
    op.create_index('idx_document_version_user', 'document_views', ['document_id', 'version_id', 'user_id'])


def downgrade() -> None:
    """
    Drop document_views table
    """
    op.drop_index('idx_document_version_user', table_name='document_views')
    op.drop_index('ix_document_views_viewed_at', table_name='document_views')
    op.drop_index('ix_document_views_user_id', table_name='document_views')
    op.drop_index('ix_document_views_version_id', table_name='document_views')
    op.drop_index('ix_document_views_document_id', table_name='document_views')
    op.drop_table('document_views')


