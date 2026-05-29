"""
Document Management API Endpoints
Handles CRUD operations for documents with RBAC enforcement
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.models import Document, DocumentVersion, User, VersionStatus
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    DocumentSearchFilters,
)
from app.core.document_utils import generate_document_number, normalize_document_number
from app.core.audit import AuditLogger

router = APIRouter()


def can_create_document(user: User) -> bool:
    """Check if user can create documents (Author or Admin)"""
    return user.has_role("Author") or user.is_admin()


def can_edit_document(user: User, document: Document) -> bool:
    """Check if user can edit document metadata"""
    if user.is_admin():
        return True
    if user.has_role("Author") and document.owner_id == user.id:
        return True
    return False


def can_view_document(user: User, document: Document) -> bool:
    """Check if user can view document (all authenticated users for now)"""
    # In production, add more granular permissions based on department, etc.
    return True


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_in: DocumentCreate
):
    """
    Create a new document (URS-DVM-001)
    
    Requires: Author or DMS_Admin role
    """
    # Check permissions
    if not can_create_document(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Authors and Admins can create documents"
        )
    
    # Generate or normalize document number
    if document_in.document_number:
        doc_number = normalize_document_number(document_in.document_number)
        # Check uniqueness
        existing = db.query(Document).filter(Document.document_number == doc_number).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document number {doc_number} already exists"
            )
    else:
        doc_number = generate_document_number(
            db, 
            prefix="SOP", 
            department=document_in.department
        )
    
    # Determine owner
    owner_id = document_in.owner_id if document_in.owner_id else current_user.id
    
    # If setting different owner, must be admin
    if owner_id != current_user.id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create documents for other users"
        )
    
    # Create document
    document = Document(
        document_number=doc_number,
        title=document_in.title,
        description=document_in.description,
        department=document_in.department,
        tags=document_in.tags or [],
        owner_id=owner_id,
        created_by_id=current_user.id,
        status="DRAFT"
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="DOCUMENT_CREATED",
        entity_type="Document",
        entity_id=document.id,
        description=f"Created document {document.document_number}: {document.title}",
        details={
            "document_number": document.document_number,
            "title": document.title,
            "department": document.department,
            "owner_id": owner_id,
        }
    )
    
    # Prepare response
    response = DocumentResponse.from_orm(document)
    response.owner_username = document.owner.username if document.owner else None
    response.owner_full_name = document.owner.full_name if document.owner else None
    response.version_count = 0
    
    return response


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    title: Optional[str] = Query(None, description="Filter by title (partial match)"),
    document_number: Optional[str] = Query(None, description="Filter by document number"),
    department: Optional[str] = Query(None, description="Filter by department"),
    status: Optional[str] = Query(None, description="Filter by status"),
    owner_id: Optional[int] = Query(None, description="Filter by owner ID"),
    show_all_statuses: bool = Query(False, description="Show all document statuses including obsolete"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    List and search documents with filters (URS-DVM-011)
    
    By default, shows only Effective documents (controlled versioning).
    Set show_all_statuses=true to see all documents including drafts and obsolete.
    
    All authenticated users can list documents
    """
    # Build query
    query = db.query(Document).filter(Document.is_deleted == False)
    
    # Workflow statuses that are stored on DocumentVersion, not Document
    # These include all version workflow states except EFFECTIVE, OBSOLETE, ARCHIVED
    workflow_statuses = {
        VersionStatus.DRAFT,
        VersionStatus.UNDER_REVIEW, 
        VersionStatus.PENDING_APPROVAL, 
        VersionStatus.APPROVED,
        VersionStatus.REJECTED
    }
    
    # Check if status is a workflow status (stored on versions)
    is_workflow_status = status and status.upper() in [s.value for s in workflow_statuses]
    
    # Default filter: Show only EFFECTIVE documents unless explicitly requested otherwise
    if not show_all_statuses and not status:
        query = query.filter(Document.status == "EFFECTIVE")
    
    # Apply filters
    if title:
        query = query.filter(Document.title.ilike(f"%{title}%"))
    if document_number:
        query = query.filter(Document.document_number.ilike(f"%{document_number}%"))
    if department:
        query = query.filter(Document.department == department)
    if status:
        if is_workflow_status:
            # Filter by latest version's status for workflow statuses
            # Use a subquery to find documents with latest versions matching the status
            # Convert string status to VersionStatus enum
            try:
                status_enum = VersionStatus(status.upper())
            except ValueError:
                # Invalid status, skip this filter
                pass
            else:
                # Subquery to get document IDs with latest versions matching the status
                from sqlalchemy import select
                subquery = select(DocumentVersion.document_id).filter(
                    DocumentVersion.is_latest == True,
                    DocumentVersion.status == status_enum
                )
                query = query.filter(Document.id.in_(subquery))
        else:
            # Filter by document status for non-workflow statuses (case-insensitive)
            # Document.status might be stored as "Draft" or "EFFECTIVE" etc.
            query = query.filter(Document.status.ilike(status))
    if owner_id:
        query = query.filter(Document.owner_id == owner_id)
    
    # Count total
    total = query.count()
    
    # Paginate
    documents = query.options(
        joinedload(Document.owner),
        joinedload(Document.versions)
    ).order_by(Document.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    # Prepare responses
    doc_responses = []
    for doc in documents:
        response = DocumentResponse.from_orm(doc)
        response.owner_username = doc.owner.username if doc.owner else None
        response.owner_full_name = doc.owner.full_name if doc.owner else None
        response.version_count = len(doc.versions)
        doc_responses.append(response)
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return DocumentListResponse(
        items=doc_responses,
        total=total,
        page=page,
        size=page_size,
        pages=total_pages
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int
):
    """
    Get document details with version history
    
    Returns document metadata and list of all versions
    """
    document = db.query(Document).options(
        joinedload(Document.owner),
        joinedload(Document.versions).joinedload(DocumentVersion.created_by)
    ).filter(
        Document.id == document_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if not can_view_document(current_user, document):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this document"
        )
    
    # Prepare response
    from app.schemas.document_version import DocumentVersionListItem
    
    response = DocumentDetailResponse.from_orm(document)
    response.owner_username = document.owner.username if document.owner else None
    response.owner_full_name = document.owner.full_name if document.owner else None
    response.version_count = len(document.versions)
    
    # Add version list
    response.versions = [
        DocumentVersionListItem(
            id=v.id,
            document_id=v.document_id,
            version_number=v.version_number,
            status=v.status,
            change_summary=v.change_summary,
            created_by_id=v.created_by_id,
            created_by_username=v.created_by.username if v.created_by else None,
            created_at=v.created_at,
            updated_at=v.updated_at
        )
        for v in document.versions
    ]
    
    return response


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    document_in: DocumentUpdate
):
    """
    Update document metadata
    
    Requires: Owner (Author) or Admin
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if not can_edit_document(current_user, document):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this document"
        )
    
    # Track changes for audit
    changes = {}
    
    # Update fields
    if document_in.title is not None:
        changes["title"] = {"old": document.title, "new": document_in.title}
        document.title = document_in.title
    if document_in.description is not None:
        changes["description"] = {"old": document.description, "new": document_in.description}
        document.description = document_in.description
    if document_in.department is not None:
        changes["department"] = {"old": document.department, "new": document_in.department}
        document.department = document_in.department
    if document_in.tags is not None:
        changes["tags"] = {"old": document.tags, "new": document_in.tags}
        document.tags = document_in.tags
    if document_in.owner_id is not None:
        if not current_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change document owner"
            )
        changes["owner_id"] = {"old": document.owner_id, "new": document_in.owner_id}
        document.owner_id = document_in.owner_id
    
    document.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(document)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="DOCUMENT_UPDATED",
        entity_type="Document",
        entity_id=document.id,
        description=f"Updated document {document.document_number}",
        details={"changes": changes}
    )
    
    # Prepare response
    response = DocumentResponse.from_orm(document)
    response.owner_username = document.owner.username if document.owner else None
    response.owner_full_name = document.owner.full_name if document.owner else None
    response.version_count = len(document.versions)
    
    return response


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int
):
    """
    Soft delete a document
    
    Requires: Owner (Author) or Admin
    Only drafts can be deleted
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if not can_edit_document(current_user, document):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this document"
        )
    
    # Check if document can be deleted (only drafts)
    if document.status not in ["Draft", "Rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete document with status: {document.status}"
        )
    
    # Soft delete
    document.is_deleted = True
    document.deleted_at = datetime.utcnow()
    document.deleted_by_id = current_user.id
    
    db.commit()
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="DOCUMENT_DELETED",
        entity_type="Document",
        entity_id=document.id,
        description=f"Deleted document {document.document_number}: {document.title}",
        details={"document_number": document.document_number}
    )
    
    return None

