"""
Comment Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CommentCreate(BaseModel):
    """Schema for creating a comment"""
    comment_text: str
    selected_text: Optional[str] = None
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None
    text_context: Optional[str] = None


class CommentUpdate(BaseModel):
    """Schema for updating a comment"""
    comment_text: Optional[str] = None
    is_resolved: Optional[bool] = None


class CommentResponse(BaseModel):
    """Schema for comment response"""
    id: int
    document_version_id: int
    user_id: int
    user_name: Optional[str] = None
    user_full_name: Optional[str] = None
    comment_text: str
    selected_text: Optional[str] = None
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None
    text_context: Optional[str] = None
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[int] = None
    resolved_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Schema for list of comments"""
    comments: list[CommentResponse]
    total: int

