"""
Authentication Schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login credentials"""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=1, max_length=100)
    force_login: bool = Field(default=False, description="Force login and override existing session")


class UserInfo(BaseModel):
    """Basic user information included in token response"""
    id: int
    username: str
    email: str
    full_name: str
    roles: List[str]
    is_active: bool


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserInfo
    requires_password_change: bool = False


class SessionConflictResponse(BaseModel):
    """Response when there's an existing active session"""
    session_conflict: bool = True
    message: str = "Another session is already active"
    existing_session_created_at: Optional[datetime] = None
    detail: str = "Please confirm to override the existing session"


class TokenData(BaseModel):
    """Data stored in JWT token"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    roles: List[str] = []


