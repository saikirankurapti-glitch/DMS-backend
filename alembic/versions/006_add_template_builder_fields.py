"""Add template builder fields

Revision ID: 006_template_builder
Revises: 005_add_templates
Create Date: 2024-12-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_template_builder'
down_revision = '005_add_templates'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new fields to templates table
    op.add_column('templates', sa.Column('template_code', sa.String(length=100), nullable=True))
    op.add_column('templates', sa.Column('confidentiality', sa.String(length=50), nullable=True))
    op.add_column('templates', sa.Column('template_type', sa.String(length=50), nullable=False, server_default='block_builder'))
    op.create_index(op.f('ix_templates_template_code'), 'templates', ['template_code'], unique=True)

    # Add new fields to template_versions table
    op.add_column('template_versions', sa.Column('revision', sa.String(length=50), nullable=True))
    op.add_column('template_versions', sa.Column('template_data', sa.JSON(), nullable=True))
    op.add_column('template_versions', sa.Column('generated_docx_path', sa.String(length=500), nullable=True))
    op.add_column('template_versions', sa.Column('generated_pdf_path', sa.String(length=500), nullable=True))
    op.add_column('template_versions', sa.Column('sample_values', sa.JSON(), nullable=True))
    
    # Make docx_file_path nullable (for block-based templates)
    op.alter_column('template_versions', 'docx_file_path', nullable=True)


def downgrade() -> None:
    op.alter_column('template_versions', 'docx_file_path', nullable=False)
    op.drop_column('template_versions', 'sample_values')
    op.drop_column('template_versions', 'generated_pdf_path')
    op.drop_column('template_versions', 'generated_docx_path')
    op.drop_column('template_versions', 'template_data')
    op.drop_column('template_versions', 'revision')
    op.drop_index(op.f('ix_templates_template_code'), table_name='templates')
    op.drop_column('templates', 'template_type')
    op.drop_column('templates', 'confidentiality')
    op.drop_column('templates', 'template_code')







