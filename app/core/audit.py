"""
Audit logging utilities for compliance tracking
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogger:
    """
    Utility class for creating audit log entries
    Supports FDA 21 CFR Part 11 compliance requirements
    """
    
    @staticmethod
    def log(
        db: Session,
        user_id: Optional[int],
        username: str,
        action: str,
        entity_type: str,
        entity_id: Optional[int],
        description: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Create an audit log entry
        
        Args:
            db: Database session
            user_id: ID of user performing action (None for system actions)
            username: Username of user performing action
            action: Action code (e.g., "USER_CREATED", "USER_DEACTIVATED")
            entity_type: Type of entity affected (e.g., "User", "Document")
            entity_id: ID of affected entity
            description: Human-readable description of the action
            details: Additional structured data (JSON)
            ip_address: IP address of the user
            user_agent: User agent string
            
        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        return audit_log
    
    @staticmethod
    def log_user_created(
        db: Session,
        admin_user_id: int,
        admin_username: str,
        new_user_id: int,
        new_username: str,
        roles: list,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log user creation event"""
        return AuditLogger.log(
            db=db,
            user_id=admin_user_id,
            username=admin_username,
            action="USER_CREATED",
            entity_type="User",
            entity_id=new_user_id,
            description=f"Created user '{new_username}' with roles: {', '.join(roles)}",
            details={"new_username": new_username, "roles": roles},
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    @staticmethod
    def log_user_updated(
        db: Session,
        admin_user_id: int,
        admin_username: str,
        updated_user_id: int,
        updated_username: str,
        changes: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log user update event"""
        return AuditLogger.log(
            db=db,
            user_id=admin_user_id,
            username=admin_username,
            action="USER_UPDATED",
            entity_type="User",
            entity_id=updated_user_id,
            description=f"Updated user '{updated_username}'",
            details={"updated_username": updated_username, "changes": changes},
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    @staticmethod
    def log_user_deactivated(
        db: Session,
        admin_user_id: int,
        admin_username: str,
        deactivated_user_id: int,
        deactivated_username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log user deactivation event"""
        return AuditLogger.log(
            db=db,
            user_id=admin_user_id,
            username=admin_username,
            action="USER_DEACTIVATED",
            entity_type="User",
            entity_id=deactivated_user_id,
            description=f"Deactivated user '{deactivated_username}'",
            details={"deactivated_username": deactivated_username},
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    @staticmethod
    def log_user_activated(
        db: Session,
        admin_user_id: int,
        admin_username: str,
        activated_user_id: int,
        activated_username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log user activation event"""
        return AuditLogger.log(
            db=db,
            user_id=admin_user_id,
            username=admin_username,
            action="USER_ACTIVATED",
            entity_type="User",
            entity_id=activated_user_id,
            description=f"Activated user '{activated_username}'",
            details={"activated_username": activated_username},
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    @staticmethod
    def log_password_reset(
        db: Session,
        admin_user_id: int,
        admin_username: str,
        target_user_id: int,
        target_username: str,
        force_change: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log password reset event"""
        return AuditLogger.log(
            db=db,
            user_id=admin_user_id,
            username=admin_username,
            action="PASSWORD_RESET",
            entity_type="User",
            entity_id=target_user_id,
            description=f"Reset password for user '{target_username}' (force_change={force_change})",
            details={"target_username": target_username, "force_change": force_change},
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    @staticmethod
    def log_login(
        db: Session,
        user_id: int,
        username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log successful login event"""
        return AuditLogger.log(
            db=db,
            user_id=user_id,
            username=username,
            action="USER_LOGIN",
            entity_type="User",
            entity_id=user_id,
            description=f"User '{username}' logged in",
            details={},
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    @staticmethod
    def log_login_failed(
        db: Session,
        username: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log failed login attempt"""
        return AuditLogger.log(
            db=db,
            user_id=None,
            username=username,
            action="LOGIN_FAILED",
            entity_type="User",
            entity_id=None,
            description=f"Failed login attempt for '{username}': {reason}",
            details={"reason": reason},
            ip_address=ip_address,
            user_agent=user_agent,
        )


