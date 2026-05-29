"""Add template management tables

Revision ID: 005_add_templates
Revises: 004_session_management
Create Date: 2024-12-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_templates'
down_revision = '004_session_management'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create templates table (without foreign key to template_versions yet)
    op.create_table('templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('template_code', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('confidentiality', sa.String(length=50), nullable=True, server_default='Internal'),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('current_published_version_id', sa.Integer(), nullable=True),
        sa.Column('template_type', sa.String(length=50), nullable=False, server_default='block_builder'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_templates_id'), 'templates', ['id'], unique=False)
    op.create_index(op.f('ix_templates_name'), 'templates', ['name'], unique=False)
    op.create_index(op.f('ix_templates_category'), 'templates', ['category'], unique=False)
    op.create_index(op.f('ix_templates_department'), 'templates', ['department'], unique=False)

    # Create template_versions table
    op.create_table('template_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('revision', sa.String(length=50), nullable=True),
        sa.Column('docx_file_path', sa.String(length=500), nullable=True),
        sa.Column('preview_html_path', sa.String(length=500), nullable=True),
        sa.Column('template_data', sa.JSON(), nullable=True),
        sa.Column('generated_docx_path', sa.String(length=500), nullable=True),
        sa.Column('generated_pdf_path', sa.String(length=500), nullable=True),
        sa.Column('status', sa.Enum('Draft', 'UnderReview', 'PendingApproval', 'Rejected', 'Published', name='templatestatus'), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('submitted_for_review_at', sa.DateTime(), nullable=True),
        sa.Column('submitted_for_review_by_id', sa.Integer(), nullable=True),
        sa.Column('submitted_for_approval_at', sa.DateTime(), nullable=True),
        sa.Column('submitted_for_approval_by_id', sa.Integer(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('published_by_id', sa.Integer(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_by_id', sa.Integer(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('sample_values', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['published_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['rejected_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['submitted_for_approval_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['submitted_for_review_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_template_versions_id'), 'template_versions', ['id'], unique=False)
    op.create_index(op.f('ix_template_versions_template_id'), 'template_versions', ['template_id'], unique=False)
    op.create_index(op.f('ix_template_versions_status'), 'template_versions', ['status'], unique=False)

    # Create template_reviews table
    op.create_table('template_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_version_id', sa.Integer(), nullable=False),
        sa.Column('reviewer_id', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['template_version_id'], ['template_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_template_reviews_id'), 'template_reviews', ['id'], unique=False)
    op.create_index(op.f('ix_template_reviews_template_version_id'), 'template_reviews', ['template_version_id'], unique=False)

    # Create template_approvals table
    op.create_table('template_approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_version_id', sa.Integer(), nullable=False),
        sa.Column('approver_id', sa.Integer(), nullable=False),
        sa.Column('decision', sa.String(length=20), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('e_signature_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['template_version_id'], ['template_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_template_approvals_id'), 'template_approvals', ['id'], unique=False)
    op.create_index(op.f('ix_template_approvals_template_version_id'), 'template_approvals', ['template_version_id'], unique=False)

    # Add foreign key constraint for current_published_version_id after template_versions is created
    # Note: SQLite doesn't support adding foreign keys after table creation, so we skip this for SQLite
    try:
        op.create_foreign_key(
            'fk_templates_current_published_version',
            'templates', 'template_versions',
            ['current_published_version_id'], ['id']
        )
    except:
        pass  # SQLite doesn't support this, but it's okay - the constraint is enforced at application level


def downgrade() -> None:
    op.drop_index(op.f('ix_template_approvals_template_version_id'), table_name='template_approvals')
    op.drop_index(op.f('ix_template_approvals_id'), table_name='template_approvals')
    op.drop_table('template_approvals')
    
    op.drop_index(op.f('ix_template_reviews_template_version_id'), table_name='template_reviews')
    op.drop_index(op.f('ix_template_reviews_id'), table_name='template_reviews')
    op.drop_table('template_reviews')
    
    op.drop_index(op.f('ix_template_versions_status'), table_name='template_versions')
    op.drop_index(op.f('ix_template_versions_template_id'), table_name='template_versions')
    op.drop_index(op.f('ix_template_versions_id'), table_name='template_versions')
    op.drop_table('template_versions')
    
    op.drop_index(op.f('ix_templates_department'), table_name='templates')
    op.drop_index(op.f('ix_templates_category'), table_name='templates')
    op.drop_index(op.f('ix_templates_name'), table_name='templates')
    op.drop_index(op.f('ix_templates_id'), table_name='templates')
    op.drop_table('templates')
    
    # Drop enum type (PostgreSQL only)
    try:
        op.execute("DROP TYPE templatestatus")
    except:
        pass  # SQLite doesn't have enum types

