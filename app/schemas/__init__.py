"""
Pydantic Schemas for API request/response validation
"""
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserResponse,
    UserListResponse,
    PasswordReset,
)
from app.schemas.auth import Token, TokenData, LoginRequest
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    DocumentSearchFilters,
)
from app.schemas.document_version import (
    DocumentVersionCreate,
    DocumentVersionUpdate,
    DocumentVersionSave,
    DocumentVersionResponse,
    DocumentVersionListItem,
    DocumentVersionListResponse,
    SubmitForReviewRequest,
    ReviewRequest,
    ApprovalRequest,
    PublishRequest,
)
from app.schemas.attachment import (
    AttachmentUpload,
    AttachmentResponse,
    AttachmentListResponse,
)
from app.schemas.edit_lock import (
    EditLockAcquireRequest,
    EditLockResponse,
    EditLockHeartbeatRequest,
    EditLockReleaseRequest,
    EditLockStatus,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserResponse",
    "UserListResponse",
    "PasswordReset",
    # Auth schemas
    "Token",
    "TokenData",
    "LoginRequest",
    # Audit log schemas
    "AuditLogResponse",
    "AuditLogListResponse",
    # Document schemas
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentDetailResponse",
    "DocumentSearchFilters",
    # Document version schemas
    "DocumentVersionCreate",
    "DocumentVersionUpdate",
    "DocumentVersionSave",
    "DocumentVersionResponse",
    "DocumentVersionListItem",
    "DocumentVersionListResponse",
    "SubmitForReviewRequest",
    "ReviewRequest",
    "ApprovalRequest",
    "PublishRequest",
    # Attachment schemas
    "AttachmentUpload",
    "AttachmentResponse",
    "AttachmentListResponse",
    # Edit lock schemas
    "EditLockAcquireRequest",
    "EditLockResponse",
    "EditLockHeartbeatRequest",
    "EditLockReleaseRequest",
    "EditLockStatus",
]


