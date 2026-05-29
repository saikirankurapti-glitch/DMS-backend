"""
API v1 Routes
"""
from fastapi import APIRouter
from app.api.v1 import auth, users, audit_logs, documents, document_versions, edit_locks, attachments, comments, templates
try:
    from app.api.v1 import export
    has_export = True
except ImportError:
    has_export = False

api_router = APIRouter()

# User Management & Auth
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["User Management"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])

# Document Management
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])

# Document Versions - nested under documents  
api_router.include_router(document_versions.router, prefix="/documents", tags=["Document Versions"])

# Edit Locks - also nested under documents
api_router.include_router(edit_locks.router, prefix="/documents", tags=["Edit Locks"])

# Attachments
api_router.include_router(attachments.router, prefix="/attachments", tags=["Attachments"])

# Export (DOCX)
if has_export:
    api_router.include_router(export.router, prefix="/documents", tags=["Export"])

# Comments
api_router.include_router(comments.router, prefix="/documents", tags=["Comments"])

# Templates
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])

# Template Builder (block-based)
try:
    from app.api.v1 import template_builder
    api_router.include_router(template_builder.router, prefix="/template-builder", tags=["Template Builder"])
except ImportError:
    pass


