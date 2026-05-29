"""
Document model for DMS
Represents the master document entity with metadata
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Document(Base):
    """
    Master Document entity containing metadata and lifecycle state
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    department = Column(String(100), index=True)
    tags = Column(JSON, default=list)  # List of tag strings
    
    # Ownership & lifecycle
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    current_version_id = Column(Integer, ForeignKey('document_versions.id'), nullable=True)
    
    # Status from current version (denormalized for quick filtering)
    status = Column(String(50), default='Draft', nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_documents")
    created_by = relationship("User", foreign_keys=[created_by_id])
    current_version = relationship("DocumentVersion", foreign_keys=[current_version_id], 
                                   post_update=True, uselist=False)
    versions = relationship("DocumentVersion", foreign_keys="DocumentVersion.document_id",
                           back_populates="document", order_by="DocumentVersion.version_number.desc()")
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])

    def __repr__(self):
        return f"<Document(id={self.id}, number={self.document_number}, title={self.title})>"


