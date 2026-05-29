"""
DocumentVersion model for DMS
Represents a specific version of a document with content and workflow state
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum


class VersionStatus(str, enum.Enum):
    """Document version workflow states"""
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EFFECTIVE = "EFFECTIVE"  # Uppercase to match database
    REJECTED = "REJECTED"
    OBSOLETE = "OBSOLETE"  # Uppercase to match database
    ARCHIVED = "ARCHIVED"


class ChangeType(str, enum.Enum):
    """Version change type classification"""
    MINOR = "Minor"  # Small changes, increments by 0.1 (e.g., v1.0 → v1.1)
    MAJOR = "Major"  # Significant changes, increments by 1.0 (e.g., v1.9 → v2.0)


class DocumentVersion(Base):
    """
    Individual version of a document with content and workflow state
    """
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)  # Sequential: 1, 2, 3...
    version_string = Column(String(20), nullable=True, index=True)  # Semantic: v0.1, v1.0, v1.1, v2.0
    
    # Version hierarchy and tracking
    parent_version_id = Column(Integer, ForeignKey('document_versions.id'), nullable=True)
    is_latest = Column(Boolean, default=True, nullable=False, index=True)  # Only one latest per document
    replaced_by_version_id = Column(Integer, ForeignKey('document_versions.id'), nullable=True)
    
    # Content
    content_html = Column(Text)  # HTML or SFDT format from Syncfusion
    content_hash = Column(String(64), nullable=True)  # SHA-256 hash for optimistic concurrency
    
    # Metadata
    change_summary = Column(Text)  # Description of changes in this version
    change_reason = Column(Text)  # Why this version was created (required for new versions)
    change_type = Column(SQLEnum(ChangeType), nullable=True)  # Minor or Major change
    status = Column(SQLEnum(VersionStatus), default=VersionStatus.DRAFT, nullable=False, index=True)
    
    # Lifecycle dates
    effective_date = Column(DateTime, nullable=True)  # When version became effective
    obsolete_date = Column(DateTime, nullable=True)  # When version was obsoleted
    
    # Attachments metadata (JSON list of attachment IDs or metadata)
    attachments_metadata = Column(JSON, default=list)
    
    # DOCX reference (if uploaded)
    docx_attachment_id = Column(Integer, ForeignKey('attachments.id'), nullable=True)
    
    # Workflow
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    submitted_at = Column(DateTime, nullable=True)  # When submitted for review
    submitted_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    review_comments = Column(Text)
    
    approved_at = Column(DateTime, nullable=True)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    approval_comments = Column(Text)
    e_signature_data = Column(JSON)  # Part 11 e-signature metadata
    
    published_at = Column(DateTime, nullable=True)
    published_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    rejected_at = Column(DateTime, nullable=True)
    rejected_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    rejection_reason = Column(Text)
    
    archived_at = Column(DateTime, nullable=True)
    archived_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Optimistic locking version
    lock_version = Column(Integer, default=0, nullable=False)
    
    # Relationships
    document = relationship("Document", foreign_keys=[document_id], back_populates="versions")
    
    # Version hierarchy
    parent_version = relationship("DocumentVersion", foreign_keys=[parent_version_id], remote_side=[id], uselist=False)
    child_versions = relationship("DocumentVersion", foreign_keys=[parent_version_id], remote_side=[parent_version_id])
    replaced_by_version = relationship("DocumentVersion", foreign_keys=[replaced_by_version_id], remote_side=[id], uselist=False, post_update=True)
    
    # User relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    published_by = relationship("User", foreign_keys=[published_by_id])
    rejected_by = relationship("User", foreign_keys=[rejected_by_id])
    archived_by = relationship("User", foreign_keys=[archived_by_id])
    
    # Other relationships
    docx_attachment = relationship("Attachment", foreign_keys=[docx_attachment_id])
    edit_locks = relationship("EditLock", back_populates="document_version", cascade="all, delete-orphan")
    comments = relationship("DocumentComment", back_populates="version", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DocumentVersion(id={self.id}, doc_id={self.document_id}, v={self.version_number}, status={self.status})>"


