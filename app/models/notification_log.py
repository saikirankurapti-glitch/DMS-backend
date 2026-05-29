"""
Notification Log Model
Tracks all email notifications sent for audit compliance
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class NotificationStatus(str, enum.Enum):
    """Notification delivery status"""
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    BOUNCED = "BOUNCED"


class NotificationEventType(str, enum.Enum):
    """Types of notification events"""
    REVIEW_ASSIGNED = "REVIEW_ASSIGNED"
    REVIEW_REJECTED = "REVIEW_REJECTED"
    REVIEW_APPROVED = "REVIEW_APPROVED"
    APPROVAL_ASSIGNED = "APPROVAL_ASSIGNED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    APPROVAL_APPROVED = "APPROVAL_APPROVED"
    DOCUMENT_EFFECTIVE = "DOCUMENT_EFFECTIVE"
    VERSION_OBSOLETED = "VERSION_OBSOLETED"


class NotificationLog(Base):
    """Log of all email notifications sent"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    version_id = Column(Integer, ForeignKey('document_versions.id', ondelete='CASCADE'), nullable=True, index=True)
    event_type = Column(SQLEnum(NotificationEventType), nullable=False, index=True)
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=True)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    document = relationship("Document", foreign_keys=[document_id])
    version = relationship("DocumentVersion", foreign_keys=[version_id])
    recipient_user = relationship("User", foreign_keys=[recipient_user_id])
    
    def __repr__(self):
        return f"<NotificationLog(id={self.id}, event={self.event_type.value}, recipient={self.recipient_email}, status={self.status.value})>"

