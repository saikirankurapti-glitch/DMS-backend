"""
DocumentView model for tracking when users view document versions
Ensures users must view content before performing workflow actions
"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DocumentView(Base):
    """
    Tracks when a user views a document version
    Used to enforce that reviewers/approvers must view content before taking action
    """
    __tablename__ = "document_views"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    version_id = Column(Integer, ForeignKey('document_versions.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Timestamp when user viewed the version
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Unique constraint: one view record per user-version combination
    # (allows tracking first view time, but can be extended to track multiple views)
    __table_args__ = (
        UniqueConstraint('version_id', 'user_id', name='uq_version_user_view'),
        Index('idx_document_version_user', 'document_id', 'version_id', 'user_id'),
    )
    
    # Relationships
    document = relationship("Document", foreign_keys=[document_id])
    version = relationship("DocumentVersion", foreign_keys=[version_id])
    user = relationship("User", foreign_keys=[user_id])

