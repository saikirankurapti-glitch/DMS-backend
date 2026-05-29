"""
Attachment model for DMS
Represents uploaded files linked to document versions
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Attachment(Base):
    """
    File attachment for document versions
    """
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    
    # File metadata
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    mime_type = Column(String(200), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    
    # Storage
    storage_path = Column(String(1000), nullable=False)  # Path in storage system
    storage_type = Column(String(50), default='local', nullable=False)  # local, s3, etc.
    
    # Security
    checksum_sha256 = Column(String(64), nullable=False)  # SHA-256 hash
    
    # Linking
    document_version_id = Column(Integer, ForeignKey('document_versions.id'), nullable=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True, index=True)
    
    # Upload metadata
    uploaded_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Description/purpose
    description = Column(String(1000))
    attachment_type = Column(String(50), default='supporting_document')  # supporting_document, docx_source, image, etc.
    
    # Virus scanning (optional, for future)
    scan_status = Column(String(50), default='pending')  # pending, clean, infected, error
    scan_result = Column(String(500))
    scanned_at = Column(DateTime, nullable=True)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])
    
    def __repr__(self):
        return f"<Attachment(id={self.id}, filename={self.filename}, size={self.file_size})>"

