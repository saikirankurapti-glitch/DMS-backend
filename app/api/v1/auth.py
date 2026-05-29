"""
Authentication API Endpoints
Handles login, logout, token management, and single session enforcement
"""
from datetime import datetime, timedelta
from typing import Union
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, Token, UserInfo, SessionConflictResponse
from app.models.user import User
from app.core.security import verify_password, create_access_token
from app.core.audit import AuditLogger
from app.api.deps import get_current_active_user, get_current_user, get_client_ip, get_user_agent
from app.config import settings

router = APIRouter()


@router.post("/login", response_model=Union[Token, SessionConflictResponse], summary="User Login")
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    User login endpoint with single session enforcement
    
    **User Story: US-5.1**
    As a User, I want to log in with my username and password so that I can access the system.
    
    **Single Session Enforcement:**
    - If user already has an active session, returns session_conflict response
    - Use force_login=true to override existing session and log out other devices/tabs
    
    Returns JWT access token on successful authentication.
    """
    # Get client context
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Find user by username
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user:
        # Log failed login attempt
        AuditLogger.log_login_failed(
            db=db,
            username=login_data.username,
            reason="User not found",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        # Log failed login attempt
        AuditLogger.log_login_failed(
            db=db,
            username=login_data.username,
            reason="Invalid password",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Check if user is active
    if not user.is_active:
        AuditLogger.log_login_failed(
            db=db,
            username=login_data.username,
            reason="Account inactive",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Check for existing active session (single session enforcement)
    if user.active_session_token and not login_data.force_login:
        # There's an existing session - return conflict response
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "session_conflict": True,
                "message": "Another session is already active",
                "existing_session_created_at": user.session_created_at.isoformat() if user.session_created_at else None,
                "detail": "You are already logged in from another device/tab. Do you want to end that session and continue here?"
            }
        )
    
    # If force_login, log the session override
    if login_data.force_login and user.active_session_token:
        AuditLogger.log(
            db=db,
            user_id=user.id,
            username=user.username,
            action="SESSION_OVERRIDE",
            entity_type="User",
            entity_id=user.id,
            description=f"User {user.username} overrode existing session from new device/tab",
            details={
                "previous_session_created_at": user.session_created_at.isoformat() if user.session_created_at else None,
                "new_ip_address": ip_address,
                "new_user_agent": user_agent
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    # Update last login timestamp
    user.last_login = datetime.utcnow()
    
    # Create access token
    role_names = [role.name for role in user.roles]
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "roles": role_names,
        }
    )
    
    # Store active session token
    user.active_session_token = access_token
    user.session_created_at = datetime.utcnow()
    db.commit()
    
    # Log successful login
    AuditLogger.log_login(
        db=db,
        user_id=user.id,
        username=user.username,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=role_names,
            is_active=user.is_active,
        ),
        requires_password_change=user.is_temp_password,
    )


@router.get("/me", response_model=UserInfo, summary="Get Current User Profile")
def get_my_profile(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current user's profile information
    
    **User Story: US-10.1**
    As a User, I want to see my own profile so that I can confirm my account details.
    """
    role_names = [role.name for role in current_user.roles]
    
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        roles=role_names,
        is_active=current_user.is_active,
    )


@router.post("/logout", summary="User Logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    User logout endpoint
    
    Clears the active session token from the database.
    """
    # Clear the active session
    current_user.active_session_token = None
    current_user.session_created_at = None
    db.commit()
    
    # Log logout
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="USER_LOGOUT",
        entity_type="User",
        entity_id=current_user.id,
        description=f"User {current_user.username} logged out",
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return {"message": "Successfully logged out"}


@router.get("/validate-session", summary="Validate Current Session")
def validate_session(
    request: Request,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Validate if the current session token is still active.
    
    Used by frontend to detect when session has been invalidated
    (e.g., user logged in from another device).
    
    Returns:
    - valid: true if session is still active
    - valid: false if session has been invalidated
    """
    if not authorization or not authorization.startswith("Bearer "):
        return {"valid": False, "reason": "No token provided"}
    
    token = authorization.replace("Bearer ", "")
    
    # Try to get the current user from the token
    try:
        from app.core.security import decode_access_token
        payload = decode_access_token(token)
        if not payload:
            return {"valid": False, "reason": "Invalid token"}
        
        username = payload.get("sub")
        user_id = payload.get("user_id")
        
        if not username or not user_id:
            return {"valid": False, "reason": "Invalid token data"}
        
        # Get user and check if token matches active session
        user = db.query(User).filter(
            User.id == user_id,
            User.username == username
        ).first()
        
        if not user:
            return {"valid": False, "reason": "User not found"}
        
        if not user.is_active:
            return {"valid": False, "reason": "Account inactive"}
        
        # Check if this token matches the active session
        if user.active_session_token != token:
            return {
                "valid": False, 
                "reason": "Session invalidated",
                "message": "Your session has been ended because you logged in from another device/tab."
            }
        
        return {"valid": True}
        
    except Exception as e:
        return {"valid": False, "reason": str(e)}
