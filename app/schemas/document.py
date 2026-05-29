"""
Pydantic schemas for Document operations
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
from datetime import datetime


class DocumentBase(BaseModel):
    """Base document schema with common fields"""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    department: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = []


class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    document_number: Optional[str] = Field(None, max_length=100)
    owner_id: Optional[int] = None  # If not provided, defaults to current user


class DocumentUpdate(BaseModel):
    """Schema for updating document metadata"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    department: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    owner_id: Optional[int] = None


class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: int
    document_number: str
    owner_id: int
    created_by_id: int
    current_version_id: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    
    # Include owner info
    owner_username: Optional[str] = None
    owner_full_name: Optional[str] = None
    
    # Version count
    version_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for paginated document list"""
    items: List[DocumentResponse]
    total: int
    page: int
    size: int  # Changed from page_size to match frontend expectation
    pages: int = 1  # Total number of pages
    
    
class DocumentDetailResponse(DocumentResponse):
    """Schema for detailed document view with versions"""
    versions: List[Any] = []  # Will be List[DocumentVersionListItem] at runtime
    
    class Config:
        from_attributes = True


class DocumentSearchFilters(BaseModel):
    """Schema for document search/filter parameters"""
    title: Optional[str] = None
    document_number: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[int] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

