"""
Notification Dispatcher
Event-driven notification system for workflow transitions
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.models import User, Document, DocumentVersion
from app.models.notification_log import NotificationEventType
from app.core.email_service import send_email
from app.core.email_templates import (
    review_assigned_template,
    review_rejected_template,
    review_approved_template,
    approval_assigned_template,
    approval_rejected_template,
    document_effective_template,
    version_obsoleted_template,
)
from app.config import settings

logger = logging.getLogger(__name__)


def get_users_by_role(db: Session, role_name: str) -> List[User]:
    """Get all users with a specific role"""
    return db.query(User).join(User.roles).filter(
        User.is_active == True,
        User.roles.any(name=role_name)
    ).options(joinedload(User.roles)).all()


def get_document_url(document_id: int, version_id: Optional[int] = None) -> str:
    """Generate document URL for email links"""
    base_url = settings.BACKEND_CORS_ORIGINS[0] if settings.BACKEND_CORS_ORIGINS else "http://localhost:3000"
    if version_id:
        return f"{base_url}/documents/{document_id}?version={version_id}"
    return f"{base_url}/documents/{document_id}"


async def notify_review_assigned(
    db: Session,
    document: Document,
    version: DocumentVersion,
    author: User
) -> None:
    """Notify reviewers that a document has been assigned for review"""
    logger.info(f"notify_review_assigned called for document {document.id}, version {version.id}")
    
    if not settings.EMAIL_ENABLED:
        logger.warning("Email notifications are disabled in settings")
        return
    
    # Get all active reviewers
    reviewers = get_users_by_role(db, "Reviewer")
    logger.info(f"Found {len(reviewers)} reviewers with Reviewer role")
    
    if not reviewers:
        logger.warning(f"No reviewers found to notify for document {document.id}")
        return
    
    reviewer_emails = [r.email for r in reviewers if r.email]
    if not reviewer_emails:
        logger.warning(f"No reviewer emails found for document {document.id}. Reviewers: {[r.username for r in reviewers]}")
        return
    
    logger.info(f"Sending review assignment emails to: {reviewer_emails}")
    
    # Send email to each reviewer
    for reviewer in reviewers:
        if not reviewer.email:
            continue
        
        subject = f"New Document Pending for Review: {document.document_number}"
        html_body = review_assigned_template(
            document_number=document.document_number,
            document_title=document.title,
            version_number=version.version_string or f"v{version.version_number}",
            author_name=author.full_name or author.username,
            reviewer_name=reviewer.full_name or reviewer.username,
            document_url=get_document_url(document.id, version.id),
            change_summary=version.change_summary
        )
        
        result = await send_email(
            to=[reviewer.email],
            subject=subject,
            html_body=html_body,
            db=db,
            document_id=document.id,
            version_id=version.id,
            event_type=NotificationEventType.REVIEW_ASSIGNED.value,
            recipient_user_id=reviewer.id
        )
        if result:
            logger.info(f"Email sent successfully to {reviewer.email}")
        else:
            logger.error(f"Failed to send email to {reviewer.email}")


async def notify_review_rejected(
    db: Session,
    document: Document,
    version: DocumentVersion,
    reviewer: User,
    rejection_reason: Optional[str] = None
) -> None:
    """Notify author that review was rejected"""
    if not settings.EMAIL_ENABLED:
        return
    
    # Get document author (owner or creator)
    author = document.owner or (db.query(User).filter(User.id == document.created_by_id).first() if document.created_by_id else None)
    
    if not author or not author.email:
        logger.warning(f"No author email found for document {document.id}")
        return
    
    subject = f"Document Review Rejected: {document.document_number}"
    html_body = review_rejected_template(
        document_number=document.document_number,
        document_title=document.title,
        version_number=version.version_string or f"v{version.version_number}",
        reviewer_name=reviewer.full_name or reviewer.username,
        author_name=author.full_name or author.username,
        rejection_reason=rejection_reason,
        document_url=get_document_url(document.id, version.id)
    )
    
    await send_email(
        to=[author.email],
        subject=subject,
        html_body=html_body,
        db=db,
        document_id=document.id,
        version_id=version.id,
        event_type=NotificationEventType.REVIEW_REJECTED.value,
        recipient_user_id=author.id
    )


async def notify_review_approved(
    db: Session,
    document: Document,
    version: DocumentVersion,
    reviewer: User
) -> None:
    """Notify approvers that review was approved"""
    if not settings.EMAIL_ENABLED:
        return
    
    # Get all active approvers
    approvers = get_users_by_role(db, "Approver")
    
    if not approvers:
        logger.warning(f"No approvers found to notify for document {document.id}")
        return
    
    # Send email to each approver
    for approver in approvers:
        if not approver.email:
            continue
        
        subject = f"Document Pending for Approval: {document.document_number}"
        html_body = review_approved_template(
            document_number=document.document_number,
            document_title=document.title,
            version_number=version.version_string or f"v{version.version_number}",
            reviewer_name=reviewer.full_name or reviewer.username,
            approver_name=approver.full_name or approver.username,
            document_url=get_document_url(document.id, version.id)
        )
        
        await send_email(
            to=[approver.email],
            subject=subject,
            html_body=html_body,
            db=db,
            document_id=document.id,
            version_id=version.id,
            event_type=NotificationEventType.APPROVAL_ASSIGNED.value,
            recipient_user_id=approver.id
        )


async def notify_approval_rejected(
    db: Session,
    document: Document,
    version: DocumentVersion,
    approver: User,
    rejection_reason: Optional[str] = None
) -> None:
    """Notify author that approval was rejected"""
    if not settings.EMAIL_ENABLED:
        return
    
    # Get document author
    author = document.owner or (db.query(User).filter(User.id == document.created_by_id).first() if document.created_by_id else None)
    
    if not author or not author.email:
        logger.warning(f"No author email found for document {document.id}")
        return
    
    subject = f"Document Approval Rejected: {document.document_number}"
    html_body = approval_rejected_template(
        document_number=document.document_number,
        document_title=document.title,
        version_number=version.version_string or f"v{version.version_number}",
        approver_name=approver.full_name or approver.username,
        author_name=author.full_name or author.username,
        rejection_reason=rejection_reason,
        document_url=get_document_url(document.id, version.id)
    )
    
    await send_email(
        to=[author.email],
        subject=subject,
        html_body=html_body,
        db=db,
        document_id=document.id,
        version_id=version.id,
        event_type=NotificationEventType.APPROVAL_REJECTED.value,
        recipient_user_id=author.id
    )


async def notify_document_effective(
    db: Session,
    document: Document,
    version: DocumentVersion
) -> None:
    """Notify all related users that a document is now effective"""
    if not settings.EMAIL_ENABLED:
        return
    
    # Get all active users (or filter by department/role as needed)
    # For now, notify all active users - you can customize this based on your requirements
    users = db.query(User).filter(User.is_active == True).all()
    
    if not users:
        logger.warning(f"No users found to notify for document {document.id}")
        return
    
    effective_date = version.effective_date.strftime('%Y-%m-%d') if version.effective_date else "Immediately"
    
    # Send email to each user
    for user in users:
        if not user.email:
            continue
        
        subject = f"New Document Published: {document.document_number}"
        html_body = document_effective_template(
            document_number=document.document_number,
            document_title=document.title,
            version_number=version.version_string or f"v{version.version_number}",
            effective_date=effective_date,
            recipient_name=user.full_name or user.username,
            document_url=get_document_url(document.id, version.id)
        )
        
        await send_email(
            to=[user.email],
            subject=subject,
            html_body=html_body,
            db=db,
            document_id=document.id,
            version_id=version.id,
            event_type=NotificationEventType.DOCUMENT_EFFECTIVE.value,
            recipient_user_id=user.id
        )


async def notify_version_obsoleted(
    db: Session,
    document: Document,
    old_version: DocumentVersion,
    new_version: DocumentVersion
) -> None:
    """Notify users that a version has been obsoleted"""
    if not settings.EMAIL_ENABLED:
        return
    
    # Get all active users
    users = db.query(User).filter(User.is_active == True).all()
    
    if not users:
        return
    
    old_version_str = old_version.version_string or f"v{old_version.version_number}"
    new_version_str = new_version.version_string or f"v{new_version.version_number}"
    
    # Send email to each user
    for user in users:
        if not user.email:
            continue
        
        subject = f"Document Version Obsoleted: {document.document_number}"
        html_body = version_obsoleted_template(
            document_number=document.document_number,
            document_title=document.title,
            old_version=old_version_str,
            new_version=new_version_str,
            recipient_name=user.full_name or user.username,
            document_url=get_document_url(document.id, new_version.id)
        )
        
        await send_email(
            to=[user.email],
            subject=subject,
            html_body=html_body,
            db=db,
            document_id=document.id,
            version_id=old_version.id,
            event_type=NotificationEventType.VERSION_OBSOLETED.value,
            recipient_user_id=user.id
        )

