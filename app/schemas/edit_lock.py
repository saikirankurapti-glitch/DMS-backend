"""
Pydantic schemas for EditLock operations
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EditLockAcquireRequest(BaseModel):
    """Schema for acquiring an edit lock"""
    session_id: Optional[str] = Field(None, max_length=100)
    timeout_minutes: int = Field(default=30, ge=5, le=120)


class EditLockResponse(BaseModel):
    """Schema for edit lock response"""
    id: int
    document_version_id: int
    user_id: int
    lock_token: str
    acquired_at: datetime
    expires_at: datetime
    last_heartbeat: datetime
    session_id: Optional[str]
    
    # User info
    username: Optional[str] = None
    user_full_name: Optional[str] = None
    
    # Lock status
    is_expired: bool = False
    time_remaining_seconds: Optional[int] = None
    
    class Config:
        from_attributes = True


class EditLockHeartbeatRequest(BaseModel):
    """Schema for refreshing lock with heartbeat"""
    lock_token: str
    extend_minutes: int = Field(default=30, ge=5, le=120)


class EditLockReleaseRequest(BaseModel):
    """Schema for releasing a lock"""
    lock_token: str


class EditLockStatus(BaseModel):
    """Schema for checking lock status without acquiring"""
    is_locked: bool
    locked_by_user_id: Optional[int] = None
    locked_by_username: Optional[str] = None
    lock_expires_at: Optional[datetime] = None
    can_acquire: bool = True
    lock_token: Optional[str] = None  # Only if current user owns the lock


