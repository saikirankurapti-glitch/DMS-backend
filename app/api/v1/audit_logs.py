"""
Audit Log API Endpoints
Provides read-only access to audit logs for compliance officers and admins
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.audit_log import AuditLogListResponse
from app.models.audit_log import AuditLog
from app.models.user import User
from app.api.deps import require_admin

router = APIRouter()


@router.get("", response_model=AuditLogListResponse, summary="Get Audit Logs")
def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    username: Optional[str] = Query(None, description="Filter by username"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get audit logs with filtering and pagination (Admin only)
    
    **User Story: US-9.1**
    As a Compliance Officer, I want to see audit logs for actions like user creation, 
    deactivation, role change so that I can verify system integrity.
    
    **User Story: US-9.2**
    As an Admin, I want changes I make to be logged so that we maintain regulatory compliance.
    
    This endpoint provides comprehensive audit trail for FDA 21 CFR Part 11 compliance.
    """
    # Base query
    query = db.query(AuditLog)
    
    # Apply filters
    if action:
        query = query.filter(AuditLog.action == action)
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if username:
        query = query.filter(AuditLog.username.ilike(f"%{username}%"))
    
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    # Order by timestamp descending (most recent first)
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    logs = query.offset(offset).limit(page_size).all()
    
    return AuditLogListResponse(
        logs=logs,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/actions", summary="Get Available Actions")
def get_available_actions(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get list of all unique action types in the audit log
    Useful for building filters in the UI
    """
    actions = db.query(AuditLog.action).distinct().all()
    return {"actions": [action[0] for action in actions]}


@router.get("/entity-types", summary="Get Available Entity Types")
def get_available_entity_types(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get list of all unique entity types in the audit log
    Useful for building filters in the UI
    """
    entity_types = db.query(AuditLog.entity_type).distinct().all()
    return {"entity_types": [entity_type[0] for entity_type in entity_types]}


