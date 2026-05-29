"""
Document Comment API Endpoints
Handles inline comments and annotations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.models import DocumentComment, DocumentVersion, Document, User
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse, CommentListResponse
from app.core.audit import AuditLogger

router = APIRouter()


@router.post("/{document_id}/versions/{version_id}/comments", response_model=CommentResponse)
async def create_comment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    comment_data: CommentCreate
):
    """
    Create a comment on a document version
    
    All authenticated users can comment
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
    
    # Create comment
    comment = DocumentComment(
        document_version_id=version_id,
        user_id=current_user.id,
        comment_text=comment_data.comment_text,
        selected_text=comment_data.selected_text,
        selection_start=comment_data.selection_start,
        selection_end=comment_data.selection_end,
        text_context=comment_data.text_context,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="COMMENT_CREATED",
        entity_type="DocumentComment",
        entity_id=comment.id,
        description=f"Added comment to version {version.version_number} of document {document.document_number}"
    )
    
    return _prepare_comment_response(db, comment)


@router.get("/{document_id}/versions/{version_id}/comments", response_model=CommentListResponse)
async def list_comments(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    include_resolved: bool = False
):
    """
    List all comments for a document version
    
    All authenticated users can view comments
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
    
    # Query comments
    query = db.query(DocumentComment).filter(
        DocumentComment.document_version_id == version_id
    )
    
    if not include_resolved:
        query = query.filter(DocumentComment.is_resolved == False)
    
    comments = query.order_by(DocumentComment.created_at.desc()).all()
    
    comment_responses = [_prepare_comment_response(db, c) for c in comments]
    
    return CommentListResponse(
        comments=comment_responses,
        total=len(comment_responses)
    )


@router.patch("/{document_id}/versions/{version_id}/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    comment_id: int,
    comment_data: CommentUpdate
):
    """
    Update a comment
    
    Comment text: Only comment author or admin can update
    Resolve: Comment author, document author/owner, or admin can resolve
    """
    comment = db.query(DocumentComment).filter(
        DocumentComment.id == comment_id,
        DocumentComment.document_version_id == version_id
    ).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Get the document to check ownership
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user is the document author/owner
    is_document_author = document.owner_id == current_user.id or document.created_by_id == current_user.id
    
    # Check if user has Author role
    user_roles = [role.name for role in current_user.roles]
    has_author_role = 'Author' in user_roles
    
    # Permission logic:
    # - Comment text changes: Only comment author or admin
    # - Resolve changes: Comment author, document author/owner with Author role, or admin
    
    is_comment_author = comment.user_id == current_user.id
    is_admin = current_user.is_admin()
    
    # If trying to update comment text (not just resolve)
    if comment_data.comment_text is not None:
        if not is_comment_author and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only comment author or admin can edit comment text"
            )
    
    # If trying to resolve, allow document author with Author role
    if comment_data.is_resolved is not None:
        can_resolve = is_comment_author or is_admin or (is_document_author and has_author_role)
        if not can_resolve:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only comment author, document author, or admin can resolve this comment"
            )
    
    # Update fields
    if comment_data.comment_text is not None:
        comment.comment_text = comment_data.comment_text
    
    if comment_data.is_resolved is not None:
        comment.is_resolved = comment_data.is_resolved
        if comment_data.is_resolved:
            comment.resolved_at = datetime.utcnow()
            comment.resolved_by_id = current_user.id
        else:
            comment.resolved_at = None
            comment.resolved_by_id = None
    
    comment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(comment)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="COMMENT_UPDATED",
        entity_type="DocumentComment",
        entity_id=comment.id,
        description=f"Updated comment on version {version_id}"
    )
    
    return _prepare_comment_response(db, comment)


@router.delete("/{document_id}/versions/{version_id}/comments/{comment_id}")
async def delete_comment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    comment_id: int
):
    """
    Delete a comment
    
    Only comment author or admin can delete
    """
    comment = db.query(DocumentComment).filter(
        DocumentComment.id == comment_id,
        DocumentComment.document_version_id == version_id
    ).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Check permissions
    if comment.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only comment author or admin can delete this comment"
        )
    
    db.delete(comment)
    db.commit()
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="COMMENT_DELETED",
        entity_type="DocumentComment",
        entity_id=comment_id,
        description=f"Deleted comment from version {version_id}"
    )
    
    return {"message": "Comment deleted successfully"}


def _prepare_comment_response(db: Session, comment: DocumentComment) -> CommentResponse:
    """Helper to prepare comment response with user info"""
    response = CommentResponse.from_orm(comment)
    
    # Add author info
    if comment.author:
        response.user_name = comment.author.username
        response.user_full_name = comment.author.full_name
    
    # Add resolver info
    if comment.resolver:
        response.resolved_by_name = comment.resolver.username
    
    return response

