"""
Pydantic schemas for DocumentVersion operations
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.document_version import VersionStatus, ChangeType


class DocumentVersionBase(BaseModel):
    """Base version schema"""
    change_summary: Optional[str] = None


class DocumentVersionCreate(DocumentVersionBase):
    """Schema for creating a new document version"""
    content_html: Optional[str] = None
    attachments_metadata: Optional[List[Dict[str, Any]]] = []
    change_reason: Optional[str] = None
    change_type: Optional[ChangeType] = None
    parent_version_id: Optional[int] = None


class DocumentVersionUpdate(BaseModel):
    """Schema for updating a draft version"""
    content_html: Optional[str] = None
    change_summary: Optional[str] = None
    attachments_metadata: Optional[List[Dict[str, Any]]] = None


class DocumentVersionSave(BaseModel):
    """Schema for saving version content (autosave/manual save)"""
    content_html: str
    content_hash: Optional[str] = None  # For optimistic locking
    lock_token: Optional[str] = None  # For edit lock verification
    is_autosave: bool = False


class DocumentVersionResponse(BaseModel):
    """Schema for version response"""
    id: int
    document_id: int
    version_number: int
    version_string: Optional[str]  # Semantic version (v0.1, v1.0, v1.1, v2.0)
    content_html: Optional[str]
    content_hash: Optional[str]
    change_summary: Optional[str]
    change_reason: Optional[str]
    change_type: Optional[ChangeType]
    status: VersionStatus
    attachments_metadata: Optional[List[Dict[str, Any]]]
    docx_attachment_id: Optional[int]
    
    # Version hierarchy
    parent_version_id: Optional[int]
    is_latest: bool
    replaced_by_version_id: Optional[int]
    
    # Lifecycle dates
    effective_date: Optional[datetime]
    obsolete_date: Optional[datetime]
    
    # Workflow metadata
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    
    submitted_at: Optional[datetime]
    submitted_by_id: Optional[int]
    
    reviewed_at: Optional[datetime]
    reviewed_by_id: Optional[int]
    review_comments: Optional[str]
    
    approved_at: Optional[datetime]
    approved_by_id: Optional[int]
    approval_comments: Optional[str]
    
    published_at: Optional[datetime]
    published_by_id: Optional[int]
    
    rejected_at: Optional[datetime]
    rejected_by_id: Optional[int]
    rejection_reason: Optional[str]
    
    archived_at: Optional[datetime]
    archived_by_id: Optional[int]
    
    lock_version: int
    
    # User info
    created_by_username: Optional[str] = None
    created_by_full_name: Optional[str] = None
    approved_by_username: Optional[str] = None
    approved_by_full_name: Optional[str] = None
    
    # Lock status
    is_locked: bool = False
    locked_by_user_id: Optional[int] = None
    locked_by_username: Optional[str] = None
    lock_expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


class DocumentVersionListItem(BaseModel):
    """Schema for version in list (minimal info)"""
    id: int
    document_id: int
    version_number: int
    version_string: Optional[str] = None
    status: VersionStatus
    change_summary: Optional[str] = None
    change_reason: Optional[str] = None
    change_type: Optional[ChangeType] = None
    is_latest: Optional[bool] = None
    effective_date: Optional[datetime] = None
    obsolete_date: Optional[datetime] = None
    created_by_id: int
    created_by_username: Optional[str] = None
    approved_by_username: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True


class DocumentVersionListResponse(BaseModel):
    """Schema for paginated version list"""
    versions: List[DocumentVersionListItem]
    total: int
    page: int
    page_size: int


class WorkflowAction(BaseModel):
    """Schema for workflow actions (submit, approve, reject, etc.)"""
    comments: Optional[str] = None
    e_signature_password: Optional[str] = None  # For Part 11 compliance


class SubmitForReviewRequest(WorkflowAction):
    """Schema for submitting version for review"""
    reviewer_ids: Optional[List[int]] = []
    password: str  # E-signature: user password for authentication


class ReviewRequest(WorkflowAction):
    """Schema for review action (approve or request changes)"""
    password: str  # E-signature: user password for authentication


class ApprovalRequest(WorkflowAction):
    """Schema for approval/rejection action"""
    password: str  # E-signature: user password for authentication


class PublishRequest(WorkflowAction):
    """Schema for publishing action"""
    effective_date: Optional[datetime] = None
    password: str  # E-signature: user password for authentication


class CreateNewVersionRequest(BaseModel):
    """Schema for creating a new version from an existing effective version"""
    change_reason: str = Field(..., min_length=10, max_length=1000, description="Reason for creating new version")
    change_type: ChangeType = Field(..., description="Type of change: Minor or Major")
    
    class Config:
        use_enum_values = True




class SubmitForReviewRequest(WorkflowAction):
    """Schema for submitting version for review"""
    reviewer_ids: Optional[List[int]] = []
    password: str  # E-signature: user password for authentication


class ReviewRequest(WorkflowAction):
    """Schema for review action (approve or request changes)"""
    password: str  # E-signature: user password for authentication


class ApprovalRequest(WorkflowAction):
    """Schema for approval/rejection action"""
    password: str  # E-signature: user password for authentication


class PublishRequest(WorkflowAction):
    """Schema for publishing action"""
    effective_date: Optional[datetime] = None
    password: str  # E-signature: user password for authentication


class CreateNewVersionRequest(BaseModel):
    """Schema for creating a new version from an existing effective version"""
    change_reason: str = Field(..., min_length=10, max_length=1000, description="Reason for creating new version")
    change_type: ChangeType = Field(..., description="Type of change: Minor or Major")
    
    class Config:
        use_enum_values = True


