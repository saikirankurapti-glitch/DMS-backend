"""
Role-Based Access Control (RBAC) utilities and decorators
"""
from enum import Enum
from typing import List, Optional


class RoleEnum(str, Enum):
    """
    Enumeration of available roles in the system
    """
    AUTHOR = "Author"
    REVIEWER = "Reviewer"
    APPROVER = "Approver"
    DMS_ADMIN = "DMS_Admin"


# Role capabilities mapping
ROLE_CAPABILITIES = {
    RoleEnum.DMS_ADMIN: [
        "user.create",
        "user.read",
        "user.update",
        "user.delete",
        "user.activate",
        "user.deactivate",
        "user.reset_password",
        "role.assign",
        "audit.view",
        "document.create",
        "document.read",
        "document.update",
        "document.delete",
        "document.publish",
        "document.archive",
        "document.approve",
        "document.review",
    ],
    RoleEnum.AUTHOR: [
        "document.create",
        "document.read",
        "document.update",
        "document.submit",
        "document.withdraw",
    ],
    RoleEnum.REVIEWER: [
        "document.read",
        "document.review",
        "document.comment",
        "document.suggest_changes",
    ],
    RoleEnum.APPROVER: [
        "document.read",
        "document.approve",
        "document.reject",
        "document.sign",
    ],
}


def has_permission(user_roles: List[str], required_permission: str) -> bool:
    """
    Check if any of the user's roles grant the required permission
    
    Args:
        user_roles: List of role names the user has
        required_permission: Permission string (e.g., "user.create")
        
    Returns:
        True if user has permission, False otherwise
    """
    for role_name in user_roles:
        try:
            role = RoleEnum(role_name)
            if required_permission in ROLE_CAPABILITIES.get(role, []):
                return True
        except ValueError:
            # Invalid role name
            continue
    
    return False


def has_any_role(user_roles: List[str], required_roles: List[str]) -> bool:
    """
    Check if user has any of the required roles
    
    Args:
        user_roles: List of role names the user has
        required_roles: List of required role names
        
    Returns:
        True if user has at least one required role
    """
    return any(role in required_roles for role in user_roles)


def is_admin(user_roles: List[str]) -> bool:
    """
    Check if user has DMS_Admin role
    
    Args:
        user_roles: List of role names the user has
        
    Returns:
        True if user is an admin
    """
    return RoleEnum.DMS_ADMIN.value in user_roles


def get_user_permissions(user_roles: List[str]) -> List[str]:
    """
    Get all permissions for a user based on their roles
    
    Args:
        user_roles: List of role names the user has
        
    Returns:
        List of all permissions the user has
    """
    permissions = set()
    
    for role_name in user_roles:
        try:
            role = RoleEnum(role_name)
            permissions.update(ROLE_CAPABILITIES.get(role, []))
        except ValueError:
            continue
    
    return list(permissions)


