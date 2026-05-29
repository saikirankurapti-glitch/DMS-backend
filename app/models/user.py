"""
User Model - Core user entity with authentication and profile data
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.role import user_roles


class User(Base):
    """
    User model representing system users
    Supports multiple roles per user for flexible RBAC
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_temp_password = Column(Boolean, default=False, nullable=False)
    
    # Session Management - Single session enforcement
    active_session_token = Column(String(500), nullable=True)  # Current active JWT token
    session_created_at = Column(DateTime, nullable=True)  # When current session was created
    
    # Profile
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user", foreign_keys="AuditLog.user_id")
    owned_documents = relationship("Document", foreign_keys="Document.owner_id", back_populates="owner")
    
    @property
    def full_name(self):
        """Returns user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return any(role.name == role_name for role in self.roles)
    
    def is_admin(self) -> bool:
        """Check if user has DMS_Admin role"""
        return self.has_role("DMS_Admin")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


