"""
Pydantic schemas for Block-Based Template Builder
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date


# Block Types
class TemplateBlock(BaseModel):
    """A content block in the template"""
    id: str = Field(..., description="Unique block ID")
    type: str = Field(..., description="Block type: title, heading, paragraph, table, list, image, annexure_table, signatory_table")
    html: str = Field(..., description="HTML content from CKEditor with tokens")
    order: int = Field(..., description="Display order")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional block metadata")


class TemplateMetadata(BaseModel):
    """Template metadata - minimal for template creation"""
    template_title: Optional[str] = Field(None, max_length=500, description="Placeholder, filled at document creation")
    category: str = Field(..., description="SOP, STP, Form, Report, Annexure")


class RequiredMetadataField(BaseModel):
    """A metadata field that can be required"""
    key: str = Field(..., description="Field key (e.g., 'template_title', 'template_code')")
    label: str = Field(..., description="Field label (e.g., 'SOP Title', 'SOP Number')")
    required: bool = Field(False, description="Whether this field is required")


class TemplateConfig(BaseModel):
    """Template configuration"""
    required_metadata_fields: List[RequiredMetadataField] = Field(default_factory=list)
    category: str = Field(..., description="Template category")


class TemplateData(BaseModel):
    """Complete template data structure"""
    metadata: TemplateMetadata
    blocks: List[TemplateBlock] = Field(default_factory=list)
    config: Optional[TemplateConfig] = Field(None, description="Template configuration including required metadata fields")


class TemplateCreateRequest(BaseModel):
    """Request to create a new template"""
    template_data: TemplateData
    sample_values: Optional[Dict[str, str]] = Field(None, description="Sample token values for preview")


class TemplateUpdateRequest(BaseModel):
    """Request to update template"""
    template_data: TemplateData
    sample_values: Optional[Dict[str, str]] = None


class TemplatePreviewRequest(BaseModel):
    """Request for template preview"""
    sample_values: Optional[Dict[str, str]] = Field(None, description="Token values to use in preview")


class TemplateGenerateRequest(BaseModel):
    """Request to generate document from template"""
    token_values: Dict[str, str] = Field(..., description="Token values for replacement")
    format: str = Field("docx", description="Output format: docx, pdf, html")
    strict_mode: bool = Field(False, description="If True, fail on missing tokens; if False, use defaults")


class TokenInfo(BaseModel):
    """Information about a token"""
    name: str
    category: str  # Metadata, Signatories, Dates, Annexures, System
    description: Optional[str] = None
    example: Optional[str] = None


class TokenUsageResponse(BaseModel):
    """Response showing token usage in template"""
    tokens_found: List[str]
    tokens_used: List[TokenInfo]
    missing_required: List[str] = Field(default_factory=list)
    unknown_tokens: List[str] = Field(default_factory=list)


class TemplateResponse(BaseModel):
    """Template response with full data"""
    id: int
    name: str
    template_code: Optional[str]
    category: Optional[str]
    department: Optional[str]
    template_type: str
    status: str
    version_number: int
    revision: Optional[str]
    template_data: Optional[Dict[str, Any]]
    created_by_id: int
    created_by_username: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

