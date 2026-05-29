"""
User Management API Endpoints
Admin-only endpoints for CRUD operations on users
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    PasswordReset,
)
from app.models.user import User
from app.models.role import Role
from app.core.security import get_password_hash
from app.core.audit import AuditLogger
from app.api.deps import require_admin, get_current_active_user, get_client_ip, get_user_agent

router = APIRouter()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create User")
def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Create a new user (Admin only)
    
    **User Story: US-1.1**
    As an Admin, I want to create new users so that they can access the DMS system.
    
    **User Story: US-1.2**
    As an Admin, I want to assign one or more roles during user creation so they get correct access.
    
    **Requirement: URS-7**
    System shall hash & securely store user passwords.
    """
    # Get client context
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Validate roles exist
    roles = db.query(Role).filter(Role.id.in_(user_data.role_ids)).all()
    if len(roles) != len(user_data.role_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more role IDs are invalid",
        )
    
    # Create user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        department=user_data.department,
        phone=user_data.phone,
        is_active=user_data.is_active,
        is_temp_password=False,  # Initial password is set by admin, not temp
    )
    
    # Assign roles
    new_user.roles = roles
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Audit log
    role_names = [role.name for role in roles]
    AuditLogger.log_user_created(
        db=db,
        admin_user_id=admin.id,
        admin_username=admin.username,
        new_user_id=new_user.id,
        new_username=new_user.username,
        roles=role_names,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return new_user


@router.get("", response_model=UserListResponse, summary="List Users")
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by username, email, or name"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get list of all users with filtering and pagination (Admin only)
    
    **User Story: US-2.1**
    As an Admin, I want to see all users so that I can manage them easily.
    
    **User Story: US-2.2**
    As an Admin, I want to filter users by role/status so that I can find the right user quickly.
    """
    # Base query
    query = db.query(User)
    
    # Apply filters
    if role:
        query = query.join(User.roles).filter(Role.name == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()
    
    return UserListResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=UserResponse, summary="Get User Details")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get user details by ID (Admin only)
    
    **User Story: US-10.2**
    As an Admin, I want to view a user's profile including roles and active status.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse, summary="Update User")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Update user information (Admin only)
    
    **User Story: US-3.1**
    As an Admin, I want to update user information so that user profiles stay current.
    
    **User Story: US-3.2**
    As an Admin, I want to modify a user's assigned roles so that I can change their responsibilities.
    """
    # Get client context
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Track changes for audit
    changes = {}
    
    # Update fields
    if user_data.email is not None and user_data.email != user.email:
        # Check email uniqueness
        existing = db.query(User).filter(User.email == user_data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        changes["email"] = {"old": user.email, "new": user_data.email}
        user.email = user_data.email
    
    if user_data.first_name is not None:
        changes["first_name"] = {"old": user.first_name, "new": user_data.first_name}
        user.first_name = user_data.first_name
    
    if user_data.last_name is not None:
        changes["last_name"] = {"old": user.last_name, "new": user_data.last_name}
        user.last_name = user_data.last_name
    
    if user_data.department is not None:
        changes["department"] = {"old": user.department, "new": user_data.department}
        user.department = user_data.department
    
    if user_data.phone is not None:
        changes["phone"] = {"old": user.phone, "new": user_data.phone}
        user.phone = user_data.phone
    
    if user_data.is_active is not None:
        changes["is_active"] = {"old": user.is_active, "new": user_data.is_active}
        user.is_active = user_data.is_active
    
    # Update roles
    if user_data.role_ids is not None:
        # Validate roles exist
        new_roles = db.query(Role).filter(Role.id.in_(user_data.role_ids)).all()
        if len(new_roles) != len(user_data.role_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more role IDs are invalid",
            )
        
        old_role_names = [role.name for role in user.roles]
        new_role_names = [role.name for role in new_roles]
        
        if set(old_role_names) != set(new_role_names):
            changes["roles"] = {"old": old_role_names, "new": new_role_names}
            user.roles = new_roles
    
    db.commit()
    db.refresh(user)
    
    # Audit log
    if changes:
        AuditLogger.log_user_updated(
            db=db,
            admin_user_id=admin.id,
            admin_username=admin.username,
            updated_user_id=user.id,
            updated_username=user.username,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    return user


@router.patch("/{user_id}/activate", response_model=UserResponse, summary="Activate User")
def activate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Activate a user account (Admin only)
    
    **User Story: US-4.2**
    As an Admin, I want to reactivate a user if needed so they can resume workflow activities.
    """
    # Get client context
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already active",
        )
    
    user.is_active = True
    db.commit()
    db.refresh(user)
    
    # Audit log
    AuditLogger.log_user_activated(
        db=db,
        admin_user_id=admin.id,
        admin_username=admin.username,
        activated_user_id=user.id,
        activated_username=user.username,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return user


@router.patch("/{user_id}/deactivate", response_model=UserResponse, summary="Deactivate User")
def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Deactivate a user account (Admin only)
    
    **User Story: US-4.1**
    As an Admin, I want to deactivate a user so that they cannot log in anymore.
    """
    # Get client context
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already inactive",
        )
    
    # Prevent admin from deactivating themselves
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )
    
    user.is_active = False
    db.commit()
    db.refresh(user)
    
    # Audit log
    AuditLogger.log_user_deactivated(
        db=db,
        admin_user_id=admin.id,
        admin_username=admin.username,
        deactivated_user_id=user.id,
        deactivated_username=user.username,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return user


@router.post("/{user_id}/reset-password", summary="Reset User Password")
def reset_user_password(
    user_id: int,
    password_data: PasswordReset,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Reset user password (Admin only)
    
    **User Story: US-8.1**
    As an Admin, I want to reset a user's password so that I can help them regain access.
    
    **User Story: US-8.2**
    As an Admin, I want password reset actions to be fully logged in the audit trail.
    
    **User Story: US-8.3**
    As an Admin, I want the system to enforce temporary/reset passwords (force first login password change).
    """
    # Get client context
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update password
    user.hashed_password = get_password_hash(password_data.new_password)
    user.is_temp_password = password_data.force_change
    
    db.commit()
    
    # Audit log
    AuditLogger.log_password_reset(
        db=db,
        admin_user_id=admin.id,
        admin_username=admin.username,
        target_user_id=user.id,
        target_username=user.username,
        force_change=password_data.force_change,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return {
        "message": "Password reset successfully",
        "requires_password_change": password_data.force_change,
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete User")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Delete a user (Admin only)
    
    Note: For compliance, consider deactivating users instead of deleting them.
    Deletion is permanent and may affect audit trail integrity.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Prevent admin from deleting themselves
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    
    # Get client context for audit
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Audit log before deletion
    AuditLogger.log(
        db=db,
        user_id=admin.id,
        username=admin.username,
        action="USER_DELETED",
        entity_type="User",
        entity_id=user.id,
        description=f"Deleted user '{user.username}'",
        details={"deleted_username": user.username, "deleted_user_email": user.email},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    db.delete(user)
    db.commit()
    
    return None


