"""
Audit Log Model - Records all significant system actions for compliance
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class AuditLog(Base):
    """
    Audit Log model for tracking all user and system actions
    Critical for FDA 21 CFR Part 11 compliance
    """
    __tablename__ = "audit_logs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Who performed the action
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username = Column(String(100), nullable=False)  # Stored for historical record even if user deleted
    
    # What action was performed
    action = Column(String(100), nullable=False, index=True)  # e.g., "USER_CREATED", "USER_DEACTIVATED"
    entity_type = Column(String(50), nullable=False, index=True)  # e.g., "User", "Document"
    entity_id = Column(Integer, nullable=True, index=True)  # ID of affected entity
    
    # Details
    description = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # Additional structured data
    
    # Context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user='{self.username}', timestamp='{self.timestamp}')>"


