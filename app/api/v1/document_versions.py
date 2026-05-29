"""
Document Version Management API Endpoints
Handles version creation, editing, workflow, and content management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.models import Document, DocumentVersion, User, VersionStatus, ChangeType, EditLock, DocumentView
from app.schemas.document_version import (
    DocumentVersionCreate,
    DocumentVersionUpdate,
    DocumentVersionSave,
    DocumentVersionResponse,
    DocumentVersionListResponse,
    DocumentVersionListItem,
    SubmitForReviewRequest,
    ReviewRequest,
    ApprovalRequest,
    PublishRequest,
    CreateNewVersionRequest,
)
from app.core.document_utils import get_next_version_number, compute_content_hash
from app.core.audit import AuditLogger
from app.core.security import verify_password
from app.utils.template_tokens import replace_tokens, TOKEN_PATTERN
import re

router = APIRouter()

# Token pattern for signatory tokens
SIGNATORY_TOKEN_PATTERN = re.compile(r'\{\{SIGNATORY_(PREPARED|CHECKED|APPROVED)_(NAME|DESIGNATION|DEPARTMENT|DATE)\}\}')


def update_signatory_tokens(content_html: str, user: User, signatory_type: str, date: datetime = None) -> str:
    """
    Update signatory tokens in document content HTML
    
    Args:
        content_html: HTML content with signatory tokens
        user: User object with signatory information
        signatory_type: 'PREPARED', 'CHECKED', or 'APPROVED'
        date: Optional datetime, defaults to current time
    
    Returns:
        Updated HTML content with signatory tokens replaced
    """
    if not content_html:
        return content_html
    
    if date is None:
        date = datetime.utcnow()
    
    # Get user designation - use primary role name if available, else 'N/A'
    designation = 'N/A'
    if user.roles:
        # Get the first role as designation (or prioritize certain roles)
        role_names = [role.name for role in user.roles]
        # Prioritize: Approver > Reviewer > Author > Admin
        for priority_role in ['Approver', 'Reviewer', 'Author', 'DMS_Admin']:
            if priority_role in role_names:
                designation = priority_role
                break
        else:
            designation = role_names[0] if role_names else 'N/A'
    
    # Prepare token values
    token_values = {
        f'SIGNATORY_{signatory_type}_NAME': user.full_name or user.username,
        f'SIGNATORY_{signatory_type}_DESIGNATION': designation,
        f'SIGNATORY_{signatory_type}_DEPARTMENT': user.department or 'N/A',
        f'SIGNATORY_{signatory_type}_DATE': date.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    # Replace tokens in content
    updated_content = replace_tokens(content_html, token_values, strict=False)
    
    return updated_content


def get_signatory_section_html() -> str:
    """
    Get the signatory section HTML with tokens
    """
    return """
    <div style="page-break-before: always; margin-top: 40pt;">
      <h2 style="margin-bottom: 20pt; font-size: 14pt; font-weight: bold;">Document Signatory Page</h2>
      <table border="1" style="border-collapse: collapse; width: 100%; max-width: 100%; table-layout: fixed; border: 1px solid #000;">
        <thead>
          <tr style="background-color: #f0f0f0;">
            <th style="padding: 6pt; font-weight: bold; width: 15%; font-size: 9pt; border: 1px solid #000; text-align: left; word-wrap: break-word;">Signature Type</th>
            <th style="padding: 6pt; font-weight: bold; width: 20%; font-size: 9pt; border: 1px solid #000; text-align: left; word-wrap: break-word;">Name</th>
            <th style="padding: 6pt; font-weight: bold; width: 20%; font-size: 9pt; border: 1px solid #000; text-align: left; word-wrap: break-word;">Designation</th>
            <th style="padding: 6pt; font-weight: bold; width: 20%; font-size: 9pt; border: 1px solid #000; text-align: left; word-wrap: break-word;">Department</th>
            <th style="padding: 6pt; font-weight: bold; width: 25%; font-size: 9pt; border: 1px solid #000; text-align: left; word-wrap: break-word;">Date & Time</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding: 6pt; font-size: 9pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word;">Prepared By</td>
            <td style="padding: 6pt; font-size: 8pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word; max-width: 0;">{{SIGNATORY_PREPARED_NAME}}</td>
            <td style="padding: 6pt; font-size: 8pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word; max-width: 0;">{{SIGNATORY_PREPARED_DESIGNATION}}</td>
            <td style="padding: 6pt; font-size: 8pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word; max-width: 0;">{{SIGNATORY_PREPARED_DEPARTMENT}}</td>
            <td style="padding: 6pt; font-size: 8pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word; max-width: 0;">{{SIGNATORY_PREPARED_DATE}}</td>
          </tr>
          <tr>
            <td style="padding: 6pt; font-size: 9pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word;">Checked By</td>
            <td style="padding: 6pt; font-size: 8pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word; max-width: 0;">{{SIGNATORY_CHECKED_NAME}}</td>
            <td style="padding: 6pt; font-size: 8pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word; max-width: 0;">{{SIGNATORY_CHECKED_DESIGNATION}}</td>
            <td style="padding: 6pt; font-size: 8pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word; max-width: 0;">{{SIGNATORY_CHECKED_DEPARTMENT}}</td>
            <td style="padding: 6pt; font-size: 8pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word; max-width: 0;">{{SIGNATORY_CHECKED_DATE}}</td>
          </tr>
          <tr>
            <td style="padding: 6pt; font-size: 9pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word;">Approved By</td>
            <td style="padding: 6pt; font-size: 8pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word; max-width: 0;">{{SIGNATORY_APPROVED_NAME}}</td>
            <td style="padding: 6pt; font-size: 8pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word; max-width: 0;">{{SIGNATORY_APPROVED_DESIGNATION}}</td>
            <td style="padding: 6pt; font-size: 8pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word; max-width: 0;">{{SIGNATORY_APPROVED_DEPARTMENT}}</td>
            <td style="padding: 6pt; font-size: 8pt; border: 1px solid #000; word-wrap: break-word; overflow-wrap: break-word; max-width: 0;">{{SIGNATORY_APPROVED_DATE}}</td>
          </tr>
        </tbody>
      </table>
    </div>
    """


def update_all_signatory_tokens(
    content_html: str,
    prepared_user: User = None,
    prepared_date: datetime = None,
    checked_user: User = None,
    checked_date: datetime = None,
    approved_user: User = None,
    approved_date: datetime = None
) -> str:
    """
    Update all signatory tokens at once
    
    If signatory section doesn't exist in content_html, it will be appended.
    
    Args:
        content_html: HTML content with signatory tokens
        prepared_user: User who prepared the document
        prepared_date: Date when prepared
        checked_user: User who checked the document
        checked_date: Date when checked
        approved_user: User who approved the document
        approved_date: Date when approved
    
    Returns:
        Updated HTML content with all signatory tokens replaced
    """
    if not content_html:
        content_html = ""
    
    # Check if signatory section exists in content_html (look for actual tokens, not replaced values)
    has_signatory_section = (
        '{{SIGNATORY_PREPARED_NAME}}' in content_html or
        '{{SIGNATORY_CHECKED_NAME}}' in content_html or
        '{{SIGNATORY_APPROVED_NAME}}' in content_html or
        'Document Signatory Page' in content_html
    )
    
    # If signatory section doesn't exist, append it
    if not has_signatory_section:
        signatory_html = get_signatory_section_html()
        content_html = content_html + signatory_html
    else:
        # If signatory section exists but tokens have been replaced with "-NA-", 
        # we need to restore the tokens first so we can update them
        # This handles the case where tokens were replaced with defaults in a previous update
        # Restore CHECKED tokens if they were replaced with -NA- and we have checked_user
        if checked_user:
            # Restore CHECKED tokens from -NA- back to tokens
            content_html = content_html.replace(
                '>Checked By</td><td>-NA-</td><td>-NA-</td><td>-NA-</td><td></td>',
                '>Checked By</td><td>{{SIGNATORY_CHECKED_NAME}}</td><td>{{SIGNATORY_CHECKED_DESIGNATION}}</td><td>{{SIGNATORY_CHECKED_DEPARTMENT}}</td><td>{{SIGNATORY_CHECKED_DATE}}</td>'
            )
            # Also handle case with different spacing
            content_html = re.sub(
                r'(>Checked By</td>\s*<td[^>]*>)-NA-(</td>\s*<td[^>]*>)-NA-(</td>\s*<td[^>]*>)-NA-(</td>\s*<td[^>]*>)\s*(</td>)',
                r'\1{{SIGNATORY_CHECKED_NAME}}\2{{SIGNATORY_CHECKED_DESIGNATION}}\3{{SIGNATORY_CHECKED_DEPARTMENT}}\4{{SIGNATORY_CHECKED_DATE}}\5',
                content_html,
                flags=re.IGNORECASE
            )
        
        # Restore APPROVED tokens if they were replaced with -NA- and we have approved_user
        if approved_user:
            # Restore APPROVED tokens from -NA- back to tokens
            content_html = content_html.replace(
                '>Approved By</td><td>-NA-</td><td>-NA-</td><td>-NA-</td><td></td>',
                '>Approved By</td><td>{{SIGNATORY_APPROVED_NAME}}</td><td>{{SIGNATORY_APPROVED_DESIGNATION}}</td><td>{{SIGNATORY_APPROVED_DEPARTMENT}}</td><td>{{SIGNATORY_APPROVED_DATE}}</td>'
            )
            # Also handle case with different spacing
            content_html = re.sub(
                r'(>Approved By</td>\s*<td[^>]*>)-NA-(</td>\s*<td[^>]*>)-NA-(</td>\s*<td[^>]*>)-NA-(</td>\s*<td[^>]*>)\s*(</td>)',
                r'\1{{SIGNATORY_APPROVED_NAME}}\2{{SIGNATORY_APPROVED_DESIGNATION}}\3{{SIGNATORY_APPROVED_DEPARTMENT}}\4{{SIGNATORY_APPROVED_DATE}}\5',
                content_html,
                flags=re.IGNORECASE
            )
    
    # Collect all token values
    token_values = {}
    
    # Helper function to get user designation
    def get_designation(user):
        if not user:
            return 'N/A'
        try:
            # Check if roles is a list/collection or needs to be accessed differently
            if hasattr(user, 'roles'):
                # Try to get roles - handle both lazy-loaded and already-loaded cases
                roles = user.roles if user.roles else []
                if not roles:
                    return 'N/A'
                role_names = [role.name if hasattr(role, 'name') else str(role) for role in roles]
                for priority_role in ['Approver', 'Reviewer', 'Author', 'DMS_Admin']:
                    if priority_role in role_names:
                        return priority_role
                return role_names[0] if role_names else 'N/A'
        except Exception:
            # If there's any error accessing roles, return N/A
            return 'N/A'
        return 'N/A'
    
    # Update Prepared By tokens
    if prepared_user:
        token_values['SIGNATORY_PREPARED_NAME'] = prepared_user.full_name or prepared_user.username
        token_values['SIGNATORY_PREPARED_DESIGNATION'] = get_designation(prepared_user)
        token_values['SIGNATORY_PREPARED_DEPARTMENT'] = prepared_user.department or 'N/A'
        token_values['SIGNATORY_PREPARED_DATE'] = (prepared_date or datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')
    
    # Update Checked By tokens
    if checked_user:
        token_values['SIGNATORY_CHECKED_NAME'] = checked_user.full_name or checked_user.username
        token_values['SIGNATORY_CHECKED_DESIGNATION'] = get_designation(checked_user)
        token_values['SIGNATORY_CHECKED_DEPARTMENT'] = checked_user.department or 'N/A'
        token_values['SIGNATORY_CHECKED_DATE'] = (checked_date or datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')
    
    # Update Approved By tokens
    if approved_user:
        token_values['SIGNATORY_APPROVED_NAME'] = approved_user.full_name or approved_user.username
        token_values['SIGNATORY_APPROVED_DESIGNATION'] = get_designation(approved_user)
        token_values['SIGNATORY_APPROVED_DEPARTMENT'] = approved_user.department or 'N/A'
        token_values['SIGNATORY_APPROVED_DATE'] = (approved_date or datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')
    
    # Replace only tokens we have values for (don't use defaults for missing values)
    # This ensures tokens remain as tokens until we have actual user data
    def replace_only_provided_tokens(html_content: str, provided_values: dict) -> str:
        """Replace only tokens that have values provided, leave others as tokens"""
        def replace_token(match):
            token_name = match.group(1)
            if token_name in provided_values:
                return provided_values[token_name]
            else:
                # Keep the token as-is if we don't have a value
                return match.group(0)  # Return the full match including {{}}
        
        return TOKEN_PATTERN.sub(replace_token, html_content)
    
    # Use custom replacement that only replaces tokens we have values for
    updated_content = replace_only_provided_tokens(content_html, token_values)
    
    return updated_content


def verify_esignature(user: User, password: str) -> bool:
    """
    Verify user password for e-signature compliance (21 CFR Part 11)
    
    Returns True if password is valid, raises HTTPException if not
    """
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password. E-signature authentication failed."
        )
    return True


def can_create_version(user: User, document: Document) -> bool:
    """Check if user can create a version"""
    if user.is_admin():
        return True
    if user.has_role("Author") and document.owner_id == user.id:
        return True
    return False


def can_edit_version(user: User, document: Document, version: DocumentVersion) -> bool:
    """Check if user can edit a version"""
    # Only draft versions can be edited
    if version.status != VersionStatus.DRAFT:
        return False
    if user.is_admin():
        return True
    if user.has_role("Author") and (document.owner_id == user.id or version.created_by_id == user.id):
        return True
    return False


def can_view_version(user: User, document: Document, version: DocumentVersion) -> bool:
    """Check if user can view a version"""
    # For now, all authenticated users can view
    # In production, add more granular checks
    return True


def has_user_viewed_content(db: Session, user_id: int, version_id: int) -> bool:
    """
    Check if user has viewed the document version content
    
    Returns True if user has viewed, False otherwise
    """
    view_record = db.query(DocumentView).filter(
        DocumentView.version_id == version_id,
        DocumentView.user_id == user_id
    ).first()
    
    return view_record is not None


def mark_content_as_viewed(db: Session, user_id: int, document_id: int, version_id: int) -> DocumentView:
    """
    Mark document version as viewed by user
    Creates or updates view record (using unique constraint to prevent duplicates)
    """
    # Check if view already exists
    view_record = db.query(DocumentView).filter(
        DocumentView.version_id == version_id,
        DocumentView.user_id == user_id
    ).first()
    
    if view_record:
        # Update timestamp if already viewed
        view_record.viewed_at = datetime.utcnow()
    else:
        # Create new view record
        view_record = DocumentView(
            document_id=document_id,
            version_id=version_id,
            user_id=user_id,
            viewed_at=datetime.utcnow()
        )
        db.add(view_record)
    
    db.commit()
    db.refresh(view_record)
    return view_record


def requires_content_view(user: User, version: DocumentVersion) -> bool:
    """
    Check if user role requires viewing content before workflow actions
    
    Reviewers and Approvers must view content before approving/rejecting
    """
    if not user:
        return False
    
    # Check if version is in a state that requires review/approval
    if version.status not in [VersionStatus.UNDER_REVIEW, VersionStatus.PENDING_APPROVAL]:
        return False
    
    # Reviewers must view before approving/rejecting Under Review documents
    if version.status == VersionStatus.UNDER_REVIEW and user.has_role("Reviewer"):
        return True
    
    # Approvers must view before approving/rejecting Pending Approval documents
    if version.status == VersionStatus.PENDING_APPROVAL and user.has_role("Approver"):
        return True
    
    # Admins also need to view (they can act as reviewers/approvers)
    if user.is_admin():
        return True
    
    return False


@router.post("/{document_id}/versions", response_model=DocumentVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_in: DocumentVersionCreate
):
    """
    Create a new document version (URS-DVM-002)
    
    Auto-increments version number
    Requires: Author (owner) or Admin
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
    
    # Check permissions
    if not can_create_version(current_user, document):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create versions for this document"
        )
    
    # Get next version number
    version_number = get_next_version_number(db, document_id)
    
    # Compute content hash
    content_hash = compute_content_hash(version_in.content_html or "")
    
    # Set initial version string (first version starts as v0.1)
    version_string = f"v0.{version_number}"
    
    # Create version
    version = DocumentVersion(
        document_id=document_id,
        version_number=version_number,
        version_string=version_string,
        parent_version_id=version_in.parent_version_id,
        is_latest=True,
        content_html=version_in.content_html,
        content_hash=content_hash,
        change_summary=version_in.change_summary,
        change_reason=version_in.change_reason,
        change_type=version_in.change_type,
        status=VersionStatus.DRAFT,
        attachments_metadata=version_in.attachments_metadata or [],
        created_by_id=current_user.id
    )
    
    db.add(version)
    db.flush()  # Get version ID
    
    # Update document's current version to this new draft
    document.current_version_id = version.id
    document.status = VersionStatus.DRAFT.value
    document.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(version)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="VERSION_CREATED",
        entity_type="DocumentVersion",
        entity_id=version.id,
        description=f"Created version {version_number} for document {document.document_number}",
        details={
            "document_id": document_id,
            "document_number": document.document_number,
            "version_number": version_number,
            "change_summary": version_in.change_summary,
        }
    )
    
    # Prepare response
    return _prepare_version_response(db, version, current_user)


@router.get("/{document_id}/versions", response_model=DocumentVersionListResponse)
async def list_versions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    page: int = 1,
    page_size: int = 20,
    include_obsolete: bool = Query(False, description="Include obsolete versions in results"),
    status_filter: Optional[str] = Query(None, description="Filter by status")
):
    """
    List all versions for a document with filtering options
    """
    # Check document exists
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Query versions
    query = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id
    ).options(
        joinedload(DocumentVersion.created_by),
        joinedload(DocumentVersion.approved_by)
    )
    
    # Apply filters
    if not include_obsolete:
        # By default, exclude obsolete versions
        query = query.filter(DocumentVersion.status != VersionStatus.OBSOLETE)
    
    if status_filter:
        query = query.filter(DocumentVersion.status == status_filter)
    
    total = query.count()
    versions = query.order_by(DocumentVersion.version_number.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    # Prepare response
    version_items = [
        DocumentVersionListItem(
            id=v.id,
            document_id=v.document_id,
            version_number=v.version_number,
            version_string=v.version_string,
            status=v.status,
            change_summary=v.change_summary,
            change_reason=v.change_reason,
            change_type=v.change_type,
            is_latest=v.is_latest,
            effective_date=v.effective_date,
            obsolete_date=v.obsolete_date,
            created_by_id=v.created_by_id,
            created_by_username=v.created_by.username if v.created_by else None,
            approved_by_username=v.approved_by.username if v.approved_by else None,
            created_at=v.created_at,
            updated_at=v.updated_at
        )
        for v in versions
    ]
    
    return DocumentVersionListResponse(
        versions=version_items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{document_id}/versions/{version_id}", response_model=DocumentVersionResponse)
async def get_version(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int
):
    """
    Get a specific version with full content
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
    if not can_view_version(current_user, document, version):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this version"
        )
    
    return _prepare_version_response(db, version, current_user)


@router.patch("/{document_id}/versions/{version_id}", response_model=DocumentVersionResponse)
async def update_version(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    version_in: DocumentVersionUpdate
):
    """
    Update version metadata (URS-DVM-003)
    
    Only drafts can be updated
    Does not update content - use save endpoint for that
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
    if not can_edit_version(current_user, document, version):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this version or version is not a draft"
        )
    
    # Track changes
    changes = {}
    
    # Update fields
    if version_in.change_summary is not None:
        changes["change_summary"] = {"old": version.change_summary, "new": version_in.change_summary}
        version.change_summary = version_in.change_summary
    if version_in.attachments_metadata is not None:
        changes["attachments_metadata"] = {"old": version.attachments_metadata, "new": version_in.attachments_metadata}
        version.attachments_metadata = version_in.attachments_metadata
    
    version.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(version)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="VERSION_UPDATED",
        entity_type="DocumentVersion",
        entity_id=version.id,
        description=f"Updated version {version.version_number} metadata",
        details={"changes": changes}
    )
    
    return _prepare_version_response(db, version, current_user)


@router.post("/{document_id}/versions/{version_id}/save", response_model=DocumentVersionResponse)
async def save_version_content(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request,
    document_id: int,
    version_id: int,
    save_data: DocumentVersionSave
):
    """
    Save version content (URS-DVM-005)
    
    Supports both manual save and autosave
    Enforces optimistic locking and edit lock
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
    if not can_edit_version(current_user, document, version):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this version or version is not a draft"
        )
    
    # Check edit lock
    lock = db.query(EditLock).filter(
        EditLock.document_version_id == version_id
    ).first()
    
    if lock:
        # Verify lock ownership
        if lock.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Version is locked by another user: {lock.user.username}"
            )
        
        # Verify lock token
        if save_data.lock_token and lock.lock_token != save_data.lock_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid lock token"
            )
        
        # Check expiry
        if lock.is_expired():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lock has expired, please reacquire"
            )
    
    # Optimistic concurrency check
    if save_data.content_hash:
        if version.content_hash != save_data.content_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Content has been modified by another user",
                headers={
                    "X-Current-Content-Hash": version.content_hash,
                    "X-Conflict": "true"
                }
            )
    
    # Save before snapshot for audit
    before_snapshot = {
        "content_hash": version.content_hash,
        "updated_at": version.updated_at.isoformat() if version.updated_at else None
    }
    
    # Update content
    version.content_html = save_data.content_html
    version.content_hash = compute_content_hash(save_data.content_html)
    version.updated_at = datetime.utcnow()
    version.lock_version += 1
    
    db.commit()
    db.refresh(version)
    
    # Audit log (conditional based on autosave policy)
    if not save_data.is_autosave or (save_data.is_autosave and version.lock_version % 10 == 0):
        # Log manual saves always, autosaves every 10th time
        AuditLogger.log(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="VERSION_SAVED" if not save_data.is_autosave else "VERSION_AUTOSAVED",
            entity_type="DocumentVersion",
            entity_id=version.id,
            description=f"{'Saved' if not save_data.is_autosave else 'Auto-saved'} version {version.version_number} content",
            details={
                "before": before_snapshot,
                "after": {
                    "content_hash": version.content_hash,
                    "updated_at": version.updated_at.isoformat()
                },
                "is_autosave": save_data.is_autosave,
                "lock_version": version.lock_version
            }
        )
    
    return _prepare_version_response(db, version, current_user)


def _prepare_version_response(db: Session, version: DocumentVersion, current_user: User) -> DocumentVersionResponse:
    """Helper to prepare version response with additional metadata"""
    response = DocumentVersionResponse.from_orm(version)
    
    # Add creator info
    if version.created_by:
        response.created_by_username = version.created_by.username
        response.created_by_full_name = version.created_by.full_name
    
    # Add approver info
    if version.approved_by:
        response.approved_by_username = version.approved_by.username
        response.approved_by_full_name = version.approved_by.full_name
    
    # Add lock info
    lock = db.query(EditLock).filter(
        EditLock.document_version_id == version.id
    ).first()
    
    if lock and not lock.is_expired():
        response.is_locked = True
        response.locked_by_user_id = lock.user_id
        response.locked_by_username = lock.user.username if lock.user else None
        response.lock_expires_at = lock.expires_at
    
    return response


def _compute_next_version_string(parent_version_string: str, change_type: ChangeType) -> str:
    """
    Compute next semantic version string based on change type
    
    Args:
        parent_version_string: Current version (e.g., "v1.0", "v1.1", "v2.3", "v1")
        change_type: MINOR or MAJOR (enum or string)
        
    Returns:
        Next version string (e.g., "v1.1", "v2.0") - always in vX.Y format
    """
    # Normalize change_type to handle both enum and string values
    if isinstance(change_type, str):
        change_type_str = change_type
    else:
        change_type_str = change_type.value if hasattr(change_type, 'value') else str(change_type)
    
    # Normalize parent_version_string - ensure it has both major and minor
    version_str = parent_version_string.lstrip('v')
    version_parts = version_str.split('.')
    
    # Parse major version
    try:
        major = int(version_parts[0])
    except (ValueError, IndexError):
        major = 1  # Default to 1 if we can't parse
    
    # Parse minor version (default to 0 if missing)
    if len(version_parts) > 1:
        try:
            minor = int(version_parts[1])
        except ValueError:
            minor = 0
    else:
        minor = 0
    
    # Compare using string value to ensure correct comparison
    is_major = (change_type_str == "Major" or 
                change_type_str == ChangeType.MAJOR.value or
                change_type_str == "MAJOR")
    
    if is_major:
        # Major change: increment major, reset minor to 0
        return f"v{major + 1}.0"
    else:
        # Minor change: keep major, increment minor
        return f"v{major}.{minor + 1}"


@router.get("/{document_id}/versions/history", response_model=List[DocumentVersionListItem])
async def get_version_history_tree(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int
):
    """
    Get full version history tree for a document
    
    Returns all versions including obsolete ones, ordered by version number descending.
    Useful for displaying complete version history with parent-child relationships.
    """
    # Check document exists
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get all versions
    versions = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id
    ).options(
        joinedload(DocumentVersion.created_by),
        joinedload(DocumentVersion.approved_by)
    ).order_by(DocumentVersion.version_number.desc()).all()
    
    # Prepare response
    version_items = [
        DocumentVersionListItem(
            id=v.id,
            document_id=v.document_id,
            version_number=v.version_number,
            version_string=v.version_string,
            status=v.status,
            change_summary=v.change_summary,
            change_reason=v.change_reason,
            change_type=v.change_type,
            is_latest=v.is_latest,
            effective_date=v.effective_date,
            obsolete_date=v.obsolete_date,
            created_by_id=v.created_by_id,
            created_by_username=v.created_by.username if v.created_by else None,
            approved_by_username=v.approved_by.username if v.approved_by else None,
            created_at=v.created_at,
            updated_at=v.updated_at
        )
        for v in versions
    ]
    
    return version_items


@router.post("/{document_id}/versions/{version_id}/create-new", response_model=DocumentVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_new_version_from_existing(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    request_data: CreateNewVersionRequest
):
    """
    Create a new version from an existing Effective version
    
    This is the main versioning endpoint that:
    1. Clones content from the current Effective version
    2. Creates a new Draft version with incremented version number
    3. Maintains parent-child relationship
    4. Does NOT obsolete the current version (obsolescence happens on approval)
    
    Requires: Author (owner) or Admin
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
    
    # Check permissions
    if not can_create_version(current_user, document):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create versions for this document"
        )
    
    # Get parent version (must be Effective)
    parent_version = db.query(DocumentVersion).filter(
        DocumentVersion.id == version_id,
        DocumentVersion.document_id == document_id
    ).first()
    
    if not parent_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent version not found"
        )
    
    # Validate parent version is Effective
    if parent_version.status != VersionStatus.EFFECTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only create new version from Effective versions. Current status: {parent_version.status.value}"
        )
    
    # Check if there's already a Draft version
    existing_draft = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id,
        DocumentVersion.status == VersionStatus.DRAFT
    ).first()
    
    if existing_draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A draft version already exists. Please complete or delete it before creating a new version."
        )
    
    # Validate and normalize change_type
    if not request_data.change_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="change_type is required (Minor or Major)"
        )
    
    # Ensure change_type is the enum value
    if isinstance(request_data.change_type, str):
        # Convert string to enum
        if request_data.change_type.lower() == "major":
            change_type_enum = ChangeType.MAJOR
        elif request_data.change_type.lower() == "minor":
            change_type_enum = ChangeType.MINOR
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid change_type: {request_data.change_type}. Must be 'Minor' or 'Major'"
            )
    else:
        change_type_enum = request_data.change_type
    
    # Normalize parent version_string to ensure it's in vX.Y format
    parent_version_string = parent_version.version_string or "v1.0"
    # If parent version_string is malformed (e.g., "v1" instead of "v1.0"), normalize it
    if parent_version_string and not '.' in parent_version_string.lstrip('v'):
        # It's missing the minor version (e.g., "v1" -> "v1.0")
        version_num = parent_version_string.lstrip('v')
        try:
            major = int(version_num)
            parent_version_string = f"v{major}.0"
        except ValueError:
            # If we can't parse it, default to v1.0
            parent_version_string = "v1.0"
    
    # Compute next version string based on change type
    next_version_string = _compute_next_version_string(
        parent_version_string,
        change_type_enum
    )
    
    # Get next sequential version number
    next_version_number = get_next_version_number(db, document_id)
    
    # Clone content from parent
    cloned_content = parent_version.content_html
    content_hash = compute_content_hash(cloned_content or "")
    
    # Create new version
    new_version = DocumentVersion(
        document_id=document_id,
        version_number=next_version_number,
        version_string=next_version_string,
        parent_version_id=parent_version.id,
        is_latest=True,
        content_html=cloned_content,
        content_hash=content_hash,
        change_reason=request_data.change_reason,
        change_type=change_type_enum,
        status=VersionStatus.DRAFT,
        attachments_metadata=parent_version.attachments_metadata or [],
        created_by_id=current_user.id
    )
    
    db.add(new_version)
    db.flush()  # Get version ID
    
    # Mark parent version as no longer latest (but still Effective)
    parent_version.is_latest = False
    
    # Update document's current version to this new draft
    document.current_version_id = new_version.id
    document.status = VersionStatus.DRAFT.value
    document.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(new_version)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="NEW_VERSION_CREATED",
        entity_type="DocumentVersion",
        entity_id=new_version.id,
        description=f"Created new version {next_version_string} from parent {parent_version.version_string} for document {document.document_number}",
        details={
            "document_id": document_id,
            "document_number": document.document_number,
            "parent_version_id": parent_version.id,
            "parent_version_string": parent_version.version_string,
            "new_version_string": next_version_string,
            "change_type": change_type_enum.value,
            "change_reason": request_data.change_reason,
        }
    )
    
    return _prepare_version_response(db, new_version, current_user)


# ==================== WORKFLOW ENDPOINTS ====================

@router.post("/{document_id}/versions/{version_id}/submit", response_model=DocumentVersionResponse)
async def submit_for_review(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    request_data: SubmitForReviewRequest
):
    """
    Submit document version for review (Draft → Under Review)
    
    Requires: Author or Admin + Password for E-Signature
    """
    # Verify e-signature (password)
    verify_esignature(current_user, request_data.password)
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
    
    # Check permissions - Author or Admin
    if not (current_user.has_role("Author") or current_user.is_admin()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Authors and Admins can submit for review"
        )
    
    # Check status
    if version.status != VersionStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only submit Draft versions. Current status: {version.status.value}"
        )
    
    # Update status
    version.status = VersionStatus.UNDER_REVIEW
    version.submitted_at = datetime.utcnow()
    version.submitted_by_id = current_user.id
    
    # Update signatory tokens - fill "Prepared By" section
    if version.content_html:
        # Always reload user with roles to ensure we have the data
        prepared_user = db.query(User).options(joinedload(User.roles)).filter(User.id == current_user.id).first()
        
        if not prepared_user:
            prepared_user = current_user  # Fallback to current_user if query fails
        
        # Update only Prepared By tokens at this step
        updated_content = update_all_signatory_tokens(
            version.content_html,
            prepared_user=prepared_user,
            prepared_date=version.submitted_at
        )
        # Update content_html and content_hash (important for proper saving)
        version.content_html = updated_content
        version.content_hash = compute_content_hash(updated_content)
        version.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(version)
    
    # Audit log with e-signature
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="VERSION_SUBMITTED",
        entity_type="DocumentVersion",
        entity_id=version.id,
        description=f"E-Signature: {current_user.username} submitted version {version.version_number} of document {document.document_number} for review. Action authenticated with password (21 CFR Part 11 compliant)."
    )
    
    # Send email notification to reviewers
    from app.core.notification_dispatcher import notify_review_assigned
    try:
        await notify_review_assigned(db, document, version, current_user)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send review assignment notification: {str(e)}", exc_info=True)
    
    return _prepare_version_response(db, version, current_user)


@router.post("/{document_id}/versions/{version_id}/approve", response_model=DocumentVersionResponse)
async def approve_version(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    request_data: ApprovalRequest
):
    """
    Approve document version
    
    If Under Review → Pending Approval (Reviewer approval)
    If Pending Approval → Approved (Approver approval)
    
    Requires: Reviewer (for Under Review) or Approver (for Pending Approval) or Admin + Password for E-Signature
    """
    # Verify e-signature (password)
    verify_esignature(current_user, request_data.password)
    
    comments = request_data.comments
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
    
    # VALIDATION: Check if user has viewed content before allowing workflow action
    if requires_content_view(current_user, version):
        if not has_user_viewed_content(db, current_user.id, version_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must view the document content before performing this action. Please open and review the document first."
            )
    
    # Check permissions based on current status
    if version.status == VersionStatus.UNDER_REVIEW:
        # Reviewer or Admin can approve review
        if not (current_user.has_role("Reviewer") or current_user.is_admin()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Reviewers and Admins can approve review"
            )
        # Move to Pending Approval
        version.status = VersionStatus.PENDING_APPROVAL
        version.reviewed_at = datetime.utcnow()
        version.reviewed_by_id = current_user.id
        action_desc = "approved review"
        
        # Update signatory tokens - fill "Checked By" section while preserving "Prepared By"
        if version.content_html:
            # Get Prepared By user to preserve those tokens (with roles loaded)
            prepared_user = None
            if version.submitted_by_id:
                prepared_user = db.query(User).options(joinedload(User.roles)).filter(User.id == version.submitted_by_id).first()
            
            # Always reload current_user with roles to ensure we have the data
            checked_user = db.query(User).options(joinedload(User.roles)).filter(User.id == current_user.id).first()
            if not checked_user:
                checked_user = current_user  # Fallback to current_user if query fails
            
            # Update both Prepared and Checked tokens at once
            updated_content = update_all_signatory_tokens(
                version.content_html,
                prepared_user=prepared_user,
                prepared_date=version.submitted_at,
                checked_user=checked_user,
                checked_date=version.reviewed_at
            )
            # Update content_html and content_hash (important for proper saving)
            version.content_html = updated_content
            version.content_hash = compute_content_hash(updated_content)
            version.updated_at = datetime.utcnow()
        
    elif version.status == VersionStatus.PENDING_APPROVAL:
        # Approver or Admin can approve
        if not (current_user.has_role("Approver") or current_user.is_admin()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Approvers and Admins can approve document"
            )
        # Move to Approved
        version.status = VersionStatus.APPROVED
        version.approved_at = datetime.utcnow()
        version.approved_by_id = current_user.id
        action_desc = "approved document"
        
        # Update ALL signatory tokens when document is fully approved
        # This ensures Prepared By, Checked By, and Approved By are all filled
        if version.content_html:
            # Get all signatory users from the database (with roles loaded)
            # Get Prepared By user (submitted_by)
            prepared_user = None
            if version.submitted_by_id:
                prepared_user = db.query(User).options(joinedload(User.roles)).filter(User.id == version.submitted_by_id).first()
            
            # Get Checked By user (reviewed_by)
            checked_user = None
            if version.reviewed_by_id:
                checked_user = db.query(User).options(joinedload(User.roles)).filter(User.id == version.reviewed_by_id).first()
            
            # Always reload current_user with roles to ensure we have the data
            approved_user = db.query(User).options(joinedload(User.roles)).filter(User.id == current_user.id).first()
            if not approved_user:
                approved_user = current_user  # Fallback to current_user if query fails
            
            # Update all signatory tokens at once using the new function
            updated_content = update_all_signatory_tokens(
                version.content_html,
                prepared_user=prepared_user,
                prepared_date=version.submitted_at,
                checked_user=checked_user,
                checked_date=version.reviewed_at,
                approved_user=approved_user,
                approved_date=version.approved_at
            )
            # Update content_html and content_hash (important for proper saving)
            version.content_html = updated_content
            version.content_hash = compute_content_hash(updated_content)
            version.updated_at = datetime.utcnow()
        
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve version with status: {version.status.value}"
        )
    
    db.commit()
    db.refresh(version)
    
    # Audit log with e-signature
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="VERSION_APPROVED",
        entity_type="DocumentVersion",
        entity_id=version.id,
        description=f"E-Signature: {current_user.username} {action_desc} for version {version.version_number} of document {document.document_number}. Comments: {comments or 'None'}. Action authenticated with password (21 CFR Part 11 compliant)."
    )
    
    # Send email notifications based on workflow state
    from app.core.notification_dispatcher import notify_review_approved
    try:
        if version.status == VersionStatus.PENDING_APPROVAL:
            # Review was approved, notify approvers
            await notify_review_approved(db, document, version, current_user)
        elif version.status == VersionStatus.APPROVED:
            # Document was approved - no notification needed here
            # Publication notification will be sent when document is published
            pass
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send approval notification: {str(e)}", exc_info=True)
    
    return _prepare_version_response(db, version, current_user)


@router.post("/{document_id}/versions/{version_id}/reject", response_model=DocumentVersionResponse)
async def reject_version(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    request_data: ReviewRequest
):
    """
    Reject document version (return to Draft)
    
    Requires: Reviewer, Approver, or Admin + Password for E-Signature
    """
    # Verify e-signature (password)
    verify_esignature(current_user, request_data.password)
    
    reason = request_data.comments or "No reason provided"
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
    
    # VALIDATION: Check if user has viewed content before allowing workflow action
    if requires_content_view(current_user, version):
        if not has_user_viewed_content(db, current_user.id, version_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must view the document content before performing this action. Please open and review the document first."
            )
    
    # Check permissions - Reviewer, Approver, or Admin
    if not (current_user.has_role("Reviewer") or current_user.has_role("Approver") or current_user.is_admin()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Reviewers, Approvers, and Admins can reject documents"
        )
    
    # Check status - can only reject if Under Review or Pending Approval
    if version.status not in [VersionStatus.UNDER_REVIEW, VersionStatus.PENDING_APPROVAL]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject version with status: {version.status.value}"
        )
    
    # Return to Draft
    old_status = version.status.value
    version.status = VersionStatus.DRAFT
    version.rejected_at = datetime.utcnow()
    version.rejected_by_id = current_user.id
    
    db.commit()
    db.refresh(version)
    
    # Audit log with e-signature
    reason = request_data.comments or "No reason provided"
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="VERSION_REJECTED",
        entity_type="DocumentVersion",
        entity_id=version.id,
        description=f"E-Signature: {current_user.username} rejected version {version.version_number} of document {document.document_number}. Previous status: {old_status}. Reason: {reason}. Action authenticated with password (21 CFR Part 11 compliant)."
    )
    
    # Send email notification based on rejection type
    from app.core.notification_dispatcher import notify_review_rejected, notify_approval_rejected
    try:
        if old_status == "UNDER_REVIEW":
            # Review was rejected, notify author
            await notify_review_rejected(db, document, version, current_user, reason)
        elif old_status == "PENDING_APPROVAL":
            # Approval was rejected, notify author
            await notify_approval_rejected(db, document, version, current_user, reason)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send rejection notification: {str(e)}", exc_info=True)
    
    return _prepare_version_response(db, version, current_user)


@router.post("/{document_id}/versions/{version_id}/publish", response_model=DocumentVersionResponse)
async def publish_version(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    request_data: PublishRequest
):
    """
    Publish document version (Approved → Effective)
    
    This endpoint implements the controlled versioning logic:
    1. Changes status from APPROVED to EFFECTIVE
    2. Sets effective_date
    3. Finds any previous EFFECTIVE versions and marks them as OBSOLETE
    4. Updates version_string if needed (v0.x → v1.0 for first effective)
    5. Ensures only ONE version is EFFECTIVE at any time
    
    Requires: DMS_Admin only + Password for E-Signature
    """
    # Verify e-signature (password)
    verify_esignature(current_user, request_data.password)
    
    # Check permissions - Admin only
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only DMS Admins can publish documents"
        )
    
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
    
    # VALIDATION: Admin must view content before publishing
    if not has_user_viewed_content(db, current_user.id, version_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must view the document content before publishing. Please open and review the document first."
        )
    
    # Check status - must be Approved
    if version.status != VersionStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only publish Approved versions. Current status: {version.status.value}"
        )
    
    # OBSOLESCENCE LOGIC: Find and obsolete any previous EFFECTIVE versions
    previous_effective_versions = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id,
        DocumentVersion.status == VersionStatus.EFFECTIVE,
        DocumentVersion.id != version_id
    ).all()
    
    obsoleted_versions = []
    now = datetime.utcnow()
    
    for prev_version in previous_effective_versions:
        prev_version.status = VersionStatus.OBSOLETE
        prev_version.obsolete_date = now
        prev_version.replaced_by_version_id = version.id
        prev_version.is_latest = False
        obsoleted_versions.append({
            "id": prev_version.id,
            "version_string": prev_version.version_string,
            "effective_date": prev_version.effective_date.isoformat() if prev_version.effective_date else None
        })
    
    # Update version_string if this is the first effective version (from v0.x to v1.0)
    if version.version_string and version.version_string.startswith('v0.'):
        version.version_string = "v1.0"
    
    # Make this version EFFECTIVE
    version.status = VersionStatus.EFFECTIVE
    version.effective_date = request_data.effective_date or now
    version.published_at = now
    version.published_by_id = current_user.id
    version.is_latest = True
    
    # Update document current version
    document.current_version_id = version.id
    document.status = "EFFECTIVE"
    document.updated_at = now
    
    db.commit()
    db.refresh(version)
    db.refresh(document)
    
    # Audit log with e-signature
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="VERSION_PUBLISHED",
        entity_type="DocumentVersion",
        entity_id=version.id,
        description=f"E-Signature: {current_user.username} published version {version.version_string} of document {document.document_number} as EFFECTIVE. {len(obsoleted_versions)} previous version(s) marked as OBSOLETE. Action authenticated with password (21 CFR Part 11 compliant).",
        details={
            "version_string": version.version_string,
            "effective_date": version.effective_date.isoformat(),
            "obsoleted_versions": obsoleted_versions
        }
    )
    
    # Send email notifications
    from app.core.notification_dispatcher import notify_document_effective, notify_version_obsoleted
    try:
        # Notify all users that document is now effective
        await notify_document_effective(db, document, version)
        
        # Notify users about obsoleted versions
        for prev_version in previous_effective_versions:
            await notify_version_obsoleted(db, document, prev_version, version)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send publication notification: {str(e)}", exc_info=True)
    
    return _prepare_version_response(db, version, current_user)


@router.post("/{document_id}/versions/{version_id}/mark-viewed", status_code=status.HTTP_200_OK)
async def mark_version_as_viewed(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int
):
    """
    Mark document version as viewed by the current user
    This endpoint is called when user opens the document editor/viewer
    Required before performing workflow actions (approve, reject, publish)
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
    
    # Mark as viewed
    view_record = mark_content_as_viewed(db, current_user.id, document_id, version_id)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="VERSION_VIEWED",
        entity_type="DocumentVersion",
        entity_id=version.id,
        description=f"User {current_user.username} viewed version {version.version_number} of document {document.document_number}",
        details={
            "document_id": document_id,
            "version_id": version_id,
            "viewed_at": view_record.viewed_at.isoformat()
        }
    )
    
    return {
        "message": "Document version marked as viewed",
        "viewed_at": view_record.viewed_at.isoformat()
    }


@router.post("/{document_id}/versions/{version_id}/archive", response_model=DocumentVersionResponse)
async def archive_version(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_id: int,
    version_id: int,
    request_data: PublishRequest
):
    """
    Archive document version
    
    Requires: DMS_Admin only + Password for E-Signature
    """
    # Verify e-signature (password)
    verify_esignature(current_user, request_data.password)
    
    # Check permissions - Admin only
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only DMS Admins can archive documents"
        )
    
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
    
    # Archive
    old_status = version.status.value
    version.status = VersionStatus.ARCHIVED
    version.archived_at = datetime.utcnow()
    version.archived_by_id = current_user.id
    
    # Update document status if this is current version
    if document.current_version_id == version.id:
        document.status = "ARCHIVED"
    
    db.commit()
    db.refresh(version)
    db.refresh(document)
    
    # Audit log with e-signature
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="VERSION_ARCHIVED",
        entity_type="DocumentVersion",
        entity_id=version.id,
        description=f"E-Signature: {current_user.username} archived version {version.version_number} of document {document.document_number}. Previous status: {old_status}. Action authenticated with password (21 CFR Part 11 compliant)."
    )
    
    return _prepare_version_response(db, version, current_user)


