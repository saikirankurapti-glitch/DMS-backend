"""Add controlled versioning and obsolescence fields

Revision ID: 007_controlled_versioning
Revises: 006_template_builder
Create Date: 2025-12-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '007_controlled_versioning'
down_revision = '006_template_builder'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add controlled versioning and obsolescence fields to document_versions table
    """
    # Add new columns to document_versions
    with op.batch_alter_table('document_versions', schema=None) as batch_op:
        # Version string for semantic versioning (v0.1, v1.0, v1.1, v2.0)
        batch_op.add_column(sa.Column('version_string', sa.String(length=20), nullable=True))
        
        # Version hierarchy
        batch_op.add_column(sa.Column('parent_version_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_latest', sa.Boolean(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('replaced_by_version_id', sa.Integer(), nullable=True))
        
        # Change tracking
        batch_op.add_column(sa.Column('change_reason', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('change_type', sa.String(length=10), nullable=True))
        
        # Lifecycle dates
        batch_op.add_column(sa.Column('effective_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('obsolete_date', sa.DateTime(), nullable=True))
        
        # Create foreign key constraints
        batch_op.create_foreign_key('fk_dv_parent_version_id', 'document_versions', ['parent_version_id'], ['id'])
        batch_op.create_foreign_key('fk_dv_replaced_by_version_id', 'document_versions', ['replaced_by_version_id'], ['id'])
        
        # Create indexes for better query performance
        batch_op.create_index('ix_document_versions_version_string', ['version_string'], unique=False)
        batch_op.create_index('ix_document_versions_is_latest', ['is_latest'], unique=False)
    
    # Update existing records to have version_string based on version_number
    # First version starts as v0.1 (Draft), becomes v1.0 when approved
    # Cast status to text for PostgreSQL ENUM compatibility
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE document_versions 
        SET version_string = CASE 
            WHEN status::text IN ('Draft', 'Under Review', 'Pending Approval', 'Rejected') THEN 'v0.' || version_number
            ELSE 'v' || version_number || '.0'
        END
        WHERE version_string IS NULL
    """))
    
    # Update is_latest flag - only the most recent version per document should be latest
    # Use TRUE/FALSE for PostgreSQL boolean compatibility
    connection.execute(sa.text("""
        UPDATE document_versions
        SET is_latest = CASE
            WHEN id IN (
                SELECT MAX(id) 
                FROM document_versions 
                GROUP BY document_id
            ) THEN TRUE
            ELSE FALSE
        END
    """))


def downgrade():
    """
    Remove controlled versioning fields
    """
    with op.batch_alter_table('document_versions', schema=None) as batch_op:
        # Drop indexes
        batch_op.drop_index('ix_document_versions_is_latest')
        batch_op.drop_index('ix_document_versions_version_string')
        
        # Drop foreign keys
        batch_op.drop_constraint('fk_dv_replaced_by_version_id', type_='foreignkey')
        batch_op.drop_constraint('fk_dv_parent_version_id', type_='foreignkey')
        
        # Drop columns
        batch_op.drop_column('obsolete_date')
        batch_op.drop_column('effective_date')
        batch_op.drop_column('change_type')
        batch_op.drop_column('change_reason')
        batch_op.drop_column('replaced_by_version_id')
        batch_op.drop_column('is_latest')
        batch_op.drop_column('parent_version_id')
        batch_op.drop_column('version_string')

