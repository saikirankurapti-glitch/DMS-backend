"""
Pydantic schemas for Template operations
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
from datetime import datetime


# Template Schemas
class TemplateBase(BaseModel):
    """Base template schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)


class TemplateCreate(TemplateBase):
    """Schema for creating a new template (via upload)"""
    owner_id: Optional[int] = None  # If not provided, defaults to current user


class TemplateUpdate(BaseModel):
    """Schema for updating template metadata"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)


class TemplateResponse(TemplateBase):
    """Schema for template response"""
    id: int
    owner_id: int
    created_by_id: int
    current_published_version_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    
    # Include owner info
    owner_username: Optional[str] = None
    owner_full_name: Optional[str] = None
    created_by_username: Optional[str] = None
    
    # Version count
    version_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """Schema for paginated template list"""
    items: List[TemplateResponse]
    total: int
    page: int
    size: int
    pages: int = 1


# TemplateVersion Schemas
class TemplateVersionResponse(BaseModel):
    """Schema for template version response"""
    id: int
    template_id: int
    version_number: int
    docx_file_path: Optional[str] = None  # None for block-based templates
    preview_html_path: Optional[str] = None  # None for block-based templates
    template_data: Optional[dict] = None  # For block-based templates
    generated_docx_path: Optional[str] = None
    generated_pdf_path: Optional[str] = None
    status: str
    created_by_id: int
    created_by_username: Optional[str] = None
    submitted_for_review_at: Optional[datetime] = None
    submitted_for_review_by_id: Optional[int] = None
    submitted_for_approval_at: Optional[datetime] = None
    submitted_for_approval_by_id: Optional[int] = None
    published_at: Optional[datetime] = None
    published_by_id: Optional[int] = None
    rejected_at: Optional[datetime] = None
    rejected_by_id: Optional[int] = None
    rejection_reason: Optional[str] = None
    revision: Optional[str] = None
    sample_values: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TemplateVersionListResponse(BaseModel):
    """Schema for paginated template version list"""
    items: List[TemplateVersionResponse]
    total: int
    page: int
    size: int
    pages: int = 1


class TemplateVersionDetailResponse(TemplateVersionResponse):
    """Schema for detailed template version with reviews and approvals"""
    reviews: List[Any] = []  # Will be List[TemplateReviewResponse] at runtime
    approvals: List[Any] = []  # Will be List[TemplateApprovalResponse] at runtime
    
    class Config:
        from_attributes = True


# TemplateReview Schemas
class TemplateReviewCreate(BaseModel):
    """Schema for creating a review comment"""
    comment: str = Field(..., min_length=1)


class TemplateReviewResponse(BaseModel):
    """Schema for review response"""
    id: int
    template_version_id: int
    reviewer_id: int
    reviewer_username: Optional[str] = None
    reviewer_full_name: Optional[str] = None
    comment: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# TemplateApproval Schemas
class TemplateApprovalCreate(BaseModel):
    """Schema for creating an approval decision"""
    decision: str = Field(..., pattern="^(Approved|Rejected)$")
    comment: Optional[str] = None
    password: str = Field(..., min_length=1)  # For e-signature verification


class TemplateApprovalResponse(BaseModel):
    """Schema for approval response"""
    id: int
    template_version_id: int
    approver_id: int
    approver_username: Optional[str] = None
    approver_full_name: Optional[str] = None
    decision: str
    comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Workflow Schemas
class SubmitForReviewRequest(BaseModel):
    """Schema for submitting template for review"""
    pass  # No additional fields needed


class SubmitForApprovalRequest(BaseModel):
    """Schema for submitting template for approval"""
    pass  # No additional fields needed


class PublishTemplateRequest(BaseModel):
    """Schema for publishing a template"""
    pass  # No additional fields needed


# Template Usage Schema
class TemplateUsageResponse(BaseModel):
    """Schema for template HTML content when using template to create document"""
    template_id: int
    template_version_id: int
    template_name: str
    html_content: str
    required_metadata_fields: Optional[List[dict]] = Field(default_factory=list)


# Validation Schema
class TemplateValidationRequest(BaseModel):
    """Schema for validating template headings"""
    required_headings: Optional[List[str]] = Field(default_factory=list)


class TemplateValidationResponse(BaseModel):
    """Schema for validation response"""
    is_valid: bool
    missing_headings: List[str] = []

