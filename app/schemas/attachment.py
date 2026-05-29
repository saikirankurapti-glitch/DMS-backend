"""
Pydantic schemas for Attachment operations
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AttachmentBase(BaseModel):
    """Base attachment schema"""
    description: Optional[str] = Field(None, max_length=1000)
    attachment_type: str = Field(default="supporting_document", max_length=50)


class AttachmentUpload(AttachmentBase):
    """Schema for attachment upload metadata"""
    document_id: Optional[int] = None
    document_version_id: Optional[int] = None


class AttachmentResponse(BaseModel):
    """Schema for attachment response"""
    id: int
    filename: str
    original_filename: str
    mime_type: str
    file_size: int
    storage_path: str
    storage_type: str
    checksum_sha256: str
    document_version_id: Optional[int]
    document_id: Optional[int]
    uploaded_by_id: int
    uploaded_at: datetime
    description: Optional[str]
    attachment_type: str
    scan_status: str
    scan_result: Optional[str]
    scanned_at: Optional[datetime]
    is_deleted: bool
    
    # User info
    uploaded_by_username: Optional[str] = None
    uploaded_by_full_name: Optional[str] = None
    
    # Download URL (computed)
    download_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class AttachmentListResponse(BaseModel):
    """Schema for attachment list"""
    attachments: list[AttachmentResponse]
    total: int


