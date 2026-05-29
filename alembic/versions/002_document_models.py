"""Add document, document_version, attachment, and edit_lock tables

Revision ID: 002_document_models
Revises: 001
Create Date: 2025-11-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_document_models'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create documents table
    op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_number', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('current_version_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
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
    op.create_index(op.f('ix_documents_department'), 'documents', ['department'], unique=False)
    op.create_index(op.f('ix_documents_document_number'), 'documents', ['document_number'], unique=True)
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)
    op.create_index(op.f('ix_documents_title'), 'documents', ['title'], unique=False)

    # Create document_versions table
    op.create_table('document_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'UNDER_REVIEW', 'PENDING_APPROVAL', 'APPROVED', 'PUBLISHED', 'REJECTED', 'ARCHIVED', 'OBSOLETE', name='versionstatus'), nullable=False),
        sa.Column('attachments_metadata', sa.JSON(), nullable=True),
        sa.Column('docx_attachment_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('submitted_by_id', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by_id', sa.Integer(), nullable=True),
        sa.Column('review_comments', sa.Text(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approval_comments', sa.Text(), nullable=True),
        sa.Column('e_signature_data', sa.JSON(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('published_by_id', sa.Integer(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_by_id', sa.Integer(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.Column('archived_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('lock_version', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['archived_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['published_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['rejected_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['submitted_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_versions_document_id'), 'document_versions', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_versions_id'), 'document_versions', ['id'], unique=False)
    op.create_index(op.f('ix_document_versions_status'), 'document_versions', ['status'], unique=False)

    # Create attachments table
    op.create_table('attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=200), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('storage_path', sa.String(length=1000), nullable=False),
        sa.Column('storage_type', sa.String(length=50), nullable=False),
        sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
        sa.Column('document_version_id', sa.Integer(), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('attachment_type', sa.String(length=50), nullable=True),
        sa.Column('scan_status', sa.String(length=50), nullable=True),
        sa.Column('scan_result', sa.String(length=500), nullable=True),
        sa.Column('scanned_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attachments_document_id'), 'attachments', ['document_id'], unique=False)
    op.create_index(op.f('ix_attachments_document_version_id'), 'attachments', ['document_version_id'], unique=False)
    op.create_index(op.f('ix_attachments_id'), 'attachments', ['id'], unique=False)

    # Add foreign key from document_versions to attachments for docx_attachment_id
    op.create_foreign_key(
        'fk_document_versions_docx_attachment_id', 
        'document_versions', 
        'attachments', 
        ['docx_attachment_id'], 
        ['id']
    )

    # Add foreign key from documents to document_versions for current_version_id
    op.create_foreign_key(
        'fk_documents_current_version_id',
        'documents',
        'document_versions',
        ['current_version_id'],
        ['id']
    )

    # Create edit_locks table
    op.create_table('edit_locks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_version_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lock_token', sa.String(length=64), nullable=False),
        sa.Column('acquired_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_version_id', name='uq_edit_locks_document_version_id')
    )
    op.create_index(op.f('ix_edit_locks_document_version_id'), 'edit_locks', ['document_version_id'], unique=False)
    op.create_index(op.f('ix_edit_locks_expires_at'), 'edit_locks', ['expires_at'], unique=False)
    op.create_index(op.f('ix_edit_locks_id'), 'edit_locks', ['id'], unique=False)
    op.create_index(op.f('ix_edit_locks_lock_token'), 'edit_locks', ['lock_token'], unique=True)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_edit_locks_lock_token'), table_name='edit_locks')
    op.drop_index(op.f('ix_edit_locks_id'), table_name='edit_locks')
    op.drop_index(op.f('ix_edit_locks_expires_at'), table_name='edit_locks')
    op.drop_index(op.f('ix_edit_locks_document_version_id'), table_name='edit_locks')
    op.drop_table('edit_locks')
    
    op.drop_index(op.f('ix_attachments_document_version_id'), table_name='attachments')
    op.drop_index(op.f('ix_attachments_document_id'), table_name='attachments')
    op.drop_index(op.f('ix_attachments_id'), table_name='attachments')
    op.drop_table('attachments')
    
    op.drop_index(op.f('ix_document_versions_status'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_id'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_document_id'), table_name='document_versions')
    op.drop_table('document_versions')
    
    op.drop_index(op.f('ix_documents_title'), table_name='documents')
    op.drop_index(op.f('ix_documents_status'), table_name='documents')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_document_number'), table_name='documents')
    op.drop_index(op.f('ix_documents_department'), table_name='documents')
    op.drop_table('documents')
    
    # Drop enum type
    sa.Enum(name='versionstatus').drop(op.get_bind(), checkfirst=True)

