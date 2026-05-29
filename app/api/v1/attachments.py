"""
Attachment Management API Endpoints
Handles file uploads, downloads, and metadata (URS-DVM-007)
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import hashlib
import aiofiles
from pathlib import Path
from datetime import datetime
import mimetypes

from app.api.deps import get_db, get_current_user
from app.models import Attachment, Document, DocumentVersion, User
from app.schemas.attachment import AttachmentUpload, AttachmentResponse, AttachmentListResponse
from app.core.audit import AuditLogger

router = APIRouter()

# Storage configuration
UPLOAD_DIR = Path("storage/attachments")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


async def save_upload_file(upload_file: UploadFile, dest_path: Path) -> tuple[int, str]:
    """
    Save uploaded file to disk and compute checksum
    
    Returns: (file_size, checksum_sha256)
    """
    file_size = 0
    hash_sha256 = hashlib.sha256()
    
    async with aiofiles.open(dest_path, 'wb') as out_file:
        while content := await upload_file.read(1024 * 1024):  # Read 1MB chunks
            file_size += len(content)
            
            # Check file size limit
            if file_size > MAX_FILE_SIZE:
                # Clean up
                dest_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024} MB"
                )
            
            hash_sha256.update(content)
            await out_file.write(content)
    
    return file_size, hash_sha256.hexdigest()


@router.post("", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    attachment_type: str = Form("supporting_document"),
    document_id: Optional[int] = Form(None),
    document_version_id: Optional[int] = Form(None)
):
    """
    Upload attachment file (URS-DVM-007)
    
    Stores file in local storage and creates metadata record
    Files are stored with checksum-based naming to prevent duplicates
    """
    # Validate document/version exists if provided
    if document_id:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.is_deleted == False
        ).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
    
    if document_version_id:
        version = db.query(DocumentVersion).filter(
            DocumentVersion.id == document_version_id
        ).first()
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document version not found"
            )
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    original_filename = file.filename or "unnamed"
    
    # Get file extension
    ext = Path(original_filename).suffix or ""
    
    # Temporary filename (will rename after computing checksum)
    temp_filename = f"temp_{timestamp}_{current_user.id}{ext}"
    temp_path = UPLOAD_DIR / temp_filename
    
    try:
        # Save file and compute checksum
        file_size, checksum = await save_upload_file(file, temp_path)
        
        # Rename file with checksum
        final_filename = f"{checksum}{ext}"
        final_path = UPLOAD_DIR / final_filename
        
        # Check if file with same checksum already exists
        if final_path.exists():
            # Reuse existing file (deduplication)
            temp_path.unlink()
            storage_path = str(final_path.relative_to(Path.cwd()))
        else:
            # Rename temp file to final name
            temp_path.rename(final_path)
            storage_path = str(final_path.relative_to(Path.cwd()))
        
        # Detect MIME type
        mime_type = file.content_type or mimetypes.guess_type(original_filename)[0] or "application/octet-stream"
        
        # Create attachment record
        attachment = Attachment(
            filename=final_filename,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            storage_path=storage_path,
            storage_type="local",
            checksum_sha256=checksum,
            document_id=document_id,
            document_version_id=document_version_id,
            uploaded_by_id=current_user.id,
            description=description,
            attachment_type=attachment_type,
            scan_status="pending"  # TODO: Implement virus scanning
        )
        
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        
        # Audit log
        AuditLogger.log(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="ATTACHMENT_UPLOADED",
            entity_type="Attachment",
            entity_id=attachment.id,
            description=f"Uploaded attachment: {original_filename}",
            details={
                "filename": original_filename,
                "file_size": file_size,
                "mime_type": mime_type,
                "checksum": checksum,
                "document_id": document_id,
                "document_version_id": document_version_id
            }
        )
        
        # Prepare response
        response = AttachmentResponse.from_orm(attachment)
        response.uploaded_by_username = current_user.username
        response.uploaded_by_full_name = current_user.full_name
        response.download_url = f"/api/v1/attachments/{attachment.id}/download"
        
        return response
        
    except HTTPException:
        # Clean up on error
        temp_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        # Clean up on error
        temp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment_metadata(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    attachment_id: int
):
    """
    Get attachment metadata
    """
    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id,
        Attachment.is_deleted == False
    ).first()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Prepare response
    response = AttachmentResponse.from_orm(attachment)
    if attachment.uploaded_by:
        response.uploaded_by_username = attachment.uploaded_by.username
        response.uploaded_by_full_name = attachment.uploaded_by.full_name
    response.download_url = f"/api/v1/attachments/{attachment.id}/download"
    
    return response


@router.get("/{attachment_id}/download")
async def download_attachment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    attachment_id: int
):
    """
    Download attachment file
    
    Returns file as streaming response with original filename
    """
    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id,
        Attachment.is_deleted == False
    ).first()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Check file exists
    file_path = Path(attachment.storage_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    # Audit log (optional - might be too verbose)
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="ATTACHMENT_DOWNLOADED",
        entity_type="Attachment",
        entity_id=attachment.id,
        description=f"Downloaded attachment: {attachment.original_filename}",
        details={"attachment_id": attachment_id}
    )
    
    # Return file
    return FileResponse(
        path=file_path,
        filename=attachment.original_filename,
        media_type=attachment.mime_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{attachment.original_filename}\""
        }
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    attachment_id: int
):
    """
    Soft delete an attachment
    
    File remains on disk for audit/recovery purposes
    """
    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id,
        Attachment.is_deleted == False
    ).first()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Check permissions (uploader or admin)
    if attachment.uploaded_by_id != current_user.id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this attachment"
        )
    
    # Soft delete
    attachment.is_deleted = True
    attachment.deleted_at = datetime.utcnow()
    attachment.deleted_by_id = current_user.id
    
    db.commit()
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="ATTACHMENT_DELETED",
        entity_type="Attachment",
        entity_id=attachment.id,
        description=f"Deleted attachment: {attachment.original_filename}",
        details={"attachment_id": attachment_id, "filename": attachment.original_filename}
    )
    
    return None


@router.get("/document/{document_id}/list", response_model=AttachmentListResponse)
async def list_document_attachments(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int
):
    """
    List all attachments for a document (across all versions)
    """
    # Verify document exists
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get attachments
    attachments = db.query(Attachment).filter(
        Attachment.document_id == document_id,
        Attachment.is_deleted == False
    ).order_by(Attachment.uploaded_at.desc()).all()
    
    # Prepare responses
    attachment_responses = []
    for att in attachments:
        response = AttachmentResponse.from_orm(att)
        if att.uploaded_by:
            response.uploaded_by_username = att.uploaded_by.username
            response.uploaded_by_full_name = att.uploaded_by.full_name
        response.download_url = f"/api/v1/attachments/{att.id}/download"
        attachment_responses.append(response)
    
    return AttachmentListResponse(
        attachments=attachment_responses,
        total=len(attachment_responses)
    )

