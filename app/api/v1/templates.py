"""
Template Management API Endpoints
Handles template upload, workflow, review, approval, and publishing
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import os
import shutil

from app.api.deps import get_db, get_current_user, get_client_ip, get_user_agent
from app.models import User, Template, TemplateVersion, TemplateReview, TemplateApproval, TemplateStatus
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    TemplateVersionResponse,
    TemplateVersionListResponse,
    TemplateVersionDetailResponse,
    TemplateReviewCreate,
    TemplateReviewResponse,
    TemplateApprovalCreate,
    TemplateApprovalResponse,
    SubmitForReviewRequest,
    SubmitForApprovalRequest,
    PublishTemplateRequest,
    TemplateUsageResponse,
    TemplateValidationRequest,
    TemplateValidationResponse,
)
from app.utils.template_converter import (
    convert_docx_to_html,
    validate_required_headings,
    get_template_storage_paths,
)
from app.core.audit import AuditLogger
from app.core.security import verify_password

router = APIRouter()


def can_upload_template(user: User) -> bool:
    """Check if user can upload templates (Author or Admin)"""
    return user.has_role("Author") or user.is_admin()


def can_review_template(user: User) -> bool:
    """Check if user can review templates"""
    return user.has_role("Reviewer") or user.is_admin()


def can_approve_template(user: User) -> bool:
    """Check if user can approve templates"""
    return user.has_role("Approver") or user.is_admin()


@router.post("/upload", response_model=TemplateVersionResponse, status_code=status.HTTP_201_CREATED)
async def upload_template(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request,
    file: UploadFile = File(...),
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    department: Optional[str] = None,
    owner_id: Optional[int] = None,
):
    """
    Upload a DOCX template file
    
    Creates a new Template and TemplateVersion in DRAFT status
    Requires: Author or Admin
    """
    # Check permissions
    if not can_upload_template(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Authors and Admins can upload templates"
        )
    
    # Validate file type
    if not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .docx files are allowed"
        )
    
    # Determine owner
    owner_id = owner_id if owner_id else current_user.id
    if owner_id != current_user.id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create templates for other users"
        )
    
    # Get template name from filename if not provided
    template_name = name or file.filename.replace('.docx', '')
    
    # Create template
    template = Template(
        name=template_name,
        description=description,
        category=category,
        department=department,
        owner_id=owner_id,
        created_by_id=current_user.id,
    )
    db.add(template)
    db.flush()  # Get template ID
    
    # Get next version number
    existing_versions = db.query(TemplateVersion).filter(
        TemplateVersion.template_id == template.id
    ).count()
    version_number = existing_versions + 1
    
    # Get storage paths
    storage_paths = get_template_storage_paths(template.id, version_number)
    
    # Save DOCX file
    os.makedirs(os.path.dirname(storage_paths["originals"]), exist_ok=True)
    with open(storage_paths["originals"], "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Convert DOCX to HTML
    try:
        html_content, image_map = convert_docx_to_html(
            storage_paths["originals"],
            storage_paths["previews"],
            storage_paths["images"]
        )
    except Exception as e:
        # Clean up saved file on error
        if os.path.exists(storage_paths["originals"]):
            os.remove(storage_paths["originals"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting DOCX to HTML: {str(e)}"
        )
    
    # Create template version
    template_version = TemplateVersion(
        template_id=template.id,
        version_number=version_number,
        docx_file_path=storage_paths["originals"],
        preview_html_path=storage_paths["previews"],
        status=TemplateStatus.DRAFT,
        created_by_id=current_user.id,
    )
    db.add(template_version)
    db.commit()
    db.refresh(template_version)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="TEMPLATE_UPLOADED",
        entity_type="Template",
        entity_id=template.id,
        description=f"Uploaded template '{template_name}' version {version_number}",
        details={
            "template_id": template.id,
            "template_version_id": template_version.id,
            "version_number": version_number,
            "filename": file.filename,
        },
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    # Prepare response
    response = TemplateVersionResponse.from_orm(template_version)
    response.created_by_username = current_user.username
    
    return response


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    name: Optional[str] = None,
    category: Optional[str] = None,
    department: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    List templates with filters
    
    All authenticated users can list templates
    """
    query = db.query(Template).filter(Template.is_deleted == False)
    
    # Apply filters
    if name:
        query = query.filter(Template.name.ilike(f"%{name}%"))
    if category:
        query = query.filter(Template.category == category)
    if department:
        query = query.filter(Template.department == department)
    
    # Count total
    total = query.count()
    
    # Paginate
    templates = query.options(
        joinedload(Template.owner),
        joinedload(Template.created_by)
    ).order_by(Template.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    # Prepare responses
    template_responses = []
    for template in templates:
        response = TemplateResponse.from_orm(template)
        response.owner_username = template.owner.username if template.owner else None
        response.owner_full_name = template.owner.full_name if template.owner else None
        response.created_by_username = template.created_by.username if template.created_by else None
        response.version_count = len(template.versions)
        template_responses.append(response)
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return TemplateListResponse(
        items=template_responses,
        total=total,
        page=page,
        size=page_size,
        pages=total_pages
    )


@router.get("/published", response_model=List[TemplateResponse])
async def list_published_templates(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List only published templates (for document creation)
    
    Returns templates that have at least one published version
    """
    # Get templates with published versions
    # Explicitly specify the join condition to avoid ambiguous foreign key error
    templates = db.query(Template).join(
        TemplateVersion, Template.id == TemplateVersion.template_id
    ).filter(
        Template.is_deleted == False,
        TemplateVersion.status == TemplateStatus.PUBLISHED
    ).options(
        joinedload(Template.owner),
        joinedload(Template.created_by)
    ).distinct().all()
    
    # Prepare responses
    template_responses = []
    for template in templates:
        response = TemplateResponse.from_orm(template)
        response.owner_username = template.owner.username if template.owner else None
        response.owner_full_name = template.owner.full_name if template.owner else None
        response.created_by_username = template.created_by.username if template.created_by else None
        response.version_count = len(template.versions)
        
        # Find the published version ID for this template
        published_version = db.query(TemplateVersion).filter(
            TemplateVersion.template_id == template.id,
            TemplateVersion.status == TemplateStatus.PUBLISHED
        ).order_by(TemplateVersion.version_number.desc()).first()
        
        if published_version:
            response.current_published_version_id = published_version.id
        
        template_responses.append(response)
    
    return template_responses


@router.get("/{template_id}/versions", response_model=TemplateVersionListResponse)
async def list_template_versions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int,
    page: int = 1,
    page_size: int = 20,
):
    """
    List all versions of a template
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    query = db.query(TemplateVersion).filter(
        TemplateVersion.template_id == template_id
    )
    
    total = query.count()
    
    versions = query.options(
        joinedload(TemplateVersion.created_by)
    ).order_by(TemplateVersion.version_number.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    version_responses = []
    for version in versions:
        response = TemplateVersionResponse.from_orm(version)
        response.created_by_username = version.created_by.username if version.created_by else None
        version_responses.append(response)
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return TemplateVersionListResponse(
        items=version_responses,
        total=total,
        page=page,
        size=page_size,
        pages=total_pages
    )


@router.get("/{template_id}/versions/{version_id}", response_model=TemplateVersionDetailResponse)
async def get_template_version(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int,
    version_id: int,
):
    """
    Get template version details with reviews and approvals
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    version = db.query(TemplateVersion).options(
        joinedload(TemplateVersion.created_by),
        joinedload(TemplateVersion.reviews).joinedload(TemplateReview.reviewer),
        joinedload(TemplateVersion.approvals).joinedload(TemplateApproval.approver)
    ).filter(
        TemplateVersion.id == version_id,
        TemplateVersion.template_id == template_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template version not found"
        )
    
    response = TemplateVersionDetailResponse.from_orm(version)
    response.created_by_username = version.created_by.username if version.created_by else None
    
    # Add reviews
    from app.schemas.template import TemplateReviewResponse
    response.reviews = [
        TemplateReviewResponse(
            id=r.id,
            template_version_id=r.template_version_id,
            reviewer_id=r.reviewer_id,
            reviewer_username=r.reviewer.username if r.reviewer else None,
            reviewer_full_name=r.reviewer.full_name if r.reviewer else None,
            comment=r.comment,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in version.reviews
    ]
    
    # Add approvals
    from app.schemas.template import TemplateApprovalResponse
    response.approvals = [
        TemplateApprovalResponse(
            id=a.id,
            template_version_id=a.template_version_id,
            approver_id=a.approver_id,
            approver_username=a.approver.username if a.approver else None,
            approver_full_name=a.approver.full_name if a.approver else None,
            decision=a.decision,
            comment=a.comment,
            created_at=a.created_at,
        )
        for a in version.approvals
    ]
    
    return response


@router.post("/{template_id}/versions/{version_id}/submit-for-review", response_model=TemplateVersionResponse)
async def submit_for_review(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request,
    template_id: int,
    version_id: int,
    validation: Optional[TemplateValidationRequest] = None,
):
    """
    Submit template version for review
    
    Validates required headings if provided
    Requires: Author (owner) or Admin
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    version = db.query(TemplateVersion).filter(
        TemplateVersion.id == version_id,
        TemplateVersion.template_id == template_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template version not found"
        )
    
    # Check permissions
    if not can_upload_template(current_user) or (template.owner_id != current_user.id and not current_user.is_admin()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to submit this template for review"
        )
    
    # Check status
    if version.status != TemplateStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit template version with status: {version.status}"
        )
    
    # Validate headings if required
    if validation and validation.required_headings:
        if not os.path.exists(version.preview_html_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Template HTML preview not found"
            )
        
        with open(version.preview_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        is_valid, missing = validate_required_headings(html_content, validation.required_headings)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template validation failed. Missing required headings: {', '.join(missing)}",
            )
    
    # Update status
    version.status = TemplateStatus.UNDER_REVIEW
    version.submitted_for_review_at = datetime.utcnow()
    version.submitted_for_review_by_id = current_user.id
    db.commit()
    db.refresh(version)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="TEMPLATE_SUBMITTED_FOR_REVIEW",
        entity_type="TemplateVersion",
        entity_id=version.id,
        description=f"Submitted template '{template.name}' version {version.version_number} for review",
        details={
            "template_id": template.id,
            "template_version_id": version.id,
        },
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    response = TemplateVersionResponse.from_orm(version)
    response.created_by_username = version.created_by.username if version.created_by else None
    
    return response


@router.post("/{template_id}/versions/{version_id}/reviews", response_model=TemplateReviewResponse, status_code=status.HTTP_201_CREATED)
async def add_review_comment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request,
    template_id: int,
    version_id: int,
    review_in: TemplateReviewCreate,
):
    """
    Add a review comment to a template version
    
    Requires: Reviewer or Admin
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    version = db.query(TemplateVersion).filter(
        TemplateVersion.id == version_id,
        TemplateVersion.template_id == template_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template version not found"
        )
    
    # Check permissions
    if not can_review_template(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Reviewers and Admins can add review comments"
        )
    
    # Check status
    if version.status != TemplateStatus.UNDER_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add review comment to template version with status: {version.status}"
        )
    
    # Create review
    review = TemplateReview(
        template_version_id=version_id,
        reviewer_id=current_user.id,
        comment=review_in.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="TEMPLATE_REVIEW_COMMENT_ADDED",
        entity_type="TemplateReview",
        entity_id=review.id,
        description=f"Added review comment to template '{template.name}' version {version.version_number}",
        details={
            "template_id": template.id,
            "template_version_id": version.id,
            "comment": review_in.comment[:100],  # First 100 chars
        },
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    response = TemplateReviewResponse.from_orm(review)
    response.reviewer_username = current_user.username
    response.reviewer_full_name = current_user.full_name
    
    return response


@router.post("/{template_id}/versions/{version_id}/submit-for-approval", response_model=TemplateVersionResponse)
async def submit_for_approval(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request,
    template_id: int,
    version_id: int,
    validation: Optional[TemplateValidationRequest] = None,
):
    """
    Submit template version for approval
    
    Validates required headings if provided
    Requires: Reviewer or Admin
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    version = db.query(TemplateVersion).filter(
        TemplateVersion.id == version_id,
        TemplateVersion.template_id == template_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template version not found"
        )
    
    # Check permissions
    if not can_review_template(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Reviewers and Admins can submit templates for approval"
        )
    
    # Check status
    if version.status != TemplateStatus.UNDER_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit template version with status: {version.status} for approval"
        )
    
    # Validate headings if required
    if validation and validation.required_headings:
        if not os.path.exists(version.preview_html_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Template HTML preview not found"
            )
        
        with open(version.preview_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        is_valid, missing = validate_required_headings(html_content, validation.required_headings)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template validation failed. Missing required headings: {', '.join(missing)}",
            )
    
    # Update status
    version.status = TemplateStatus.PENDING_APPROVAL
    version.submitted_for_approval_at = datetime.utcnow()
    version.submitted_for_approval_by_id = current_user.id
    db.commit()
    db.refresh(version)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="TEMPLATE_SUBMITTED_FOR_APPROVAL",
        entity_type="TemplateVersion",
        entity_id=version.id,
        description=f"Submitted template '{template.name}' version {version.version_number} for approval",
        details={
            "template_id": template.id,
            "template_version_id": version.id,
        },
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    response = TemplateVersionResponse.from_orm(version)
    response.created_by_username = version.created_by.username if version.created_by else None
    
    return response


@router.post("/{template_id}/versions/{version_id}/approve", response_model=TemplateApprovalResponse)
async def approve_template(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request,
    template_id: int,
    version_id: int,
    approval_in: TemplateApprovalCreate,
):
    """
    Approve or reject a template version
    
    Requires: Approver or Admin
    Requires password for e-signature
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    version = db.query(TemplateVersion).filter(
        TemplateVersion.id == version_id,
        TemplateVersion.template_id == template_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template version not found"
        )
    
    # Check permissions
    if not can_approve_template(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Approvers and Admins can approve templates"
        )
    
    # Check status
    if version.status != TemplateStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve template version with status: {version.status}"
        )
    
    # Verify password for e-signature
    if not verify_password(approval_in.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password. E-signature authentication failed."
        )
    
    # Create approval record
    import json
    e_signature_data = json.dumps({
        "approver_id": current_user.id,
        "approver_username": current_user.username,
        "timestamp": datetime.utcnow().isoformat(),
        "ip_address": get_client_ip(request),
        "user_agent": get_user_agent(request),
    })
    
    approval = TemplateApproval(
        template_version_id=version_id,
        approver_id=current_user.id,
        decision=approval_in.decision,
        comment=approval_in.comment,
        e_signature_data=e_signature_data,
    )
    db.add(approval)
    
    # Update version status
    if approval_in.decision == "Approved":
        version.status = TemplateStatus.PUBLISHED
        version.published_at = datetime.utcnow()
        version.published_by_id = current_user.id
        
        # Update template's current published version
        template.current_published_version_id = version_id
    else:
        version.status = TemplateStatus.REJECTED
        version.rejected_at = datetime.utcnow()
        version.rejected_by_id = current_user.id
        version.rejection_reason = approval_in.comment
    
    db.commit()
    db.refresh(approval)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action=f"TEMPLATE_{approval_in.decision.upper()}",
        entity_type="TemplateApproval",
        entity_id=approval.id,
        description=f"{approval_in.decision} template '{template.name}' version {version.version_number}",
        details={
            "template_id": template.id,
            "template_version_id": version.id,
            "decision": approval_in.decision,
            "comment": approval_in.comment[:100] if approval_in.comment else None,
        },
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    response = TemplateApprovalResponse.from_orm(approval)
    response.approver_username = current_user.username
    response.approver_full_name = current_user.full_name
    
    return response


@router.post("/{template_id}/versions/{version_id}/publish", response_model=TemplateVersionResponse)
async def publish_template(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request,
    template_id: int,
    version_id: int,
):
    """
    Publish a template version (if already approved)
    
    Requires: Approver or Admin
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    version = db.query(TemplateVersion).filter(
        TemplateVersion.id == version_id,
        TemplateVersion.template_id == template_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template version not found"
        )
    
    # Check permissions
    if not can_approve_template(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Approvers and Admins can publish templates"
        )
    
    # Check status - must be approved
    if version.status != TemplateStatus.PUBLISHED:
        # Check if there's an approval
        approval = db.query(TemplateApproval).filter(
            TemplateApproval.template_version_id == version_id,
            TemplateApproval.decision == "Approved"
        ).first()
        
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template version must be approved before publishing"
            )
        
        # Update status
        version.status = TemplateStatus.PUBLISHED
        version.published_at = datetime.utcnow()
        version.published_by_id = current_user.id
    
    # Update template's current published version
    template.current_published_version_id = version_id
    db.commit()
    db.refresh(version)
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="TEMPLATE_PUBLISHED",
        entity_type="TemplateVersion",
        entity_id=version.id,
        description=f"Published template '{template.name}' version {version.version_number}",
        details={
            "template_id": template.id,
            "template_version_id": version.id,
        },
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    response = TemplateVersionResponse.from_orm(version)
    response.created_by_username = version.created_by.username if version.created_by else None
    
    return response


@router.get("/{template_id}/versions/{version_id}/html", response_model=TemplateUsageResponse)
async def get_template_html(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int,
    version_id: int,
):
    """
    Get template HTML content for use in document creation
    
    Only published templates can be used
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    version = db.query(TemplateVersion).filter(
        TemplateVersion.id == version_id,
        TemplateVersion.template_id == template_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template version not found"
        )
    
    # Check if published
    if version.status != TemplateStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only published templates can be used to create documents"
        )
    
    # Check if this is a block-based template
    html_content = ""
    if template.template_type == 'block_builder' and version.template_data:
        # Generate HTML from blocks
        blocks = version.template_data.get('blocks', [])
        if blocks:
            # Sort blocks by order
            sorted_blocks = sorted(blocks, key=lambda b: b.get('order', 0))
            # Concatenate HTML from all blocks
            html_content = ''.join(block.get('html', '') for block in sorted_blocks)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Template blocks not found"
            )
    else:
        # DOCX-based template: read from preview_html_path
        if not version.preview_html_path or not os.path.exists(version.preview_html_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Template HTML preview not found"
            )
        
        with open(version.preview_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="TEMPLATE_USED_FOR_DOCUMENT",
        entity_type="TemplateVersion",
        entity_id=version.id,
        description=f"Used template '{template.name}' version {version.version_number} to create document",
        details={
            "template_id": template.id,
            "template_version_id": version.id,
        },
    )
    
    # Get required metadata fields from template config
    required_metadata_fields = []
    if version.template_data and version.template_data.get('config'):
        config = version.template_data.get('config', {})
        required_metadata_fields = config.get('required_metadata_fields', [])
    
    return TemplateUsageResponse(
        template_id=template.id,
        template_version_id=version.id,
        template_name=template.name,
        html_content=html_content,
        required_metadata_fields=required_metadata_fields,
    )


@router.get("/{template_id}/images/{filename}")
async def get_template_image(
    template_id: int,
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Serve template images with access control.
    
    - Restricts lookup to the specific template's image directory.
    - Enforces ownership/admin access.
    - Blocks directory traversal.
    """
    # Prevent traversal
    if Path(filename).name != filename or '..' in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )
    
    # Validate template and permissions
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    if not (current_user.is_admin() or template.owner_id == current_user.id or template.created_by_id == current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this template"
        )
    
    base_dir = Path("storage") / "templates" / str(template_id) / "images"
    image_path = (base_dir / filename).resolve()
    
    # Ensure resolved path remains within base_dir
    if base_dir.resolve() not in image_path.parents and base_dir.resolve() != image_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )
    
    if image_path.exists() and image_path.is_file():
        return FileResponse(image_path)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Image not found"
    )

