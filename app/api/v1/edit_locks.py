"""
Edit Lock Management API Endpoints
Handles concurrent editing locks with heartbeat and expiry (URS-DVM-006)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_user
from app.models import Document, DocumentVersion, User, EditLock, VersionStatus
from app.schemas.edit_lock import (
    EditLockAcquireRequest,
    EditLockResponse,
    EditLockHeartbeatRequest,
    EditLockReleaseRequest,
    EditLockStatus,
)
from app.core.audit import AuditLogger

router = APIRouter()


def can_acquire_lock(user: User, document: Document, version: DocumentVersion) -> bool:
    """Check if user can acquire edit lock"""
    # Only draft versions can be locked
    if version.status != VersionStatus.DRAFT:
        return False
    if user.is_admin():
        return True
    if user.has_role("Author") and (document.owner_id == user.id or version.created_by_id == user.id):
        return True
    return False


@router.post("/{document_id}/versions/{version_id}/lock", response_model=EditLockResponse)
async def acquire_lock(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request,
    document_id: int,
    version_id: int,
    lock_request: EditLockAcquireRequest
):
    """
    Acquire edit lock on a document version (URS-DVM-006)
    
    Returns lock token that must be included in save requests
    Locks expire after timeout_minutes (default 30)
    """
    # Get document and version
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
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
    if not can_acquire_lock(current_user, document, version):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to lock this version or version is not a draft"
        )
    
    # Check for existing lock
    existing_lock = db.query(EditLock).filter(
        EditLock.document_version_id == version_id
    ).first()
    
    if existing_lock:
        # Check if lock is expired
        if not existing_lock.is_expired():
            # Lock still valid
            if existing_lock.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Version is currently locked by {existing_lock.user.username}",
                    headers={
                        "X-Lock-Owner": existing_lock.user.username,
                        "X-Lock-Expires": existing_lock.expires_at.isoformat()
                    }
                )
            else:
                # User already owns the lock, refresh it
                existing_lock.refresh(extend_minutes=lock_request.timeout_minutes)
                db.commit()
                db.refresh(existing_lock)
                return _prepare_lock_response(existing_lock)
        else:
            # Lock expired, remove it
            db.delete(existing_lock)
            db.commit()
    
    # Create new lock
    lock_token = EditLock.generate_token()
    expires_at = EditLock.default_expiry(minutes=lock_request.timeout_minutes)
    
    new_lock = EditLock(
        document_version_id=version_id,
        user_id=current_user.id,
        lock_token=lock_token,
        expires_at=expires_at,
        session_id=lock_request.session_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    try:
        db.add(new_lock)
        db.commit()
        db.refresh(new_lock)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Lock was just acquired by another user"
        )
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="LOCK_ACQUIRED",
        entity_type="DocumentVersion",
        entity_id=version_id,
        description=f"Acquired edit lock on version {version.version_number}",
        details={
            "document_id": document_id,
            "version_id": version_id,
            "expires_at": expires_at.isoformat(),
            "timeout_minutes": lock_request.timeout_minutes
        }
    )
    
    return _prepare_lock_response(new_lock)


@router.get("/{document_id}/versions/{version_id}/lock", response_model=EditLockStatus)
async def check_lock_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int
):
    """
    Check lock status without acquiring
    
    Returns lock information if locked, or can_acquire if available
    """
    # Verify document and version exist
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    version = db.query(DocumentVersion).filter(
        DocumentVersion.id == version_id,
        DocumentVersion.document_id == document_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    # Get lock
    lock = db.query(EditLock).filter(
        EditLock.document_version_id == version_id
    ).first()
    
    if not lock or lock.is_expired():
        # No active lock
        can_acquire = can_acquire_lock(current_user, document, version)
        return EditLockStatus(
            is_locked=False,
            can_acquire=can_acquire
        )
    
    # Lock exists and is active
    return EditLockStatus(
        is_locked=True,
        locked_by_user_id=lock.user_id,
        locked_by_username=lock.user.username if lock.user else None,
        lock_expires_at=lock.expires_at,
        can_acquire=False,
        lock_token=lock.lock_token if lock.user_id == current_user.id else None
    )


@router.post("/{document_id}/versions/{version_id}/lock/heartbeat", response_model=EditLockResponse)
async def refresh_lock(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    heartbeat: EditLockHeartbeatRequest
):
    """
    Refresh lock with heartbeat to extend expiry
    
    Frontend should call this every 10-15 seconds while editing
    """
    # Get lock
    lock = db.query(EditLock).filter(
        EditLock.document_version_id == version_id,
        EditLock.lock_token == heartbeat.lock_token
    ).first()
    
    if not lock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lock not found or invalid token"
        )
    
    # Verify ownership
    if lock.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the lock owner"
        )
    
    # Refresh lock
    lock.refresh(extend_minutes=heartbeat.extend_minutes)
    db.commit()
    db.refresh(lock)
    
    return _prepare_lock_response(lock)


@router.delete("/{document_id}/versions/{version_id}/lock", status_code=status.HTTP_204_NO_CONTENT)
async def release_lock(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    release_request: EditLockReleaseRequest
):
    """
    Release edit lock manually
    
    Called when user closes editor or cancels editing
    """
    # Get lock
    lock = db.query(EditLock).filter(
        EditLock.document_version_id == version_id,
        EditLock.lock_token == release_request.lock_token
    ).first()
    
    if not lock:
        # Lock doesn't exist or already released
        return None
    
    # Verify ownership (or admin can force release)
    if lock.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the lock owner"
        )
    
    # Delete lock
    db.delete(lock)
    db.commit()
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="LOCK_RELEASED",
        entity_type="DocumentVersion",
        entity_id=version_id,
        description=f"Released edit lock on version",
        details={
            "document_id": document_id,
            "version_id": version_id,
            "was_owner": lock.user_id == current_user.id,
            "forced_by_admin": lock.user_id != current_user.id
        }
    )
    
    return None


def _prepare_lock_response(lock: EditLock) -> EditLockResponse:
    """Helper to prepare lock response"""
    # Manually build response to avoid method vs property confusion
    is_expired = lock.is_expired()
    time_remaining_seconds = None
    
    if not is_expired:
        time_remaining = (lock.expires_at - datetime.utcnow()).total_seconds()
        time_remaining_seconds = int(max(0, time_remaining))
    
    response = EditLockResponse(
        id=lock.id,
        document_version_id=lock.document_version_id,
        user_id=lock.user_id,
        lock_token=lock.lock_token,
        acquired_at=lock.acquired_at,
        expires_at=lock.expires_at,
        last_heartbeat=lock.last_heartbeat,
        session_id=lock.session_id,
        username=lock.user.username if lock.user else None,
        user_full_name=lock.user.full_name if lock.user else None,
        is_expired=is_expired,
        time_remaining_seconds=time_remaining_seconds
    )
    
    return response

