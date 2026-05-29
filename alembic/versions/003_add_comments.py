"""Add comments table

Revision ID: 003
Revises: 002
Create Date: 2025-12-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_comments'
down_revision = '002_document_models'
branch_labels = None
depends_on = None


def upgrade():
    # Create document_comments table
    op.create_table(
        'document_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_version_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('selected_text', sa.Text(), nullable=True),
        sa.Column('selection_start', sa.Integer(), nullable=True),
        sa.Column('selection_end', sa.Integer(), nullable=True),
        sa.Column('text_context', sa.Text(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), default=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resolved_by_id'], ['users.id'], ),
    )
    
    # Create indexes
    op.create_index('ix_document_comments_version_id', 'document_comments', ['document_version_id'])
    op.create_index('ix_document_comments_user_id', 'document_comments', ['user_id'])
    op.create_index('ix_document_comments_is_resolved', 'document_comments', ['is_resolved'])


def downgrade():
    op.drop_index('ix_document_comments_is_resolved', table_name='document_comments')
    op.drop_index('ix_document_comments_user_id', table_name='document_comments')
    op.drop_index('ix_document_comments_version_id', table_name='document_comments')
    op.drop_table('document_comments')

