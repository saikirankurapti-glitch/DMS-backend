"""
Template Models for Document Templates Module
Handles template metadata, versions, reviews, and approvals
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum


class TemplateStatus(str, enum.Enum):
    """Template version workflow states"""
    DRAFT = "Draft"
    UNDER_REVIEW = "UnderReview"
    PENDING_APPROVAL = "PendingApproval"
    REJECTED = "Rejected"
    PUBLISHED = "Published"


class TemplateStatusType(TypeDecorator):
    """Custom type to ensure enum values are used, not names"""
    # Provide a fully constructed ENUM type instance as the underlying impl
    impl = ENUM(
        'Draft', 'UnderReview', 'PendingApproval', 'Rejected', 'Published',
        name='templatestatus',
        native_enum=True
    )
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """Convert enum to its value string before binding"""
        if value is None:
            return None
        if isinstance(value, TemplateStatus):
            return value.value  # Return the enum value, not name
        return value
    
    def process_result_value(self, value, dialect):
        """Convert database value back to enum"""
        if value is None:
            return None
        if isinstance(value, str):
            # Find enum member by value
            for status in TemplateStatus:
                if status.value == value:
                    return status
        return value


class Template(Base):
    """
    Template model - stores template metadata
    Supports both DOCX upload and block-based builder templates
    """
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    template_code = Column(String(100), unique=True, nullable=True, index=True)  # Unique code like SP-KQA-007-01
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)  # SOP, STP, Form, Report, Annexure
    department = Column(String(100), nullable=True, index=True)
    confidentiality = Column(String(50), default='Internal', nullable=True)  # Public, Internal, Restricted
    
    # Ownership
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Current published version (if any)
    current_published_version_id = Column(Integer, ForeignKey('template_versions.id'), nullable=True)
    
    # Template type: 'docx_upload' or 'block_builder'
    template_type = Column(String(50), default='block_builder', nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    owner = relationship("User", foreign_keys=[owner_id])
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])
    versions = relationship("TemplateVersion", back_populates="template", 
                          foreign_keys="TemplateVersion.template_id",
                          order_by="TemplateVersion.version_number.desc()")
    current_published_version = relationship("TemplateVersion", 
                                           foreign_keys=[current_published_version_id],
                                           post_update=True, uselist=False)
    
    def __repr__(self):
        return f"<Template(id={self.id}, name='{self.name}')>"


class TemplateVersion(Base):
    """
    TemplateVersion model - stores template content
    For DOCX upload: stores file paths
    For block builder: stores JSON structure with blocks
    """
    __tablename__ = "template_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('templates.id', ondelete='CASCADE'), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)  # 1, 2, 3...
    revision = Column(String(50), nullable=True)  # Revision number like "01", "02"
    
    # For DOCX upload templates
    docx_file_path = Column(String(500), nullable=True)  # Path to original DOCX (if uploaded)
    preview_html_path = Column(String(500), nullable=True)  # Path to converted HTML preview
    
    # For block-based templates - JSON storage
    template_data = Column(JSON, nullable=True)  # Stores: {metadata: {}, blocks: []}
    # Structure:
    # {
    #   "metadata": {
    #     "template_title": "...",
    #     "template_code": "...",
    #     "category": "SOP",
    #     "revision": "01",
    #     "effective_date": "2024-01-01",
    #     "next_review_date": "2025-01-01",
    #     "cc_number": "...",
    #     "department": "...",
    #     "confidentiality": "Internal",
    #     "owner_id": 1
    #   },
    #   "blocks": [
    #     {"id": "b1", "type": "title", "html": "<h1>...{{TEMPLATE_TITLE}}...</h1>"},
    #     {"id": "b2", "type": "paragraph", "html": "<p>Objective: {{OBJECTIVE}}</p>"},
    #     ...
    #   ]
    # }
    
    # Generated files (after approval)
    generated_docx_path = Column(String(500), nullable=True)
    generated_pdf_path = Column(String(500), nullable=True)
    
    # Status
    # Use custom type to ensure enum values are used, not names
    status = Column(
        TemplateStatusType(),
        default=TemplateStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    # Workflow tracking
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    submitted_for_review_at = Column(DateTime, nullable=True)
    submitted_for_review_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    submitted_for_approval_at = Column(DateTime, nullable=True)
    submitted_for_approval_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    published_at = Column(DateTime, nullable=True)
    published_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    rejected_at = Column(DateTime, nullable=True)
    rejected_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Sample values for preview (JSON)
    sample_values = Column(JSON, nullable=True)  # {"TEMPLATE_TITLE": "Sample Title", ...}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    template = relationship("Template", foreign_keys=[template_id], back_populates="versions")
    created_by = relationship("User", foreign_keys=[created_by_id])
    submitted_for_review_by = relationship("User", foreign_keys=[submitted_for_review_by_id])
    submitted_for_approval_by = relationship("User", foreign_keys=[submitted_for_approval_by_id])
    published_by = relationship("User", foreign_keys=[published_by_id])
    rejected_by = relationship("User", foreign_keys=[rejected_by_id])
    reviews = relationship("TemplateReview", back_populates="template_version", cascade="all, delete-orphan")
    approvals = relationship("TemplateApproval", back_populates="template_version", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TemplateVersion(id={self.id}, template_id={self.template_id}, v={self.version_number}, status={self.status})>"


class TemplateReview(Base):
    """
    TemplateReview model - stores reviewer comments
    """
    __tablename__ = "template_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    template_version_id = Column(Integer, ForeignKey('template_versions.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Reviewer info
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    comment = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    template_version = relationship("TemplateVersion", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    
    def __repr__(self):
        return f"<TemplateReview(id={self.id}, template_version_id={self.template_version_id}, reviewer_id={self.reviewer_id})>"


class TemplateApproval(Base):
    """
    TemplateApproval model - stores approver decisions
    """
    __tablename__ = "template_approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    template_version_id = Column(Integer, ForeignKey('template_versions.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Approver info
    approver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    decision = Column(String(20), nullable=False)  # "Approved" or "Rejected"
    comment = Column(Text, nullable=True)
    
    # E-signature data (for compliance)
    e_signature_data = Column(Text, nullable=True)  # JSON string with signature metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    template_version = relationship("TemplateVersion", back_populates="approvals")
    approver = relationship("User", foreign_keys=[approver_id])
    
    def __repr__(self):
        return f"<TemplateApproval(id={self.id}, template_version_id={self.template_version_id}, decision={self.decision})>"

