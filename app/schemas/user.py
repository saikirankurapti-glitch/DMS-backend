"""
User Schemas for API validation and serialization
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


class RoleSchema(BaseModel):
    """Role information"""
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    """Base user schema with common fields"""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """Schema for creating a new user (Admin only)"""
    password: str = Field(..., min_length=8, max_length=100)
    role_ids: List[int] = Field(..., min_items=1, description="List of role IDs to assign")
    is_active: bool = True
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password meets minimum requirements"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information (Admin only)"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role_ids: Optional[List[int]] = Field(None, min_items=1)
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """User schema as stored in database"""
    id: int
    is_active: bool
    is_temp_password: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    roles: List[RoleSchema] = []
    
    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    """User schema for API responses"""
    pass


class UserListResponse(BaseModel):
    """Paginated list of users"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    
    class Config:
        from_attributes = True


class PasswordReset(BaseModel):
    """Schema for admin password reset"""
    new_password: str = Field(..., min_length=8, max_length=100)
    force_change: bool = Field(
        True, 
        description="If true, user must change password on next login"
    )
    
    @validator("new_password")
    def validate_password(cls, v):
        """Validate password meets minimum requirements"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserActivate(BaseModel):
    """Schema for activating/deactivating users"""
    is_active: bool


