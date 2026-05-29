"""
Document Export API Endpoints
Handles DOCX export and import with e-signature verification
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from io import BytesIO
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.models import Document, DocumentVersion, User
from app.utils.docx_export import html_to_docx, docx_to_html
from app.core.audit import AuditLogger
from app.core.security import verify_password

router = APIRouter()


class ExportRequest(BaseModel):
    """Schema for export request with e-signature"""
    password: str
    reason: Optional[str] = None


@router.post("/{document_id}/versions/{version_id}/export/docx")
async def export_version_to_docx(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    export_request: ExportRequest
):
    """
    Export document version as DOCX file
    
    Requires password verification for e-signature compliance (FDA 21 CFR Part 11)
    All authenticated users can export
    """
    # Verify password for e-signature
    if not verify_password(export_request.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password. E-signature verification failed."
        )
    
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get version
    version = db.query(DocumentVersion).filter(
        DocumentVersion.id == version_id,
        DocumentVersion.document_id == document_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    if not version.content_html:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Version has no content to export"
        )
    
    # Convert to DOCX
    try:
        docx_buffer = html_to_docx(
            html_content=version.content_html,
            title=document.title,
            doc_number=document.document_number,
            department=document.department
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate DOCX: {str(e)}"
        )
    
    # Audit log with e-signature details
    export_reason = export_request.reason or "Document export for offline review/printing"
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="VERSION_EXPORTED",
        entity_type="DocumentVersion",
        entity_id=version.id,
        description=f"Exported version {version.version_number} of document {document.document_number} as DOCX",
        details={
            "document_id": document.id,
            "document_number": document.document_number,
            "document_title": document.title,
            "version_number": version.version_number,
            "version_status": version.status.value,
            "export_reason": export_reason,
            "e_signature": {
                "signed_by": current_user.username,
                "signed_by_name": f"{current_user.first_name} {current_user.last_name}",
                "signed_at": datetime.utcnow().isoformat(),
                "action": "DOCUMENT_EXPORT",
                "meaning": "I confirm this export for authorized use"
            }
        }
    )
    
    # Create filename
    filename = f"{document.document_number}_v{version.version_number}.docx"
    
    # Return as download
    return StreamingResponse(
        docx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.post("/{document_id}/versions/{version_id}/import/docx")
async def import_docx_to_version(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    file: UploadFile = File(...)
):
    """
    Import DOCX file and update version content
    
    Requires: Author or Admin, and version must be Draft
    """
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get version
    version = db.query(DocumentVersion).filter(
        DocumentVersion.id == version_id,
        DocumentVersion.document_id == document_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    # Check permissions
    if not (current_user.has_role("Author") or current_user.is_admin()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Authors and Admins can import documents"
        )
    
    # Check version status
    if version.status.value != "Draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only import to Draft versions"
        )
    
    # Validate file type
    if not file.filename or not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .docx files are supported"
        )
    
    # Read file
    try:
        content = await file.read()
        docx_buffer = BytesIO(content)
        
        # Convert to HTML
        html_content = docx_to_html(docx_buffer)
        
        # Update version content
        version.content_html = html_content
        version.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(version)
        
        # Audit log
        AuditLogger.log(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="VERSION_IMPORTED",
            entity_type="DocumentVersion",
            entity_id=version.id,
            description=f"Imported DOCX file '{file.filename}' to version {version.version_number} of document {document.document_number}"
        )
        
        return {
            "message": "DOCX imported successfully",
            "version_id": version.id,
            "content_length": len(html_content)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import DOCX: {str(e)}"
        )
