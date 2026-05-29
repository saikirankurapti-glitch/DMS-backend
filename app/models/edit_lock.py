"""
EditLock model for DMS
Manages concurrent editing locks on document versions
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.database import Base
import secrets


class EditLock(Base):
    """
    Edit lock for preventing concurrent modifications to document versions
    """
    __tablename__ = "edit_locks"
    
    __table_args__ = (
        UniqueConstraint('document_version_id', name='uq_edit_locks_document_version_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    document_version_id = Column(Integer, ForeignKey('document_versions.id', ondelete='CASCADE'), 
                                 nullable=False, index=True)
    
    # Lock ownership
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    lock_token = Column(String(64), unique=True, nullable=False, index=True)
    
    # Lock timing
    acquired_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Session info for debugging
    session_id = Column(String(100))  # Frontend session identifier
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Relationships
    document_version = relationship("DocumentVersion", back_populates="edit_locks")
    user = relationship("User")
    
    @staticmethod
    def generate_token():
        """Generate a secure random lock token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def default_expiry(minutes=30):
        """Get default expiry time"""
        return datetime.utcnow() + timedelta(minutes=minutes)
    
    def is_expired(self):
        """Check if lock is expired"""
        return datetime.utcnow() > self.expires_at
    
    def refresh(self, extend_minutes=30):
        """Refresh lock expiry and update heartbeat"""
        self.last_heartbeat = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(minutes=extend_minutes)
    
    def __repr__(self):
        return f"<EditLock(id={self.id}, version_id={self.document_version_id}, user_id={self.user_id}, expires={self.expires_at})>"


