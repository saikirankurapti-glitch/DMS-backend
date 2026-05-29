"""add_notification_logs_table

Revision ID: 8ea00ab4174f
Revises: d4a9c2c8603f
Create Date: 2025-12-17 11:25:21.319991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ea00ab4174f'
down_revision = 'd4a9c2c8603f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notification_logs table
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('recipient_user_id', sa.Integer(), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['version_id'], ['document_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipient_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_notification_logs_id'), 'notification_logs', ['id'], unique=False)
    op.create_index(op.f('ix_notification_logs_document_id'), 'notification_logs', ['document_id'], unique=False)
    op.create_index(op.f('ix_notification_logs_version_id'), 'notification_logs', ['version_id'], unique=False)
    op.create_index(op.f('ix_notification_logs_event_type'), 'notification_logs', ['event_type'], unique=False)
    op.create_index(op.f('ix_notification_logs_recipient_email'), 'notification_logs', ['recipient_email'], unique=False)
    op.create_index(op.f('ix_notification_logs_recipient_user_id'), 'notification_logs', ['recipient_user_id'], unique=False)
    op.create_index(op.f('ix_notification_logs_status'), 'notification_logs', ['status'], unique=False)
    op.create_index(op.f('ix_notification_logs_created_at'), 'notification_logs', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_notification_logs_created_at'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_status'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_recipient_user_id'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_recipient_email'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_event_type'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_version_id'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_document_id'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_id'), table_name='notification_logs')
    
    # Drop table
    op.drop_table('notification_logs')


